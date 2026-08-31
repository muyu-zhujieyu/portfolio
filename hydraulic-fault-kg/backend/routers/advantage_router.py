"""
系统优势分析路由 - 展示本系统相比普通大模型的核心优势

API:
  GET /api/advantages       获取完整优势分析
  GET /api/advantages/table 获取对比表格（简洁版）
"""
from fastapi import APIRouter
from services.advantage_service import advantage_service

router = APIRouter(prefix="/api/advantages", tags=["系统优势"])


@router.get("")
def get_advantages():
    """获取本系统相对于普通大模型的完整方法优势分析

    返回 6 大优势模块:
      1. 数据来源可追溯 — source_id/paragraph_id/evidence_span
      2. 机理一致性校验 — 6条液压机理模板
      3. 事件化知识建模 — 6类事件+6类中文边
      4. 双时态增量融合 — 有效时间+观察时间+版本状态
      5. 可选导入资料增量更新 — 自动抽取+增量融合
      6. 大模型图谱问答可解释 — 事件链+模板+证据+置信度

    每个模块说明：普通大模型不足 + 本系统方法优势 + 技术实现 + 应用场景
    """
    return advantage_service.get_advantages()


@router.get("/table")
def get_comparison_table():
    """获取简洁对比表格

    8 个对比维度 × 2 列（普通大模型 vs 本系统）
    """
    data = advantage_service.get_advantages()
    return {
        "标题": data.get("标题", ""),
        "对比表格": data.get("对比表格", {}),
        "核心结论": data.get("核心结论", ""),
    }


@router.get("/summary")
def get_summary():
    """获取优势摘要（一句话总结）"""
    return {
        "总结": (
            "普通大模型是自由创作，"
            "本系统是有据可查的液压故障知识问答平台。"
            "核心创新：事件化建模 + 机理约束 + 证据锚定 + 大模型角色重新定义。"
        ),
        "六大优势": [
            "数据来源可追溯 - 每个论断可追溯到原始资料的具体段落和句子",
            "机理一致性校验 - 6条液压机理模板确保故障推理符合物理规律",
            "事件化知识建模 - 92个中文节点+177条中文边构建知识图谱",
            "双时态增量融合 - 支持历史版本追溯和增量知识更新",
            "可选导入资料增量更新 - 新资料自动抽取结构化知识并融合入库",
            "大模型图谱问答可解释 - 展示事件链、模板、证据、置信度",
        ]
    }
