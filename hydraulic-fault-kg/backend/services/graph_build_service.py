# -*- coding: utf-8 -*-
"""
知识图谱构建服务 - 从融合三元组构建节点和边

核心规则:
  1. 节点来自三元组 subject/object
  2. 边来自三元组 predicate
  3. 模板补全节点/边必须标注"机理模板补全"
  4. 孤立节点(无边/无证据/无链条归属)默认隐藏，写入 orphan_nodes.json
  5. T1-T6 链条的 chain_links 必须保证每条链都有边
"""
import json
import os
from typing import List, Dict, Any, Set

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NODE_COLORS = {
    "部件": "#9B59B6",
    "故障模式": "#E74C3C",
    "异常状态": "#F39C12",
    "检测方式": "#3498DB",
    "维修动作": "#2ECC71",
    "证据来源": "#95A5A6",
    "机理模板": "#1ABC9C",
    "影响结果": "#E91E63",
}

SIZES = {
    "部件": 32, "故障模式": 28, "异常状态": 26,
    "检测方式": 24, "维修动作": 24, "证据来源": 20,
    "机理模板": 34, "影响结果": 26,
}


class GraphBuildService:
    """从融合三元组构建知识图谱，过滤孤立节点"""

    def build_full_graph(
        self,
        merged_triples: List[Dict] = None,
        completed_triples: List[Dict] = None,
        chains: List[Dict] = None,
    ) -> Dict[str, Any]:
        merged_triples = merged_triples or []
        completed_triples = completed_triples or []
        chains = chains or []

        # 合并所有三元组
        all_triples = list(merged_triples)
        for ct in completed_triples:
            all_triples.append(ct)

        # 构建节点和边
        nodes: Dict[str, Dict] = {}
        links: List[Dict] = []
        link_seen: Set[str] = set()

        for triple in all_triples:
            subject = triple.get("subject", "")
            object_ = triple.get("object", "")
            predicate = triple.get("predicate", "")
            if not subject or not object_:
                continue

            subject_type = triple.get("subject_type", "故障模式")
            object_type = triple.get("object_type", "故障模式")
            triple_source = triple.get("triple_source", "公开资料抽取")
            template_id = triple.get("template_id", "")

            self._add_or_update_node(nodes, subject, subject_type, triple_source, triple, template_id)
            self._add_or_update_node(nodes, object_, object_type, triple_source, triple, template_id)

            link_key = f"{subject}|{predicate}|{object_}"
            if link_key not in link_seen:
                link_seen.add(link_key)
                links.append(self._build_link(subject, predicate, object_, triple, template_id, triple_source))

        # ── 后处理：将 links 与 chains 关联，标记 matched_template_ids ──
        if chains:
            for link in links:
                link_src = link["source"]
                link_tgt = link["target"]
                link_pred = link["relation_zh"]
                link_norm = f"{link_src}|{link_pred}|{link_tgt}"
                for ch in chains:
                    tid = ch.get("template_id", "")
                    for cl in ch.get("chain_links", []):
                        if link_norm in cl or cl in link_norm or link["id"] == cl:
                            if tid not in link.get("matched_template_ids", []):
                                if not link.get("matched_template_ids"):
                                    link["matched_template_ids"] = []
                                link["matched_template_ids"].append(tid)
                            break

        # 收集所有链条节点名称
        chain_node_names: Set[str] = set()
        for ch in chains:
            for cn in ch.get("chain_nodes", []):
                chain_node_names.add(cn)

        # 收集有边的节点ID
        connected_ids: Set[str] = set()
        for l in links:
            connected_ids.add(l["source"])
            connected_ids.add(l["target"])

        # 分类：主图谱节点 vs 孤立节点
        main_nodes = []
        orphan_nodes = []

        for name, node in nodes.items():
            nid = node["id"]
            has_evidence = node.get("证据数量", 0) > 0
            has_triples = node.get("关联三元组数量", 0) > 0
            is_connected = nid in connected_ids or name in connected_ids
            in_chain = name in chain_node_names or nid in chain_node_names
            is_template_only = node.get("node_source") == "机理模板补全"

            if is_connected or (has_evidence and has_triples) or in_chain:
                main_nodes.append(node)

                # 模板补全但已接入链的节点，给出说明
                if is_template_only and not has_evidence:
                    if not node.get("说明"):
                        node["说明"] = "该节点由机理模板补全，暂无直接原始证据"
            else:
                # 孤立节点 → 隐藏
                reasons = []
                if not is_connected:
                    reasons.append("无边连接")
                if not has_evidence:
                    reasons.append("无证据")
                if not has_triples:
                    reasons.append("无三元组关联")
                if not in_chain:
                    reasons.append("不属于任何T1-T6链")

                orphan_nodes.append({
                    "id": nid,
                    "name": name,
                    "category_zh": node.get("category_zh", ""),
                    "孤立原因": "；".join(reasons),
                    "是否有证据": has_evidence,
                    "是否参与三元组": has_triples,
                    "是否属于模板链": in_chain,
                    "node_source": node.get("node_source", ""),
                })

        # 统计
        cat_count = {}
        for n in main_nodes:
            c = n.get("category_zh", "其他")
            cat_count[c] = cat_count.get(c, 0) + 1

        # 证据覆盖统计
        public_triples = [t for t in merged_triples if t.get("triple_source") != "机理模板补全"]
        public_with_evidence = [t for t in public_triples if t.get("evidence_texts") and len(t.get("evidence_texts", [])) > 0]
        evidence_coverage = round(len(public_with_evidence) / max(len(public_triples), 1), 4)
        template_ratio = round(len(completed_triples) / max(len(merged_triples) + len(completed_triples), 1), 4)

        main_nodes_with_evidence = len([n for n in main_nodes if n.get("证据数量", 0) > 0])
        main_links_with_evidence = len([l for l in links if l.get("evidence_texts") and len(l.get("evidence_texts", [])) > 0])

        stats = {
            "节点总数": len(nodes),
            "主图谱节点数": len(main_nodes),
            "边总数": len(links),
            "孤立节点数": len(orphan_nodes),
            "孤立节点比例": f"{round(len(orphan_nodes)/max(len(nodes),1)*100)}%",
            "被隐藏孤立节点数": len(orphan_nodes),
            "部件节点数": cat_count.get("部件", 0),
            "故障模式节点数": cat_count.get("故障模式", 0),
            "异常状态节点数": cat_count.get("异常状态", 0),
            "检测方式节点数": cat_count.get("检测方式", 0),
            "维修动作节点数": cat_count.get("维修动作", 0),
            "公开资料证据覆盖率": evidence_coverage,
            "模板补全比例": template_ratio,
            "有证据节点数": main_nodes_with_evidence,
            "有证据边数": main_links_with_evidence,
            "无证据节点数": len(main_nodes) - main_nodes_with_evidence,
            "无证据边数": len(links) - main_links_with_evidence,
        }

        # 保存到文件
        gdir = os.path.join(BASE, "data", "graph")
        os.makedirs(gdir, exist_ok=True)

        with open(os.path.join(gdir, "nodes.json"), "w", encoding="utf-8") as f:
            json.dump(main_nodes, f, ensure_ascii=False, indent=2)
        with open(os.path.join(gdir, "links.json"), "w", encoding="utf-8") as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        with open(os.path.join(gdir, "orphan_nodes.json"), "w", encoding="utf-8") as f:
            json.dump(orphan_nodes, f, ensure_ascii=False, indent=2)
        with open(os.path.join(gdir, "graph_statistics.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        return {
            "图谱名称": "液压伺服阀故障维修知识图谱",
            "节点总数": len(main_nodes),
            "边总数": len(links),
            "节点列表": main_nodes,
            "边列表": links,
            "事件链列表": chains,
            "孤立节点": orphan_nodes,
            "图例": {k: NODE_COLORS.get(k) for k in NODE_COLORS},
            "统计": stats,
        }

    def _add_or_update_node(self, nodes, name, node_type, triple_source, triple, template_id=""):
        if name in nodes:
            node = nodes[name]
        else:
            node = {
                "id": name, "name": name, "label_zh": name,
                "category_zh": node_type, "node_type_zh": node_type,
                "node_source": triple_source,
                "source_ids": [], "source_types": [], "source_titles": [],
                "source_files": [], "paragraph_ids": [],
                "evidence_ids": [], "evidence_texts": [], "evidence_spans": [],
                "related_triple_ids": [], "matched_template_ids": [],
                "证据数量": 0, "关联三元组数量": 0,
                "置信度": 0.0, "说明": "",
                "symbolSize": SIZES.get(node_type, 24),
                "itemStyle": {"color": NODE_COLORS.get(node_type, "#95A5A6")},
            }
            nodes[name] = node

        for sid in triple.get("source_ids", [triple.get("source_id", "")]):
            if sid and sid not in node["source_ids"]:
                node["source_ids"].append(sid)
        for st in triple.get("source_titles", [triple.get("source_title", "")]):
            if st and st not in node["source_titles"]:
                node["source_titles"].append(st)
        for pid in triple.get("paragraph_ids", [triple.get("paragraph_id", 0)]):
            if pid and pid not in node["paragraph_ids"]:
                node["paragraph_ids"].append(pid)
        for et in triple.get("evidence_texts", [triple.get("evidence_text", "")]):
            if et and et not in node["evidence_texts"]:
                node["evidence_texts"].append(et)
        for es in triple.get("evidence_spans", [triple.get("evidence_span", "")]):
            if es and es not in node["evidence_spans"]:
                node["evidence_spans"].append(es)

        tid = triple.get("merged_triple_id", triple.get("triple_id", ""))
        if tid and tid not in node["related_triple_ids"]:
            node["related_triple_ids"].append(tid)
        if template_id and template_id not in node["matched_template_ids"]:
            node["matched_template_ids"].append(template_id)

        node["证据数量"] = len(node["evidence_texts"])
        node["关联三元组数量"] = len(node["related_triple_ids"])

        conf = triple.get("confidence", 0.0)
        if conf > node["置信度"]:
            node["置信度"] = conf

        if triple_source == "机理模板补全":
            if node["node_source"] != "公开资料抽取" and node["node_source"] != "多来源融合":
                node["node_source"] = "机理模板补全"
        elif triple_source == "多来源融合":
            node["node_source"] = "多来源融合"
        elif triple_source == "公开资料抽取":
            if node["node_source"] == "机理模板补全":
                node["node_source"] = "多来源融合"

        if triple_source == "机理模板补全" and not node.get("证据数量"):
            node["说明"] = "该节点由机理模板补全，暂无直接原始证据。需要在公开资料中找到对应原文支撑。"

    def _build_link(self, subject, predicate, object_, triple, template_id="", triple_source="公开资料抽取"):
        link_id = f"LINK-{subject}-{predicate}-{object_}"[:80]

        color_map = {
            "包含": "#9B59B6", "发生于": "#E74C3C", "导致": "#E74C3C",
            "演化为": "#F39C12", "表现为": "#F39C12",
            "由检测确认": "#3498DB", "由维修处理": "#2ECC71",
            "复测验证": "#1ABC9C", "具有证据": "#95A5A6",
            "匹配机理模板": "#1ABC9C", "影响": "#E91E63", "伴随": "#FF9800",
        }

        edge_source = triple_source
        description = ""
        if triple_source == "机理模板补全":
            description = triple.get("说明", "该边由液压伺服阀机理模板补全，用于表达故障演化逻辑，暂无直接原始证据。")
            edge_source = "机理模板补全"

        evidence_texts = triple.get("evidence_texts", [triple.get("evidence_text", "")])
        evidence_texts = [e for e in evidence_texts if e]

        return {
            "id": link_id,
            "source": subject, "target": object_,
            "source_name": subject, "target_name": object_,
            "relation": predicate, "relation_zh": predicate, "label_zh": predicate,
            "edge_source": edge_source,
            "source_ids": triple.get("source_ids", [triple.get("source_id", "")]),
            "source_types": triple.get("source_types", [triple.get("source_type", "")]),
            "source_titles": triple.get("source_titles", [triple.get("source_title", "")]),
            "paragraph_ids": triple.get("paragraph_ids", [triple.get("paragraph_id", 0)]),
            "evidence_ids": triple.get("evidence_ids", []),
            "evidence_texts": evidence_texts,
            "evidence_spans": triple.get("evidence_spans", [triple.get("evidence_span", "")]),
            "triple_id": triple.get("merged_triple_id", triple.get("triple_id", "")),
            "matched_template_ids": [template_id] if template_id else [],
            "置信度": triple.get("confidence", 0.5),
            "说明": description,
            "lineStyle": {"color": color_map.get(predicate, "#95A5A6"), "width": 2},
        }

    def build_kg_response(self, nodes, links):
        cats = [{"name": k, "itemStyle": {"color": v}} for k, v in NODE_COLORS.items()]
        return {"nodes": nodes, "links": links, "categories": cats}


graph_builder = GraphBuildService()
