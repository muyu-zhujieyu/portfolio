"""
数据源管理模块
管理 source_id、source_type、title、author、year、publisher、file_path、license_note、source_url、doc_type。
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
SOURCES_INDEX_FILE = os.path.join(DATA_DIR, "sources_index.json")


# 文档类型中文映射
DOC_TYPE_MAP = {
    "maintenance_manual": "维修手册",
    "paper": "学术论文",
    "textbook": "教材",
    "datasheet": "产品说明书",
    "fault_case": "故障案例",
    "inspection_record": "检修记录",
    "fmea": "FMEA分析",
    "unknown": "其他"
}


def _detect_doc_type(filename: str, text_preview: str) -> str:
    """从文件名和内容推断文档类型"""
    name_lower = filename.lower()
    text_lower = text_preview[:500].lower() if text_preview else ""

    if any(kw in text_lower for kw in ["维修手册", "维护手册", "maintenance manual"]):
        return "维修手册"
    if any(kw in text_lower for kw in ["论文", "综述", "研究", "摘要", "abstract"]):
        return "学术论文"
    if any(kw in text_lower for kw in ["教材", "教科书", "第.*章", "textbook"]):
        return "教材"
    if any(kw in text_lower for kw in ["说明书", "产品概述", "技术参数", "datasheet", "规格"]):
        return "产品说明书"
    if any(kw in text_lower for kw in ["案例", "故障实例", "case"]):
        return "故障案例"

    if "维修" in name_lower or "manual" in name_lower:
        return "维修手册"
    if "论文" in name_lower or "paper" in name_lower:
        return "学术论文"
    if "教材" in name_lower or "textbook" in name_lower:
        return "教材"
    if "说明书" in name_lower or "datasheet" in name_lower:
        return "产品说明书"
    if "案例" in name_lower or "case" in name_lower:
        return "故障案例"

    return "其他"


def create_source_record(
    source_id: str,
    filename: str,
    file_path: str,
    metadata: Dict,
    doc_type: str = None
) -> Dict:
    """创建一条数据源记录"""
    if doc_type is None:
        doc_type = _detect_doc_type(filename, metadata.get("raw_text", ""))

    record = {
        "source_id": source_id,
        "source_type": metadata.get("source_type", doc_type) or "未知来源",
        "doc_type": doc_type,
        "title": metadata.get("title", filename) or filename,
        "author": metadata.get("author", "未知"),
        "year": metadata.get("year", str(datetime.now().year)),
        "publisher": metadata.get("publisher", "未知"),
        "file_path": file_path,
        "filename": filename,
        "license_note": metadata.get("license_note", "公开资料，用于教学研究参考"),
        "source_url": metadata.get("source_url", ""),
        "created_at": datetime.now().isoformat(),
        "paragraph_count": 0,
        "sentence_count": 0,
        "char_count": metadata.get("char_count", 0)
    }
    return record


def build_sources_index(sources: List[Dict]) -> List[Dict]:
    """构建并保存数据源索引"""
    index = []
    for src in sources:
        index.append({
            "source_id": src["source_id"],
            "source_type": src["source_type"],
            "doc_type": src["doc_type"],
            "title": src["title"],
            "author": src["author"],
            "year": src["year"],
            "publisher": src["publisher"],
            "file_path": src["file_path"],
            "filename": src["filename"],
            "license_note": src["license_note"],
            "source_url": src["source_url"],
            "created_at": src["created_at"],
            "paragraph_count": src.get("paragraph_count", 0),
            "sentence_count": src.get("sentence_count", 0),
            "char_count": src.get("char_count", 0)
        })
    # 保存到 JSON 文件
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SOURCES_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index


def load_sources_index() -> List[Dict]:
    """加载数据源索引"""
    if os.path.exists(SOURCES_INDEX_FILE):
        with open(SOURCES_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []
