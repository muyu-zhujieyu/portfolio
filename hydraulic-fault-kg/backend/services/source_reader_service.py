"""
来源资料读取服务 - 解析不同格式的公开资料文档

支持格式: TXT / MD / PDF / DOCX

输出统一结构:
  source_id, 来源类型, 标题, 段落编号, 句子编号, 原始文本, 页码, 文件路径
"""
import json
import os
import re
from typing import List, Dict, Any, Optional


class SourceReaderService:
    """来源资料读取器 - 从 source_registry.json 读取并解析文档"""

    # ================================================================
    # 公开接口
    # ================================================================

    def read_source_registry(self) -> Dict[str, Any]:
        """读取 source_registry.json 并返回所有来源登记"""
        registry_path = self._get_data_path("source_registry.json")
        if not os.path.exists(registry_path):
            return {"错误": f"来源登记文件不存在: {registry_path}", "来源列表": []}
        with open(registry_path, encoding="utf-8") as f:
            return json.load(f)

    def parse_all_sources(self) -> Dict[str, Any]:
        """解析 source_registry.json 中登记的所有来源资料

        Returns:
            {
                "状态": "成功",
                "来源总数": N,
                "解析成功数": M,
                "解析失败数": K,
                "段落总数": P,
                "解析结果": [...]
            }
        """
        registry = self.read_source_registry()
        sources = registry.get("sources", [])
        if not sources:
            return {"状态": "失败", "错误": "来源登记为空", "解析结果": []}

        results = []
        success_count = 0
        fail_count = 0

        for source in sources:
            try:
                parsed = self.parse_single_source(source)
                if parsed.get("解析状态") == "成功":
                    success_count += 1
                else:
                    fail_count += 1
                results.append(parsed)
            except Exception as e:
                fail_count += 1
                results.append({
                    "source_id": source.get("source_id", "未知"),
                    "标题": source.get("标题", "未知"),
                    "解析状态": "失败",
                    "错误信息": str(e),
                    "段落列表": []
                })

        total_paragraphs = sum(len(r.get("段落列表", [])) for r in results)

        return {
            "状态": "成功",
            "来源总数": len(sources),
            "解析成功数": success_count,
            "解析失败数": fail_count,
            "段落总数": total_paragraphs,
            "解析结果": results
        }

    def parse_single_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个来源资料

        Args:
            source: 来源字典（来自 source_registry.json）

        Returns:
            {
                "source_id": str,
                "来源类型": str,
                "标题": str,
                "解析状态": "成功"/"失败",
                "段落列表": [
                    {"段落编号": int, "句子编号": int, "原始文本": str, "页码": int, "文件路径": str}
                ]
            }
        """
        source_id = source.get("source_id", "未知")
        title = source.get("标题", "未知")
        source_type = source.get("来源类型", "未知")
        file_path_rel = source.get("文件路径", "")
        doc_type = (source.get("文档类型", "TXT") or "TXT").upper()

        # 解析相对路径为绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path_abs = os.path.join(base_dir, file_path_rel.replace("/", os.sep))

        if not os.path.exists(file_path_abs):
            return {
                "source_id": source_id,
                "来源类型": source_type,
                "标题": title,
                "解析状态": "失败",
                "错误信息": f"文件不存在: {file_path_abs}",
                "段落列表": []
            }

        try:
            # 根据文档类型选择解析器
            full_text = ""
            if doc_type in ("TXT", "MD", "TEXT"):
                full_text = self.read_text(file_path_abs)
            elif doc_type == "PDF":
                full_text = self.read_pdf(file_path_abs)
            elif doc_type in ("DOCX", "DOC"):
                full_text = self.read_docx(file_path_abs)
            else:
                # 默认尝试按文本读取
                full_text = self.read_text(file_path_abs)

            if not full_text:
                return {
                    "source_id": source_id,
                    "来源类型": source_type,
                    "标题": title,
                    "解析状态": "失败",
                    "错误信息": "文件内容为空或无法解析",
                    "段落列表": []
                }

            # 将文本拆分为段落和句子
            paragraphs = self._split_into_paragraphs(full_text)
            paragraph_list = []
            for para_idx, para_text in enumerate(paragraphs, 1):
                if not para_text.strip():
                    continue
                sentences = self._split_into_sentences(para_text)
                for sent_idx, sent_text in enumerate(sentences, 1):
                    if not sent_text.strip():
                        continue
                    paragraph_list.append({
                        "段落编号": para_idx,
                        "句子编号": sent_idx,
                        "原始文本": sent_text.strip(),
                        "页码": 0,  # TXT文件无页码，PDF后续可扩展
                        "文件路径": file_path_rel
                    })

            return {
                "source_id": source_id,
                "来源类型": source_type,
                "标题": title,
                "解析状态": "成功",
                "文档类型": doc_type,
                "段落列表": paragraph_list
            }

        except Exception as e:
            return {
                "source_id": source_id,
                "来源类型": source_type,
                "标题": title,
                "解析状态": "失败",
                "错误信息": str(e),
                "段落列表": []
            }

    # ================================================================
    # 文档解析器
    # ================================================================

    def read_text(self, filepath: str) -> str:
        """读取纯文本 / Markdown 文件（完整支持）"""
        # 尝试多种编码
        for encoding in ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]:
            try:
                with open(filepath, encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        # 最后尝试忽略错误的编码
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return f.read()

    def read_pdf(self, filepath: str) -> str:
        """读取 PDF 文件（使用 pypdf）"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except ImportError:
            return f"[PDF解析错误] pypdf 未安装，无法解析: {filepath}"
        except Exception as e:
            return f"[PDF解析错误] {e}"

    def read_docx(self, filepath: str) -> str:
        """读取 Word 文档（使用 python-docx）"""
        try:
            from docx import Document
            doc = Document(filepath)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return "\n".join(text_parts)
        except ImportError:
            return f"[DOCX解析错误] python-docx 未安装，无法解析: {filepath}"
        except Exception as e:
            return f"[DOCX解析错误] {e}"

    # ================================================================
    # 内部辅助方法
    # ================================================================

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """将文本拆分为段落（按空行和节标题分隔）"""
        # 先按空行拆分
        raw_paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = []
        for p in raw_paragraphs:
            p = p.strip()
            if not p:
                continue
            # 如果段落太长且包含多个独立句子块，尝试按换行再拆
            if len(p) > 500 and p.count('\n') > 3:
                sub_paras = [s.strip() for s in p.split('\n') if s.strip() and len(s.strip()) > 10]
                if len(sub_paras) > 1:
                    paragraphs.extend(sub_paras)
                else:
                    paragraphs.append(p)
            else:
                paragraphs.append(p)
        return paragraphs

    def _split_into_sentences(self, text: str) -> List[str]:
        """将段落拆分为句子（基于中文标点）"""
        if not text or not text.strip():
            return []
        # Use findall-based approach to avoid Python 3.7+ re.split empty-match error
        try:
            sentences = re.split(r'(?<=[。！？；])(?![」』）\)])', text)
        except ValueError:
            # Fallback: split on punctuation and rejoin
            parts = []
            current = ''
            for ch in text:
                current += ch
                if ch in '。！？；':
                    parts.append(current.strip())
                    current = ''
            if current.strip():
                parts.append(current.strip())
            sentences = parts

        result = []
        for s in sentences:
            s = s.strip()
            if s and len(s) >= 2:
                result.append(s)

        # 如果拆分后没有结果，返回原文本
        if not result and text.strip():
            result = [text.strip()]

        return result

    def _get_data_path(self, filename: str) -> str:
        """获取 data 目录下的文件绝对路径"""
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_dir = os.path.dirname(backend_dir)
        return os.path.join(project_dir, "data", filename)


# 单例
source_reader = SourceReaderService()
