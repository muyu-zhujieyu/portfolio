# -*- coding: utf-8 -*-
"""
数据库初始化脚本

运行方式：
    python init_db.py

功能：
    1. 创建所有 16 张数据表（调用 database.init_db）
    2. 从 data/source_registry.json 读取来源资料并写入 sources 表
    3. 将 data/raw_sources 下的样例文本解析为段落写入 paragraphs 表
    4. 将 data/dictionaries 下的词典数据写入 maintenance_rules / mechanism_templates 表
"""
import sys
import os
import json
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import (
    init_db, get_connection, fetch_all, fetch_one,
    execute_sql, get_all_tables, get_table_count
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def generate_id(prefix: str) -> str:
    """生成唯一ID"""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = str(uuid.uuid4())[:6]
    return f"{prefix}-{ts}-{rand}"


def import_sources():
    """从 data/source_registry.json 导入来源资料到 sources 表"""
    registry_path = os.path.join(BASE_DIR, "data", "source_registry.json")
    if not os.path.exists(registry_path):
        print(f"  [WARN] 来源登记文件不存在: {registry_path}")
        return 0

    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    conn = get_connection()
    count = 0
    for source in registry.get("sources", []):
        sid = source.get("source_id", "")
        if not sid:
            continue
        existing = fetch_one(
            "SELECT id FROM sources WHERE source_id = ?",
            (sid,)
        )
        if existing:
            continue

        # 安全方式获取值：将 dict 转为 (key_bytes, value) 列表，
        # 通过 UTF-8 字节匹配获取中文键对应的值，避免 Windows GBK 编码问题
        items = list(source.items())

        def get_val(target):
            """通过字节匹配查找 dict 中的值"""
            target_b = target.encode('utf-8')
            for k, v in items:
                if k.encode('utf-8') == target_b:
                    return v if v is not None else ""
            return ""

        conn.execute("""
            INSERT INTO sources
                (source_id, \"来源类型\", \"标题\", \"作者\", \"年份\", \"出版方\",
                 \"文件路径\", \"文档类型\", \"公开说明\", \"资料描述\")
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            get_val('source_id'),
            get_val('来源类型'),
            get_val('标题'),
            get_val('作者'),
            get_val('年份'),
            get_val('出版方'),
            get_val('文件路径'),
            get_val('文档类型'),
            get_val('公开说明'),
            get_val('资料描述'),
        ))
        count += 1

    conn.commit()
    return count


def import_sample_texts():
    """将 raw_sources 下的样例 .txt 解析为段落写入 paragraphs 表"""
    raw_dir = os.path.join(BASE_DIR, "data", "raw_sources")
    if not os.path.exists(raw_dir):
        print(f"  [WARN] 原始资料目录不存在: {raw_dir}")
        return 0

    conn = get_connection()
    count = 0

    sources = fetch_all("SELECT source_id, 文件路径 FROM sources")
    path_to_source = {s["文件路径"]: s["source_id"] for s in sources if s["文件路径"]}

    for root, dirs, files in os.walk(raw_dir):
        for filename in files:
            if not filename.endswith(".txt"):
                continue
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, BASE_DIR).replace("\\", "/")

            # 查找匹配的 source_id
            source_id = None
            for reg_path, sid in path_to_source.items():
                if rel_path == reg_path or filename in reg_path:
                    source_id = sid
                    break

            if source_id is None:
                for subdir in ["manuals", "papers", "textbooks", "component_docs", "cases"]:
                    if subdir in rel_path:
                        for reg_path, sid in path_to_source.items():
                            if subdir in reg_path:
                                source_id = sid
                                break
                        break

            if source_id is None:
                print(f"  [SKIP] 未找到匹配来源: {rel_path}")
                continue

            with open(filepath, encoding="utf-8") as f:
                content = f.read()

            paragraphs_raw = content.split("\n\n")
            paragraph_index = 0

            for para_text in paragraphs_raw:
                para_text = para_text.strip()
                if not para_text:
                    continue
                if para_text.startswith("====") and para_text.endswith("===="):
                    continue
                if len(para_text) < 10:
                    continue

                paragraph_index += 1
                para_id = f"PARA-{source_id}-{paragraph_index:04d}"

                existing = fetch_one(
                    "SELECT id FROM paragraphs WHERE paragraph_id = ?", (para_id,)
                )
                if existing:
                    continue

                conn.execute("""
                    INSERT INTO paragraphs
                        (paragraph_id, source_id, 段落序号, 段落内容, 字符数)
                    VALUES (?, ?, ?, ?, ?)
                """, (para_id, source_id, paragraph_index, para_text, len(para_text)))
                count += 1

    conn.commit()
    return count


def import_dictionaries():
    """从 data/dictionaries 导入维修规则和机理模板"""
    dict_dir = os.path.join(BASE_DIR, "data", "dictionaries")
    if not os.path.exists(dict_dir):
        print(f"  [WARN] 词典目录不存在: {dict_dir}")
        return

    conn = get_connection()

    # --- 维修规则 (maintenance_actions.json) ---
    actions_path = os.path.join(dict_dir, "maintenance_actions.json")
    if os.path.exists(actions_path):
        with open(actions_path, encoding="utf-8") as f:
            actions_data = json.load(f)

        for action in actions_data.get("maintenance_actions", []):
            existing = fetch_one(
                "SELECT id FROM maintenance_rules WHERE rule_id = ?",
                (action["action_id"],)
            )
            if existing:
                continue

            conn.execute("""
                INSERT INTO maintenance_rules
                    (rule_id, 规则名称, 故障模式, 适用条件, 维修方案,
                     所需工具, 所需材料, 操作步骤JSON, 参考来源)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action["action_id"],
                action["action_name"],
                ", ".join(action.get("applicable_faults", [])),
                ", ".join(action.get("applicable_components", [])),
                "; ".join(action.get("steps", [])),
                ", ".join(action.get("tools_required", [])),
                ", ".join(action.get("materials_required", [])),
                json.dumps(action.get("steps", []), ensure_ascii=False),
                action.get("quality_check", "")
            ))

    # --- 机理模板 (从 hydraulic_terms.json 故障模式生成) ---
    terms_path = os.path.join(dict_dir, "hydraulic_terms.json")
    if os.path.exists(terms_path):
        with open(terms_path, encoding="utf-8") as f:
            terms_data = json.load(f)

        fault_modes = terms_data.get("categories", {}).get("故障模式", {}).get("terms", [])
        limited = fault_modes[:15]
        for i, fault in enumerate(limited, 1):
            template_id = f"TMP-{i:03d}"
            existing = fetch_one(
                "SELECT id FROM mechanism_templates WHERE template_id = ?",
                (template_id,)
            )
            if existing:
                continue
            conn.execute("""
                INSERT INTO mechanism_templates
                    (template_id, 模板名称, 模板描述, 适用事件类型)
                VALUES (?, ?, ?, ?)
            """, (
                template_id,
                fault,
                f"液压系统{fault}的机理模板——描述{fault}的发生条件、演化过程和物理约束",
                "故障事件"
            ))

    conn.commit()
    print(f"  [OK] 词典数据已导入")


def init_metrics():
    """初始化构建质量评价指标"""
    conn = get_connection()
    default_metrics = [
        ("MET-001", "事件抽取准确率", None, "%", "事件抽取的正确率"),
        ("MET-002", "证据锚定覆盖率", None, "%", "有证据支撑的事件占比"),
        ("MET-003", "机理模板匹配率", None, "%", "匹配到机理模板的事件链占比"),
        ("MET-004", "事件归一冗余率", None, "%", "归一后消除的冗余事件占比"),
        ("MET-005", "问答引用准确率", None, "%", "问答中引用证据的准确率"),
        ("MET-006", "图谱节点完整度", None, "%", "图谱中属性完整的节点占比"),
        ("MET-007", "构建流程总耗时", None, "秒", "从文档解析到图谱入库的总耗时"),
        ("MET-008", "维修方案匹配率", None, "%", "故障模式匹配到维修规则的占比"),
    ]
    for m in default_metrics:
        existing = fetch_one("SELECT id FROM metrics WHERE metric_id = ?", (m[0],))
        if existing:
            continue
        conn.execute("""
            INSERT INTO metrics (metric_id, 指标名称, 指标值, 指标单位, 说明)
            VALUES (?, ?, ?, ?, ?)
        """, m)
    conn.commit()


def print_summary():
    """打印数据库摘要"""
    tables = get_all_tables()
    print("\n" + "=" * 50)
    print("  数据库状态摘要")
    print("=" * 50)
    for t in sorted(tables):
        count = get_table_count(t)
        print(f"  {t:30s}: {count:4d} 行")
    print("=" * 50)


# ================================================================
# 主入口
# ================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  液压故障知识图谱系统 - 数据库初始化")
    print("=" * 60)

    # 1. 创建表结构
    print("\n[1/5] 创建数据表...")
    init_db()

    # 2. 导入来源资料
    print("\n[2/5] 导入来源资料...")
    source_count = import_sources()
    print(f"  [OK] 已导入 {source_count} 条来源资料")

    # 3. 导入样例段落
    print("\n[3/5] 导入样例段落...")
    para_count = import_sample_texts()
    print(f"  [OK] 已导入 {para_count} 个段落")

    # 4. 导入词典数据
    print("\n[4/5] 导入词典数据...")
    import_dictionaries()

    # 5. 初始化评价指标
    print("\n[5/5] 初始化评价指标...")
    init_metrics()
    print("  [OK] 评价指标已初始化")

    # 打印摘要
    print_summary()
    print("\n  初始化完成！")
    print(f"  数据库路径: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kg.db')}")
