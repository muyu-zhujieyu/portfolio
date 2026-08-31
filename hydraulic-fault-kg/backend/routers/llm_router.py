"""
大模型路由 - 管理大模型提供者状态和配置

API:
  GET /api/llm/status    获取当前大模型提供者状态
  GET /api/llm/config    获取当前配置信息
"""
from fastapi import APIRouter
from services.llm_provider import llm_provider, MockLLMProvider, OpenAICompatibleProvider

router = APIRouter(prefix="/api/llm", tags=["大模型"])


@router.get("/status")
def llm_status():
    """获取当前大模型提供者状态

    返回:
        - 提供者类型（MockLLMProvider 或 OpenAICompatibleProvider）
        - 是否可用
        - 模型名称
        - 核心约束说明
    """
    is_mock = isinstance(llm_provider, MockLLMProvider)
    is_openai = isinstance(llm_provider, OpenAICompatibleProvider)

    status_info = {
        "状态": "就绪" if llm_provider.is_available() else "未配置",
        "提供者类型": llm_provider.provider_name,
        "提供者类别": "模拟大模型（MockLLMProvider）" if is_mock else "远程大模型（OpenAICompatibleProvider）",
        "是否可用": llm_provider.is_available(),
        "说明": "",
    }

    if is_mock:
        status_info["说明"] = (
            "当前使用 MockLLMProvider（模拟大模型提供者）。"
            "该提供者基于知识图谱检索上下文使用预定义模板组装中文回答，"
            "所有事实来自事件知识图谱、证据span、机理模板和维修规则，"
            "不编造任何内容。无需 API Key。"
        )
        status_info["模型名称"] = "MockLLM-v1"
        status_info["核心约束"] = [
            "大模型只负责组织自然语言表达",
            "事实来源: 事件知识图谱 + 故障演化链 + 机理模板 + 证据span + 维修规则",
            "每个论断可追溯到来源编号 + 段落编号 + 原文片段",
            "不编造知识图谱中不存在的故障原因和维修方法",
        ]
    elif is_openai:
        status_info["说明"] = (
            "当前使用 OpenAICompatibleProvider（远程大模型提供者）。"
            "该提供者通过 API 调用远程大模型，基于知识图谱检索上下文生成回答。"
        )
        status_info["模型名称"] = llm_provider._model_name
        status_info["API地址"] = llm_provider._base_url

    return status_info


@router.get("/config")
def llm_config():
    """获取当前大模型配置信息（不暴露 API Key）"""
    import os

    api_key_set = bool(os.environ.get("LLM_API_KEY", ""))
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    model_name = os.environ.get("LLM_MODEL_NAME", "gpt-3.5-turbo")

    return {
        "LLM_API_KEY已设置": api_key_set,
        "LLM_BASE_URL": base_url,
        "LLM_MODEL_NAME": model_name,
        "当前提供者": llm_provider.provider_name,
        "如何切换到远程大模型": (
            "设置以下环境变量后重启服务:\n"
            "  $env:LLM_API_KEY = 'your-api-key'\n"
            "  $env:LLM_BASE_URL = 'https://api.openai.com/v1'\n"
            "  $env:LLM_MODEL_NAME = 'gpt-4o'\n\n"
            "如果不设置这些环境变量，系统默认使用 MockLLMProvider（无需 API Key）。"
        )
    }
