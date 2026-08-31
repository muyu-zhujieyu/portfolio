# -*- coding: utf-8 -*-
"""
三元组融合服务 - subject/predicate/object 同义归一后融合

融合规则：
  1. subject、predicate、object 同义归一后相同的三元组进行融合
  2. 融合时不能丢失来源信息
  3. merged_triple 必须保留所有 source_ids、source_titles、paragraph_ids、evidence_texts
  4. 不同 predicate 不能融合
  5. 不同 subject-object 方向不能融合
  6. "油液污染—导致—阀芯卡滞"和"阀芯卡滞—导致—油液污染"不能融合
  7. 融合后的三元组仍然可以追溯所有原始资料

triple_source 取值：
  公开资料抽取 - 完全来自公开资料
  多来源融合 - 多个公开资料来源融合
  机理模板补全 - 由T1-T6模板补全
"""
import json
import os
from typing import List, Dict, Any, Tuple

# 同义词映射
SYN_MAP = {}
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = os.path.join(BASE, "data", "dictionaries", "synonyms.json")
if os.path.exists(sp):
    with open(sp, encoding="utf-8") as f:
        for g in json.load(f).get("synonym_groups", []):
            for v in g.get("variants", []):
                SYN_MAP[v] = g["canonical"]

# 额外的液压伺服阀领域同义词
HYDRAULIC_SYNONYMS = {
    # 部件同义词
    "伺服阀": "液压伺服阀",
    "电液伺服阀": "液压伺服阀",
    # 故障模式同义词
    "阀芯卡住": "阀芯卡滞",
    "滑阀卡滞": "阀芯卡滞",
    "阀芯卡阻": "阀芯卡滞",
    "阀芯卡死": "阀芯卡滞",
    "喷嘴孔堵塞": "喷嘴堵塞",
    "喷嘴阻塞": "喷嘴堵塞",
    "油液脏污": "油液污染",
    "液压油污染": "油液污染",
    "气隙偏差": "气隙不对称",
    "气隙不均": "气隙不对称",
    "零点漂移": "零位漂移",
    "零偏": "零位漂移",
    "内部泄漏": "内泄漏",
    "泵内泄": "内泄漏",
    "内泄": "内泄漏",
    # 异常状态同义词
    "压力不稳": "压力波动",
    "压力脉动": "压力波动",
    "响应变慢": "响应迟缓",
    "动作迟缓": "响应迟缓",
    "输出不对称": "输出偏差",
    "温升异常": "线圈发热异常",
    # 检测方式同义词
    "复测": "维修后复测",
    "响应测试": "响应曲线检测",
    "污染度测试": "污染度检测",
    # 维修动作同义词
    "换油": "更换液压油",
    "换滤芯": "更换滤芯",
    "清洗": "清洗阀芯",
}

for k, v in HYDRAULIC_SYNONYMS.items():
    SYN_MAP[k] = v


class FusionService:
    """三元组融合器"""

    def normalize_term(self, term: str) -> str:
        """将术语归一化为规范表达"""
        if not term:
            return ""
        for v, c in sorted(SYN_MAP.items(), key=lambda x: -len(x[0])):
            if v == term:
                return c
        return term

    def normalize_triple(self, triple: Dict) -> Tuple[str, str, str]:
        """归一化三元组 subject/predicate/object"""
        subj = self.normalize_term(triple.get("subject", ""))
        pred = triple.get("predicate", "")  # predicate 不归一，必须完全一致
        obj = self.normalize_term(triple.get("object", ""))
        return subj, pred, obj

    def build_fusion_key(self, triple: Dict) -> str:
        """构建融合键：subject|predicate|object"""
        subj, pred, obj = self.normalize_triple(triple)
        return f"{subj}|{pred}|{obj}"

    def merge_triples(self, triples: List[Dict]) -> Dict[str, Any]:
        """融合三元组列表

        Args:
            triples: 原始三元组列表 (from event_extract_service)

        Returns:
            {"状态": "成功", "原始三元组数": N, "融合后三元组数": M, "融合三元组列表": [...]}
        """
        if not triples:
            return {
                "状态": "成功",
                "原始三元组数": 0,
                "融合后三元组数": 0,
                "融合三元组列表": [],
            }

        # 计算归一化键并分组
        groups: Dict[str, List[Dict]] = {}
        for t in triples:
            key = self.build_fusion_key(t)
            groups.setdefault(key, []).append(t)

        merged = []
        seq = 0

        for key, group in groups.items():
            seq += 1
            first = group[0]
            subj_norm, pred_norm, obj_norm = self.normalize_triple(first)

            # 收集所有来源信息
            source_ids = []
            source_types = []
            source_titles = []
            source_files = []
            paragraph_ids = []
            evidence_texts = []
            evidence_spans = []
            raw_triple_ids = []
            template_ids = []

            seen_sids = set()
            for t in group:
                sid = t.get("source_id", "")
                if sid and sid not in seen_sids:
                    seen_sids.add(sid)
                    source_ids.append(sid)
                    source_types.append(t.get("source_type", ""))
                    source_titles.append(t.get("source_title", ""))
                    source_files.append(t.get("source_file", ""))
                pid = t.get("paragraph_id", 0)
                if pid not in paragraph_ids:
                    paragraph_ids.append(pid)
                et = t.get("evidence_text", "")
                if et and et not in evidence_texts:
                    evidence_texts.append(et)
                es = t.get("evidence_span", "")
                if es and es not in evidence_spans:
                    evidence_spans.append(es)
                raw_triple_ids.append(t.get("triple_id", ""))
                tc = t.get("template_candidate", "")
                if tc and tc not in template_ids:
                    template_ids.append(tc)

            # 确定三元组来源
            if len(source_ids) >= 2:
                triple_source = "多来源融合"
            elif source_ids:
                triple_source = "公开资料抽取"
            else:
                triple_source = "机理模板补全"

            merged_triple = {
                "merged_triple_id": f"MRG-TRP-{seq:06d}",
                "subject": subj_norm,
                "predicate": pred_norm,
                "object": obj_norm,
                "subject_type": first.get("subject_type", ""),
                "object_type": first.get("object_type", ""),
                "relation_type": first.get("relation_type", ""),
                "source_ids": source_ids,
                "source_types": source_types,
                "source_titles": source_titles,
                "source_files": source_files,
                "paragraph_ids": paragraph_ids,
                "evidence_ids": [],  # 由证据锚定服务回填
                "evidence_texts": evidence_texts,
                "evidence_spans": evidence_spans,
                "raw_triple_ids": raw_triple_ids,
                "template_ids": template_ids,
                "triple_source": triple_source,
                "confidence": max(t.get("confidence", 0.5) for t in group),
                "support_count": len(group),
            }

            merged.append(merged_triple)

        # 统计
        by_source = {}
        by_relation = {}
        for m in merged:
            src = m["triple_source"]
            by_source[src] = by_source.get(src, 0) + 1
            rel = m["relation_type"]
            by_relation[rel] = by_relation.get(rel, 0) + 1

        compression_pct = round((1 - len(merged) / max(len(triples), 1)) * 100)

        # 保存融合报告
        odir = os.path.join(BASE, "data", "extracted")
        os.makedirs(odir, exist_ok=True)
        report = {
            "原始三元组数": len(triples),
            "融合后三元组数": len(merged),
            "压缩率": f"{compression_pct}%",
            "按来源": by_source,
            "按关系类型": by_relation,
        }
        with open(os.path.join(odir, "fusion_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return {
            "状态": "成功",
            "原始三元组数": len(triples),
            "融合后三元组数": len(merged),
            "压缩率": f"{compression_pct}%",
            "融合三元组列表": merged,
        }


# 单例
fusion = FusionService()
