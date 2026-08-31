"""
段落清洗模块
去除页眉页脚、目录、参考文献、空行、重复段落、过短段落。
"""
import re
from typing import List, Dict, Set


def clean_paragraphs(paragraphs: List[Dict]) -> List[Dict]:
    """
    清洗段落列表：
    1. 去除空段落
    2. 去除过短段落（少于10个字符）
    3. 去除目录行
    4. 去除参考文献段落
    5. 去除页眉页脚标记
    6. 去除重复段落
    7. 去除纯分隔线
    """
    if not paragraphs:
        return []

    cleaned = []

    for para in paragraphs:
        text = para.get("text", "").strip()

        # 1. 跳过空段落
        if not text:
            continue

        # 2. 跳过过短段落
        if len(text) < 10:
            continue

        # 3. 跳过目录行（常见模式：数字.空格...数字 或 1.1 标题...页码）
        if re.match(r'^[\d\.]+\s+.+\d+$', text) and len(text) < 80:
            # 看起来像目录条目（章节号 + 标题 + 页码）
            if not any(kw in text for kw in ["故障", "泄漏", "堵塞", "压力", "油液", "液压"]):
                # 如果段落不含液压领域关键词，且像目录条目，则跳过
                if re.search(r'\d{2,}$', text):  # 末尾有数字（页码）
                    continue

        # 4. 跳过参考文献段落
        if text.startswith("参考文献") or text.startswith("References"):
            continue
        if re.match(r'^\[\d+\]', text) and len(text) < 500:
            # [1] 某某某. 论文标题...
            if any(kw in text for kw in ["出版社", "Journal", "Conference", "vol.", "pp.", "年"]):
                continue

        # 5. 去除明显的页眉页脚（包含页码的行）
        page_patterns = [
            r'^第\d+页\s*共\d+页$',  # 第1页 共10页
            r'^-\s*\d+\s*-$',  # - 5 -
            r'^\d+\s*/\s*\d+$',  # 5 / 20
            r'^第[一二三四五六七八九十\d]+章',  # 章节标题保留
        ]
        is_header_footer = False
        for pat in page_patterns[:3]:  # 不包括章节标题模式
            if re.match(pat, text):
                is_header_footer = True
                break
        if is_header_footer:
            continue

        # 6. 跳过纯分隔线
        if re.match(r'^[=\-*#~_]{10,}$', text):
            continue

        # 7. 去除段落开头的"======"装饰线
        cleaned_text = re.sub(r'^[=\-*#~]{5,}\s*', '', text).strip()

        if cleaned_text and len(cleaned_text) >= 10:
            cleaned.append({
                **para,
                "text": cleaned_text,
                "char_count": len(cleaned_text)
            })

    # 8. 去除重复段落
    seen_texts: Set[str] = set()
    deduped = []
    for para in cleaned:
        # 使用前100个字符作为去重指纹
        fingerprint = para["text"][:100].strip()
        if fingerprint not in seen_texts:
            seen_texts.add(fingerprint)
            deduped.append(para)

    return deduped


def get_cleaning_stats(original: List[Dict], cleaned: List[Dict]) -> Dict:
    """获取清洗统计"""
    return {
        "原始段落数量": len(original),
        "清洗后段落数量": len(cleaned),
        "去除段落数量": len(original) - len(cleaned),
        "保留比例": round(len(cleaned) / max(len(original), 1), 3),
        "原始总字符数": sum(p.get("char_count", 0) for p in original),
        "清洗后总字符数": sum(p.get("char_count", 0) for p in cleaned),
        "去除原因统计": {
            "空段落": sum(1 for p in original if not p.get("text", "").strip()),
            "过短段落": sum(1 for p in original if 0 < len(p.get("text", "").strip()) < 10),
            "其他原因": len(original) - len(cleaned) - sum(1 for p in original if not p.get("text", "").strip()) - sum(1 for p in original if 0 < len(p.get("text", "").strip()) < 10)
        }
    }
