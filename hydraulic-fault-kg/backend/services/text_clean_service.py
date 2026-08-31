"""
文本清洗服务 - 对解析后的段落进行系统清洗

清洗步骤（按顺序执行）：
  1. 去除空行和空白段落
  2. 去除重复段落（基于文本相似度）
  3. 去除过短段落（少于最小字符数）
  4. 去除目录类文本（包含章节编号模式的段落）
  5. 去除参考文献类文本
  6. 去除页眉页脚类文本（分隔符、页码等）
"""
import re
from typing import List, Dict, Any, Set, Tuple


class TextCleanService:
    """文本清洗器"""

    # 目录识别模式
    TOC_PATTERNS = [
        re.compile(r'^第[一二三四五六七八九十\d]+章'),          # 第一章
        re.compile(r'^第[一二三四五六七八九十\d]+节'),          # 第一节
        re.compile(r'^\d+[\.\s、]'),                           # 1. 或 1、
        re.compile(r'^[一二三四五六七八九十]+[、．.]'),         # 一、
        re.compile(r'^[（(][一二三四五六七八九十\d]+[）)]'),    # (一)
    ]

    # 参考文献识别模式
    REFERENCE_PATTERNS = [
        re.compile(r'^\[\d+\]'),                               # [1]
        re.compile(r'^参考文献$'),
        re.compile(r'^References?$', re.IGNORECASE),
        re.compile(r'^【\d+】'),
    ]

    # 页眉页脚/分隔符识别模式
    HEADER_FOOTER_PATTERNS = [
        re.compile(r'^={3,}'),                                 # ======
        re.compile(r'^-{3,}'),                                 # ------
        re.compile(r'^\*{3,}'),                                # ******
        re.compile(r'^第\d+页'),                               # 第1页
        re.compile(r'^Page\s+\d+', re.IGNORECASE),             # Page 1
        re.compile(r'^\d+/\d+$'),                              # 1/10
        re.compile(r'^[=＊#]{3,}'),                            # 各种分隔符
    ]

    def __init__(self):
        self.min_paragraph_length: int = 10   # 最小段落长度
        self.similarity_threshold: float = 0.85  # 去重相似度阈值

    # ================================================================
    # 公开接口
    # ================================================================

    def clean_paragraphs(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """对解析结果中的所有段落执行完整清洗流水线

        Args:
            parse_result: source_reader.parse_all_sources() 的返回结果

        Returns:
            {
                "状态": "成功",
                "原始段落数": int,
                "清洗后段落数": int,
                "去除空行数": int,
                "去除重复数": int,
                "去除过短数": int,
                "去除目录数": int,
                "去除参考文献数": int,
                "去除页眉页脚数": int,
                "清洗后段落": [...]
            }
        """
        parse_results = parse_result.get("解析结果", [])
        if not parse_results:
            return {"状态": "失败", "错误": "无解析结果可清洗", "清洗后段落": []}

        all_cleaned = []
        stats = {
            "去除空行数": 0,
            "去除重复数": 0,
            "去除过短数": 0,
            "去除目录数": 0,
            "去除参考文献数": 0,
            "去除页眉页脚数": 0,
        }

        total_original = 0

        for src_result in parse_results:
            if src_result.get("解析状态") != "成功":
                continue

            source_id = src_result.get("source_id", "")
            source_type = src_result.get("来源类型", "")
            title = src_result.get("标题", "")
            paragraphs = src_result.get("段落列表", [])

            if not paragraphs:
                continue

            total_original += len(paragraphs)

            # 提取纯文本列表
            texts = [p.get("原始文本", "") for p in paragraphs]

            # 步骤1: 去除空行
            texts, empty_count = self._remove_empty_lines(texts)
            stats["去除空行数"] += empty_count

            # 步骤2: 去除页眉页脚
            texts, hf_count = self._remove_header_footer(texts)
            stats["去除页眉页脚数"] += hf_count

            # 步骤3: 去除目录类文本
            texts, toc_count = self._remove_toc_like(texts)
            stats["去除目录数"] += toc_count

            # 步骤4: 去除参考文献类文本
            texts, ref_count = self._remove_reference_like(texts)
            stats["去除参考文献数"] += ref_count

            # 步骤5: 去除过短段落
            texts, short_count = self._remove_short_paragraphs(texts)
            stats["去除过短数"] += short_count

            # 步骤6: 去除重复段落
            texts, dup_count = self._remove_duplicates(texts)
            stats["去除重复数"] += dup_count

            # 构建清洗后的结果
            for para_idx, text in enumerate(texts, 1):
                all_cleaned.append({
                    "source_id": source_id,
                    "来源类型": source_type,
                    "标题": title,
                    "段落编号": para_idx,
                    "原始文本": text,
                    "清洗后文本": text,  # 当前清洗后与原文本一致
                    "字符数": len(text)
                })

        return {
            "状态": "成功",
            "原始段落数": total_original,
            "清洗后段落数": len(all_cleaned),
            **stats,
            "清洗后段落": all_cleaned
        }

    def clean_single_source(self, source_result: Dict[str, Any]) -> Dict[str, Any]:
        """清洗单个来源的段落"""
        wrapper = {
            "状态": "成功",
            "来源总数": 1,
            "解析成功数": 1,
            "解析失败数": 0,
            "段落总数": len(source_result.get("段落列表", [])),
            "解析结果": [source_result]
        }
        return self.clean_paragraphs(wrapper)

    # ================================================================
    # 清洗步骤（内部方法）
    # ================================================================

    def _remove_empty_lines(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除空行和仅包含空白字符的行"""
        original = len(texts)
        cleaned = [t for t in texts if t and t.strip() and len(t.strip()) > 0]
        return cleaned, original - len(cleaned)

    def _remove_short_paragraphs(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除过短段落（少于最小字符数）"""
        original = len(texts)
        cleaned = [t for t in texts if len(t.strip()) >= self.min_paragraph_length]
        return cleaned, original - len(cleaned)

    def _remove_duplicates(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除重复段落（完全重复和高度相似）"""
        original = len(texts)
        seen: Set[str] = set()
        cleaned = []
        for t in texts:
            # 使用归一化后的文本作为去重键
            normalized = self._normalize_for_dedup(t)
            if normalized not in seen and len(normalized) > 0:
                seen.add(normalized)
                cleaned.append(t)
        return cleaned, original - len(cleaned)

    def _remove_toc_like(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除目录类文本（包含章节编号模式、纯数字编号等）"""
        original = len(texts)
        cleaned = []

        for t in texts:
            stripped = t.strip()
            is_toc = False

            # 检查是否匹配目录模式
            for pattern in self.TOC_PATTERNS:
                if pattern.match(stripped):
                    # 额外检查：目录条目通常较短，且不以标点结束
                    if len(stripped) < 80 and not stripped.endswith(('。', '！', '？')):
                        is_toc = True
                        break

            # 纯页码行
            if stripped.isdigit():
                is_toc = True

            # 包含大量省略号的行（目录特征）
            if stripped.count('……') > 2 or stripped.count('...') > 2:
                is_toc = True

            if not is_toc:
                cleaned.append(t)

        return cleaned, original - len(cleaned)

    def _remove_reference_like(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除参考文献类文本"""
        original = len(texts)
        cleaned = []
        in_reference_section = False

        for t in texts:
            stripped = t.strip()

            # 检测是否进入参考文献区域
            for pattern in self.REFERENCE_PATTERNS:
                if pattern.match(stripped):
                    in_reference_section = True
                    break

            # 参考文献区域内的文本也跳过
            if in_reference_section:
                # 检查是否已经离开参考文献区域
                if len(stripped) > 100 and not any(p.match(stripped) for p in self.REFERENCE_PATTERNS):
                    in_reference_section = False
                    cleaned.append(t)
                continue

            if not in_reference_section and not any(p.match(stripped) for p in self.REFERENCE_PATTERNS):
                cleaned.append(t)

        return cleaned, original - len(cleaned)

    def _remove_header_footer(self, texts: List[str]) -> Tuple[List[str], int]:
        """去除页眉页脚和分隔符类文本"""
        original = len(texts)
        cleaned = []

        for t in texts:
            stripped = t.strip()
            is_hf = False

            # 检查分隔符模式
            for pattern in self.HEADER_FOOTER_PATTERNS:
                if pattern.match(stripped):
                    is_hf = True
                    break

            # 纯页码
            if re.match(r'^\d{1,4}$', stripped):
                is_hf = True

            # 以分隔符开头且内容极少的行
            if stripped.startswith('===') or stripped.startswith('---'):
                is_hf = True

            if not is_hf:
                cleaned.append(t)

        return cleaned, original - len(cleaned)

    # ================================================================
    # 辅助方法
    # ================================================================

    def _normalize_for_dedup(self, text: str) -> str:
        """归一化文本用于去重比较（去除标点和空白差异）"""
        # 去除所有空白字符
        normalized = re.sub(r'\s+', '', text)
        # 去除标点符号
        punct_pattern = re.compile(
            r'[，。！？、；：“”‘’'
            r'（）《》【】…—\-,.!?;:\'\"(){}\[\]　]'
        )
        normalized = punct_pattern.sub('', normalized)
        # 取前100个字符作为指纹
        return normalized[:100].lower()


# 单例
text_cleaner = TextCleanService()
