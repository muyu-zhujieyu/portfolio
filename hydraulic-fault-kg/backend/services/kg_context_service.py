"""
知识图谱上下文构建服务 - 为问答提供基于三元组的图谱检索支持

检索内容:
  - 相关三元组（按关键词匹配 subject/object）
  - 相关三元组路径（BFS连接路径）
  - 相关故障链（T1-T6模板匹配）
  - 相关证据（evidence原文）
  - 相关节点和边（图谱可视化数据）

必须支持的关键词检索:
  油液污染、阀芯卡滞、喷嘴堵塞、压力波动、零位漂移、响应迟缓、
  内泄漏、线圈发热、力矩马达、气隙、密封、维修、证据
"""
import json
import os
from typing import List, Dict, Any, Optional, Set


class KGContextService:
    """知识图谱上下文检索器 - 基于三元组构建问答上下文"""

    # 关键词映射到故障模式/状态
    KEYWORD_MAPPING = {
        "油液污染": ["油液污染", "液压油污染", "油液脏污"],
        "阀芯卡滞": ["阀芯卡滞", "阀芯卡住", "滑阀卡滞", "阀芯卡阻"],
        "喷嘴堵塞": ["喷嘴堵塞", "喷嘴孔堵塞", "喷嘴阻塞"],
        "压力波动": ["压力波动", "压力不稳", "压力脉动"],
        "零位漂移": ["零位漂移", "零点漂移", "零位偏移"],
        "响应迟缓": ["响应迟缓", "响应变慢", "动作迟缓"],
        "内泄漏": ["内泄漏", "内部泄漏", "泵内泄", "内泄"],
        "线圈发热异常": ["线圈发热异常", "线圈发热", "温升异常"],
        "力矩马达异常": ["力矩马达异常", "力矩马达故障"],
        "气隙不对称": ["气隙不对称", "气隙偏差", "气隙不均匀"],
        "密封失效": ["密封失效", "密封磨损", "密封泄漏"],
        "维修": ["维修", "更换", "清洗", "修复", "调整", "检查"],
        "证据": ["证据", "检测结果", "实测", "确认"],
    }

    def __init__(self):
        self._merged_triples: List[Dict] = []
        self._graph_nodes: List[Dict] = []
        self._graph_links: List[Dict] = []
        self._graph_chains: List[Dict] = []
        self._loaded = False

    def _ensure_loaded(self):
        """确保图谱数据已加载"""
        if self._loaded:
            return
        self._load_graph_data()
        self._loaded = True

    def _load_graph_data(self):
        """从 data/ 加载三元组和图谱数据"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 加载融合三元组
        mtp = os.path.join(base_dir, "data", "extracted", "merged_triples.json")
        if os.path.exists(mtp):
            with open(mtp, encoding="utf-8") as f:
                data = json.load(f)
                self._merged_triples = data if isinstance(data, list) else data.get("融合三元组列表", [])

        # 加载图谱数据
        for fname, attr in [
            ("nodes.json", "_graph_nodes"),
            ("links.json", "_graph_links"),
            ("chains.json", "_graph_chains"),
        ]:
            fp = os.path.join(base_dir, "data", "graph", fname)
            if os.path.exists(fp):
                with open(fp, encoding="utf-8") as f:
                    setattr(self, attr, json.load(f))

    # ================================================================
    # 公开接口：构建问答上下文
    # ================================================================

    def build_qa_context(self, question: str) -> Dict[str, Any]:
        """根据用户问题构建完整的图谱检索上下文"""
        self._ensure_loaded()

        # 1. 关键词提取
        keywords = self._extract_keywords(question)

        # 2. 检索相关三元组
        related_triples = self._search_triples(keywords)

        # 3. 检索三元组路径（BFS）
        triple_paths = self._find_triple_paths(keywords)

        # 4. 检索相关故障链
        chains = self._search_chains(keywords)

        # 5. 检索相关证据
        evidence_list = self._collect_evidence(related_triples)

        # 6. 检索相关节点和边
        nodes, links = self._search_graph(keywords, related_triples)

        # 7. 图谱统计
        stats = {
            "三元组总数": len(self._merged_triples),
            "节点总数": len(self._graph_nodes),
            "边总数": len(self._graph_links),
            "事件链总数": len(self._graph_chains),
        }

        return {
            "问题": question,
            "提取关键词": keywords,
            "相关三元组": related_triples,
            "三元组路径": triple_paths,
            "相关故障链": chains,
            "相关证据": evidence_list,
            "相关节点": nodes,
            "相关边": links,
            "图谱统计": stats,
        }

    # ================================================================
    # 关键词提取
    # ================================================================

    def _extract_keywords(self, question: str) -> List[str]:
        """从用户问题中提取液压领域关键词"""
        keywords = []

        for kw, aliases in self.KEYWORD_MAPPING.items():
            for alias in aliases:
                if alias in question:
                    keywords.append(kw)
                    break

        # 也从节点名称中匹配
        for node in self._graph_nodes[:100]:
            name = node.get("name", "")
            if len(name) >= 2 and name in question:
                if name not in keywords:
                    keywords.append(name)

        return list(set(keywords))[:15]

    # ================================================================
    # 三元组检索
    # ================================================================

    def _search_triples(self, keywords: List[str]) -> List[Dict]:
        """根据关键词检索相关三元组"""
        matched = []
        seen = set()

        for triple in self._merged_triples:
            subj = triple.get("subject", "")
            obj = triple.get("object", "")
            pred = triple.get("predicate", "")
            search_text = f"{subj} {pred} {obj}"

            for kw in keywords:
                if kw in search_text:
                    key = triple.get("merged_triple_id", "")
                    if key not in seen:
                        seen.add(key)
                        matched.append(triple)
                    break

        return matched[:30]

    # ================================================================
    # 三元组路径查找 (BFS)
    # ================================================================

    def _find_triple_paths(self, keywords: List[str]) -> List[Dict]:
        """在融合三元组中查找关键词之间的连接路径"""
        if len(keywords) < 2:
            return []

        # 构建邻接表
        adj = {}
        for t in self._merged_triples:
            subj = t.get("subject", "")
            obj = t.get("object", "")
            if subj not in adj:
                adj[subj] = []
            adj[subj].append((obj, t))

        paths = []
        for kw1 in keywords[:3]:
            for kw2 in keywords[:3]:
                if kw1 == kw2:
                    continue
                # BFS 找路径
                path = self._bfs_shortest_path(adj, kw1, kw2)
                if path:
                    paths.append({
                        "start": kw1,
                        "end": kw2,
                        "path_triples": path,
                        "path_text": " → ".join(
                            [p.get("subject", "") + " —" + p.get("predicate", "") + "→ " + p.get("object", "")
                             for p in path]
                        ),
                    })

        return paths[:10]

    def _bfs_shortest_path(self, adj: Dict, start: str, end: str) -> List[Dict]:
        """BFS最短路径"""
        from collections import deque

        if start not in adj or end == start:
            return []

        queue = deque([(start, [])])
        visited = {start}

        while queue:
            node, path = queue.popleft()
            if node == end:
                return path

            for neighbor, triple in adj.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [triple]))

        return []

    # ================================================================
    # 故障链检索
    # ================================================================

    def _search_chains(self, keywords: List[str]) -> List[Dict]:
        """检索相关故障演化链"""
        matched = []

        for chain in self._graph_chains:
            if not isinstance(chain, dict):
                continue
            chain_text = chain.get("chain_text", "")
            tname = chain.get("template_name", "")

            for kw in keywords:
                if kw in chain_text or kw in tname:
                    matched.append(chain)
                    break

        return matched[:10]

    # ================================================================
    # 证据收集
    # ================================================================

    def _collect_evidence(self, triples: List[Dict]) -> List[Dict]:
        """从相关三元组中收集证据"""
        evidence_list = []
        seen = set()

        for t in triples:
            evidence_texts = t.get("evidence_texts", [])
            source_titles = t.get("source_titles", [])

            for i, et in enumerate(evidence_texts):
                if et and et not in seen:
                    seen.add(et)
                    title = source_titles[i] if i < len(source_titles) else ""
                    evidence_list.append({
                        "triple_id": t.get("merged_triple_id", ""),
                        "triple_text": f"{t.get('subject','')} — {t.get('predicate','')} — {t.get('object','')}",
                        "source_title": title,
                        "evidence_text": et,
                        "triple_source": t.get("triple_source", ""),
                    })

        return evidence_list[:20]

    # ================================================================
    # 图谱节点/边检索
    # ================================================================

    def _search_graph(self, keywords: List[str], triples: List[Dict]) -> tuple:
        """检索相关图谱节点和边"""
        matched_node_ids: Set[str] = set()
        matched_nodes = []
        matched_links = []

        # 从三元组中提取相关节点名称
        related_names = set()
        for t in triples:
            related_names.add(t.get("subject", ""))
            related_names.add(t.get("object", ""))

        for node in self._graph_nodes:
            if not isinstance(node, dict):
                continue
            name = node.get("name", "")
            cat = node.get("category_zh", "")
            # 关键词匹配或三元组关联
            matched = False
            for kw in keywords:
                if kw in name or kw in cat:
                    matched = True
                    break
            if name in related_names:
                matched = True

            if matched:
                nid = node.get("id", name)
                if nid not in matched_node_ids:
                    matched_node_ids.add(nid)
                    matched_nodes.append(node)

        # 匹配相关边
        for link in self._graph_links:
            if not isinstance(link, dict):
                continue
            src = link.get("source", "")
            tgt = link.get("target", "")
            if src in matched_node_ids or tgt in matched_node_ids:
                matched_links.append(link)

        return matched_nodes[:20], matched_links[:20]


# 单例
kg_context = KGContextService()
