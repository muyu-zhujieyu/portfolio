"""
图谱入库模块
从抽取结果生成中文 nodes 和 links，写入 SQLite。
"""
import os
import json
from typing import List, Dict, Tuple
from datetime import datetime

# 导入数据库模型
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import (
    SessionLocal, engine, Base,
    Source, Corpus, EventSchema, Event, Evidence,
    MechanismTemplate, EventRelation, VersionLog, QARecord
)

# ── 中文节点颜色方案 ──
NODE_COLORS = {
    "故障事件": "#c41e3a",    # 红色
    "状态事件": "#e6a23c",    # 橙色
    "检测事件": "#409eff",    # 蓝色
    "维修事件": "#67c23a",    # 绿色
    "传播事件": "#8b5cf6",    # 紫色
    "证据事件": "#909399",    # 灰色
    "部件": "#1a3a5c",        # 深蓝
    "机理模板": "#00bcd4",    # 青色
}

# ── 中文关系类型映射 ──
RELATION_TYPE_MAP = {
    "导致": "导致",
    "先于": "先于",
    "由检测确认": "由检测确认",
    "由维修处理": "由维修处理",
    "具有证据": "具有证据",
    "匹配机理模板": "匹配机理模板",
    "演化为": "演化为",
    "由措施解决": "由措施解决",
    "由检测发现": "由检测发现",
}


def generate_graph_data(
    events: List[Dict],
    mechanism_results: Dict,
    evidence_records: List[Dict],
    merge_records: List[Dict]
) -> Dict:
    """从抽取的事件、模板校验结果和证据生成图谱数据（全部中文）"""

    nodes = []
    links = []
    categories = [
        {"name": "故障事件", "itemStyle": {"color": NODE_COLORS["故障事件"]}},
        {"name": "状态事件", "itemStyle": {"color": NODE_COLORS["状态事件"]}},
        {"name": "检测事件", "itemStyle": {"color": NODE_COLORS["检测事件"]}},
        {"name": "维修事件", "itemStyle": {"color": NODE_COLORS["维修事件"]}},
        {"name": "传播事件", "itemStyle": {"color": NODE_COLORS["传播事件"]}},
        {"name": "部件", "itemStyle": {"color": NODE_COLORS["部件"]}},
        {"name": "机理模板", "itemStyle": {"color": NODE_COLORS["机理模板"]}},
    ]

    event_ids_set = set()
    component_set = set()

    # ── 创建事件节点 ──
    for i, ev in enumerate(events):
        ev_id = ev["event_id"]
        event_ids_set.add(ev_id)

        label = ev.get("fault_mode") or ev.get("state") or ev.get("trigger", "")[:30]
        if not label:
            label = ev.get("event_type", "事件")

        component = ev.get("component")
        if component:
            component_set.add(component)

        nodes.append({
            "id": ev_id,
            "name": label,
            "label": f"{ev_id}\n{label}",
            "category": ev.get("event_type", "状态事件"),
            "symbolSize": 28 + (ev.get("confidence", 0.75) * 18),
            "itemStyle": {"color": NODE_COLORS.get(ev.get("event_type", ""), "#999")},
            "properties": {
                "事件ID": ev_id,
                "事件类型": ev.get("event_type", ""),
                "触发词": ev.get("trigger", ""),
                "部件": component or "",
                "故障模式": ev.get("fault_mode", ""),
                "异常状态": ev.get("state", ""),
                "检测方式": ev.get("inspection", ""),
                "维修动作": ev.get("action", ""),
                "置信度": ev.get("confidence", 0),
                "有效时间": ev.get("valid_time", ""),
                "来源文档": ev.get("source_id", ""),
            }
        })

    # ── 创建部件节点 ──
    for comp in component_set:
        nodes.append({
            "id": f"部件_{comp}",
            "name": comp,
            "label": comp,
            "category": "部件",
            "symbolSize": 22,
            "itemStyle": {"color": NODE_COLORS["部件"], "borderColor": "#1a3a5c", "borderWidth": 1},
            "properties": {"部件名称": comp}
        })

    # ── 创建事件和部件的关联边 ──
    for ev in events:
        comp = ev.get("component")
        if comp:
            links.append({
                "source": f"部件_{comp}",
                "target": ev["event_id"],
                "label": "发生位置",
                "relation_type": "发生位置",
                "lineStyle": {"type": "dotted", "color": "#b0bec5", "width": 1},
                "properties": {}
            })

    # ── 创建机理模板节点和关联边 ──
    template_results = mechanism_results.get("模板校验结果", [])
    for tr in template_results:
        tid = tr["template_id"]
        template_event_ids = tr.get("template_event_ids", [])

        nodes.append({
            "id": f"模板_{tid}",
            "name": tr["template_name"],
            "label": f"{tid}\n{tr['template_name']}",
            "category": "机理模板",
            "symbolSize": 40,
            "itemStyle": {"color": NODE_COLORS["机理模板"], "borderColor": "#00bcd4", "borderWidth": 2},
            "properties": {
                "模板ID": tid,
                "模板名称": tr["template_name"],
                "描述": tr.get("description", ""),
                "匹配类型": tr.get("match_type", ""),
                "完整度": tr.get("completeness", 0),
            }
        })

        # 创建从模板到事件的关联边
        for ev_id in template_event_ids:
            if ev_id in event_ids_set:
                links.append({
                    "source": f"模板_{tid}",
                    "target": ev_id,
                    "label": "匹配机理模板",
                    "relation_type": "匹配机理模板",
                    "lineStyle": {"type": "dashed", "color": "#00bcd4", "width": 1},
                    "properties": {"模板ID": tid}
                })

    # ── 创建事件间关系边（基于模板链中的事件顺序） ──
    relation_counter = 0
    for tr in template_results:
        matched_steps = tr.get("matched_steps", [])
        tid = tr["template_id"]

        # 按步骤排序
        sorted_steps = sorted(matched_steps, key=lambda s: s["step"])

        for i in range(len(sorted_steps) - 1):
            source_ev = sorted_steps[i]["event_id"]
            target_ev = sorted_steps[i + 1]["event_id"]

            if source_ev in event_ids_set and target_ev in event_ids_set:
                relation_counter += 1
                links.append({
                    "source": source_ev,
                    "target": target_ev,
                    "label": "导致",
                    "relation_type": "导致",
                    "template_id": tid,
                    "lineStyle": {"color": "#c41e3a", "width": 1.5},
                    "properties": {
                        "关系ID": f"REL{relation_counter:03d}",
                        "类型": "导致",
                        "模板ID": tid,
                        "置信度": 0.8
                    }
                })

    # ── 创建证据事件节点和关联边 ──
    for evd in evidence_records:
        ev_id = evd["event_id"]
        evidence_node_id = evd["evidence_id"]

        nodes.append({
            "id": evidence_node_id,
            "name": evd.get("evidence_span", "")[:30] or "证据",
            "label": evd.get("evidence_span", "")[:25] + ("..." if len(evd.get("evidence_span", "")) > 25 else ""),
            "category": "证据事件",
            "symbolSize": 15,
            "itemStyle": {"color": NODE_COLORS["证据事件"], "borderColor": "#909399", "borderWidth": 1},
            "properties": {
                "证据ID": evd["evidence_id"],
                "来源": evd.get("source_id", ""),
                "可靠性": evd.get("reliability", ""),
                "审查状态": evd.get("review_status", ""),
                "证据片段": evd.get("evidence_span", "")[:200],
            }
        })

        if ev_id in event_ids_set:
            links.append({
                "source": ev_id,
                "target": evidence_node_id,
                "label": "具有证据",
                "relation_type": "具有证据",
                "lineStyle": {"type": "dotted", "color": "#909399", "width": 0.5},
                "properties": {"可靠性": evd.get("reliability", "")}
            })

    return {
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "stats": {
            "总节点数": len(nodes),
            "总边数": len(links),
            "事件节点数": len(events),
            "部件节点数": len(component_set),
            "模板节点数": len(template_results),
            "证据节点数": len(evidence_records),
            "事件类型分布": _count_by(events, "event_type"),
            "关系类型分布": _count_by(links, "relation_type"),
        }
    }


def _count_by(items: List[Dict], key: str) -> Dict:
    """统计列表中某个字段的分布"""
    dist = {}
    for item in items:
        val = item.get(key, "未知")
        dist[val] = dist.get(val, 0) + 1
    return dist


def ingest_to_database(
    events: List[Dict],
    evidence_records: List[Dict],
    mechanism_results: Dict,
    sources: List[Dict]
) -> Dict:
    """
    将抽取结果写入 SQLite 数据库。
    清空旧数据并重新导入。
    """
    db = SessionLocal()

    try:
        # 清空所有表
        for table in [QARecord, VersionLog, EventRelation, Evidence, Event, EventSchema, MechanismTemplate, Corpus, Source]:
            db.query(table).delete()
        db.commit()

        # ── 1. 写入数据源 ──
        for src in sources:
            db.add(Source(
                source_id=src["source_id"],
                name=src.get("title", src.get("source_id", "")),
                doc_type=src.get("doc_type", ""),
                created_at=src.get("created_at", datetime.now().isoformat())
            ))

        # ── 2. 写入事件 Schema（中文） ──
        schema_types = [
            {"event_type": "故障事件", "label": "故障事件", "description": "液压系统中发生的故障，如泄漏、堵塞、卡滞、气蚀等",
             "slots": {"trigger": {}, "component": {}, "fault_mode": {"required": True}, "cause": {}},
             "domain_constraints": "故障模式必须在已知故障模式词典中", "range_constraints": "必须包含故障模式字段"},
            {"event_type": "状态事件", "label": "状态事件", "description": "故障导致的异常状态，如压力下降、油温升高、动作缓慢等",
             "slots": {"trigger": {}, "state": {"required": True}, "component": {}},
             "domain_constraints": "状态必须在已知异常状态词典中", "range_constraints": "必须包含state字段"},
            {"event_type": "检测事件", "label": "检测事件", "description": "对液压系统进行的检测和诊断活动",
             "slots": {"trigger": {}, "inspection": {"required": True}, "component": {}},
             "domain_constraints": "检测方法必须在已知检测方式词典中", "range_constraints": "必须包含inspection字段"},
            {"event_type": "维修事件", "label": "维修事件", "description": "对液压系统进行的维修和修复操作",
             "slots": {"trigger": {}, "action": {"required": True}, "component": {}},
             "domain_constraints": "维修动作必须在已知维修动作词典中", "range_constraints": "必须包含action字段"},
            {"event_type": "传播事件", "label": "传播事件", "description": "故障在系统内的传播和扩散",
             "slots": {"trigger": {}, "from_component": {}, "to_component": {}},
             "domain_constraints": "传播路径必须在合理范围内", "range_constraints": ""},
        ]
        for st in schema_types:
            db.add(EventSchema(**st))

        # ── 3. 写入事件 ──
        for ev in events:
            db.add(Event(
                event_id=ev["event_id"],
                event_type=ev.get("event_type", ""),
                trigger=ev.get("trigger", ""),
                component=ev.get("component", ""),
                fault_mode=ev.get("fault_mode"),
                state=ev.get("state"),
                cause=ev.get("cause"),
                action=ev.get("action"),
                valid_time=ev.get("valid_time", ""),
                observed_time=ev.get("observed_time", ""),
                confidence=ev.get("confidence", 0.75),
                version_status="active",
                template_id=ev.get("template_id"),
                template_step=ev.get("template_step")
            ))

        # ── 4. 写入证据 ──
        for evd in evidence_records:
            db.add(Evidence(
                evidence_id=evd["evidence_id"],
                event_id=evd["event_id"],
                source_id=evd.get("source_id", ""),
                paragraph_id=evd.get("sentence_id", ""),
                sentence_id=evd.get("sentence_id", ""),
                evidence_span=evd.get("evidence_span", ""),
                extractor=evd.get("extractor", "keyword_pattern_matcher"),
                reliability=evd.get("reliability", "中"),
                review_status="已确认" if evd.get("review_status") == "已确认" else "待审核"
            ))

        # ── 5. 写入机理模板（中文） ──
        from modules.mechanism_validator import MECHANISM_TEMPLATES
        for t in MECHANISM_TEMPLATES:
            db.add(MechanismTemplate(
                template_id=t["template_id"],
                name=t["name"],
                description=t["description"],
                chain=t["chain"],
                constraints=t.get("constraints", {})
            ))

        # ── 6. 写入事件关系 ──
        template_results = mechanism_results.get("模板校验结果", [])
        relation_counter = 0
        for tr in template_results:
            matched_steps = tr.get("matched_steps", [])
            tid = tr["template_id"]
            sorted_steps = sorted(matched_steps, key=lambda s: s["step"])

            for i in range(len(sorted_steps) - 1):
                relation_counter += 1
                db.add(EventRelation(
                    relation_id=f"REL{relation_counter:03d}",
                    source_event=sorted_steps[i]["event_id"],
                    relation_type="导致",
                    target_event=sorted_steps[i + 1]["event_id"],
                    template_id=tid,
                    confidence=0.80,
                    evidence_id=""
                ))

        db.commit()

        return {
            "状态": "成功",
            "数据源数量": len(sources),
            "事件数量": len(events),
            "证据数量": len(evidence_records),
            "模板数量": len(MECHANISM_TEMPLATES),
            "关系数量": relation_counter,
            "数据库路径": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kg.db")
        }

    except Exception as e:
        db.rollback()
        return {"状态": "失败", "错误": str(e)}
    finally:
        db.close()
