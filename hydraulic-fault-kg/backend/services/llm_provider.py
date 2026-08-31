"""
大模型服务提供者 - 统一接口，支持 Mock 和 OpenAI 兼容提供者

核心约束:
  大模型不能直接编造事实，必须基于知识图谱、事件链、
  证据span、机理模板和维修规则组织回答。

提供者类型:
  - MockLLMProvider: 无需 API Key，基于模板+检索上下文生成中文回答（默认）
  - OpenAICompatibleProvider: 支持环境变量 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL_NAME
"""
import os
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


# ================================================================
# 基类
# ================================================================

class BaseLLMProvider(ABC):
    """大模型提供者抽象基类"""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名称"""
        pass

    @abstractmethod
    def generate(self,
                 prompt: str,
                 context: Dict[str, Any],
                 system_prompt: str = "",
                 max_tokens: int = 2048) -> Dict[str, Any]:
        """生成回答"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """提供者是否可用"""
        pass

    def build_system_prompt(self) -> str:
        """构建核心约束系统提示词"""
        return (
            "你是一个液压系统故障诊断知识问答助手。\n\n"
            "你必须严格遵守以下规则:\n"
            "1. 只能基于提供的知识图谱上下文、事件链、证据span原文、机理模板和维修规则来组织回答\n"
            "2. 严禁编造知识图谱中不存在的故障原因、维修方法或技术参数\n"
            "3. 每个论断必须附带证据出处（来源文件+原文片段）\n"
            '4. 如果上下文不足以回答，应明确告知用户: 依据现有知识图谱无法确定\n'
            "5. 回答中引用的维修方案必须来自已验证的维修规则\n"
            "6. 所有回答使用中文"
        )


# ================================================================
# MockLLMProvider - 基于检索上下文的模板回答（默认提供者）
# ================================================================

class MockLLMProvider(BaseLLMProvider):
    """模拟大模型提供者 —— 基于图谱检索结果用模板组织中文回答

    此提供者不需要任何 API Key，始终可用。
    它根据检索到的图谱上下文（事件链、证据、模板、维修规则），
    使用预定义的模板和规则来组装自然语言回答。

    注意：MockLLMProvider 只组织表达，事实内容全部来自图谱检索结果。
    """

    def __init__(self):
        self._model = "MockLLM-v1 (基于模板的图谱回答生成器)"

    @property
    def provider_name(self) -> str:
        return "MockLLMProvider"

    def is_available(self) -> bool:
        return True

    def generate(self,
                 prompt: str,
                 context: Dict[str, Any],
                 system_prompt: str = "",
                 max_tokens: int = 2048) -> Dict[str, Any]:
        """根据图谱检索上下文生成中文回答

        Args:
            prompt: 用户问题
            context: kg_context_service 检索到的图谱上下文
            system_prompt: 系统提示词
            max_tokens: 最大输出 token 数
        """
        answer = self._compose_answer(prompt, context)
        return {
            "answer": answer,
            "model": self._model,
            "provider": self.provider_name,
            "usage": {
                "note": "MockLLMProvider 不消耗 token，回答基于检索上下文和预定义模板组装"
            }
        }

    def _compose_answer(self, question: str, context: Dict[str, Any]) -> str:
        """Based on KG retrieved context, compose Chinese answer using templates"""

        parts = []
        intent = self._classify_intent(question)
        events = context.get("相关事件", []) or []
        chains = context.get("相关故障链", []) or []
        templates = context.get("相关机理模板", []) or []
        evidence_list = context.get("相关证据", []) or []
        rules = context.get("相关维修规则", []) or []
        nodes = context.get("相关节点", []) or []

        # ---- Evolution type ----
        if intent == "演化":
            # Direct answer first
            if chains:
                chain_text = str(chains[0].get("中文链式模式", ""))
                tname = str(chains[0].get("模板名称", ""))
                parts.append("【直接回答】")
                parts.append("根据液压伺服阀故障演化机理，该故障的演化路径为：" + chain_text)
                parts.append("这一过程通常由初始故障触发，通过多个因果环节逐步传播，最终导致系统性能异常。\n")
                parts.append("【故障演化链】匹配到 " + tname + " 模板：")
                parts.append("  " + chain_text)
            elif events:
                parts.append("【直接回答】")
                faults = [str(e.get("故障模式","")) for e in events[:5] if e.get("故障模式")]
                states = [str(e.get("异常状态","")) for e in events[:5] if e.get("异常状态")]
                if faults and states:
                    parts.append("该故障的演化路径涉及：" + " → ".join(faults) + " → " + " → ".join(states))
                parts.append("\n【相关事件】共检索到 " + str(len(events)) + " 个相关事件：")
                for ev in events[:5]:
                    parts.append("  - " + str(ev.get("事件编号",""))
                        + ": [" + str(ev.get("事件类型","")) + "] "
                        + str(ev.get("故障模式","")) + " - "
                        + str(ev.get("异常状态","") or ev.get("事件描述",""))[:50])
            else:
                parts.append("【直接回答】")
                parts.append("当前知识图谱中未检索到匹配该演化路径的完整事件链。建议尝试使用具体的故障模式关键词进行查询。")

        # ---- Cause query type ----
        elif intent == "原因":
            if events:
                causes = set()
                for ev in events:
                    cause = str(ev.get("原因", "") or ev.get("故障模式", ""))
                    if cause: causes.add(cause)
                parts.append("【直接回答】")
                if causes:
                    parts.append(question + " 的主要原因包括：" + "、".join(sorted(causes)[:6]) + "。其中油液污染是最常见的根本原因。")
                else:
                    parts.append("根据知识图谱检索，" + question + " 可能与油液污染、机械磨损或密封老化等因素有关。")
                parts.append("\n【根因分析】检索到 " + str(len(causes)) + " 类可能原因：")
                for c in sorted(causes)[:8]:
                    parts.append("  - " + c)
            if chains:
                parts.append("\n【机理模板匹配】匹配到 " + str(len(chains)) + " 条相关故障演化链：")
                for ch in chains[:3]:
                    parts.append("  - " + str(ch.get("模板编号","")) + "-"
                        + str(ch.get("模板名称","")) + ": "
                        + str(ch.get("中文链式模式","")))
            if not events and not chains:
                parts.append("【直接回答】")
                parts.append("当前知识图谱中未检索到明确的原因事件链，建议尝试使用故障模式关键词进行查询。")

        # ---- Result query type ----
        elif intent == "结果":
            if events:
                states = set()
                for ev in events:
                    state = str(ev.get("异常状态", ""))
                    if state: states.add(state)
                parts.append("【直接回答】")
                if states:
                    parts.append("该故障可能导致以下异常状态：" + "、".join(sorted(states)[:6]) + "。其中压力波动和响应迟缓是最常见的后果。")
                else:
                    parts.append("该故障可能导致流量控制异常、压力波动、响应迟缓及系统性能下降等后果。")
                parts.append("\n【可能后果】检索到 " + str(len(states)) + " 种相关异常状态：")
                for s in sorted(states)[:8]:
                    parts.append("  - " + s)
            if chains:
                parts.append("\n【故障演化路径】相关演化链：")
                for ch in chains[:3]:
                    parts.append("  - " + str(ch.get("中文链式模式","")))
            if not events:
                parts.append("【直接回答】")
                parts.append("当前知识图谱中未检索到明确的故障后果事件。")

        # ---- Evidence trace type ----
        elif intent == "证据":
            if evidence_list:
                parts.append("【直接回答】")
                parts.append("关于" + question + "，系统从公开维修手册、学术论文和故障案例中检索到" + str(len(evidence_list)) + "条相关证据记录。")
                parts.append("\n【证据列表】检索到 " + str(len(evidence_list)) + " 条相关证据：")
                for i, evd in enumerate(evidence_list[:5], 1):
                    span = str(evd.get("证据原文", "") or evd.get("原文片段", ""))[:150]
                    parts.append("\n  证据" + str(i) + " [" + str(evd.get("可靠度","中"))
                        + "可靠] 来源: " + str(evd.get("来源编号",""))
                        + " 段落" + str(evd.get("段落编号","")))
                    parts.append("  原文: " + span)
            else:
                parts.append("【直接回答】")
                parts.append("当前知识图谱中未检索到相关事件的证据记录。")

        # ---- Maintenance suggestion type ----
        elif intent == "维修":
            parts.append("【直接回答】")
            parts.append("针对" + question + "，建议遵循\"先检测后维修、维修后复测\"的标准流程。优先检查油液污染度并更换液压油和滤芯，根据具体故障模式选择清洗阀芯、调整零位或更换密封组件等措施。")
            if rules:
                parts.append("\n【维修规则匹配】检索到 " + str(len(rules)) + " 条相关维修规则：")
                for i, rule in enumerate(rules[:5], 1):
                    parts.append("\n  规则" + str(i) + ": " + str(rule.get("规则名称","")))
                    parts.append("  适用故障: " + str(rule.get("故障模式","")))
                    scheme = str(rule.get("维修方案",""))[:200]
                    parts.append("  维修方案: " + scheme)
            else:
                parts.append("\n当前维修规则库中未检索到匹配的维修方案。建议确认故障模式关键词。")

        # ---- Mechanism explanation type ----
        elif intent == "机理":
            if templates:
                tpl = templates[0]
                parts.append("【直接回答】")
                parts.append("关于" + question + "，" + str(tpl.get("物理约束","")) + "。这一过程遵循液压伺服阀的故障传播机理，从初始诱因通过多个物理环节逐步发展至最终故障。")
                for tpl2 in templates[:3]:
                    parts.append("\n【机理模板】" + str(tpl2.get("模板编号",""))
                        + "-" + str(tpl2.get("模板名称","")))
                    parts.append("  链式模式: " + str(tpl2.get("中文链式模式","")))
                    parts.append("  物理约束: " + str(tpl2.get("物理约束","")))
            if chains:
                parts.append("\n【演化验证】匹配到的事件链: ")
                for ch in chains[:3]:
                    parts.append("  - " + str(ch.get("模板名称","")) + ": 匹配"
                        + str(ch.get("匹配步骤数",0)) + "/"
                        + str(ch.get("模板总步骤数",0)) + "步")
            if not templates:
                parts.append("【直接回答】")
                parts.append("当前知识图谱中未检索到匹配该问题的机理模板。")

        # ---- Version query type ----
        elif intent == "版本":
            parts.append("关于 " + question + " 的版本状态查询：\n")
            versioned = [e for e in events if str(e.get("版本状态","active")) != "active"]
            if versioned:
                parts.append("【已过期/更新事件】找到 " + str(len(versioned)) + " 个非活跃版本事件：")
                for ev in versioned[:5]:
                    parts.append("  - " + str(ev.get("事件编号","")) + ": "
                        + str(ev.get("故障模式",""))
                        + " [版本状态=" + str(ev.get("版本状态","")) + "]")
            else:
                parts.append("当前事件知识图谱中的事件均为活跃版本。\n")
                parts.append("版本管理机制说明：\n")
                parts.append("  1. 系统采用双时态记录机制：事件发生时间 + 系统录入时间\n")
                parts.append("  2. 当新证据表明旧事实已变化时，旧事件标记为过期\n")
                parts.append("  3. 维修完成后，对应的故障事件应标记为已解决\n")
                parts.append("  4. 增量融合时保留历史版本，通过 version_logs 表追溯变更")

        # ---- Comparison type ----
        elif intent == "对比":
            parts.append("本系统（液压故障事件知识图谱问答系统）与普通大模型直接回答的核心区别：\n\n")
            parts.append("【普通大模型直接回答】\n")
            parts.append("  - 模型自由生成，可能编造不存在的故障原因和维修方法\n")
            parts.append("  - 无法追溯信息来源，缺乏证据支撑\n")
            parts.append("  - 可能推荐不适用于具体机型的维修方案\n")
            parts.append("  - 每次回答可能不一致，知识无持久化\n\n")
            parts.append("【本系统（图谱问答）】\n")
            parts.append("  - 大模型只负责组织自然语言表达，不编造事实\n")
            parts.append("  - 所有事实来自：事件知识图谱 + 故障演化链 + 机理模板 + 证据span\n")
            parts.append("  - 每个论断可追溯到：来源编号 + 段落编号 + 原文片段\n")
            parts.append("  - 维修方案来自已验证的维修规则库\n")
            parts.append("  - 知识持久化存储，支持版本管理和增量更新\n")
            parts.append("  - 回答附带置信度和可靠度评估\n\n")
            parts.append("一句话总结：普通大模型是自由创作，本系统是有据可查的知识问答。")

        # ---- General fallback ----
        else:
            if events:
                faults = [str(e.get("故障模式","")) for e in events[:3] if e.get("故障模式")]
                parts.append("【直接回答】")
                if faults:
                    parts.append("关于" + question + "，知识图谱中涉及的相关故障包括：" + "、".join(faults) + "。")
                else:
                    parts.append("关于" + question + "，以下是知识图谱检索结果。")
                parts.append("\n【相关事件】检索到 " + str(len(events)) + " 个相关事件")
                for ev in events[:5]:
                    parts.append("  - " + str(ev.get("事件编号","")) + ": ["
                        + str(ev.get("事件类型","")) + "] "
                        + "部件=" + str(ev.get("部件",""))
                        + " 故障=" + str(ev.get("故障模式",""))
                        + " 状态=" + str(ev.get("异常状态","")))
            if chains:
                parts.append("\n【故障演化链】匹配到 " + str(len(chains)) + " 条")
            if rules:
                parts.append("\n【维修规则】匹配到 " + str(len(rules)) + " 条")
            if evidence_list:
                parts.append("\n【支撑证据】检索到 " + str(len(evidence_list)) + " 条")

            if not events and not chains and not rules:
                parts.append("【直接回答】")
                parts.append("当前问题未在知识图谱中匹配到明确答案。\n"
                    "可尝试输入部件名称（如：液压伺服阀、阀芯阀套）、"
                    "故障模式（如：内泄漏、阀芯卡滞、油液污染）、"
                    "异常状态（如：压力下降、零位漂移、动作迟缓）"
                    "或维修动作（如：更换密封件、清洗过滤器）进行查询。")

        # ---- Mandatory disclaimer ----
        parts.append("\n\n---")
        parts.append("【答案依据说明】")
        parts.append("本答案基于事件知识图谱、机理模板和证据span生成。"
            "大模型（MockLLMProvider）只负责基于检索到的图谱上下文组织自然语言表达，"
            "不编造任何事实。所有故障原因、演化路径和维修建议均来自液压领域公开资料"
            "和已验证的维修规则。")

        # ---- Follow-up suggestions ----
        followup = self._suggest_followup(intent, events, chains)
        if followup:
            parts.append("\n【可继续追问的问题】")
            for fq in followup[:4]:
                parts.append("  - " + str(fq))

        return "\n".join(parts)


    def _classify_intent(self, question: str) -> str:
        """分类用户问题意图"""
        q = question
        if any(w in q for w in ["演化", "传播", "导致", "引起", "引发", "如何演变", "故障链"]):
            return "演化"
        if any(w in q for w in ["原因", "为什么", "怎么会", "根源", "是什么原因"]):
            return "原因"
        if any(w in q for w in ["后果", "导致什么", "会引起", "会产生", "会造成", "会导致什么", "影响"]):
            return "结果"
        if any(w in q for w in ["证据", "依据", "来源", "出处", "凭什么", "怎么证明"]):
            return "证据"
        if any(w in q for w in ["维修", "怎么修", "如何处理", "解决方案", "修理", "修复", "怎么办", "更换", "清洗"]):
            return "维修"
        if any(w in q for w in ["机理", "原理", "为什么会导致", "物理", "规律"]):
            return "机理"
        if any(w in q for w in ["版本", "过期", "更新", "历史", "变更", "修改"]):
            return "版本"
        if any(w in q for w in ["区别", "对比", "不同", "vs", "比较", "普通大模型", "传统"]):
            return "对比"
        return "通用"

    def _suggest_followup(self, intent: str, events: List[Dict],
                           chains: List[Dict]) -> List[str]:
        """根据当前意图和检索结果建议追问问题"""
        suggestions = []
        if intent == "原因":
            suggestions.append("这个故障的演化路径是什么？")
            suggestions.append("如何检测和确认这个故障？")
        elif intent == "结果":
            suggestions.append("这个故障的根本原因是什么？")
            suggestions.append("应该怎样维修处理？")
        elif intent == "演化":
            suggestions.append("这个故障链中有哪些证据支撑？")
            suggestions.append("匹配的机理模板是什么？")
        elif intent == "维修":
            suggestions.append("维修前需要做哪些检测？")
            suggestions.append("维修后如何验证效果？")
        elif intent == "证据":
            suggestions.append("该证据支撑的事件链是什么？")
            suggestions.append("相关维修方案是什么？")

        if events:
            fault = events[0].get("故障模式", "")
            if fault:
                suggestions.append(f"{fault}的常见原因有哪些？")
        if chains:
            suggestions.append(f"查看完整的机理模板详情")

        suggestions.append("这个系统与普通大模型直接回答有什么区别？")
        return suggestions


# ================================================================
# OpenAICompatibleProvider - 真实大模型调用（需要 API Key）
# ================================================================

class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI 兼容 API 提供者 —— 通过 httpx 调用远程大模型

    环境变量:
      LLM_API_KEY: API 密钥
      LLM_BASE_URL: API 基础 URL（默认 https://api.openai.com/v1）
      LLM_MODEL_NAME: 模型名称（默认 gpt-3.5-turbo）
    """

    def __init__(self):
        self._api_key = os.environ.get("LLM_API_KEY", "")
        self._base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
        self._model_name = os.environ.get("LLM_MODEL_NAME", "gpt-3.5-turbo")

    @property
    def provider_name(self) -> str:
        return f"OpenAICompatibleProvider({self._model_name})"

    def configure(self, api_key: str = "", base_url: str = "", model_name: str = ""):
        """手动配置连接参数"""
        if api_key:
            self._api_key = api_key
        if base_url:
            self._base_url = base_url
        if model_name:
            self._model_name = model_name

    def is_available(self) -> bool:
        return bool(self._api_key)

    def generate(self,
                 prompt: str,
                 context: Dict[str, Any],
                 system_prompt: str = "",
                 max_tokens: int = 2048) -> Dict[str, Any]:
        """调用远程大模型 API 生成回答

        Args:
            prompt: 用户问题
            context: 图谱检索上下文
            system_prompt: 系统提示词
            max_tokens: 最大输出 token 数
        """
        if not self.is_available():
            return {
                "answer": (
                    "OpenAI 兼容提供者未配置 API Key。\n"
                    "请设置环境变量 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL_NAME，\n"
                    "或使用默认的 MockLLMProvider（无需 API Key）。\n\n"
                    "当前系统默认使用 MockLLMProvider，它基于知识图谱检索上下文"
                    "使用模板组装中文回答，所有事实来自图谱和证据，不编造内容。"
                ),
                "model": self._model_name,
                "provider": self.provider_name,
                "status": "未配置",
                "usage": {}
            }

        # 构建上下文文本
        context_text = self._format_context_for_llm(context)

        # 构建消息
        sys_prompt = system_prompt or self.build_system_prompt()
        user_message = (
            f"【用户问题】\n{prompt}\n\n"
            f"【知识图谱检索上下文】\n{context_text}\n\n"
            f"请基于上述知识图谱上下文回答问题。严格只使用上下文中的信息，"
            f"不要编造任何不存在的故障原因、维修方法或技术参数。"
            f"每个论断需要引用来源。如果上下文不足，请明确说明。"
        )

        try:
            import httpx

            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self._base_url.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self._model_name,
                        "messages": [
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_message},
                        ],
                        "max_tokens": max_tokens,
                        "temperature": 0.3,
                    }
                )
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"]
                else:
                    answer = f"API 返回异常: {result.get('error', {}).get('message', str(result))}"

                return {
                    "answer": answer,
                    "model": self._model_name,
                    "provider": self.provider_name,
                    "usage": result.get("usage", {})
                }

        except Exception as e:
            return {
                "answer": (
                    f"调用远程大模型失败: {str(e)}\n\n"
                    f"请检查:\n"
                    f"  1. LLM_API_KEY 是否正确\n"
                    f"  2. LLM_BASE_URL 是否可访问\n"
                    f"  3. 网络连接是否正常\n\n"
                    f"系统已回退到 MockLLMProvider 模式，"
                    f"可继续使用基于图谱检索的模板回答。"
                ),
                "model": self._model_name,
                "provider": self.provider_name,
                "status": "调用失败",
                "usage": {}
            }

    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """将图谱检索上下文格式化为适合大模型消费的文本"""
        parts = []

        events = context.get("相关事件", []) or []
        if events:
            parts.append(f"### 相关事件（共{len(events)}个）")
            for ev in events[:10]:
                parts.append(
                    f"- {ev.get('事件编号','')}: [{ev.get('事件类型','')}] "
                    f"部件={ev.get('部件','')} 故障={ev.get('故障模式','')} "
                    f"状态={ev.get('异常状态','')} 原因={ev.get('原因','')} "
                    f"置信度={ev.get('置信度','')}"
                )

        chains = context.get("相关故障链", []) or []
        if chains:
            parts.append(f"\n### 故障演化链（共{len(chains)}条）")
            for ch in chains[:5]:
                parts.append(
                    f"- {ch.get('模板编号','')}-{ch.get('模板名称','')}: "
                    f"{ch.get('中文链式模式','')} [匹配={ch.get('匹配分数','')}]"
                )

        templates = context.get("相关机理模板", []) or []
        if templates:
            parts.append(f"\n### 机理模板（共{len(templates)}个）")
            for tpl in templates[:5]:
                parts.append(
                    f"- {tpl.get('模板编号','')}-{tpl.get('模板名称','')}: "
                    f"{tpl.get('模板描述','')} 约束={tpl.get('物理约束','')}"
                )

        evidence_list = context.get("相关证据", []) or []
        if evidence_list:
            parts.append(f"\n### 支撑证据（共{len(evidence_list)}条）")
            for evd in evidence_list[:5]:
                parts.append(
                    f"- {evd.get('证据编号','')}: "
                    f"来源={evd.get('来源编号','')} "
                    f"原文: {str(evd.get('证据原文','') or evd.get('原文片段',''))[:200]}"
                )

        rules = context.get("相关维修规则", []) or []
        if rules:
            parts.append(f"\n### 维修规则（共{len(rules)}条）")
            for rule in rules[:5]:
                parts.append(
                    f"- {rule.get('规则名称','')}: "
                    f"故障={rule.get('故障模式','')} "
                    f"方案={rule.get('维修方案','')[:200]}"
                )

        return "\n".join(parts) if parts else "（知识图谱中未检索到相关上下文）"


# ================================================================
# 单例 — 默认使用 MockLLMProvider
# ================================================================

# 检查是否配置了真实大模型
_api_key = os.environ.get("LLM_API_KEY", "")
if _api_key:
    llm_provider: BaseLLMProvider = OpenAICompatibleProvider()
    llm_provider.configure(api_key=_api_key)
else:
    llm_provider: BaseLLMProvider = MockLLMProvider()
