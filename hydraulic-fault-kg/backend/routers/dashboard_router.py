# -*- coding: utf-8 -*-
"""
首页统计摘要路由 - 显示三元组、证据、图谱统计

统计指标:
  公开资料, 液压段落,
  原始三元组, 融合三元组, 公开资料抽取三元组, 机理模板补全三元组,
  证据数量, 证据覆盖率, 模板补全比例,
  图谱节点, 图谱边, 孤立节点数, 孤立节点比例
"""
import os, json
from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["首页统计"])
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.get("/summary")
def dashboard_summary():
    stats = {
        "公开资料": 0, "液压段落": 0,
        "原始三元组": 0, "融合三元组": 0,
        "公开资料抽取三元组": 0, "机理模板补全三元组": 0,
        "证据数量": 0, "公开资料证据覆盖率": 0, "模板补全比例": 0,
        "图谱节点": 0, "图谱边": 0,
        "孤立节点数": 0, "孤立节点比例": "0%",
        "问答记录": 0,
    }

    # 公开资料
    reg_path = os.path.join(BASE, "data", "source_registry.json")
    if os.path.exists(reg_path):
        with open(reg_path, encoding="utf-8") as f:
            stats["公开资料"] = len(json.load(f).get("sources", []))

    # 液压段落
    fp_path = os.path.join(BASE, "data", "processed", "filtered_paragraphs.json")
    if os.path.exists(fp_path):
        with open(fp_path, encoding="utf-8") as f:
            stats["液压段落"] = len(json.load(f).get("过滤后段落", []))

    # 原始三元组
    tp = os.path.join(BASE, "data", "extracted", "triples.json")
    if os.path.exists(tp):
        with open(tp, encoding="utf-8") as f:
            data = json.load(f)
            stats["原始三元组"] = data.get("三元组总数", len(data.get("三元组列表", [])))

    # 融合三元组
    mp = os.path.join(BASE, "data", "extracted", "merged_triples.json")
    if os.path.exists(mp):
        with open(mp, encoding="utf-8") as f:
            data = json.load(f)
            merged = data.get("融合三元组列表", [])
            stats["融合三元组"] = data.get("融合三元组数", len(merged))
            stats["公开资料抽取三元组"] = len([t for t in merged if t.get("triple_source") == "公开资料抽取" or t.get("triple_source") == "多来源融合"])
            stats["机理模板补全三元组"] = len([t for t in merged if t.get("triple_source") == "机理模板补全"])

    # 证据
    ep = os.path.join(BASE, "data", "extracted", "evidence.json")
    if os.path.exists(ep):
        with open(ep, encoding="utf-8") as f:
            data = json.load(f)
            evd_list = data.get("证据列表", [])
            stats["证据数量"] = len([e for e in evd_list if e.get("evidence_text")])

    # 图谱统计
    gs_path = os.path.join(BASE, "data", "graph", "graph_statistics.json")
    if os.path.exists(gs_path):
        with open(gs_path, encoding="utf-8") as f:
            gs = json.load(f)
            for k in ["公开资料证据覆盖率", "模板补全比例", "孤立节点数", "孤立节点比例",
                       "有证据节点数", "有证据边数", "无证据节点数", "无证据边数"]:
                if k in gs:
                    stats[k] = gs[k]

    # 如果stats中没有从gs中得到，从文件直接计算
    if not stats["公开资料证据覆盖率"]:
        mtp = os.path.join(BASE, "data", "extracted", "merged_triples.json")
        if os.path.exists(mtp):
            with open(mtp, encoding="utf-8") as f:
                data = json.load(f)
                merged = data.get("融合三元组列表", [])
                public = [t for t in merged if t.get("triple_source") != "机理模板补全"]
                if public:
                    with_ev = [t for t in public if t.get("evidence_texts") and len(t.get("evidence_texts", [])) > 0]
                    stats["公开资料证据覆盖率"] = round(len(with_ev) / len(public), 4)
                total = len(merged)
                tpl = len([t for t in merged if t.get("triple_source") == "机理模板补全"])
                if total:
                    stats["模板补全比例"] = round(tpl / total, 4)

    # 节点/边
    nodes_path = os.path.join(BASE, "data", "graph", "nodes.json")
    links_path = os.path.join(BASE, "data", "graph", "links.json")
    orphan_path = os.path.join(BASE, "data", "graph", "orphan_nodes.json")

    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            stats["图谱节点"] = len(json.load(f))
    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            stats["图谱边"] = len(json.load(f))
    if os.path.exists(orphan_path):
        with open(orphan_path, encoding="utf-8") as f:
            orphan = json.load(f)
            if not stats["孤立节点数"]:
                stats["孤立节点数"] = len(orphan)

    if stats["图谱节点"] and stats["孤立节点数"]:
        total_nodes = stats["图谱节点"] + stats["孤立节点数"]
        stats["孤立节点比例"] = f"{round(stats['孤立节点数']/max(total_nodes,1)*100)}%"

    try:
        from database import get_table_count
        stats["问答记录"] = get_table_count("qa_records")
    except:
        pass

    return stats
