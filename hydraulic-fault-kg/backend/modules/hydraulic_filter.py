"""
液压领域相关性过滤模块
只保留包含液压相关关键词的段落：
液压系统、液压泵、阀、过滤器、蓄能器、冷却器、油液、压力、流量、泄漏、堵塞、卡滞、气蚀、油温、黏度等。
"""
import re
from typing import List, Dict, Set

# 液压领域核心关键词（用于相关性判断）
HYDRAULIC_KEYWORDS = [
    # 系统层级
    "液压系统", "液压传动", "液压控制", "液压站", "液压回路", "液压装置",

    # 元件类型
    "液压泵", "柱塞泵", "齿轮泵", "叶片泵", "泵",
    "液压缸", "油缸", "液压马达",
    "液压阀", "换向阀", "方向阀", "溢流阀", "减压阀", "节流阀", "比例阀", "伺服阀",
    "单向阀", "平衡阀", "调速阀", "流量阀", "压力阀",
    "阀芯", "阀体", "阀座", "阀口", "滑阀", "锥阀", "电磁阀",

    # 辅助元件
    "过滤器", "滤芯", "滤油器",
    "蓄能器", "皮囊",
    "冷却器", "散热器", "换热器",
    "油箱", "管路", "接头", "密封件", "密封圈", "密封",

    # 工作参数
    "压力", "流量", "油液", "液压油", "油温", "温度", "黏度",
    "清洁度", "污染度",

    # 故障模式
    "泄漏", "内泄漏", "外泄漏", "漏油",
    "堵塞", "卡滞", "卡住", "卡死",
    "气蚀", "穴蚀",
    "磨损", "老化", "疲劳", "破裂",
    "噪声", "振动", "爬行",
    "过热", "油温过高",

    # 状态描述
    "压力不足", "压力下降", "压力波动", "压力脉动",
    "流量不足", "流量下降",
    "动作缓慢", "速度下降", "无力",
    "油液污染", "污染",

    # 维修动作
    "清洗", "更换", "维修", "检修", "拆检", "研磨", "冲洗",

    # 英文 (for bilingual documents)
    "hydraulic", "pump", "valve", "cylinder", "filter", "accumulator",
    "cooler", "pressure", "flow", "leakage", "cavitation", "contamination",
    "viscosity", "seal", "actuator", "relief", "proportional", "servo",
]


def is_hydraulic_related(text: str, keyword_list: List[str] = None) -> bool:
    """判断一段文本是否与液压领域相关"""
    if keyword_list is None:
        keyword_list = HYDRAULIC_KEYWORDS

    text_lower = text.lower()
    for kw in keyword_list:
        if kw.lower() in text_lower:
            return True
    return False


def filter_hydraulic_paragraphs(paragraphs: List[Dict]) -> List[Dict]:
    """
    从段落列表中筛选出与液压领域相关的段落。
    返回：
    - kept: 保留的段落列表
    """
    kept = []
    for para in paragraphs:
        text = para.get("text", "")
        if is_hydraulic_related(text):
            # 记录匹配的关键词
            matched_keywords = [kw for kw in HYDRAULIC_KEYWORDS if kw.lower() in text.lower()]
            kept.append({
                **para,
                "matched_keywords": matched_keywords,
                "keyword_count": len(matched_keywords)
            })
    return kept


def keyword_coverage_report(paragraphs: List[Dict]) -> Dict:
    """生成关键词覆盖报告"""
    keyword_hits = {}
    for para in paragraphs:
        text = para.get("text", "")
        for kw in HYDRAULIC_KEYWORDS:
            if kw.lower() in text.lower():
                keyword_hits[kw] = keyword_hits.get(kw, 0) + 1

    sorted_hits = sorted(keyword_hits.items(), key=lambda x: x[1], reverse=True)
    return {
        "总关键词数": len(HYDRAULIC_KEYWORDS),
        "命中关键词数": len(keyword_hits),
        "关键词覆盖率": round(len(keyword_hits) / len(HYDRAULIC_KEYWORDS), 3),
        "高频关键词": sorted_hits[:20],
        "未命中关键词数": len(HYDRAULIC_KEYWORDS) - len(keyword_hits)
    }


def get_filtering_stats(original: List[Dict], filtered: List[Dict]) -> Dict:
    """获取过滤统计"""
    return {
        "清洗后段落数量": len(original),
        "液压领域相关段落数量": len(filtered),
        "过滤去除段落数量": len(original) - len(filtered),
        "保留比例": round(len(filtered) / max(len(original), 1), 3),
        "平均关键词命中数": round(
            sum(p.get("keyword_count", 0) for p in filtered) / max(len(filtered), 1), 1
        ) if filtered else 0
    }
