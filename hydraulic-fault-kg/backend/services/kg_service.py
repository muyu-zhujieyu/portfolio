"""知识图谱查询与可视化服务"""
import math
from typing import List, Dict
from sqlalchemy.orm import Session
from database import Event, Evidence, MechanismTemplate, EventRelation


# 颜色方案：按事件类型着色
EVENT_COLORS = {
    "FaultEvent": "#c41e3a",        # 红色
    "StateEvent": "#e6a23c",        # 橙色
    "InspectionEvent": "#409eff",   # 蓝色
    "MaintenanceEvent": "#67c23a",  # 绿色
    "PropagationEvent": "#909399",  # 灰色
    "EvidenceEvent": "#f56c6c",     # 浅红
}

# 机理模板节点颜色
TEMPLATE_COLOR = "#1a3a5c"  # 深蓝


def _get_evidence_for_events(db: Session, event_ids: List[str]) -> Dict[str, List[dict]]:
    """获取事件的证据映射"""
    evidence_map = {}  # type: Dict[str, List[dict]]
    for evd in db.query(Evidence).filter(Evidence.event_id.in_(event_ids)).all():
        if evd.event_id not in evidence_map:
            evidence_map[evd.event_id] = []
        evidence_map[evd.event_id].append({
            "evidence_id": evd.evidence_id,
            "source_id": evd.source_id,
            "evidence_span": evd.evidence_span,
            "reliability": evd.reliability,
            "review_status": evd.review_status
        })
    return evidence_map


def get_kg_graph(db: Session) -> dict:
    """返回完整的知识图谱数据（ECharts graph 格式）"""
    events = db.query(Event).all()
    relations = db.query(EventRelation).all()
    templates = db.query(MechanismTemplate).all()

    categories = [
        {"name": "FaultEvent", "itemStyle": {"color": EVENT_COLORS["FaultEvent"]}},
        {"name": "StateEvent", "itemStyle": {"color": EVENT_COLORS["StateEvent"]}},
        {"name": "InspectionEvent", "itemStyle": {"color": EVENT_COLORS["InspectionEvent"]}},
        {"name": "MaintenanceEvent", "itemStyle": {"color": EVENT_COLORS["MaintenanceEvent"]}},
        {"name": "PropagationEvent", "itemStyle": {"color": EVENT_COLORS["PropagationEvent"]}},
        {"name": "MechanismTemplate", "itemStyle": {"color": TEMPLATE_COLOR}},
    ]

    # 构建节点
    nodes = []
    event_ids_set = set()
    node_index = {}
    for i, ev in enumerate(events):
        ev_id = ev.event_id
        event_ids_set.add(ev_id)
        label = ev.fault_mode or ev.state or ev.trigger[:20] if ev.trigger else ev.event_type
        nodes.append({
            "id": ev_id,
            "name": label if label else ev_id,
            "label": f"{ev_id}\n{label}" if label else ev_id,
            "category": ev.event_type,
            "symbolSize": 30 + (ev.confidence or 0.8) * 20,
            "itemStyle": {"color": EVENT_COLORS.get(ev.event_type, "#999")},
            "properties": {
                "event_id": ev_id,
                "event_type": ev.event_type,
                "trigger": ev.trigger,
                "component": ev.component,
                "fault_mode": ev.fault_mode,
                "state": ev.state,
                "confidence": ev.confidence,
                "valid_time": ev.valid_time,
                "version_status": ev.version_status
            }
        })
        node_index[ev_id] = i

    # 添加机理模板节点
    for t in templates:
        tid = f"TEMPLATE_{t.template_id}"
        nodes.append({
            "id": tid,
            "name": t.template_id,
            "label": f"{t.template_id}\n{t.name}",
            "category": "MechanismTemplate",
            "symbolSize": 40,
            "itemStyle": {"color": TEMPLATE_COLOR, "borderColor": "#1a3a5c", "borderWidth": 2},
            "properties": {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description
            }
        })
        node_index[tid] = len(nodes) - 1

    # 构建边
    links = []
    for rel in relations:
        source = rel.source_event
        target = rel.target_event
        if source in event_ids_set and target in event_ids_set:
            link = {
                "source": source,
                "target": target,
                "label": rel.relation_type,
                "relation_type": rel.relation_type,
                "properties": {
                    "relation_id": rel.relation_id,
                    "confidence": rel.confidence,
                    "template_id": rel.template_id,
                    "evidence_id": rel.evidence_id
                }
            }
            # 传播关系用虚线
            if rel.relation_type in ("propagates_to", "worsen"):
                link["lineStyle"] = {"type": "dashed", "color": "#909399"}
            links.append(link)

    # 证据映射
    evidence_map = _get_evidence_for_events(db, list(event_ids_set))

    return {
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "evidence_map": evidence_map,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "total_event_nodes": len(events),
            "total_template_nodes": len(templates),
            "event_type_distribution": {
                et: len([n for n in nodes if n.get("category") == et])
                for et in EVENT_COLORS
            }
        }
    }


def get_event_detail(db: Session, event_id: str) -> dict:
    """获取单个事件的详细信息"""
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if not event:
        return {}

    # 证据列表
    evidence_list = []
    for evd in db.query(Evidence).filter(Evidence.event_id == event_id).all():
        evidence_list.append({
            "evidence_id": evd.evidence_id,
            "source_id": evd.source_id,
            "paragraph_id": evd.paragraph_id,
            "sentence_id": evd.sentence_id,
            "evidence_span": evd.evidence_span,
            "extractor": evd.extractor,
            "reliability": evd.reliability,
            "review_status": evd.review_status
        })

    # 作为 source 的关系
    relations_as_source = []
    for rel in db.query(EventRelation).filter(EventRelation.source_event == event_id).all():
        relations_as_source.append({
            "relation_id": rel.relation_id,
            "relation_type": rel.relation_type,
            "target_event": rel.target_event,
            "template_id": rel.template_id,
            "confidence": rel.confidence
        })

    # 作为 target 的关系
    relations_as_target = []
    for rel in db.query(EventRelation).filter(EventRelation.target_event == event_id).all():
        relations_as_target.append({
            "relation_id": rel.relation_id,
            "relation_type": rel.relation_type,
            "source_event": rel.source_event,
            "template_id": rel.template_id,
            "confidence": rel.confidence
        })

    return {
        "event": {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "trigger": event.trigger,
            "component": event.component,
            "fault_mode": event.fault_mode,
            "state": event.state,
            "cause": event.cause,
            "action": event.action,
            "valid_time": event.valid_time,
            "observed_time": event.observed_time,
            "confidence": event.confidence,
            "version_status": event.version_status,
            "template_id": event.template_id,
            "template_step": event.template_step
        },
        "evidence_list": evidence_list,
        "relations_as_source": relations_as_source,
        "relations_as_target": relations_as_target
    }


def get_evidence_for_event(db: Session, event_id: str) -> dict:
    """获取事件的证据锚定信息"""
    event = db.query(Event).filter(Event.event_id == event_id).first()
    evidence_list = []
    for evd in db.query(Evidence).filter(Evidence.event_id == event_id).all():
        evidence_list.append({
            "evidence_id": evd.evidence_id,
            "source_id": evd.source_id,
            "paragraph_id": evd.paragraph_id,
            "sentence_id": evd.sentence_id,
            "evidence_span": evd.evidence_span,
            "extractor": evd.extractor,
            "reliability": evd.reliability,
            "review_status": evd.review_status
        })
    return {"event_id": event_id, "evidence_list": evidence_list}


def get_chain_by_template(db: Session, template_id: str) -> dict:
    """按机理模板获取事件链"""
    template = db.query(MechanismTemplate).filter(
        MechanismTemplate.template_id == template_id
    ).first()
    if not template:
        return {}

    # 获取此模板相关的所有关系
    relations = db.query(EventRelation).filter(
        EventRelation.template_id == template_id
    ).all()

    # 收集所有涉及的事件
    event_ids = set()
    for rel in relations:
        event_ids.add(rel.source_event)
        event_ids.add(rel.target_event)

    # 按模板步骤排序
    events = []
    for ev_id in event_ids:
        ev = db.query(Event).filter(Event.event_id == ev_id).first()
        if ev:
            events.append({
                "event_id": ev.event_id,
                "event_type": ev.event_type,
                "trigger": ev.trigger,
                "component": ev.component,
                "fault_mode": ev.fault_mode,
                "state": ev.state,
                "template_step": ev.template_step,
                "confidence": ev.confidence
            })

    events.sort(key=lambda x: x.get("template_step") or 999)

    # 关系列表
    rel_list = [{
        "relation_id": rel.relation_id,
        "source_event": rel.source_event,
        "relation_type": rel.relation_type,
        "target_event": rel.target_event,
        "confidence": rel.confidence
    } for rel in relations]

    # 证据映射
    evidence_map = _get_evidence_for_events(db, list(event_ids))

    # 完整性
    chain_steps = template.chain if isinstance(template.chain, list) else []
    total_steps = len(chain_steps)
    matched_steps = len(set(e.get("template_step") for e in events if e.get("template_step")))
    completeness = matched_steps / total_steps if total_steps > 0 else 0

    return {
        "template_id": template.template_id,
        "template_name": template.name,
        "events": events,
        "relations": rel_list,
        "evidence_map": evidence_map,
        "is_complete": completeness >= 0.75,
        "completeness": round(completeness, 2)
    }
