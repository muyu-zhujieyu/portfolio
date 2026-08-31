# -*- coding: utf-8 -*-
"""
一键重建流水线路由 - 从source_registry到图谱入库的完整流程

POST /api/pipeline/rebuild-all 执行完整重建流程:
  1. 读取公开资料
  2. 清洗过滤段落
  3. 抽取原始三元组 triples.json
  4. 生成证据 evidence.json
  5. 融合三元组 merged_triples.json
  6. 机理模板校验
  7. 模板缺失关系补全
  8. 构建 nodes.json
  9. 构建 links.json
  10. 构建 chains.json
  11. 更新 dashboard summary
  12. 更新 /api/kg
"""
import json
import os
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/pipeline", tags=["重建流水线"])

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.post("/rebuild-all")
def rebuild_all():
    """一键重建：加载来源→解析→过滤→三元组抽取→证据锚定→融合→机理校验→图谱构建"""
    logs = []
    def log(msg):
        logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        print(msg)

    try:
        # ─── 步骤1: 加载来源 ───
        log("[1/12] 加载 source_registry.json...")
        reg_path = os.path.join(BASE, "data", "source_registry.json")
        if not os.path.exists(reg_path):
            return {"状态": "失败", "错误": "source_registry.json不存在"}

        with open(reg_path, encoding="utf-8") as f:
            registry = json.load(f)
        source_count = len(registry.get("sources", []))
        log(f"  来源: {source_count} 份")

        # ─── 步骤2: 解析文档 ──
        log("[2/12] 解析文档...")
        from services.source_reader_service import source_reader
        parse_result = source_reader.parse_all_sources()
        log(f"  解析: {parse_result.get('解析成功数', 0)}/{parse_result.get('来源总数', 0)}")

        # ─── 步骤3: 清洗段落 ──
        log("[3/12] 清洗段落...")
        from services.text_clean_service import text_cleaner
        clean_result = text_cleaner.clean_paragraphs(parse_result)
        log(f"  清洗后: {clean_result.get('清洗后段落数', 0)} 段")

        # ─── 步骤4: 领域过滤 ──
        log("[4/12] 液压领域过滤...")
        from services.domain_filter_service import domain_filter
        filter_result = domain_filter.filter_cleaned_paragraphs(clean_result, threshold=0.02)
        fp_count = filter_result.get("液压相关段落数", 0)
        log(f"  液压相关: {fp_count} 段 (保留率 {filter_result.get('过滤保留率', 0)})")

        # 保存 filtered_paragraphs.json
        os.makedirs(os.path.join(BASE, "data", "processed"), exist_ok=True)
        with open(os.path.join(BASE, "data", "processed", "filtered_paragraphs.json"), "w", encoding="utf-8") as f:
            json.dump(filter_result, f, ensure_ascii=False, indent=2)

        # ─── 步骤5: 三元组抽取 ──
        log("[5/12] 液压伺服阀故障维修三元组抽取...")
        from services.event_extract_service import event_extractor
        extract_result = event_extractor.extract_from_filtered(filter_result)
        raw_triples = extract_result.get("三元组列表", [])
        raw_count = len(raw_triples)
        log(f"  原始三元组: {raw_count} 条")
        log(f"  类型统计: {extract_result.get('类型统计', {})}")

        # ─── 步骤6: 证据锚定 ──
        log("[6/12] 证据锚定...")
        from services.evidence_anchor_service import evidence_anchor
        anchor_result = evidence_anchor.anchor_triples(extract_result)
        evidence_list = anchor_result.get("证据列表", [])
        evd_count = len(evidence_list)
        log(f"  证据: {evd_count} 条 (锚定率 {anchor_result.get('锚定统计', {}).get('锚定率', 0)})")

        # ─── 步骤7: 保存原始三元组 ──
        log("[7/12] 保存原始三元组 triples.json...")
        edir = os.path.join(BASE, "data", "extracted")
        os.makedirs(edir, exist_ok=True)
        with open(os.path.join(edir, "triples.json"), "w", encoding="utf-8") as f:
            json.dump({"三元组总数": raw_count, "三元组列表": raw_triples}, f, ensure_ascii=False, indent=2)

        # ─── 步骤8: 三元组融合 ──
        log("[8/12] 三元组融合...")
        from services.fusion_service import fusion
        fusion_result = fusion.merge_triples(raw_triples)
        merged_triples = fusion_result.get("融合三元组列表", [])
        merged_count = len(merged_triples)
        compression = fusion_result.get("压缩率", "0%")
        log(f"  融合后: {merged_count} 条 (压缩率 {compression})")

        # 保存融合三元组
        with open(os.path.join(edir, "merged_triples.json"), "w", encoding="utf-8") as f:
            json.dump({"融合三元组数": merged_count, "融合三元组列表": merged_triples}, f, ensure_ascii=False, indent=2)

        # 保存证据
        with open(os.path.join(edir, "evidence.json"), "w", encoding="utf-8") as f:
            json.dump({"证据总数": evd_count, "证据列表": evidence_list}, f, ensure_ascii=False, indent=2)

        # ─── 步骤9: 机理模板校验 ──
        log("[9/12] 机理模板校验 (T1-T6)...")
        from services.mechanism_validation_service import mechanism_validator
        validation_result = mechanism_validator.validate_all(merged_triples)
        completed_triples = validation_result.get("completed_triples", [])
        chains = validation_result.get("chains", [])
        stats = validation_result.get("统计", {})
        log(f"  命中: {stats.get('总命中三元组数', 0)}条, 缺失: {stats.get('总缺失三元组数', 0)}条, 补全: {stats.get('总补全三元组数', 0)}条")

        # ─── 步骤10: 图谱构建 ──
        log("[10/12] 图谱节点/边构建...")
        from services.graph_build_service import graph_builder
        graph_result = graph_builder.build_full_graph(
            merged_triples=merged_triples,
            completed_triples=completed_triples,
            chains=chains,
        )
        node_count = graph_result.get("节点总数", 0)
        link_count = graph_result.get("边总数", 0)
        log(f"  节点: {node_count}, 边: {link_count}")

        # ─── 步骤11: 更新 dashboard summary ──
        log("[11/12] 更新统计...")
        # 保存统计摘要
        summary = {
            "公开资料": source_count,
            "液压段落": fp_count,
            "原始三元组": raw_count,
            "融合三元组": merged_count,
            "证据数量": evd_count,
            "图谱节点": node_count,
            "图谱边": link_count,
            "模板命中三元组": stats.get("总命中三元组数", 0),
            "模板补全三元组": stats.get("总补全三元组数", 0),
        }
        with open(os.path.join(BASE, "data", "graph", "graph_statistics.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # ─── 步骤12: 完成 ──
        log("[12/12] 完成")

        return {
            "状态": "成功",
            "公开资料数量": source_count,
            "原始三元组数量": raw_count,
            "融合三元组数量": merged_count,
            "融合压缩率": compression,
            "证据数量": evd_count,
            "模板命中三元组数量": stats.get("总命中三元组数", 0),
            "模板缺失三元组数量": stats.get("总缺失三元组数", 0),
            "模板补全三元组数量": stats.get("总补全三元组数", 0),
            "图谱节点数量": node_count,
            "图谱边数量": link_count,
            "事件链数量": len(chains),
            "保存路径": {
                "原始三元组": "data/extracted/triples.json",
                "融合三元组": "data/extracted/merged_triples.json",
                "证据文件": "data/extracted/evidence.json",
                "节点文件": "data/graph/nodes.json",
                "边文件": "data/graph/links.json",
                "链条文件": "data/graph/chains.json",
                "校验报告": "data/graph/mechanism_validation_report.json",
            },
            "重建日志": logs,
        }

    except Exception as e:
        import traceback
        log(f"  错误: {str(e)}")
        return {
            "状态": "失败",
            "错误": str(e),
            "堆栈": traceback.format_exc(),
            "重建日志": logs,
        }


@router.get("/status")
def pipeline_status():
    """查看当前数据统计"""
    stats = {
        "公开资料": 0,
        "液压段落": 0,
        "原始三元组": 0,
        "融合三元组": 0,
        "证据数量": 0,
        "图谱节点": 0,
        "图谱边": 0,
        "事件链": 0,
    }

    # 从文件读取
    reg_path = os.path.join(BASE, "data", "source_registry.json")
    if os.path.exists(reg_path):
        with open(reg_path, encoding="utf-8") as f:
            stats["公开资料"] = len(json.load(f).get("sources", []))

    fp_path = os.path.join(BASE, "data", "processed", "filtered_paragraphs.json")
    if os.path.exists(fp_path):
        with open(fp_path, encoding="utf-8") as f:
            stats["液压段落"] = len(json.load(f).get("过滤后段落", []))

    triples_path = os.path.join(BASE, "data", "extracted", "triples.json")
    if os.path.exists(triples_path):
        with open(triples_path, encoding="utf-8") as f:
            data = json.load(f)
            stats["原始三元组"] = data.get("三元组总数", len(data.get("三元组列表", [])))

    merged_path = os.path.join(BASE, "data", "extracted", "merged_triples.json")
    if os.path.exists(merged_path):
        with open(merged_path, encoding="utf-8") as f:
            data = json.load(f)
            stats["融合三元组"] = data.get("融合三元组数", len(data.get("融合三元组列表", [])))

    evd_path = os.path.join(BASE, "data", "extracted", "evidence.json")
    if os.path.exists(evd_path):
        with open(evd_path, encoding="utf-8") as f:
            data = json.load(f)
            stats["证据数量"] = data.get("证据总数", len(data.get("证据列表", [])))

    nodes_path = os.path.join(BASE, "data", "graph", "nodes.json")
    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            stats["图谱节点"] = len(json.load(f))

    links_path = os.path.join(BASE, "data", "graph", "links.json")
    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            stats["图谱边"] = len(json.load(f))

    chains_path = os.path.join(BASE, "data", "graph", "chains.json")
    if os.path.exists(chains_path):
        with open(chains_path, encoding="utf-8") as f:
            stats["事件链"] = len(json.load(f))

    return stats
