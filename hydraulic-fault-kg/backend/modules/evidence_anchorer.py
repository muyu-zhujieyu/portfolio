"""
证据锚定模块
每条事件必须绑定：
source_id、paragraph_id、sentence_id、evidence_span、
source_type、title、page_no 或 paragraph_no。
"""
import uuid
from typing import List, Dict, Optional


def anchor_evidence(
    events: List[Dict],
    source_metadata: Dict,
    reliability: str = "medium"
) -> List[Dict]:
    """
    为每条事件创建证据锚定记录。
    每条事件绑定到其来源文档的具体段落和句子。
    """
    evidence_records = []

    for ev in events:
        evidence_id = f"EVD_{ev['event_id']}"

        evidence = {
            "evidence_id": evidence_id,
            "event_id": ev["event_id"],
            "source_id": ev.get("source_id", source_metadata.get("source_id", "")),
            "paragraph_no": ev.get("paragraph_no", 0),
            "sentence_id": ev.get("sentence_id", ""),
            "evidence_span": ev.get("evidence_span", ev.get("trigger", "")),
            "source_type": source_metadata.get("source_type", ""),
            "title": source_metadata.get("title", ""),
            "author": source_metadata.get("author", ""),
            "year": source_metadata.get("year", ""),
            "extractor": "keyword_pattern_matcher",
            "reliability": _assess_reliability(ev),
            "review_status": "已确认" if ev.get("confidence", 0) >= 0.8 else "待审核",
            "anchored_at": ev.get("observed_time", ""),
            "paragraph_text": ev.get("evidence_span", "")[:300],
        }
        evidence_records.append(evidence)

    return evidence_records


def _assess_reliability(event: Dict) -> str:
    """评估证据可靠性"""
    confidence = event.get("confidence", 0.7)

    # 高可靠性：多个关键词命中 + 明确故障模式
    keyword_count = len(event.get("matched_keywords", []))
    if confidence >= 0.85 and keyword_count >= 3:
        return "高"
    elif confidence >= 0.7:
        return "中"
    else:
        return "低"


def get_anchoring_stats(events: List[Dict], evidence_records: List[Dict]) -> Dict:
    """获取证据锚定统计"""
    reliability_dist = {"高": 0, "中": 0, "低": 0}
    review_dist = {"已确认": 0, "待审核": 0}

    for evd in evidence_records:
        rel = evd.get("reliability", "中")
        reliability_dist[rel] = reliability_dist.get(rel, 0) + 1

        rev = evd.get("review_status", "待审核")
        review_dist[rev] = review_dist.get(rev, 0) + 1

    events_with_evidence = len(set(evd["event_id"] for evd in evidence_records))

    return {
        "抽取事件数量": len(events),
        "证据锚定数量": len(evidence_records),
        "锚定覆盖率": round(events_with_evidence / max(len(events), 1), 3),
        "可靠性分布": reliability_dist,
        "审查状态分布": review_dist,
        "平均证据片段长度": round(
            sum(len(evd.get("evidence_span", "")) for evd in evidence_records) / max(len(evidence_records), 1), 0
        )
    }
