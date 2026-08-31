"""
证据锚定服务 - 将每条三元组绑定到原文证据

核心原则:
  - 每条公开资料抽取三元组必须有 evidence_text
  - 证据原文必须来自原始段落中的连续片段
  - 不能凭空生成证据
  - 如果三元组来自公开资料抽取，则 evidence_text 不允许为空

每条证据保存:
  evidence_id, triple_id, merged_triple_id, source_id, source_type,
  source_title, source_file, paragraph_id, sentence_id,
  evidence_text, evidence_span, reliability, audit_status
"""
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


class EvidenceAnchorService:
    """证据锚定器 - 将三元组与原文证据绑定"""

    # 可靠度评估的关键信号词
    HIGH_RELIABILITY_SIGNALS = [
        "检测结果", "实测", "测量值", "数据显示", "试验结果",
        "证实", "确认", "拆检发现", "检查发现", "经检测",
        "光谱分析", "颗粒度检测", "ISO",
    ]
    LOW_RELIABILITY_SIGNALS = [
        "可能", "怀疑", "推测", "估计", "大概", "或许",
        "疑似", "不排除", "需进一步", "有待",
    ]

    # ================================================================
    # 公开接口
    # ================================================================

    def anchor_triples(self, extract_result: Dict[str, Any]) -> Dict[str, Any]:
        """为所有抽取三元组生成证据锚定记录

        Args:
            extract_result: event_extractor.extract_from_filtered() 的返回结果
                {"三元组总数": N, "三元组列表": [...]}

        Returns:
            {
                "状态": "成功",
                "证据总数": N,
                "证据列表": [...],
                "锚定统计": {...}
            }
        """
        triples = extract_result.get("三元组列表", [])
        if not triples:
            return {
                "状态": "失败",
                "错误": "无三元组可供锚定",
                "证据总数": 0,
                "证据列表": [],
            }

        evidence_list = []
        stats = {"高可靠": 0, "中可靠": 0, "低可靠": 0, "无证据": 0}
        seen_keys = set()

        for triple in triples:
            evidence_text = triple.get("evidence_text", "")
            if not evidence_text or len(evidence_text.strip()) < 5:
                # 标记无证据但保留记录（用于后续模板补全标注）
                evd = self._make_empty_evidence(triple)
                evidence_list.append(evd)
                stats["低可靠"] += 1
                continue

            # 证据去重（同一证据原文段落不重复锚定）
            evd_key = triple.get("source_id", "") + "|" + evidence_text[:120]
            if evd_key in seen_keys:
                continue
            seen_keys.add(evd_key)

            evd = self._anchor_single_triple(triple)
            if evd:
                evidence_list.append(evd)
                reliability = evd.get("reliability", "中")
                if reliability == "高":
                    stats["高可靠"] += 1
                elif reliability == "低":
                    stats["低可靠"] += 1
                else:
                    stats["中可靠"] += 1

        return {
            "状态": "成功",
            "证据总数": len(evidence_list),
            "证据列表": evidence_list,
            "锚定统计": {
                **stats,
                "锚定率": round(
                    len([e for e in evidence_list if e.get("evidence_text")]) /
                    max(len(triples), 1), 4
                ),
            },
        }

    def _anchor_single_triple(self, triple: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """为单条三元组创建证据锚定记录"""
        evidence_text = triple.get("evidence_text", "")
        if not evidence_text or len(evidence_text.strip()) < 5:
            return None

        evidence_id = f"EVD-{uuid.uuid4().hex[:8].upper()}"
        triple_id = triple.get("triple_id", "")

        reliability = self._assess_reliability(evidence_text, triple)
        audit_status = "已通过" if reliability == "高" else "待审核"

        return {
            "evidence_id": evidence_id,
            "triple_id": triple_id,
            "merged_triple_id": "",  # 融合后回填
            "source_id": triple.get("source_id", ""),
            "source_type": triple.get("source_type", ""),
            "source_title": triple.get("source_title", ""),
            "source_file": triple.get("source_file", ""),
            "paragraph_id": triple.get("paragraph_id", 0),
            "sentence_id": triple.get("sentence_id", 0),
            "evidence_text": evidence_text,
            "evidence_span": triple.get("evidence_span", ""),
            "reliability": reliability,
            "audit_status": audit_status,
            "锚定时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _make_empty_evidence(self, triple: Dict[str, Any]) -> Dict[str, Any]:
        """为无证据三元组创建空证据标记"""
        return {
            "evidence_id": f"EVD-EMPTY-{uuid.uuid4().hex[:8].upper()}",
            "triple_id": triple.get("triple_id", ""),
            "merged_triple_id": "",
            "source_id": triple.get("source_id", "无"),
            "source_type": triple.get("source_type", ""),
            "source_title": triple.get("source_title", ""),
            "source_file": triple.get("source_file", ""),
            "paragraph_id": triple.get("paragraph_id", 0),
            "sentence_id": triple.get("sentence_id", 0),
            "evidence_text": "",
            "evidence_span": "",
            "reliability": "无证据",
            "audit_status": "需补充证据",
            "note": "该三元组缺少直接原文证据，可能来自机理模板补全",
            "锚定时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ================================================================
    # 可靠度评估
    # ================================================================

    def _assess_reliability(self, evidence_text: str, triple: Dict[str, Any]) -> str:
        """评估证据的可靠度等级"""
        score = 0

        # 高可靠信号
        for signal in self.HIGH_RELIABILITY_SIGNALS:
            if signal in evidence_text:
                score += 1

        # 低可靠信号（减分）
        for signal in self.LOW_RELIABILITY_SIGNALS:
            if signal in evidence_text:
                score -= 1

        # 三元组置信度
        conf = triple.get("confidence", 0.5)
        if conf >= 0.7:
            score += 1
        elif conf < 0.4:
            score -= 1

        # 证据长度
        ev_len = len(evidence_text)
        if ev_len >= 60:
            score += 1
        elif ev_len < 20:
            score -= 1

        if score >= 2:
            return "高"
        elif score <= 0:
            return "低"
        else:
            return "中"


# 单例
evidence_anchor = EvidenceAnchorService()
