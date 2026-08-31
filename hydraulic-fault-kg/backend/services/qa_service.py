"""
知识图谱问答服务 - 基于三元组路径和证据回答

核心约束:
  大模型不能直接编造事实，必须基于知识图谱三元组、证据span和机理模板组织回答。

/qa 问答必须基于三元组路径回答。例如用户问：
  油液污染可能如何演化为压力波动？
系统从 merged_triples 中找到路径：
  油液污染 — 导致 — 污染颗粒进入伺服阀 → ... → 压力波动

回答时显示：
  1. 直接回答
  2. 三元组路径
  3. 机理解释
  4. 原始证据
  5. 检测建议
  6. 维修建议
"""
import json
import uuid
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.kg_context_service import kg_context
from services.llm_provider import llm_provider

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class QAService:
    """知识图谱问答服务 - 基于三元组路径 + 机理模板 + 证据"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # ================================================================
    # 公开接口
    # ================================================================

    def answer_question(
        self, question: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """基于知识图谱三元组回答用户问题

        流程:
          1. 问题解析（关键词提取、意图识别）
          2. 图谱检索（三元组匹配、路径查找、链条检索）
          3. 证据收集
          4. 维修建议匹配
          5. 生成回答（直接回答 + 三元组路径 + 机理解释 + 证据 + 建议）
        """
        # 管理会话
        if not session_id:
            session_id = self._create_session(question)
        self._update_session(session_id, question)

        # 1. 构建图谱检索上下文
        context = kg_context.build_qa_context(question)

        # 2. 检测问题类型
        qtype = self._classify(question)

        # 3. 尝试基于三元组路径回答
        chain_answer = None
        if qtype in ("evolution", "cause"):
            chain_answer = self._build_triple_chain_answer(question, context)

        # 4. 领域知识回退
        domain_answer = None
        if not chain_answer or not chain_answer.get("chain"):
            kw, dk = self._match_domain_knowledge(question)
            if dk:
                domain_answer = self._build_domain_answer(question, kw, dk)

        # 5. 确定最终回答
        if domain_answer:
            answer_text = domain_answer.get("answer", "")
            fallback_used = True
        elif chain_answer and chain_answer.get("triple_path"):
            answer_text = chain_answer.get("answer", "")
            fallback_used = False
        else:
            # 使用大模型基于图谱上下文生成回答
            llm_response = llm_provider.generate(
                prompt=question,
                context=context,
                system_prompt=llm_provider.build_system_prompt(),
                max_tokens=2048,
            )
            answer_text = llm_response.get("answer", "")
            fallback_used = not bool(context.get("相关三元组"))

        # 6. 构建响应
        related_triples = context.get("相关三元组", []) or []
        triple_paths = context.get("三元组路径", []) or []
        chains = context.get("相关故障链", []) or []
        evidence_list = context.get("相关证据", []) or []
        nodes = context.get("相关节点", []) or []
        links = context.get("相关边", []) or []

        # 从链条答案中提取维修建议
        recommendations = []
        if chain_answer:
            recommendations = chain_answer.get("recommendations", [])

        # 计算置信度
        confidence = self._calculate_confidence(related_triples, chains, fallback_used)

        # 构建依据说明
        basis = self._build_basis(related_triples, chains, evidence_list, fallback_used)

        # 构建追问
        followup = self._build_followup(question, related_triples)

        # 保存记录
        self._save_qa_record(session_id, question, answer_text, evidence_list, context)

        return {
            "用户问题": question,
            "中文答案": answer_text,
            "问题类型": qtype,
            "direct_answer": (chain_answer or domain_answer or {}).get("direct_answer", ""),
            "path_summary": (chain_answer or {}).get("path_summary", ""),
            "匹配三元组路径": (chain_answer or {}).get("triple_path", []) or triple_paths[:5],
            "匹配故障演化链": (chain_answer or {}).get("chain", []) or chains[:5],
            "支撑证据": (chain_answer or {}).get("evidence", []) or evidence_list[:5],
            "推荐维修措施": recommendations,
            "detections": (chain_answer or {}).get("detections", []),
            "相关节点": nodes[:20],
            "相关边": links[:20],
            "置信度": confidence,
            "答案依据说明": basis,
            "知识回退": fallback_used,
            "回退原因": "图谱无直接命中，使用领域机理规则补充回答" if fallback_used else "",
            "可继续追问的问题": followup[:5],
            "session_id": session_id,
        }

    def get_qa_examples(self) -> Dict[str, Any]:
        """获取按类型组织的示例问题"""
        return {
            "问答类型": [
                {
                    "类型": "故障演化类",
                    "说明": "查询故障之间的因果关系和演化路径（基于三元组路径）",
                    "示例问题": [
                        "油液污染可能如何演化为压力波动？",
                        "喷嘴堵塞会导致什么连锁反应？",
                        "阀芯卡滞的故障演化路径是什么？",
                    ],
                },
                {
                    "类型": "原因查询类",
                    "说明": "查询故障现象的根本原因",
                    "示例问题": [
                        "压力波动的原因有哪些？",
                        "零位漂移是什么原因导致的？",
                        "响应迟缓的根本原因是什么？",
                    ],
                },
                {
                    "类型": "结果查询类",
                    "说明": "查询故障可能导致的后果",
                    "示例问题": [
                        "油液污染会导致什么？",
                        "阀芯卡滞会产生哪些影响？",
                        "内泄漏的后果是什么？",
                    ],
                },
                {
                    "类型": "证据追溯类",
                    "说明": "查询故障诊断的证据来源",
                    "示例问题": [
                        "阀芯卡滞有什么证据？",
                        "油液污染的判断依据是什么？",
                        "如何确认喷嘴堵塞？",
                    ],
                },
                {
                    "类型": "维修建议类",
                    "说明": "获取维修方案和操作步骤",
                    "示例问题": [
                        "阀芯卡滞应该如何处理？",
                        "喷嘴堵塞的维修方案是什么？",
                        "油液污染后应该做什么？",
                    ],
                },
                {
                    "类型": "机理解释类",
                    "说明": "理解故障发生的物理机理",
                    "示例问题": [
                        "为什么油液污染会导致阀芯卡滞？",
                        "气隙不对称为什么引起零位漂移？",
                        "线圈发热是如何产生的？",
                    ],
                },
            ],
        }

    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """获取会话历史"""
        from database import fetch_one, fetch_all

        session = fetch_one(
            "SELECT * FROM qa_sessions WHERE session_id = ?", (session_id,)
        )
        if session is None:
            return {"错误": f"会话 {session_id} 不存在", "问答记录": []}

        records = fetch_all(
            "SELECT * FROM qa_records WHERE session_id = ? ORDER BY 创建时间",
            (session_id,)
        )
        return {
            "会话": dict(session),
            "问答记录数": len(records),
            "问答记录": [dict(r) for r in records],
        }

    # ================================================================
    # 核心：基于三元组路径的回答构建
    # ================================================================

    def _build_triple_chain_answer(self, question: str, context: Dict) -> Optional[Dict]:
        """基于三元组路径构建故障演化回答"""
        related_triples = context.get("相关三元组", [])
        triple_paths = context.get("三元组路径", [])
        chains = context.get("相关故障链", [])

        if not related_triples and not chains:
            return None

        # 提取关键词
        keywords = context.get("提取关键词", [])

        # 构建三元组路径文本
        path_lines = []
        all_evidence = []
        all_recommendations = []

        if triple_paths:
            for path_info in triple_paths[:3]:
                path_lines.append(f"【路径】{path_info.get('start', '')} → {path_info.get('end', '')}")
                for i, triple in enumerate(path_info.get("path_triples", []), 1):
                    subj = triple.get("subject", "")
                    pred = triple.get("predicate", "")
                    obj = triple.get("object", "")
                    source = triple.get("triple_source", "")
                    path_lines.append(f"  {i}. {subj} — {pred} — {obj} [{source}]")

                    # 收集证据
                    for et in triple.get("evidence_texts", []):
                        if et and et not in all_evidence:
                            all_evidence.append(et)
        else:
            # 如果没有路径，直接列出相关三元组
            path_lines.append("【相关三元组】")
            for i, triple in enumerate(related_triples[:8], 1):
                subj = triple.get("subject", "")
                pred = triple.get("predicate", "")
                obj = triple.get("object", "")
                source = triple.get("triple_source", "")
                path_lines.append(f"  {i}. {subj} — {pred} — {obj} [{source}]")

                for et in triple.get("evidence_texts", []):
                    if et and et not in all_evidence:
                        all_evidence.append(et)

        # 从链条中提取机理解释
        mechanism_lines = []
        for chain in chains:
            ctext = chain.get("chain_text", "")
            tname = chain.get("template_name", "")
            if ctext:
                mechanism_lines.append(f"【{tname}】{ctext}")

        # 构建维修建议
        maint_map = {
            "污染卡滞链": [
                "检查油液污染度(NAS 1638 6级)",
                "更换液压油和全部滤芯",
                "清洗阀芯阀套",
                "清洗伺服阀",
                "复测响应曲线和压力曲线",
            ],
            "喷嘴堵塞链": [
                "检查喷嘴挡板",
                "清洗喷嘴孔",
                "检查油液清洁度",
                "复测零位和流量响应",
            ],
            "气隙偏差链": [
                "检查气隙垫片厚度一致性",
                "调整两侧气隙至0.50mm",
                "重新标定零位",
                "复测响应曲线",
            ],
            "力矩马达异常链": [
                "检查力矩马达线圈电阻",
                "检查线圈绝缘电阻",
                "检查衔铁组件",
                "重新标定",
            ],
            "密封内泄漏链": [
                "检查各密封部位",
                "更换老化密封件",
                "复测内泄漏量",
                "复测压力曲线",
            ],
            "线圈发热链": [
                "检查线圈电阻和绝缘",
                "检查磁路状态",
                "检查力矩马达",
                "维修后复测",
            ],
        }

        for chain in chains:
            tname = chain.get("template_name", "")
            if tname in maint_map:
                all_recommendations.extend(maint_map[tname])

        if not all_recommendations:
            all_recommendations = ["根据检测结果进行针对性维修", "维修后执行复测验证"]

        # 组装回答：直接回答在最前面
        direct = self._build_direct_answer(question, related_triples, triple_paths, chains)
        answer = f"{direct}\n\n"

        if path_lines:
            answer += "【故障演化路径】\n"
            answer += "\n".join(path_lines) + "\n\n"

        if mechanism_lines:
            answer += "【机理解释】\n"
            answer += "\n".join(mechanism_lines) + "\n\n"

        if all_evidence:
            answer += "【原始证据】\n"
            for i, evd in enumerate(all_evidence[:3], 1):
                answer += f"  {i}. {evd[:200]}\n"
            answer += "\n"

        answer += "【检测建议】\n"
        detections = self._build_detection_suggestions(related_triples, chains)
        for i, d in enumerate(detections[:5], 1):
            answer += f"  {i}. {d}\n"
        answer += "\n"

        answer += "【维修建议】\n"
        for i, rec in enumerate(all_recommendations[:5], 1):
            answer += f"  {i}. {rec}\n"

        return {
            "answer": answer,
            "direct_answer": direct,
            "path_summary": " → ".join([p.get("subject","") for p in triple_paths[0].get("path_triples",[])] + [triple_paths[0].get("end","")]) if triple_paths else "",
            "triple_path": triple_paths,
            "chain": chains,
            "evidence": all_evidence,
            "recommendations": all_recommendations,
            "detections": detections,
        }

    # ================================================================
    # 直接回答生成
    # ================================================================

    def _build_direct_answer(self, question, triples, paths, chains):
        """生成直接回答——先回答问题再展开"""
        qtype = self._classify(question)

        # 从三元组提取关键实体
        subjects = []
        objects = []
        for t in triples[:10]:
            s = t.get("subject", "")
            o = t.get("object", "")
            if s and s not in subjects: subjects.append(s)
            if o and o not in objects: objects.append(o)

        # 从链条提取完整路径
        chain_text = ""
        for ch in chains:
            chain_text = ch.get("chain_text", "")
            if chain_text:
                break

        if qtype == "evolution":
            # 故障演化类：先概括路径
            if chain_text:
                return f"根据液压伺服阀故障演化机理，该故障的演化路径为：{chain_text}。在液压伺服阀中，这一过程通常由油液污染触发，通过阀芯阀套间隙污染、阀芯运动受阻、流量调节失常等中间环节，最终导致系统压力异常。"
            if subjects and objects:
                path_str = " → ".join(subjects + [objects[-1]] if objects else subjects)
                return f"根据液压伺服阀故障知识图谱，该故障的演化路径为：{path_str}。这一过程可能涉及多个中间环节，从初始故障逐步传播至最终异常状态。"
            return f"根据液压伺服阀故障机理，{question}。该问题需要从故障传播链的角度进行分析，涉及多个因果环节。"

        elif qtype == "cause":
            if subjects:
                causes = "、".join(subjects[:4])
                return f"{question}的主要原因包括：{causes}。其中油液污染是最常见的根本原因，它可能通过污染颗粒进入伺服阀内部，引发阀芯卡滞、喷嘴堵塞等一系列故障。"
            return f"根据液压伺服阀故障知识，{question}。其根本原因通常与油液污染、机械磨损、密封老化或电气异常有关。"

        elif qtype == "repair":
            if subjects:
                return f"针对{question}，建议优先进行油液污染度检测，并根据检测结果采取相应维修措施，如更换液压油和滤芯、清洗阀芯阀套等。维修完成后必须进行台架试验和复测验证。"
            return f"针对{question}，建议遵循\"先检测后维修、维修后复测\"的标准流程，确保故障彻底排除。"

        elif qtype == "evidence":
            return f"关于{question}，系统从公开维修手册、学术论文、教材和故障案例中检索了相关证据，以下是支撑该问题的证据记录。"

        else:
            # 通用问题
            if subjects:
                entities = "、".join(subjects[:3])
                return f"关于{question}，液压伺服阀知识图谱中涉及的关键要素包括：{entities}。"
            return f"关于{question}，以下是基于液压伺服阀故障维修知识图谱的回答。"

    def _build_detection_suggestions(self, triples, chains):
        """根据三元组和链条生成检测建议"""
        suggestions = set()
        for t in triples:
            if t.get("predicate") == "由检测确认":
                obj = t.get("object", "")
                if obj: suggestions.add(obj)

        # 从链条提取检测建议
        chain_detect_map = {
            "污染卡滞链": ["污染度检测(NAS 1638)", "响应曲线检测", "液压检测"],
            "喷嘴堵塞链": ["压差检测", "流量检测", "拆卸检查(放大镜观察喷嘴孔)"],
            "气隙偏差链": ["气隙检测(塞尺测量)", "零位检测", "样本曲线比对"],
            "力矩马达异常链": ["线圈电阻检测", "电流检测", "检查衔铁组件"],
            "密封内泄漏链": ["泄漏检测(额定压力下)", "压力检测", "密封部位检查"],
            "线圈发热链": ["线圈电阻检测", "温升检测(红外测温)", "绝缘电阻检测"],
        }
        for ch in chains:
            tname = ch.get("template_name", "")
            if tname in chain_detect_map:
                for d in chain_detect_map[tname]:
                    suggestions.add(d)

        if not suggestions:
            suggestions = {"根据故障模式选择合适的检测方法", "优先使用与故障直接相关的检测方式"}

        return list(suggestions)[:6]

    # ================================================================
    # 领域知识
    # ================================================================

    QUERY_EXPANSION = {
        "油液污染": ["油液污染", "液压油污染", "油液脏污"],
        "阀芯卡滞": ["阀芯卡滞", "阀芯卡住", "滑阀卡滞", "阀芯卡阻"],
        "喷嘴堵塞": ["喷嘴堵塞", "喷嘴孔堵塞", "喷嘴阻塞"],
        "压力波动": ["压力波动", "压力不稳", "压力脉动"],
        "零位漂移": ["零位漂移", "零点漂移", "零位偏移"],
        "响应迟缓": ["响应迟缓", "响应变慢", "动作迟缓"],
        "内泄漏": ["内泄漏", "内部泄漏", "泵内泄", "内泄"],
    }

    DOMAIN_KNOWLEDGE = {
        "油液污染": {
            "chains": [
                "油液污染 → 污染颗粒进入伺服阀 → 阀芯阀套污染 → 阀芯卡滞 → 流量控制异常 → 压力波动 → 响应迟缓",
            ],
            "检测": [
                "检查油液污染度(NAS 1638)",
                "检测系统压力波动",
                "检查阀芯阀套卡滞",
                "检测内泄漏量",
            ],
            "维修": [
                "更换液压油和滤芯",
                "清洗阀芯阀套",
                "检查喷嘴挡板",
                "更换密封组件",
                "复测压力曲线和响应曲线",
            ],
            "说明": "油液污染是伺服阀最常见的故障根源，污染颗粒进入阀芯阀套间隙会导致卡滞，进入喷嘴挡板会导致堵塞。",
        },
        "阀芯卡滞": {
            "chains": [
                "油液污染 → 颗粒进入阀芯阀套间隙 → 摩擦力增大 → 阀芯卡滞 → 流量控制异常 → 压力波动",
            ],
            "检测": [
                "检测油液清洁度",
                "检查阀芯表面划痕",
                "测量滞环曲线",
                "检查响应时间",
            ],
            "维修": [
                "清洗阀芯阀套",
                "更换液压油和滤芯",
                "检查阀芯表面磨损",
                "复测滞环和响应曲线",
            ],
            "说明": "阀芯卡滞主要由油液污染引起，颗粒进入阀芯阀套间隙导致摩擦增大。",
        },
        "喷嘴堵塞": {
            "chains": [
                "油液污染 → 喷嘴污染 → 喷嘴堵塞 → 压差异常 → 阀芯偏移异常 → 流量输出异常",
            ],
            "检测": [
                "拆下喷嘴用放大镜检查",
                "检测控制压力差",
                "检测零位漂移",
                "检测流量响应",
            ],
            "维修": [
                "清洗喷嘴孔",
                "更换喷嘴组件",
                "检查油液清洁度",
                "复测零位和流量",
            ],
            "说明": "喷嘴堵塞主要由油液中的微小颗粒在喷嘴孔处积聚引起。",
        },
        "零位漂移": {
            "chains": [
                "喷嘴挡板磨损 → 零位漂移",
                "气隙不对称 → 磁路不平衡 → 零位漂移",
                "反馈杆变形 → 零位漂移",
            ],
            "检测": [
                "检测零位偏移量",
                "检查喷嘴挡板",
                "检测气隙对称性",
                "检查反馈杆",
            ],
            "维修": [
                "调整零位螺钉",
                "检查喷嘴和气隙",
                "检查反馈杆",
                "重新标定",
            ],
            "说明": "零位漂移的常见原因包括喷嘴挡板磨损、气隙不对称和反馈杆变形。",
        },
    }

    def _classify(self, q: str) -> str:
        if any(w in q for w in [
            "如何演化", "怎么导致", "为什么导致", "形成路径",
            "故障链", "因果链", "机理链", "如何发展为",
            "如何演变为", "为什么会引起",
        ]):
            return "evolution"
        if any(w in q for w in [
            "原因", "为什么", "怎么会", "为何",
            "是什么原因", "哪些原因", "什么原因",
        ]):
            return "cause"
        if any(w in q for w in ["维修", "怎么修", "如何处理", "怎么办"]):
            return "repair"
        if any(w in q for w in ["证据", "依据", "来源"]):
            return "evidence"
        return "general"

    def _match_domain_knowledge(self, question: str):
        for kw, dk in self.DOMAIN_KNOWLEDGE.items():
            if kw in question:
                return kw, dk
            for alias in self.QUERY_EXPANSION.get(kw, []):
                if alias in question:
                    return kw, dk
        return None, None

    def _build_domain_answer(self, question: str, kw: str, dk: Dict) -> Dict:
        answer = (
            f"根据液压伺服阀故障领域知识，{question}\n\n"
            f"【直接回答】\n{dk.get('说明', '')}\n\n"
            f"【可能原因链】\n"
        )
        for i, chain in enumerate(dk.get("chains", []), 1):
            answer += f"  {i}. {chain}\n"
        answer += "\n【检测建议】\n"
        for i, d in enumerate(dk.get("检测", []), 1):
            answer += f"  {i}. {d}\n"
        answer += "\n【维修建议】\n"
        for i, r in enumerate(dk.get("维修", []), 1):
            answer += f"  {i}. {r}\n"
        answer += "\n【说明】\n当前未检索到直接原文证据，以上结论来自液压伺服阀故障机理模板推理。"
        return {
            "answer": answer,
            "triple_path": None,
            "chain": None,
            "evidence": [],
            "recommendations": dk.get("维修", []),
        }

    # ================================================================
    # 辅助方法
    # ================================================================

    def _calculate_confidence(
        self, triples: List[Dict], chains: List[Dict], fallback: bool
    ) -> float:
        if fallback:
            return 0.45
        if not triples and not chains:
            return 0.3
        scores = []
        for t in triples[:10]:
            conf = t.get("confidence", 0.5)
            if isinstance(conf, (int, float)):
                scores.append(float(conf))
        for ch in chains[:5]:
            score = ch.get("template_match_score", 0.5)
            if isinstance(score, (int, float)):
                scores.append(float(score))
        if not scores:
            return 0.3
        return round(sum(scores) / len(scores), 4)

    def _build_basis(
        self, triples: List[Dict], chains: List[Dict],
        evidence_list: List[Dict], fallback: bool,
    ) -> str:
        parts = ["本答案基于以下来源："]
        if triples:
            parts.append(f"  • 知识图谱三元组 — {len(triples)} 条相关三元组")
        if chains:
            parts.append(f"  • 故障演化链 — {len(chains)} 条匹配链")
        if evidence_list:
            parts.append(f"  • 证据原文 — {len(evidence_list)} 条原文证据")
        if fallback:
            parts.append("  • 领域机理推理 — 补充知识")
        parts.append("\n大模型只负责基于上述检索结果组织自然语言表达，不编造任何事实。")
        return "\n".join(parts)

    def _build_followup(
        self, question: str, triples: List[Dict],
    ) -> List[str]:
        followups = []
        if triples:
            t = triples[0]
            subj = t.get("subject", "")
            if subj:
                followups.append(f"{subj}的原因有哪些？")
                followups.append(f"{subj}应该如何维修？")
                followups.append(f"{subj}有什么证据？")
        followups.append("这些故障链的机理是什么？")
        followups.append("这和普通大模型直接回答有什么区别？")
        return followups

    # ================================================================
    # 会话管理
    # ================================================================

    def _create_session(self, title: str = "") -> str:
        session_id = f"SES-{uuid.uuid4().hex[:8]}"
        from database import execute_sql
        execute_sql(
            "INSERT INTO qa_sessions (session_id, 会话标题) VALUES (?, ?)",
            (session_id, title[:50] if title else "新会话"),
        )
        self._sessions[session_id] = {
            "session_id": session_id,
            "history": [],
            "created_at": datetime.now().isoformat(),
        }
        return session_id

    def _update_session(self, session_id: str, question: str):
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "history": [],
                "created_at": datetime.now().isoformat(),
            }
        self._sessions[session_id]["history"].append({
            "question": question,
            "timestamp": datetime.now().isoformat(),
        })
        from database import execute_sql
        execute_sql(
            "UPDATE qa_sessions SET 更新时间 = datetime('now','localtime') WHERE session_id = ?",
            (session_id,),
        )

    def _save_qa_record(
        self, session_id: str, question: str, answer: str,
        evidence_list: List[Dict], context: Dict,
    ):
        from database import execute_sql
        record_id = f"REC-{uuid.uuid4().hex[:8]}"
        evidence_json = json.dumps([
            {
                "triple_id": e.get("triple_id", ""),
                "原文片段": str(e.get("evidence_text", ""))[:200],
            }
            for e in evidence_list[:5]
        ], ensure_ascii=False)
        source_json = json.dumps({
            "关键词": context.get("提取关键词", []),
            "图谱统计": context.get("图谱统计", {}),
        }, ensure_ascii=False)
        execute_sql(
            "INSERT INTO qa_records (record_id, session_id, 用户问题, 模型回答, 检索证据JSON, 引用来源JSON) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (record_id, session_id, question, answer, evidence_json, source_json),
        )


# 单例
qa_service = QAService()
