"""
事件归一与融合模块
合并同义词：
内泄漏 / 内部泄漏 / 泵内泄
阀芯卡滞 / 阀芯卡住 / 滑阀卡滞
油液污染 / 液压油污染
压力下降 / 压力不足 / 压力降低
"""
from typing import List, Dict, Set, Tuple
from collections import defaultdict


# ── 同义词映射表 ──
SYNONYM_MAP = {
    # 泄漏类
    "内泄漏": ["内泄漏", "内部泄漏", "泵内泄", "内泄", "内部泄露"],
    "外泄漏": ["外泄漏", "外部泄漏", "外泄", "漏油", "渗漏", "外部泄露"],

    # 卡滞类
    "阀芯卡滞": ["阀芯卡滞", "阀芯卡住", "滑阀卡滞", "卡滞", "卡死", "卡住", "阀芯卡涩"],

    # 污染类
    "油液污染": ["油液污染", "液压油污染", "清洁度超标", "颗粒污染", "油液脏污", "污染"],

    # 压力类
    "压力下降": ["压力下降", "压力不足", "压力降低", "压力偏低", "系统压力低"],

    # 磨损类
    "磨损": ["磨损", "磨粒磨损", "机械磨损", "摩擦磨损", "配合面磨损"],

    # 密封类
    "密封失效": ["密封失效", "密封损坏", "密封圈破损", "密封件磨损", "密封件老化", "油封老化", "密封圈损坏"],

    # 气蚀类
    "气蚀": ["气蚀", "穴蚀", "空化", "气穴"],

    # 堵塞类
    "过滤器堵塞": ["过滤器堵塞", "滤芯堵塞", "滤网堵塞", "堵塞"],

    # 弹簧类
    "弹簧疲劳": ["弹簧疲劳", "弹簧失效", "弹簧老化", "弹簧松弛"],

    # 油温类
    "油温过高": ["油温过高", "过热", "油液过热", "温度异常", "油温异常"],

    # 噪声类
    "噪声增大": ["噪声", "噪音", "高频噪声", "噪音增大", "噪声增大", "异响"],

    # 振动类
    "振动增大": ["振动", "震动", "抖动", "振动加大", "振动加剧"],

    # 爬行类
    "液压缸爬行": ["爬行", "液压缸爬行", "爬行现象", "低速爬行"],

    # 动作缓慢类
    "动作缓慢": ["动作缓慢", "速度下降", "无力", "动作迟滞", "执行缓慢"],
}


def normalize_synonym(text: str) -> str:
    """将文本中的同义词替换为标准名称"""
    for canonical, variants in SYNONYM_MAP.items():
        for variant in variants:
            if variant in text:
                return canonical
    return text


def normalize_events(events: List[Dict]) -> List[Dict]:
    """对事件列表进行同义词归一化"""
    normalized = []
    for ev in events:
        norm_ev = dict(ev)
        # 归一化故障模式
        if ev.get("fault_mode"):
            norm_ev["fault_mode_original"] = ev["fault_mode"]
            norm_ev["fault_mode"] = normalize_synonym(ev["fault_mode"])
        # 归一化状态
        if ev.get("state"):
            norm_ev["state_original"] = ev["state"]
            norm_ev["state"] = normalize_synonym(ev["state"])
        # 归一化部件
        if ev.get("component"):
            norm_ev["component"] = normalize_synonym(ev["component"])
        normalized.append(norm_ev)
    return normalized


def merge_duplicate_events(events: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    合并重复事件（相同故障模式+相同部件+相似触发词的事件）。
    返回：(去重后的事件列表, 合并记录列表)
    """
    groups = defaultdict(list)

    for ev in events:
        # 分组键：故障模式 + 部件
        key = f"{ev.get('fault_mode', '')}|{ev.get('component', '')}|{ev.get('state', '')}"
        groups[key].append(ev)

    merged_events = []
    merge_records = []

    for key, group in groups.items():
        if len(group) == 1:
            merged_events.append(group[0])
        else:
            # 合并：保留置信度最高的事件作为主事件
            best = max(group, key=lambda e: e.get("confidence", 0))
            # 合并证据
            evidence_spans = []
            for ev in group:
                if ev.get("evidence_span"):
                    evidence_spans.append(ev["evidence_span"])

            merged = dict(best)
            merged["evidence_span"] = " | ".join(evidence_spans[:3])  # 最多保留3条证据
            merged["confidence"] = max(ev.get("confidence", 0) for ev in group)
            merged["merged_from"] = [ev["event_id"] for ev in group if ev["event_id"] != best["event_id"]]
            merged["merged_count"] = len(group)
            merged_events.append(merged)

            merge_records.append({
                "主事件ID": best["event_id"],
                "被合并事件IDs": [ev["event_id"] for ev in group if ev["event_id"] != best["event_id"]],
                "合并原因": f"相同故障模式和部件，共{len(group)}条事件合并",
                "主事件置信度": best.get("confidence", 0),
            })

    return merged_events, merge_records


def get_normalization_stats(original: List[Dict], normalized: List[Dict], merged: List[Dict], merge_records: List[Dict]) -> Dict:
    """获取归一化和融合统计"""
    synonym_changes = 0
    for orig, norm in zip(original, normalized):
        if orig.get("fault_mode") != norm.get("fault_mode"):
            synonym_changes += 1
        if orig.get("state") != norm.get("state"):
            synonym_changes += 1

    return {
        "原始事件数量": len(original),
        "归一化后事件数量": len(normalized),
        "融合后事件数量": len(merged),
        "同义词替换数量": synonym_changes,
        "合并事件组数量": len(merge_records),
        "合并减少事件数量": len(normalized) - len(merged),
        "去重率": round((len(normalized) - len(merged)) / max(len(normalized), 1), 3),
        "合并记录": merge_records
    }
