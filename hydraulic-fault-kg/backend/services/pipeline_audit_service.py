# -*- coding: utf-8 -*-
"""解析诊断与审计服务 — 逐资料审计三元组抽取/证据/图谱贡献"""
import os, json
from typing import Dict, Any, List

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PipelineAuditService:
    def __init__(self):
        self._audit_cache = {}

    def run_audit(self) -> Dict[str, Any]:
        sources_contrib = self._audit_sources()
        low_contrib = [s for s in sources_contrib if s.get("贡献等级") in ("低", "无")]
        filter_samples = self._get_filter_samples()

        # 三元组统计
        tp = os.path.join(BASE, "data", "extracted", "triples.json")
        raw_triples = []
        if os.path.exists(tp):
            with open(tp, encoding="utf-8") as f:
                data = json.load(f)
                raw_triples = data.get("三元组列表", [])

        mtp = os.path.join(BASE, "data", "extracted", "merged_triples.json")
        merged_triples = []
        completed_triples = []
        if os.path.exists(mtp):
            with open(mtp, encoding="utf-8") as f:
                data = json.load(f)
                merged_triples = data.get("融合三元组列表", [])
                completed_triples = [t for t in merged_triples if t.get("triple_source") == "机理模板补全"]

        # 证据统计
        public_triples = [t for t in merged_triples if t.get("triple_source") != "机理模板补全"]
        public_with_ev = [t for t in public_triples if t.get("evidence_texts") and len(t.get("evidence_texts", [])) > 0]
        ev_coverage = round(len(public_with_ev) / max(len(public_triples), 1), 4)
        tpl_ratio = round(len(completed_triples) / max(len(merged_triples), 1), 4)

        # 图谱统计
        nodes_path = os.path.join(BASE, "data", "graph", "nodes.json")
        links_path = os.path.join(BASE, "data", "graph", "links.json")
        orphan_path = os.path.join(BASE, "data", "graph", "orphan_nodes.json")
        chains_path = os.path.join(BASE, "data", "graph", "chains.json")

        node_count = 0; link_count = 0; orphan_count = 0; orphan_list = []; chains = []
        if os.path.exists(nodes_path):
            with open(nodes_path, encoding="utf-8") as f: node_count = len(json.load(f))
        if os.path.exists(links_path):
            with open(links_path, encoding="utf-8") as f: link_count = len(json.load(f))
        if os.path.exists(orphan_path):
            with open(orphan_path, encoding="utf-8") as f:
                orphan_list = json.load(f); orphan_count = len(orphan_list)
        if os.path.exists(chains_path):
            with open(chains_path, encoding="utf-8") as f: chains = json.load(f)

        # 模板诊断
        report_path = os.path.join(BASE, "data", "graph", "mechanism_validation_report.json")
        template_diagnostics = []
        if os.path.exists(report_path):
            with open(report_path, encoding="utf-8") as f:
                report = json.load(f)
            for r in report.get("校验结果", []):
                template_diagnostics.append({
                    "template_id": r.get("template_id"),
                    "template_name": r.get("template_name"),
                    "命中三元组数": len(r.get("matched_triples", [])),
                    "补全三元组数": len(r.get("completed_triples", [])),
                    "链节点数": len(r.get("expected_triples", [])),
                    "链边数": len(r.get("expected_triples", [])),  # 每个expected triple对应一条边
                    "evidence_coverage": r.get("evidence_coverage", 0),
                    "match_score": r.get("template_match_score", 0),
                })

        # 链边诊断
        chain_link_diagnostics = []
        for ch in chains:
            chain_link_diagnostics.append({
                "template_id": ch.get("template_id"),
                "chain_links_count": len(ch.get("chain_links", [])),
                "chain_nodes_count": len(ch.get("chain_nodes", [])),
                "chain_links_empty": len(ch.get("chain_links", [])) == 0,
            })

        # 无证据诊断
        no_evidence_triples = [t for t in public_triples if not t.get("evidence_texts") or len(t.get("evidence_texts", [])) == 0]
        no_evidence_nodes = []
        if os.path.exists(nodes_path):
            with open(nodes_path, encoding="utf-8") as f:
                nodes_data = json.load(f)
            no_evidence_nodes = [{"name": n.get("name"), "node_source": n.get("node_source"), "说明": n.get("说明", "")}
                                 for n in nodes_data if n.get("证据数量", 0) == 0]

        return {
            "资料总数": len(sources_contrib),
            "成功读取资料数": sum(1 for s in sources_contrib if s.get("文件是否存在")),
            "失败资料数": sum(1 for s in sources_contrib if not s.get("文件是否存在")),
            "原始段落总数": sum(s.get("原始段落数", 0) for s in sources_contrib),
            "液压相关段落数": sum(s.get("领域过滤后段落数", 0) for s in sources_contrib),
            "过滤保留率": self._safe_div(
                sum(s.get("领域过滤后段落数", 0) for s in sources_contrib),
                sum(s.get("原始段落数", 0) for s in sources_contrib)),
            "三元组抽取诊断": {
                "原始三元组数": len(raw_triples),
                "融合三元组数": len(merged_triples),
                "平均每段三元组数": round(len(raw_triples) / max(sum(s.get("领域过滤后段落数", 0) for s in sources_contrib), 1), 2),
                "低贡献资料数": len(low_contrib),
                "低贡献资料列表": [{"source_id": s["source_id"], "标题": s.get("标题", ""), "原始三元组数": s.get("原始三元组数", 0), "原因": s.get("低贡献原因", "")} for s in low_contrib],
            },
            "证据覆盖诊断": {
                "有证据三元组数": len(public_with_ev),
                "无证据三元组数": len(no_evidence_triples),
                "公开资料证据覆盖率": ev_coverage,
                "模板补全比例": tpl_ratio,
                "无证据三元组列表": [{"triple": f"{t.get('subject','')}—{t.get('predicate','')}—{t.get('object','')}",
                                   "source_titles": t.get("source_titles", [])} for t in no_evidence_triples[:10]],
                "无证据节点列表": no_evidence_nodes[:10],
            },
            "模板补全诊断": template_diagnostics,
            "链边诊断": chain_link_diagnostics,
            "孤立节点诊断": {
                "孤立节点数": orphan_count,
                "孤立节点比例": f"{round(orphan_count/max(node_count+orphan_count,1)*100)}%" if node_count+orphan_count > 0 else "0%",
                "被隐藏孤立节点列表": orphan_list[:10],
            },
            "图谱统计": {"节点数": node_count, "边数": link_count, "链条数": len(chains)},
            "低贡献资料数": len(low_contrib),
            "各资料贡献明细": sources_contrib,
            "被过滤段落样例": filter_samples[:8],
        }

    def _audit_sources(self) -> List[Dict]:
        reg_path = os.path.join(BASE, "data", "source_registry.json")
        if not os.path.exists(reg_path): return []
        with open(reg_path, encoding="utf-8") as f: registry = json.load(f)

        triple_map = self._load_triple_source_map()
        results = []
        for src in registry.get("sources", []):
            sid = src.get("source_id", "")
            file_path = os.path.join(BASE, src.get("文件路径", ""))
            exists = os.path.exists(file_path)
            size = os.path.getsize(file_path) if exists else 0

            from database import fetch_all
            fps = fetch_all("SELECT COUNT(*) as c FROM filtered_paragraphs WHERE source_id = ?", (sid,))
            fp_count = fps[0].get("c", 0) if fps else 0

            raw_paras = 0
            if exists:
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as f:
                        text = f.read()
                    paras = [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) >= 10]
                    raw_paras = len(paras)
                except: pass

            tr_count = triple_map.get(sid, 0)
            retention = self._safe_div(fp_count, raw_paras) if raw_paras > 0 else 0

            if not exists or (raw_paras == 0 and fp_count == 0 and tr_count == 0):
                level, reason = "无", "文件不存在或无有效内容"
            elif fp_count == 0 or tr_count == 0:
                level, reason = "低", self._low_contrib_reason(raw_paras, fp_count, tr_count, retention, exists, size, file_path)
            elif tr_count < 3:
                level, reason = "中", f"三元组数较少({tr_count}条)，建议补充更多故障描述"
            else:
                level, reason = "高", "贡献正常"

            results.append({
                "source_id": sid, "来源类型": src.get("来源类型", ""),
                "标题": src.get("标题", ""), "文件路径": src.get("文件路径", ""),
                "文件是否存在": exists, "文件大小KB": round(size/1024, 1) if size else 0,
                "原始段落数": raw_paras, "领域过滤后段落数": fp_count,
                "过滤保留率": round(retention, 3),
                "原始三元组数": tr_count, "贡献等级": level,
                "低贡献原因": reason if level in ("低", "无") else "",
            })
        return results

    def _load_triple_source_map(self):
        count_map = {}
        tp = os.path.join(BASE, "data", "extracted", "triples.json")
        if os.path.exists(tp):
            with open(tp, encoding="utf-8") as f:
                triples = json.load(f).get("三元组列表", [])
            for t in triples:
                sid = t.get("source_id", "")
                if sid: count_map[sid] = count_map.get(sid, 0) + 1
        return count_map

    def _get_filter_samples(self):
        samples = []
        reg_path = os.path.join(BASE, "data", "source_registry.json")
        if not os.path.exists(reg_path): return samples
        with open(reg_path, encoding="utf-8") as f: registry = json.load(f)
        from services.domain_filter_service import domain_filter
        for src in registry.get("sources", [])[:5]:
            file_path = os.path.join(BASE, src.get("文件路径", ""))
            if not os.path.exists(file_path): continue
            try:
                with open(file_path, encoding="utf-8", errors="replace") as f: text = f.read()
                for p in [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) >= 10][:3]:
                    is_rel, score = domain_filter.is_hydraulic_related(p)
                    if not is_rel:
                        samples.append({"来源": src.get("source_id", ""), "段落内容": p[:150],
                                        "相关度分数": round(score, 3), "过滤原因": "相关度分数低于阈值"})
            except: pass
        return samples

    def get_source_contributions(self): return self._audit_sources()
    def get_filter_debug(self): return {"被过滤段落样例": self._get_filter_samples()[:10]}

    @staticmethod
    def _safe_div(a, b): return round(a / max(b, 1), 3)

    @staticmethod
    def _low_contrib_reason(raw_paras, fp_count, ev_count, retention, exists, size, path):
        if not exists: return "文件不存在"
        if size < 500: return f"文件过小({size}B)"
        if raw_paras == 0: return "未解析出段落"
        if fp_count == 0: return f"领域过滤保留率0%"
        if ev_count == 0: return f"通过过滤但无三元组，可能缺少触发词"
        return "三元组数量偏低"


pipeline_audit = PipelineAuditService()
