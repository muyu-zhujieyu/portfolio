"""
知识图谱问答路由 - 基于图谱检索+大模型组织回答

API:
  POST /api/qa                 提交问题（基于图谱+大模型）
  GET  /api/qa/examples        获取 8 类示例问题
  GET  /api/qa/history/{sid}   获取会话历史
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from services.qa_service import qa_service

router = APIRouter(prefix="/api/qa", tags=["知识图谱问答"])


class QARequestModel(BaseModel):
    """问答请求体"""
    question: str = Field(..., description="用户自然语言问题", min_length=1)
    session_id: Optional[str] = Field(None, description="会话ID（可选，用于连续追问）")


# ================================================================
# POST /api/qa - 核心问答接口
# ================================================================

@router.post("")
def ask_question(req: QARequestModel):
    """基于知识图谱回答用户问题

    系统流程:
      1. 问题解析 → 意图识别
      2. 图谱检索 → 事件链+节点+证据
      3. 大模型基于检索上下文组织回答（不编造事实）

    支持的问答类型:
      - 故障演化类: "油液污染可能如何演化为压力波动？"
      - 原因查询类: "压力下降的原因有哪些？"
      - 结果查询类: "泵内泄漏会导致什么？"
      - 证据追溯类: "这个故障事件有什么证据？"
      - 维修建议类: "阀芯卡滞应该如何处理？"
      - 机理解释类: "为什么冷却器效率下降会导致泄漏增加？"
      - 版本更新类: "维修完成后哪些故障事实应标记为过期？"
      - 方法对比类: "这和普通大模型直接回答有什么区别？"

    核心约束:
      大模型不能直接编造事实。
      事实来自: 事件知识图谱 + 故障演化链 + 机理模板 + 证据span + 维修规则
    """
    result = qa_service.answer_question(
        question=req.question,
        session_id=req.session_id
    )
    return result


# ================================================================
# GET /api/qa/examples - 示例问题
# ================================================================

@router.get("/examples")
def get_qa_examples():
    """获取 8 类示例问题列表

    每类包含说明和 3 个示例问题。
    """
    return qa_service.get_qa_examples()


# ================================================================
# GET /api/qa/history/{session_id} - 会话历史
# ================================================================

@router.get("/history/{session_id}")
def get_session_history(session_id: str):
    """获取指定会话的完整问答历史

    Args:
        session_id: 由 POST /api/qa 返回的 session_id
    """
    return qa_service.get_session_history(session_id)
