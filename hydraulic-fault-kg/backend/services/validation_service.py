"""液压机理模板校验服务"""
from typing import List, Dict
from sqlalchemy.orm import Session
from database import MechanismTemplate, Event, EventRelation


def get_all_templates(db: Session):  # type: (...) -> List[dict]
    """获取所有机理模板"""
    templates = db.query(MechanismTemplate).all()
    result = []
    for t in templates:
        chain = t.chain if isinstance(t.chain, list) else []
        constraints = t.constraints if isinstance(t.constraints, dict) else {}
        result.append({
            "template_id": t.template_id,
            "name": t.name,
            "description": t.description,
            "chain_length": len(chain),
            "chain_steps": [{
                "step": s.get("step"),
                "event_type": s.get("event_type"),
                "fault_mode": s.get("fault_mode"),
                "abnormal_state": s.get("abnormal_state"),
                "trigger_patterns": s.get("trigger_patterns", [])[:3]
            } for s in chain],
            "constraints": constraints
        })
    return result


def check_chain(db: Session, event_ids):  # type: (...) -> dict
    """检查给定的事件ID序列是否匹配某个机理模板"""
    # 获取所有事件
    events = {e.event_id: e for e in db.query(Event).filter(Event.event_id.in_(event_ids)).all()}

    # 如果只有一个事件ID，展开为完整链
    if len(event_ids) == 1:
        ev_id = event_ids[0]
        ev = db.query(Event).filter(Event.event_id == ev_id).first()
        if ev and ev.template_id:
            # 找到同一模板的所有事件
            related_events = db.query(Event).filter(Event.template_id == ev.template_id).all()
            event_ids = [e.event_id for e in related_events]
            events = {e.event_id: e for e in related_events}

    # 按template_step排序
    sorted_events = sorted(
        [events[eid] for eid in event_ids if eid in events],
        key=lambda x: x.template_step or 999
    )

    # 获取所有模板
    templates = db.query(MechanismTemplate).all()
    best_match = None
    best_score = 0

    for template in templates:
        chain = template.chain if isinstance(template.chain, list) else []
        score = 0
        total_steps = len(chain)
        matched_steps = []
        missing_steps = []
        violations = []

        for step in chain:
            step_num = step.get("step")
            expected_type = step.get("event_type")
            expected_fault = step.get("fault_mode")
            expected_state = step.get("abnormal_state")
            trigger_patterns = step.get("trigger_patterns", [])

            # 找到匹配的事件
            matched_event = None
            for ev in sorted_events:
                if ev.template_step == step_num:
                    matched_event = ev
                    break

            if matched_event:
                step_score = 0
                # 事件类型匹配
                if matched_event.event_type == expected_type:
                    step_score += 1
                # 故障模式/状态匹配
                if expected_fault and matched_event.fault_mode == expected_fault:
                    step_score += 1
                if expected_state and matched_event.state == expected_state:
                    step_score += 1
                # 触发词匹配
                if matched_event.trigger:
                    for pattern in trigger_patterns:
                        if pattern in matched_event.trigger:
                            step_score += 1
                            break

                step_match_quality = "full" if step_score >= 2 else "partial" if step_score >= 1 else "low"
                matched_steps.append({
                    "step": step_num,
                    "event_id": matched_event.event_id,
                    "event_type": matched_event.event_type,
                    "match_quality": step_match_quality,
                    "score": step_score
                })
                score += step_score
            else:
                missing_steps.append({
                    "step": step_num,
                    "event_type": expected_type,
                    "fault_mode_or_state": expected_fault or expected_state or "unknown",
                    "trigger_patterns": trigger_patterns[:2]
                })

        # 检查顺序约束
        constraints = template.constraints if isinstance(template.constraints, dict) else {}
        expected_order = constraints.get("order_must_follow", [])
        if expected_order:
            actual_steps = sorted([s["step"] for s in matched_steps])
            if len(actual_steps) >= 2:
                for o in expected_order:
                    chain_parts = [p.strip() for p in o.split("→")]
                    # 简化检查：验证 steps 是递增的
                    for i in range(len(actual_steps) - 1):
                        if actual_steps[i] >= actual_steps[i + 1]:
                            violations.append(f"步骤顺序违反：step {actual_steps[i]} 应在 step {actual_steps[i+1]} 之前")
                            break

        # 计算匹配度
        max_possible = total_steps * 3  # 每个步骤最多3分
        match_ratio = score / max_possible if max_possible > 0 else 0
        step_completeness = len(matched_steps) / total_steps if total_steps > 0 else 0

        if match_ratio > best_score and step_completeness >= 0.5:
            best_score = match_ratio
            if step_completeness >= 0.75:
                match_type = "full"
            elif step_completeness >= 0.5:
                match_type = "partial"
            else:
                match_type = "none"

            best_match = {
                "matched_template_id": template.template_id,
                "matched_template_name": template.name,
                "is_match": match_type != "none",
                "match_type": match_type,
                "matched_steps": matched_steps,
                "missing_steps": missing_steps,
                "violation_details": violations,
                "step_completeness": round(step_completeness, 2),
                "score": round(match_ratio, 3)
            }

    if not best_match:
        return {
            "request_event_ids": event_ids,
            "matched_template_id": None,
            "matched_template_name": None,
            "is_match": False,
            "match_type": "none",
            "matched_steps": [],
            "missing_steps": [],
            "violation_details": ["无法找到匹配的机理模板"]
        }

    return {
        "request_event_ids": event_ids,
        **best_match
    }


def get_validation_report(db: Session):  # type: (...) -> dict
    """获取机理校验的完整报告"""
    templates = db.query(MechanismTemplate).all()
    relations = db.query(EventRelation).all()
    events = db.query(Event).all()

    match_results = []
    violation_count = 0

    # 按template_id分组事件链
    for template in templates:
        tid = template.template_id
        template_rels = [r for r in relations if r.template_id == tid]
        template_events = set()
        for r in template_rels:
            template_events.add(r.source_event)
            template_events.add(r.target_event)

        # 对该模板的事件链进行校验
        event_ids = list(template_events)
        if event_ids:
            check_result = check_chain(db, event_ids[:1])  # 用一个事件触发链校验
            match_results.append({
                "template_id": tid,
                "template_name": template.name,
                "matched": check_result.get("is_match", False),
                "match_type": check_result.get("match_type", "none"),
                "step_completeness": check_result.get("step_completeness", 0),
                "violations": check_result.get("violation_details", [])
            })
            violation_count += len(check_result.get("violation_details", []))

    return {
        "total_templates": len(templates),
        "total_event_chains": len(match_results),
        "match_results": match_results,
        "violation_count": violation_count
    }
