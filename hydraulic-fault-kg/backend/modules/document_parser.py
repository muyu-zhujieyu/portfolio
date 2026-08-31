"""
文档解析模块
支持 txt、md、pdf、docx 格式文件的读取和解析。
从 data/raw_sources 目录读取公开资料。
"""
import os
import re
from typing import List, Dict, Optional

RAW_SOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "raw_sources")


def list_source_files(base_dir: str = None) -> List[str]:
    """列出所有可解析的源文件"""
    if base_dir is None:
        base_dir = RAW_SOURCES_DIR
    if not os.path.exists(base_dir):
        return []
    supported_exts = {".txt", ".md", ".pdf", ".docx"}
    files = []
    for f in os.listdir(base_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in supported_exts:
            files.append(os.path.join(base_dir, f))
    return sorted(files)


def parse_txt(file_path: str) -> str:
    """解析纯文本文件（txt 和 md）"""
    encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    # 最后尝试忽略错误
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def parse_pdf(file_path: str) -> str:
    """解析 PDF 文件（基础实现，使用 PyPDF2 或 pdfplumber）"""
    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)
    except ImportError:
        # 如果 PyPDF2 不可用，尝试 pdfplumber
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n".join(text_parts)
        except ImportError:
            return f"[PDF解析需要安装 PyPDF2 或 pdfplumber: {os.path.basename(file_path)}]"


def parse_docx(file_path: str) -> str:
    """解析 DOCX 文件（基础实现）"""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())
        return "\n".join(text_parts)
    except ImportError:
        return f"[DOCX解析需要安装 python-docx: {os.path.basename(file_path)}]"


def parse_document(file_path: str) -> Dict:
    """解析单个文档，返回结构化结果"""
    ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)

    parsers = {
        ".txt": parse_txt,
        ".md": parse_txt,
        ".pdf": parse_pdf,
        ".docx": parse_docx,
    }

    parser = parsers.get(ext, parse_txt)
    raw_text = parser(file_path)

    # 提取文件头部元数据（如果存在）
    metadata = _extract_metadata(raw_text)

    return {
        "file_path": file_path,
        "filename": filename,
        "ext": ext,
        "raw_text": raw_text,
        "char_count": len(raw_text),
        "metadata": metadata
    }


def parse_all_documents(base_dir: str = None) -> List[Dict]:
    """解析目录下所有支持的文档"""
    files = list_source_files(base_dir)
    results = []
    for fp in files:
        try:
            parsed = parse_document(fp)
            results.append(parsed)
        except Exception as e:
            results.append({
                "file_path": fp,
                "filename": os.path.basename(fp),
                "ext": os.path.splitext(fp)[1],
                "raw_text": "",
                "char_count": 0,
                "metadata": {},
                "error": str(e)
            })
    return results


def _extract_metadata(text: str) -> Dict:
    """从文本头部提取元数据"""
    metadata = {
        "source_type": "",
        "title": "",
        "author": "",
        "year": "",
        "publisher": "",
        "license_note": "",
        "source_url": "",
        "doc_type": ""
    }

    lines = text.split("\n")
    for line in lines[:30]:
        line = line.strip()
        if "来源类型" in line or "来源：" in line and "类型" in line:
            metadata["source_type"] = line.split("：")[-1].split(":")[-1].strip()
        elif "标题" in line or "题目" in line:
            metadata["title"] = line.split("：")[-1].split(":")[-1].strip()
        elif "作者" in line:
            metadata["author"] = line.split("：")[-1].split(":")[-1].strip()
        elif "出版年份" in line or "年份" in line:
            metadata["year"] = line.split("：")[-1].split(":")[-1].strip()
        elif "出版社" in line:
            metadata["publisher"] = line.split("：")[-1].split(":")[-1].strip()
        elif "许可" in line:
            metadata["license_note"] = line.split("：")[-1].split(":")[-1].strip()
        elif "来源URL" in line or "URL" in line:
            metadata["source_url"] = line.split("：")[-1].split(":")[-1].strip()
        elif "doc_type" in line.lower() or "文档类型" in line:
            metadata["doc_type"] = line.split("：")[-1].split(":")[-1].strip()

    # 从文件名推断文档类型
    if not metadata["source_type"]:
        filename = os.path.basename(text[:0] if not hasattr(text, 'find') else "")
    if "维修手册" in text[:500]:
        metadata["source_type"] = "维修手册"
    elif "论文" in text[:500] and ("摘要" in text[:500] or "研究" in text[:500]):
        metadata["source_type"] = "学术论文"
    elif "教材" in text[:500] or "教科书" in text[:500]:
        metadata["source_type"] = "教材"
    elif "说明书" in text[:500] or "技术参数" in text[:500] or "产品概述" in text[:500]:
        metadata["source_type"] = "产品说明书"
    elif "案例" in text[:500] and "故障" in text[:500]:
        metadata["source_type"] = "故障案例"

    return metadata


def split_into_paragraphs(text: str) -> List[Dict]:
    """将文档文本拆分为段落列表"""
    # 先按空行分段
    raw_paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = []
    for i, para in enumerate(raw_paragraphs):
        para = para.strip()
        if para:
            sentences = _split_sentences(para)
            paragraphs.append({
                "paragraph_no": i + 1,
                "text": para,
                "sentence_count": len(sentences),
                "sentences": sentences,
                "char_count": len(para)
            })
    return paragraphs


def _split_sentences(text: str) -> List[str]:
    """简单的中英文分句"""
    # 按中文标点和英文标点分句
    sentences = re.split(r'(?<=[。！？；\.\!\?\;])\s*', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) >= 5]
