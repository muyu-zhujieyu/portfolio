"""
三元组抽取路由 - 从过滤段落中抽取液压伺服阀故障维修三元组并锚定证据

API:
  POST /api/extraction/run        执行三元组抽取与证据锚定
  GET  /api/extraction/triples    获取已抽取三元组列表
  GET  /api/extraction/evidence   获取证据锚定列表
  GET  /api/extraction/statistics 获取统计信息
"""
import json
import os
from typing import Dict
from fastapi import APIRouter

from services.event_extract_service import event_extractor
from services.evidence_anchor_service import evidence_anchor

router = APIRouter(prefix="/api/extraction", tags=["三元组抽取"])

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================================================================
# POST /api/extraction/run - 执行三元组抽取与证据锚定
# ================================================================

@router.post("/run")
def run_extraction():
    """执行三元组抽取与证据锚定流水线

    流程:
      1. 读取 data/processed/filtered_paragraphs.json
      2. 从每个过滤段落中抽取液压伺服阀故障维修三元组
      3. 为每个三元组生成证据锚定记录
      4. 保存到 data/extracted/triples.json 和 data/extracted/evidence.json

    返回:
        - 三元组总数
        - 证据总数
        - 类型统计
        - 锚定统计
        - 保存路径
    """
    # 1. 加载过滤后的段落
    filtered_data = _load_filtered_paragraphs()
    if not filtered_data:
        return {
            "状态": "失败",
            "错误": "无法加载过滤段落，请先执行 POST /api/sources/filter",
        }

    # 2. 三元组抽取
    extract_result = event_extractor.extract_from_filtered(filtered_data)
    if extract_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "三元组抽取失败", "详情": extract_result}

    # 3. 证据锚定
    anchor_result = evidence_anchor.anchor_triples(extract_result)
    if anchor_result.get("状态") != "成功":
        return {"状态": "失败", "错误": "证据锚定失败", "详情": anchor_result}

    # 4. 保存到文件
    _save_extraction_results(extract_result, anchor_result)

    return {
        "状态": "成功",
        "三元组总数": extract_result.get("三元组总数", 0),
        "证据总数": anchor_result.get("证据总数", 0),
        "类型统计": extract_result.get("类型统计", {}),
        "锚定统计": anchor_result.get("锚定统计", {}),
        "保存路径": {
            "三元组文件": "data/extracted/triples.json",
            "证据文件": "data/extracted/evidence.json",
        },
    }


# ================================================================
# GET /api/extraction/triples - 获取已抽取三元组列表
# ================================================================

@router.get("/triples")
def list_triples():
    """获取已抽取的三元组列表

    优先读取 data/extracted/triples.json
    """
    triples_path = _get_extracted_path("triples.json")
    if os.path.exists(triples_path):
        with open(triples_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "来源": "文件",
            "三元组总数": data.get("三元组总数", 0),
            "三元组列表": data.get("三元组列表", []),
        }
    return {"来源": "无数据", "三元组总数": 0, "三元组列表": []}


# ================================================================
# GET /api/extraction/evidence - 获取证据锚定列表
# ================================================================

@router.get("/evidence")
def list_evidence():
    """获取证据锚定列表

    优先读取 data/extracted/evidence.json
    """
    evidence_path = _get_extracted_path("evidence.json")
    if os.path.exists(evidence_path):
        with open(evidence_path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "来源": "文件",
            "证据总数": data.get("证据总数", 0),
            "锚定统计": data.get("锚定统计", {}),
            "证据列表": data.get("证据列表", []),
        }
    return {"来源": "无数据", "证据总数": 0, "证据列表": []}


# ================================================================
# GET /api/extraction/statistics - 获取统计信息
# ================================================================

@router.get("/statistics")
def get_statistics():
    """获取三元组抽取与证据锚定的统计信息"""
    triples_path = _get_extracted_path("triples.json")
    evidence_path = _get_extracted_path("evidence.json")

    stats = {
        "三元组总数": 0,
        "证据总数": 0,
        "关系类型统计": {},
        "证据可靠度统计": {},
        "锚定率": 0.0,
        "实体频次": {},
    }

    # 读取三元组统计
    if os.path.exists(triples_path):
        with open(triples_path, encoding="utf-8") as f:
            data = json.load(f)
        triples = data.get("三元组列表", [])
        stats["三元组总数"] = len(triples)

        for t in triples:
            rt = t.get("relation_type", "未知")
            stats["关系类型统计"][rt] = stats["关系类型统计"].get(rt, 0) + 1

            subj = t.get("subject", "")
            if subj:
                stats["实体频次"][subj] = stats["实体频次"].get(subj, 0) + 1
            obj = t.get("object", "")
            if obj:
                stats["实体频次"][obj] = stats["实体频次"].get(obj, 0) + 1

    # 读取证据统计
    if os.path.exists(evidence_path):
        with open(evidence_path, encoding="utf-8") as f:
            evd_data = json.load(f)
        evd_list = evd_data.get("证据列表", [])
        stats["证据总数"] = len(evd_list)
        stats["锚定率"] = round(
            len(evd_list) / max(stats["三元组总数"], 1), 4
        )
        for evd in evd_list:
            rel = evd.get("reliability", "未知")
            stats["证据可靠度统计"][rel] = stats["证据可靠度统计"].get(rel, 0) + 1

    # 排序实体频次
    stats["实体频次"] = dict(
        sorted(stats["实体频次"].items(), key=lambda x: x[1], reverse=True)[:15]
    )

    return stats


# ================================================================
# 内部辅助函数
# ================================================================

def _load_filtered_paragraphs() -> Dict:
    """加载过滤后的段落"""
    file_path = os.path.join(BASE, "data", "processed", "filtered_paragraphs.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def _get_extracted_path(filename: str) -> str:
    """获取 data/extracted/ 下的文件路径"""
    return os.path.join(BASE, "data", "extracted", filename)


def _save_extraction_results(extract_result: Dict, anchor_result: Dict):
    """保存三元组和证据到 data/extracted/"""
    edir = os.path.join(BASE, "data", "extracted")
    os.makedirs(edir, exist_ok=True)

    triples_path = os.path.join(edir, "triples.json")
    evidence_path = os.path.join(edir, "evidence.json")

    with open(triples_path, "w", encoding="utf-8") as f:
        json.dump(extract_result, f, ensure_ascii=False, indent=2)

    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(anchor_result, f, ensure_ascii=False, indent=2)

    print(f"  [OK] 三元组已保存到: {triples_path}")
    print(f"  [OK] 证据已保存到: {evidence_path}")
