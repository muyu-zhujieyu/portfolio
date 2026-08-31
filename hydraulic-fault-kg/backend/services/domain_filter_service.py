"""
液压领域相关性过滤服务 - 基于术语词典和关键词匹配过滤非液压段落

过滤依据:
  1. 液压领域术语词典（hydraulic_terms.json）
  2. 核心关键词列表（液压系统、泵、阀、油液等）
  3. 段落长度和质量过滤
"""
import json
import os
from typing import List, Dict, Any, Tuple


class DomainFilterService:
    """液压领域相关性过滤器"""

    # 核心液压领域关键词（用于快速预过滤）
    CORE_HYDRAULIC_KEYWORDS = [
        "液压", "液压系统", "液压泵", "液压阀", "液压缸", "液压马达",
        "阀芯", "过滤器", "冷却器", "蓄能器", "执行机构",
        "油液", "液压油", "压力", "流量", "温度", "油温",
        "泄漏", "内泄漏", "内泄露", "内部泄漏",
        "堵塞", "卡滞", "气蚀", "空化",
        "噪声", "振动", "黏度", "粘度",
        "污染", "清洁度", "颗粒度", "密封",
        "维修", "检测", "容积效率", "溢流阀",
        "柱塞", "配流盘", "换向阀", "节流阀",
        "预充压力", "压差", "额定压力", "回油",
        "吸油", "吸油管路", "壳体泄漏", "磨损",
        "泵内泄", "压力下降", "压力波动", "流量损失",
        "油温升高", "动作迟缓", "密封件",
    ]

    def __init__(self):
        self._terms: List[str] = []
        self._dictionary_loaded: bool = False
        self._load_terms()

    # ================================================================
    # 公开接口
    # ================================================================

    def filter_cleaned_paragraphs(self, clean_result: Dict[str, Any],
                                   threshold: float = 0.02) -> Dict[str, Any]:
        """对清洗后的段落执行液压领域相关性过滤

        Args:
            clean_result: text_cleaner.clean_paragraphs() 的返回结果
            threshold: 相关度阈值（0~1），默认 0.02

        Returns:
            {
                "状态": "成功",
                "清洗后段落数": int,
                "液压相关段落数": int,
                "过滤掉段落数": int,
                "过滤保留率": float (0~1),
                "过滤后段落": [...]
            }
        """
        paragraphs = clean_result.get("清洗后段落", [])
        if not paragraphs:
            return {
                "状态": "失败",
                "错误": "无清洗后段落可供过滤",
                "清洗后段落数": 0,
                "液压相关段落数": 0,
                "过滤掉段落数": 0,
                "过滤保留率": 0.0,
                "过滤后段落": []
            }

        passed = []
        filtered_out = 0

        for para in paragraphs:
            text = para.get("原始文本", "") or para.get("清洗后文本", "")
            is_relevant, score = self.is_hydraulic_related(text, threshold)

            if is_relevant:
                para_copy = dict(para)
                para_copy["相关度评分"] = round(score, 4)
                para_copy["匹配关键词"] = self._get_matched_keywords(text)
                passed.append(para_copy)
            else:
                filtered_out += 1

        total = len(paragraphs)

        return {
            "状态": "成功",
            "清洗后段落数": total,
            "液压相关段落数": len(passed),
            "过滤掉段落数": filtered_out,
            "过滤保留率": round(len(passed) / total, 4) if total > 0 else 0.0,
            "过滤后段落": passed
        }

    def is_hydraulic_related(self, text: str, threshold: float = 0.02) -> Tuple[bool, float]:
        """判断文本是否与液压领域相关

        Returns:
            (是否相关, 相关度评分 0~1)
        """
        # 空文本直接过滤
        if not text or len(text.strip()) < 5:
            return False, 0.0

        score = self.calculate_relevance(text)
        return score >= threshold, score

    def calculate_relevance(self, text: str) -> float:
        """计算文本与液压领域的相关度评分 (0~1)

        评分策略:
          1. 核心关键词匹配（高权重）
          2. 词典术语匹配（中等权重）
          3. 段落长度惩罚（过短段落降权）
        """
        text_lower = text.lower()

        # --- 核心关键词匹配（高权重）---
        core_matches = 0
        for kw in self.CORE_HYDRAULIC_KEYWORDS:
            if kw in text:
                core_matches += 1

        # --- 词典术语匹配（中等权重）---
        dict_matches = 0
        if self._dictionary_loaded and self._terms:
            for term in self._terms:
                if len(term) >= 2 and term in text:
                    dict_matches += 1

        # --- 综合评分 ---
        # 核心关键词权重 0.7，词典术语权重 0.3
        core_score = min(core_matches / max(len(self.CORE_HYDRAULIC_KEYWORDS) * 0.08, 1), 1.0)
        dict_score = min(dict_matches / max(len(self._terms) * 0.02, 1), 1.0) if self._terms else 0.0

        score = core_score * 0.7 + dict_score * 0.3

        # --- 段落长度惩罚 ---
        text_len = len(text.strip())
        if text_len < 15:
            score *= 0.3
        elif text_len < 30:
            score *= 0.6

        # 如果没有匹配到任何关键词但包含"液压"一词，给予基础分
        if core_matches == 0 and dict_matches == 0 and "液压" in text:
            score = max(score, 0.05)

        return min(score, 1.0)

    def _get_matched_keywords(self, text: str) -> List[str]:
        """获取文本中匹配到的液压关键词列表"""
        matched = []
        for kw in self.CORE_HYDRAULIC_KEYWORDS:
            if kw in text:
                matched.append(kw)
        # 限制返回数量
        return matched[:10]

    # ================================================================
    # 词典加载
    # ================================================================

    def _load_terms(self):
        """加载液压领域术语词典"""
        dict_path = None
        # 尝试多个可能的路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(current_dir, "..", "..", "data", "dictionaries", "hydraulic_terms.json"),
            os.path.join(current_dir, "..", "..", "..", "data", "dictionaries", "hydraulic_terms.json"),
        ]
        for p in possible_paths:
            abs_path = os.path.normpath(p)
            if os.path.exists(abs_path):
                dict_path = abs_path
                break

        if dict_path and os.path.exists(dict_path):
            try:
                with open(dict_path, encoding="utf-8") as f:
                    data = json.load(f)
                for category in data.get("categories", {}).values():
                    terms = category.get("terms", [])
                    if isinstance(terms, list):
                        self._terms.extend(terms)
                self._dictionary_loaded = True
            except Exception:
                self._dictionary_loaded = False

        if not self._dictionary_loaded:
            # 回退：使用内置术语列表
            self._terms = [
                "液压泵", "柱塞泵", "齿轮泵", "叶片泵", "溢流阀", "换向阀",
                "节流阀", "单向阀", "液压缸", "过滤器", "冷却器", "蓄能器",
                "密封件", "配流盘", "缸体", "柱塞", "滑靴", "斜盘", "阀芯",
                "阀体", "调压弹簧", "气囊", "吸油过滤器", "回油过滤器",
            ]
            self._dictionary_loaded = True


# 单例
domain_filter = DomainFilterService()
