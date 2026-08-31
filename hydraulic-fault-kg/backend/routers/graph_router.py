"""
知识图谱路由 - 基于三元组构建图谱并提供 ECharts 可视化数据

API:
  POST /api/graph/build     执行完整图谱构建流水线（核心接口）
  GET  /api/kg              获取 ECharts 可视化数据（中文节点+中文边+中文图例）
  GET  /api/graph/nodes     获取图谱节点列表
  GET  /api/graph/links     获取图谱边列表
  GET  /api/graph/chains    获取事件链列表
  GET  /api/graph/node/{id} 获取节点详情
  GET  /api/graph/link/{id} 获取边详情
"""
import json
import os
from typing import Dict, Optional
from fastapi import APIRouter

from services.event_extract_service import event_extractor
from services.evidence_anchor_service import evidence_anchor
from services.fusion_service import fusion
from services.mechanism_validation_service import mechanism_validator
from services.graph_build_service import graph_builder

router = APIRouter(prefix="/api/graph", tags=["知识图谱"])

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================================================================
# POST /api/graph/build - 执行完整图谱构建流水线
# ================================================================

@router.post("/build")
def build_graph():
    """执行完整的知识图谱构建流水线

    流水线步骤:
      1. 加载过滤段落 (data/processed/filtered_paragraphs.json)
      2. 三元组抽取 (event_extract_service)
      3. 证据锚定 (evidence_anchor_service)
      4. 三元组融合 (fusion_service)
      5. 机理模板校验 (mechanism_validation_service)
      6. 图谱节点边生成 (graph_build_service)
      7. 保存到 data/graph/ 目录
    """
    # 步骤1: 加载过滤段落
    filtered_data = _load_filtered_paragraphs()
    if not filtered_data:
        return {"状态": "失败", "错误": "无法加载过滤段落，请先执行 POST /api/sources/filter"}

    # 步骤2: 三元组抽取
    extract_result = event_extractor.extract_from_filtered(filtered_data)
    if extract_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "三元组抽取失败"}

    raw_triples = extract_result.get("三元组列表", [])

    # 步骤3: 证据锚定
    anchor_result = evidence_anchor.anchor_triples(extract_result)
    evidence_list = anchor_result.get("证据列表", [])

    # 步骤4: 三元组融合
    fusion_result = fusion.merge_triples(raw_triples)
    merged_triples = fusion_result.get("融合三元组列表", [])

    # 步骤5: 机理模板校验
    validation_result = mechanism_validator.validate_all(merged_triples)
    completed_triples = validation_result.get("completed_triples", [])
    chains = validation_result.get("chains", [])

    # 步骤6: 图谱构建
    graph_result = graph_builder.build_full_graph(
        merged_triples=merged_triples,
        completed_triples=completed_triples,
        chains=chains,
    )

    # 步骤7: 保存到文件
    _save_all_results(
        raw_triples=raw_triples,
        merged_triples=merged_triples,
        evidence_list=evidence_list,
        graph_result=graph_result,
        chains=chains,
        validation_result=validation_result,
    )

    return {
        "状态": "成功",
        "原始三元组数": len(raw_triples),
        "融合三元组数": len(merged_triples),
        "证据数": len(evidence_list),
        "模板补全三元组数": len(completed_triples),
        "节点总数": graph_result.get("节点总数", 0),
        "边总数": graph_result.get("边总数", 0),
        "事件链总数": len(chains),
        "图例": graph_result.get("图例", {}),
        "保存路径": {
            "原始三元组": "data/extracted/triples.json",
            "融合三元组": "data/extracted/merged_triples.json",
            "证据文件": "data/extracted/evidence.json",
            "节点文件": "data/graph/nodes.json",
            "边文件": "data/graph/links.json",
            "事件链文件": "data/graph/chains.json",
        },
    }


# ================================================================
# GET /api/kg - 获取 ECharts 可视化数据
# ================================================================

@router.get("/kg")
def get_kg_for_echarts():
    """获取 ECharts 可直接渲染的中文知识图谱数据

    优先读取 data/graph/ 下的 JSON 文件。

    返回:
        {
            "nodes": [...],      # ECharts 节点数组
            "links": [...],      # ECharts 边数组
            "categories": [...]  # ECharts 分类/图例
        }
    """
    nodes_path = _get_graph_path("nodes.json")
    links_path = _get_graph_path("links.json")

    nodes = []
    links = []

    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            nodes_data = json.load(f)
            nodes = nodes_data if isinstance(nodes_data, list) else nodes_data.get("节点列表", [])

    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            links_data = json.load(f)
            links = links_data if isinstance(links_data, list) else links_data.get("边列表", [])

    # 加载孤立节点（可选显示）
    orphan_path = _get_graph_path("orphan_nodes.json")
    orphan_nodes = []
    if os.path.exists(orphan_path):
        with open(orphan_path, encoding="utf-8") as f:
            orphan_nodes = json.load(f)

    # 加载统计
    gs_path = _get_graph_path("graph_statistics.json")
    stats = {}
    if os.path.exists(gs_path):
        with open(gs_path, encoding="utf-8") as f:
            stats = json.load(f)

    # 加载链条
    chains_path = _get_graph_path("chains.json")
    chains = []
    if os.path.exists(chains_path):
        with open(chains_path, encoding="utf-8") as f:
            chains = json.load(f)

    categories = [
        {"name": "部件", "itemStyle": {"color": "#9B59B6"}},
        {"name": "故障模式", "itemStyle": {"color": "#E74C3C"}},
        {"name": "异常状态", "itemStyle": {"color": "#F39C12"}},
        {"name": "检测方式", "itemStyle": {"color": "#3498DB"}},
        {"name": "维修动作", "itemStyle": {"color": "#2ECC71"}},
        {"name": "证据来源", "itemStyle": {"color": "#95A5A6"}},
        {"name": "机理模板", "itemStyle": {"color": "#1ABC9C"}},
        {"name": "影响结果", "itemStyle": {"color": "#E91E63"}},
    ]

    return {
        "图谱名称": "液压伺服阀故障维修知识图谱",
        "节点总数": len(nodes),
        "边总数": len(links),
        "nodes": nodes,
        "links": links,
        "categories": categories,
        "chains": chains,
        "orphan_nodes": orphan_nodes,
        "统计": stats,
        "template_source": "机理约束模板",
        "template_role": "校验抽取三元组、组织故障演化路径、必要时补全缺失关系",
    }


# ================================================================
# GET /api/graph/nodes - 获取节点列表
# ================================================================

@router.get("/nodes")
def list_nodes(node_type: str = None):
    """获取图谱节点列表

    Args:
        node_type: 可选，按节点类型过滤（部件/故障模式/异常状态/检测方式/维修动作）
    """
    nodes_path = _get_graph_path("nodes.json")
    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            data = json.load(f)
        nodes = data if isinstance(data, list) else data.get("节点列表", [])

        if node_type:
            nodes = [
                n for n in nodes
                if n.get("category_zh") == node_type or n.get("node_type_zh") == node_type
            ]

        return {"总数": len(nodes), "节点列表": nodes[:200]}

    return {"总数": 0, "节点列表": []}


# ================================================================
# GET /api/graph/links - 获取边列表
# ================================================================

@router.get("/links")
def list_links(relation: str = None):
    """获取图谱边列表

    Args:
        relation: 可选，按关系类型过滤（导致/表现为/由检测确认/由维修处理等）
    """
    links_path = _get_graph_path("links.json")
    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            data = json.load(f)
        links = data if isinstance(data, list) else data.get("边列表", [])

        if relation:
            links = [l for l in links if l.get("relation_zh") == relation]

        return {"总数": len(links), "边列表": links[:200]}

    return {"总数": 0, "边列表": []}


# ================================================================
# GET /api/graph/chains - 获取事件链列表
# ================================================================

@router.get("/chains")
def list_chains():
    """获取T1-T6机理模板链条列表"""
    chains_path = _get_graph_path("chains.json")
    if os.path.exists(chains_path):
        with open(chains_path, encoding="utf-8") as f:
            chains = json.load(f)
        return {
            "总数": len(chains) if isinstance(chains, list) else 0,
            "事件链列表": chains if isinstance(chains, list) else [],
        }

    return {"总数": 0, "事件链列表": []}


# ================================================================
# GET /api/graph/node/{id} - 节点详情
# ================================================================

@router.get("/node/{node_id}")
def get_node_detail(node_id: str):
    """获取节点详情（含关联三元组和证据）

    Args:
        node_id: 节点ID（即节点名称）
    """
    nodes_path = _get_graph_path("nodes.json")
    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            nodes = json.load(f)
        nodes = nodes if isinstance(nodes, list) else nodes.get("节点列表", [])
        for node in nodes:
            if node.get("id") == node_id or node.get("name") == node_id:
                return node
        return {"错误": f"节点 {node_id} 不存在"}

    return {"错误": f"节点 {node_id} 不存在"}


# ================================================================
# GET /api/graph/link/{link_id} - 边详情（新增）
# ================================================================

@router.get("/link/{link_id}")
def get_link_detail(link_id: str):
    """获取边详情（含三元组证据）

    Args:
        link_id: 边ID
    """
    links_path = _get_graph_path("links.json")
    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            links = json.load(f)
        links = links if isinstance(links, list) else links.get("边列表", [])
        for link in links:
            if link.get("id") == link_id:
                return link
        return {"错误": f"边 {link_id} 不存在"}

    return {"错误": f"边 {link_id} 不存在"}


# ================================================================
# 内部辅助函数
# ================================================================

def _load_filtered_paragraphs() -> Dict:
    """加载过滤段落"""
    file_path = os.path.join(BASE, "data", "processed", "filtered_paragraphs.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _get_graph_path(filename: str) -> str:
    """获取 data/graph/ 下的文件路径"""
    return os.path.join(BASE, "data", "graph", filename)


def _save_all_results(
    raw_triples: list, merged_triples: list, evidence_list: list,
    graph_result: Dict, chains: list, validation_result: Dict,
):
    """保存所有结果到文件"""
    # 提取目录
    edir = os.path.join(BASE, "data", "extracted")
    gdir = os.path.join(BASE, "data", "graph")
    os.makedirs(edir, exist_ok=True)
    os.makedirs(gdir, exist_ok=True)

    # 保存原始三元组
    with open(os.path.join(edir, "triples.json"), "w", encoding="utf-8") as f:
        json.dump({
            "三元组总数": len(raw_triples),
            "三元组列表": raw_triples,
        }, f, ensure_ascii=False, indent=2)

    # 保存融合三元组
    with open(os.path.join(edir, "merged_triples.json"), "w", encoding="utf-8") as f:
        json.dump({
            "融合三元组数": len(merged_triples),
            "融合三元组列表": merged_triples,
        }, f, ensure_ascii=False, indent=2)

    # 保存证据
    with open(os.path.join(edir, "evidence.json"), "w", encoding="utf-8") as f:
        json.dump({
            "证据总数": len(evidence_list),
            "证据列表": evidence_list,
        }, f, ensure_ascii=False, indent=2)

    # 图谱数据由 graph_build_service 保存
    print(f"  [OK] 原始三元组已保存: triples.json ({len(raw_triples)}条)")
    print(f"  [OK] 融合三元组已保存: merged_triples.json ({len(merged_triples)}条)")
    print(f"  [OK] 证据已保存: evidence.json ({len(evidence_list)}条)")
    print(f"  [OK] 图谱已保存: nodes.json ({graph_result.get('节点总数', 0)}节点)")
    print(f"  [OK] 图谱已保存: links.json ({graph_result.get('边总数', 0)}边)")
    print(f"  [OK] 链条已保存: chains.json ({len(chains)}条)")
