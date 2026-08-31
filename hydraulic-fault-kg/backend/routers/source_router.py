"""
来源资料路由 - 管理公开资料来源的登记、查看、文档解析、段落清洗和领域过滤

API:
  GET  /api/sources            获取所有公开资料来源列表
  GET  /api/sources/{id}       获取单个来源详情
  POST /api/sources/read       读取（解析）所有公开资料文档
  POST /api/sources/clean      对解析结果执行段落清洗
  POST /api/sources/filter     对清洗结果执行液压领域相关性过滤
  GET  /api/sources/filtered   获取已保存的过滤结果
"""
import json
import os
from typing import Dict
from fastapi import APIRouter
from services.source_reader_service import source_reader
from services.text_clean_service import text_cleaner
from services.domain_filter_service import domain_filter

router = APIRouter(prefix="/api/sources", tags=["来源资料"])


# ================================================================
# GET /api/sources - 获取所有公开资料来源
# ================================================================

@router.get("")
def list_sources():
    """获取所有公开资料来源列表（直接读source_registry.json）"""
    registry = source_reader.read_source_registry()
    return {
        "总数": len(registry.get("sources", [])),
        "来源列表": registry.get("sources", [])
    }


@router.post("/reload")
def reload_sources():
    """重新加载source_registry.json，清空旧sources表并写入全部资料"""
    from database import get_connection
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("DELETE FROM sources")
        conn.execute("DELETE FROM paragraphs")
        conn.execute("DELETE FROM filtered_paragraphs")
        registry = source_reader.read_source_registry()
        sources_list = registry.get("sources", [])
        count = 0
        for s in sources_list:
            conn.execute("""INSERT INTO sources (source_id,来源类型,标题,作者,年份,出版方,文件路径,文档类型,公开说明,资料描述)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (s.get("source_id"),s.get("来源类型"),s.get("标题"),s.get("作者",""),
                 s.get("年份"),s.get("出版方",""),s.get("文件路径"),s.get("文档类型"),
                 s.get("公开说明",""),s.get("资料描述","")))
            count += 1
        conn.commit()
        return {"状态":"成功","资料总数":count,"说明":"已清空旧sources/paragraphs/filtered_paragraphs并重新加载"}
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


# ================================================================
# POST /api/sources/read - 解析所有公开资料文档
# ================================================================

@router.post("/read")
def read_sources():
    """读取（解析）所有公开资料文档

    根据 source_registry.json 中的文件路径，
    解析 TXT/MD/PDF/DOCX 文档，输出统一结构的段落列表。

    返回:
        - 状态: 成功/失败
        - 来源总数: 登记的资料数量
        - 解析成功数: 成功解析的文档数
        - 解析失败数: 解析失败的文档数
        - 段落总数: 所有文档解析出的段落总数量
        - 解析结果: 每个来源的详细解析结果
    """
    result = source_reader.parse_all_sources()
    return result


# ================================================================
# POST /api/sources/clean - 对解析结果执行段落清洗
# ================================================================

@router.post("/clean")
def clean_sources():
    """对解析结果执行段落清洗

    清洗步骤（按顺序执行）:
      1. 去除空行和空白段落
      2. 去除页眉页脚类文本
      3. 去除目录类文本（章节编号模式）
      4. 去除参考文献类文本
      5. 去除过短段落（少于10字符）
      6. 去除重复段落

    返回:
        - 状态: 成功/失败
        - 原始段落数: 清洗前的总段落数
        - 清洗后段落数: 清洗后保留的段落数
        - 各步骤去除数量明细
        - 清洗后段落: 清洗后的段落列表
    """
    # 步骤1: 先解析
    parse_result = source_reader.parse_all_sources()
    if parse_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "文档解析失败，无法执行清洗", "详情": parse_result}

    # 步骤2: 再清洗
    clean_result = text_cleaner.clean_paragraphs(parse_result)
    return clean_result


# ================================================================
# POST /api/sources/filter - 液压领域相关性过滤（核心接口）
# ================================================================

@router.post("/filter")
def filter_sources(threshold: float = 0.02):
    """对清洗结果执行液压领域相关性过滤

    过滤流程:
      1. 解析所有公开资料文档
      2. 执行段落清洗（去空行、去重、去过短、去目录引用等）
      3. 基于液压领域术语词典和核心关键词计算相关度评分
      4. 保留相关度 >= 阈值的段落

    执行后自动:
      - 保存过滤结果到 data/processed/filtered_paragraphs.json
      - 写入 SQLite paragraphs 表和 filtered_paragraphs 表

    Args:
        threshold: 相关度阈值（0~1），默认 0.02

    返回:
        - 清洗后段落数: 清洗后保留的段落数
        - 液压相关段落数: 通过领域过滤的段落数
        - 过滤掉段落数: 被过滤掉的段落数
        - 过滤保留率: 液压相关段落数 / 清洗后段落数
        - 过滤后段落: 过滤后的段落列表（含相关度评分和匹配关键词）
    """
    # 步骤1: 解析
    parse_result = source_reader.parse_all_sources()
    if parse_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "文档解析失败", "详情": parse_result}

    # 步骤2: 清洗
    clean_result = text_cleaner.clean_paragraphs(parse_result)
    if clean_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "段落清洗失败", "详情": clean_result}

    # 步骤3: 领域过滤
    filter_result = domain_filter.filter_cleaned_paragraphs(clean_result, threshold)

    # 步骤4: 持久化保存
    _save_filtered_result(filter_result)

    # 步骤5: 写入数据库
    _write_to_database(parse_result, clean_result, filter_result)

    return filter_result


def _save_filtered_result(filter_result: Dict):
    """将过滤结果保存到 data/processed/filtered_paragraphs.json"""
    # 计算保存路径
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.dirname(current_dir)
    processed_dir = os.path.join(project_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    output_path = os.path.join(processed_dir, "filtered_paragraphs.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filter_result, f, ensure_ascii=False, indent=2)

    print(f"  [OK] 过滤结果已保存到: {output_path}")


def _write_to_database(parse_result: Dict, clean_result: Dict, filter_result: Dict):
    """将解析、清洗、过滤结果写入 SQLite 数据库"""
    from database import get_connection, fetch_one
    import uuid

    conn = get_connection()

    # 临时禁用外键约束，允许跨步骤写入
    conn.execute("PRAGMA foreign_keys = OFF")

    try:
        # 步骤1: 解析段落写入 paragraphs 表
        parse_results = parse_result.get("解析结果", [])
        para_count = 0
        para_id_set = set()  # 跟踪已插入的 paragraph_id

        for src_result in parse_results:
            if src_result.get("解析状态") != "成功":
                continue
            source_id = src_result.get("source_id", "")
            for para in src_result.get("段落列表", []):
                para_id = f"PARA-{source_id}-{para.get('段落编号', 0):04d}"
                if para_id in para_id_set:
                    continue
                para_id_set.add(para_id)

                existing = fetch_one(
                    "SELECT id FROM paragraphs WHERE paragraph_id = ?", (para_id,)
                )
                if existing:
                    continue

                conn.execute("""
                    INSERT INTO paragraphs (paragraph_id, source_id, 段落序号, 段落内容, 字符数)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    para_id,
                    source_id,
                    para.get("段落编号", 0),
                    para.get("原始文本", ""),
                    len(para.get("原始文本", ""))
                ))
                para_count += 1

        # 步骤2: 确保过滤后段落对应的 paragraph 存在（避免外键约束失败）
        # 过滤结果中的段落编号可能不同于原始解析编号，需要补充插入
        for fp in filter_result.get("过滤后段落", []):
            source_id = fp.get("source_id", "")
            para_id = f"PARA-{source_id}-{fp.get('段落编号', 0):04d}"
            if para_id not in para_id_set:
                para_id_set.add(para_id)
                existing = fetch_one(
                    "SELECT id FROM paragraphs WHERE paragraph_id = ?", (para_id,)
                )
                if not existing:
                    conn.execute("""
                        INSERT INTO paragraphs (paragraph_id, source_id, 段落序号, 段落内容, 字符数)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        para_id,
                        source_id,
                        fp.get("段落编号", 0),
                        fp.get("原始文本", ""),
                        len(fp.get("原始文本", ""))
                    ))
                    para_count += 1

        # 步骤3: 过滤后段落写入 filtered_paragraphs 表
        filtered_paragraphs = filter_result.get("过滤后段落", [])
        filtered_count = 0
        for fp in filtered_paragraphs:
            filtered_id = f"FILT-{uuid.uuid4().hex[:8]}"
            source_id = fp.get("source_id", "")
            para_id = f"PARA-{source_id}-{fp.get('段落编号', 0):04d}"

            conn.execute("""
                INSERT INTO filtered_paragraphs
                    (filtered_id, paragraph_id, source_id, 过滤后内容, 相关度评分, 过滤原因)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                filtered_id,
                para_id,
                source_id,
                fp.get("原始文本", ""),
                fp.get("相关度评分", 0.0),
                "液压领域相关性过滤"
            ))
            filtered_count += 1

        conn.commit()
    finally:
        # 恢复外键约束
        conn.execute("PRAGMA foreign_keys = ON")

    print(f"  [OK] 数据库已更新: paragraphs +{para_count}, filtered_paragraphs +{filtered_count}")


# ================================================================
# GET /api/sources/filtered - 获取已保存的过滤结果
# ================================================================

@router.get("/filtered")
def get_filtered_paragraphs():
    """获取已保存的液压领域过滤结果

    优先读取 data/processed/filtered_paragraphs.json，
    如文件不存在则从数据库 filtered_paragraphs 表读取。
    """
    # 尝试读取文件
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.dirname(current_dir)
    file_path = os.path.join(project_dir, "data", "processed", "filtered_paragraphs.json")

    if os.path.exists(file_path):
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)

    # 回退到数据库
    from database import fetch_all
    rows = fetch_all("SELECT * FROM filtered_paragraphs ORDER BY 过滤时间 DESC")
    return {
        "状态": "从数据库读取",
        "液压相关段落数": len(rows),
        "过滤后段落": rows
    }


# ================================================================
# GET /api/sources/{id} - 获取单个来源详情（须放在动态路由最后）
# ================================================================

@router.get("/{source_id}")
def get_source(source_id: str):
    """获取单个来源详情"""
    registry = source_reader.read_source_registry()
    for src in registry.get("sources", []):
        if src.get("source_id") == source_id:
            return src
    return {"错误": f"来源 {source_id} 不存在"}
