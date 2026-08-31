"""
机理模板校验模块
使用 T1 到 T6 液压故障机理模板检查事件链是否合理。
"""
from typing import List, Dict, Optional

# T1-T6 液压故障机理模板（中文）
MECHANISM_TEMPLATES = [
    {
        "template_id": "T1",
        "name": "泄漏故障演化链",
        "description": "密封失效→内泄漏→流量损失→压力下降→执行元件动作缓慢",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "密封失效", "trigger_patterns": ["密封失效", "密封磨损", "密封圈破损", "油封老化"]},
            {"step": 2, "event_type": "状态事件", "abnormal_state": "内泄漏", "trigger_patterns": ["内泄漏", "内部泄漏", "内泄"]},
            {"step": 3, "event_type": "状态事件", "abnormal_state": "压力下降", "trigger_patterns": ["压力下降", "压力不足", "压力降低"]},
            {"step": 4, "event_type": "状态事件", "abnormal_state": "动作缓慢", "trigger_patterns": ["动作缓慢", "速度下降", "无力"]},
        ],
        "constraints": {
            "order_must_follow": ["密封失效 → 内泄漏 → 压力下降 → 动作缓慢"],
            "causal_chain_full": "密封件磨损老化 → 内泄漏 → 系统流量损失 → 工作压力下降 → 执行元件动作缓慢无力"
        }
    },
    {
        "template_id": "T2",
        "name": "过滤器堵塞故障演化链",
        "description": "过滤器堵塞→吸油阻力增大→气蚀→噪声增大",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "堵塞", "trigger_patterns": ["堵塞", "滤芯堵塞", "过滤器堵塞"]},
            {"step": 2, "event_type": "状态事件", "abnormal_state": "压力下降", "trigger_patterns": ["吸油阻力", "真空度", "压差"]},
            {"step": 3, "event_type": "故障事件", "fault_mode": "气蚀", "trigger_patterns": ["气蚀", "穴蚀", "空化"]},
            {"step": 4, "event_type": "状态事件", "abnormal_state": "噪声增大", "trigger_patterns": ["噪声", "噪音", "异响"]},
        ],
        "constraints": {
            "order_must_follow": ["堵塞 → 吸油不足 → 气蚀 → 噪声"],
            "causal_chain_full": "过滤器堵塞 → 泵吸油不足 → 气蚀 → 系统噪声异常增大"
        }
    },
    {
        "template_id": "T3",
        "name": "冷却失效故障演化链",
        "description": "冷却器效率下降→油温升高→黏度下降→泄漏增大",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "冷却失效", "trigger_patterns": ["冷却失效", "冷却不足", "散热不良", "冷却器堵塞"]},
            {"step": 2, "event_type": "状态事件", "abnormal_state": "油温升高", "trigger_patterns": ["油温升高", "油温上升", "温度升高", "过热"]},
            {"step": 3, "event_type": "状态事件", "abnormal_state": "黏度下降", "trigger_patterns": ["黏度下降", "黏度降低", "油液变稀"]},
            {"step": 4, "event_type": "状态事件", "abnormal_state": "泄漏增大", "trigger_patterns": ["泄漏增大", "泄漏加剧", "内泄漏增加"]},
        ],
        "constraints": {
            "order_must_follow": ["冷却失效 → 油温升高 → 黏度下降 → 泄漏增大"],
            "causal_chain_full": "冷却器效率下降 → 油液温度升高 → 油液黏度下降 → 元件内部泄漏增大 → 系统效率进一步下降"
        }
    },
    {
        "template_id": "T4",
        "name": "蓄能器故障演化链",
        "description": "皮囊破裂→保压失效→压力波动",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "皮囊破裂", "trigger_patterns": ["皮囊破裂", "皮囊损坏", "皮囊老化", "皮囊疲劳"]},
            {"step": 2, "event_type": "状态事件", "abnormal_state": "压力下降", "trigger_patterns": ["保压失效", "无法保压", "压力保持失效"]},
            {"step": 3, "event_type": "状态事件", "abnormal_state": "压力波动", "trigger_patterns": ["压力波动", "压力脉动", "压力不稳"]},
        ],
        "constraints": {
            "order_must_follow": ["皮囊破裂 → 保压失效 → 压力波动"],
            "causal_chain_full": "蓄能器皮囊破裂 → 丧失储能功能 → 系统压力波动 → 液压泵频繁加卸载"
        }
    },
    {
        "template_id": "T5",
        "name": "油液污染故障演化链",
        "description": "油液污染→阀芯卡滞→流量控制异常→压力波动",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "油液污染", "trigger_patterns": ["油液污染", "液压油污染", "清洁度超标"]},
            {"step": 2, "event_type": "故障事件", "fault_mode": "卡滞", "trigger_patterns": ["卡滞", "阀芯卡滞", "卡住"]},
            {"step": 3, "event_type": "状态事件", "abnormal_state": "流量损失", "trigger_patterns": ["流量控制异常", "流量异常", "动作异常"]},
            {"step": 4, "event_type": "状态事件", "abnormal_state": "压力波动", "trigger_patterns": ["压力波动", "压力脉动", "压力不稳"]},
        ],
        "constraints": {
            "order_must_follow": ["油液污染 → 卡滞 → 流量异常 → 压力波动"],
            "causal_chain_full": "油液清洁度恶化 → 阀芯卡滞 → 流量控制异常 → 系统压力波动"
        }
    },
    {
        "template_id": "T6",
        "name": "溢流阀故障演化链",
        "description": "弹簧疲劳→压力调节异常→系统负载能力下降",
        "chain": [
            {"step": 1, "event_type": "故障事件", "fault_mode": "弹簧疲劳", "trigger_patterns": ["弹簧疲劳", "弹簧失效", "弹簧蠕变"]},
            {"step": 2, "event_type": "状态事件", "abnormal_state": "压力下降", "trigger_patterns": ["压力异常", "压力调节异常", "设定压力漂移"]},
            {"step": 3, "event_type": "状态事件", "abnormal_state": "效率下降", "trigger_patterns": ["负载能力下降", "承载能力下降", "无法达到额定负载"]},
        ],
        "constraints": {
            "order_must_follow": ["弹簧疲劳 → 压力异常 → 负载能力下降"],
            "causal_chain_full": "溢流阀弹簧疲劳 → 设定压力向下漂移 → 系统最大压力不足 → 设备负载能力下降"
        }
    }
]


def validate_events_against_templates(events: List[Dict]) -> Dict:
    """
    将抽取的事件与机理模板进行匹配校验。
    将事件分配到最匹配的模板中。
    """
    results = []

    for template in MECHANISM_TEMPLATES:
        chain = template["chain"]
        matched_steps = []
        missing_steps = []
        template_event_ids = []

        for step in chain:
            step_num = step["step"]
            trigger_patterns = step.get("trigger_patterns", [])

            # 查找匹配此步骤的事件
            best_match = None
            for ev in events:
                ev_text = ev.get("trigger", "") + ev.get("evidence_span", "")
                for pat in trigger_patterns:
                    if pat in ev_text:
                        if best_match is None or ev.get("confidence", 0) > best_match.get("confidence", 0):
                            best_match = ev
                        break

            if best_match:
                matched_steps.append({
                    "step": step_num,
                    "event_id": best_match["event_id"],
                    "event_type": best_match["event_type"],
                    "trigger": best_match.get("trigger", "")[:80],
                    "expected_type": step.get("event_type", ""),
                    "is_match": True
                })
                template_event_ids.append(best_match["event_id"])
            else:
                missing_steps.append({
                    "step": step_num,
                    "expected_type": step.get("event_type", ""),
                    "expected_fault_or_state": step.get("fault_mode", step.get("abnormal_state", "")),
                    "trigger_patterns": trigger_patterns[:3]
                })

        completeness = len(matched_steps) / len(chain) if chain else 0
        if completeness >= 0.75:
            match_type = "完整匹配"
        elif completeness >= 0.5:
            match_type = "部分匹配"
        elif completeness >= 0.25:
            match_type = "弱匹配"
        else:
            match_type = "未匹配"

        results.append({
            "template_id": template["template_id"],
            "template_name": template["name"],
            "description": template["description"],
            "total_steps": len(chain),
            "matched_steps_count": len(matched_steps),
            "matched_steps": matched_steps,
            "missing_steps": missing_steps,
            "match_type": match_type,
            "completeness": round(completeness, 2),
            "template_event_ids": template_event_ids,
            "constraints": template.get("constraints", {}),
        })

    return {
        "总模板数": len(MECHANISM_TEMPLATES),
        "总事件数": len(events),
        "模板校验结果": results,
        "完整匹配模板数": sum(1 for r in results if r["match_type"] == "完整匹配"),
        "部分匹配模板数": sum(1 for r in results if r["match_type"] == "部分匹配"),
        "未匹配模板数": sum(1 for r in results if r["match_type"] == "未匹配"),
    }


def get_template_by_id(template_id: str) -> Optional[Dict]:
    """根据模板ID获取模板"""
    for t in MECHANISM_TEMPLATES:
        if t["template_id"] == template_id:
            return t
    return None
