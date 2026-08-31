"""
维修方案推荐服务 - 基于故障模式、部件、症状匹配维修规则

推荐算法:
  优先级分数 = 症状匹配度×0.4 + 机理模板匹配度×0.3 + 证据可靠度×0.2 + 风险等级权重×0.1

覆盖 6 类核心故障:
  内泄漏、过滤器堵塞、阀芯卡滞、冷却器效率下降、
  蓄能器预充压力不足、溢流阀异常
"""
import json
import os
from typing import Optional, List, Dict, Any, Tuple


class RecommendService:
    """维修方案推荐器 - 多维度匹配评分"""

    # 6 类核心故障的维修规则定义
    CORE_MAINTENANCE_RULES: Dict[str, Dict[str, Any]] = {
        "内泄漏": {
            "故障模式": "内泄漏",
            "可能故障": ["密封件老化或损坏", "柱塞与缸孔配合间隙增大", "配流盘端面磨损", "滑靴静压支承失效"],
            "推荐维修动作": [
                "检查密封件状态",
                "更换密封组件（全套密封件、O形圈、旋转轴封）",
                "拆检泵体，检查配流盘与缸体端面磨损情况",
                "检查柱塞与缸孔配合间隙是否超出允许范围",
                "更换磨损超差的柱塞副",
                "重新装配后进行台架试验",
                "复测系统压力，确认容积效率恢复至92%以上",
            ],
            "风险等级": "高",
            "风险等级权重": 0.9,
            "推荐理由": (
                "内泄漏是液压系统最常见的严重故障。根据双时态事件知识图谱，"
                "内泄漏会导致流量损失→压力下降→执行机构动作迟缓的连锁反应。"
                "如果不及时处理，可能引发油温升高、密封件加速老化的恶性循环。"
            ),
            "注意事项": [
                "拆卸前清洁泵体外部，防止污染物进入泵内",
                "必须使用原厂密封件套件",
                "更换后需进行低压磨合（5MPa/15min）→中压试验（20MPa/10min）→额定压力试验（35MPa/10min）",
                "记录试验数据备查",
            ],
            "预计停机时间_小时": 8.0,
            "是否需要人工复核": True,
        },
        "过滤器堵塞": {
            "故障模式": "过滤器堵塞",
            "可能故障": ["滤芯表面积垢", "油液污染严重", "旁通阀频繁开启损坏", "过滤器进出口压差过大"],
            "推荐维修动作": [
                "清洗过滤器壳体内部",
                "更换过滤器滤芯（吸油滤芯+回油滤芯+高压滤芯）",
                "检查吸油管路密封状态",
                "检查旁通阀是否因频繁开启而损坏",
                "分析污染物来源，排查系统异常磨损部件",
                "更换液压油并对系统进行循环冲洗",
                "冲洗后复测油液清洁度（ISO 4406 -/18/15）",
            ],
            "风险等级": "中",
            "风险等级权重": 0.6,
            "推荐理由": (
                "过滤器堵塞会导致吸油阻力增大→泵吸空→气蚀→噪声增大的连锁故障。"
                "根据机理模板T2（堵塞链），必须同时检查吸油管路和油液污染源，"
                "否则仅更换滤芯不能根本解决问题。"
            ),
            "注意事项": [
                "更换滤芯时注意方向标识",
                "更换后确认堵塞指示器复位",
                "压差不超过0.05MPa",
                "油液清洁度达标后再投入正常使用",
            ],
            "预计停机时间_小时": 4.0,
            "是否需要人工复核": False,
        },
        "阀芯卡滞": {
            "故障模式": "阀芯卡滞",
            "可能故障": ["液压油中固体颗粒进入阀芯配合间隙", "油液温度过高导致阀芯膨胀", "阀体变形", "阀芯表面沉积物"],
            "推荐维修动作": [
                "拆卸阀体，取出阀芯",
                "用清洁液压油清洗阀芯和阀体配合面",
                "使用细砂纸打磨阀芯表面轻微划痕（2000目以上）",
                "检查并疏通阀体各油孔和阻尼孔",
                "检查阀芯是否严重拉伤或弯曲变形（如变形需更换阀芯组件）",
                "清洗或更换过滤器滤芯",
                "更换液压油至标准液位",
                "复测压力波动（确认在±0.5MPa以内）",
            ],
            "风险等级": "中",
            "风险等级权重": 0.5,
            "推荐理由": (
                "阀芯卡滞的根本原因是油液污染。根据机理模板T5（污染链），"
                "油液污染→阀芯卡滞→流量控制异常→压力波动。单纯清洗阀芯不"
                "解决根本问题，必须同时处理油液污染源。"
            ),
            "注意事项": [
                "拆卸阀芯时注意不要损伤配合面",
                "清洗后阀芯应能灵活移动，无卡滞感",
                "油液清洁度应维持在ISO 4406 -/18/15以内",
                "定期采集油样检测颗粒污染度",
            ],
            "预计停机时间_小时": 6.0,
            "是否需要人工复核": True,
        },
        "冷却器效率下降": {
            "故障模式": "冷却器效率下降",
            "可能故障": ["管束内部结垢（水冷式）", "散热翅片积尘（风冷式）", "冷却水流量不足", "风扇转速不足"],
            "推荐维修动作": [
                "检查冷却器油侧进出口温差（应≥15℃）",
                "检查冷却介质进出口温差（应≥8℃）",
                "对冷却器管束进行化学清洗除垢（水冷式）",
                "清洗冷却器翅片表面污物（风冷式）",
                "检查冷却水流量或风扇转速是否正常",
                "如冷却器内部严重结垢无法清洗，更换冷却器芯体",
                "监测油温恢复情况（连续运行4小时油温应稳定在55℃以下）",
            ],
            "风险等级": "中",
            "风险等级权重": 0.5,
            "推荐理由": (
                "冷却器效率下降是油温升高的直接原因。根据机理模板T3（冷却链），"
                "冷却器效率下降→油温升高→黏度下降→泄漏增加，形成恶性循环。"
                "油温每升高10℃将加速油液氧化和密封件老化，必须及时处理。"
            ),
            "注意事项": [
                "化学清洗时注意使用合适的清洗剂",
                "清洗后测量换热效率恢复至设计值",
                "建议增加冷却水处理，防止再次结垢",
                "风冷式冷却器应定期吹扫散热翅片",
            ],
            "预计停机时间_小时": 5.0,
            "是否需要人工复核": False,
        },
        "蓄能器预充压力不足": {
            "故障模式": "蓄能器预充压力不足",
            "可能故障": ["气囊老化破损", "充气阀密封不良", "氮气泄漏", "预充压力长期未检测"],
            "推荐维修动作": [
                "检测预充压力（使用专用氮气压力表）",
                "确认预充压力是否低于设计要求（通常为系统最低工作压力的80%-90%）",
                "检查气囊完整性（使用充氮工具检查是否泄漏）",
                "更换破损气囊",
                "重新充氮至设计预充压力值",
                "检查蓄能器油侧接口密封状态",
                "24小时后复测预充压力，确认无明显下降",
            ],
            "风险等级": "中",
            "风险等级权重": 0.4,
            "推荐理由": (
                "蓄能器预充压力不足将直接导致保压失败和压力波动。"
                "根据机理模板T4（蓄能器链），预充压力不足→保压失败→压力波动。"
                "预充压力检测应纳入日常巡检项目（建议每3个月检测一次）。"
            ),
            "注意事项": [
                "检测前必须卸除蓄能器油侧压力",
                "使用高纯氮气（99.9%以上）充氮",
                "不得使用氧气或压缩空气充氮",
                "充氮压力不得超过蓄能器铭牌规定值",
            ],
            "预计停机时间_小时": 3.0,
            "是否需要人工复核": False,
        },
        "溢流阀异常": {
            "故障模式": "溢流阀异常",
            "可能故障": ["主阀芯卡滞", "调压弹簧疲劳变形或断裂", "阻尼孔堵塞", "导阀阀座密封不严", "阀芯磨损"],
            "推荐维修动作": [
                "缓慢旋转调压手柄，观察压力表是否线性变化",
                "拆卸溢流阀并彻底清洗所有零件",
                "检查并研磨主阀芯与阀座的密封锥面",
                "疏通阻尼孔",
                "检查调压弹簧是否疲劳变形（如变形或断裂需更换）",
                "重新装配后调整溢流压力至额定值",
                "反复加卸载3次确认压力重复性",
                "复测系统压力（波动不超过±0.5MPa）",
                "锁紧调压手柄防松螺母",
            ],
            "风险等级": "高",
            "风险等级权重": 0.8,
            "推荐理由": (
                "溢流阀是液压系统的关键安全保护元件。溢流阀异常可能导致"
                "系统压力失控，严重时可能造成设备损坏或安全事故。"
                "根据机理模板T6（溢流阀链），溢流阀异常→系统压力异常→负载能力下降。"
                "必须确保维修后溢流阀调压功能正常。"
            ),
            "注意事项": [
                "拆卸前标记调压手柄位置",
                "密封锥面研磨后需进行密封性测试",
                "调压弹簧必须使用原厂同规格弹簧",
                "维修后必须锁紧防松螺母",
                "在额定压力下保压5分钟无异常",
            ],
            "预计停机时间_小时": 6.0,
            "是否需要人工复核": True,
        },
    }

    def __init__(self):
        self._graph_chains: List[Dict] = []
        self._load_graph_data()

    def _load_graph_data(self):
        """加载图谱数据用于模板匹配"""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        chains_path = os.path.join(base_dir, "data", "graph", "chains.json")
        if os.path.exists(chains_path):
            with open(chains_path, encoding="utf-8") as f:
                self._graph_chains = json.load(f)

    # ================================================================
    # 公开接口
    # ================================================================

    def recommend(self,
                  component: Optional[str] = None,
                  fault_mode: Optional[str] = None,
                  symptoms: Optional[List[str]] = None) -> Dict[str, Any]:
        """根据故障信息推荐维修方案

        Args:
            component: 部件名称（如：液压泵、溢流阀、过滤器）
            fault_mode: 故障模式（如：内泄漏、过滤器堵塞）
            symptoms: 异常状态列表（如：压力下降、油温升高）

        Returns:
            包含完整推荐结果的字典
        """
        # 1. 匹配维修规则
        matched_rule, rule_source = self._match_rule(fault_mode, symptoms)

        # 2. 匹配机理模板链
        matched_chains, template_score = self._match_templates(fault_mode, symptoms)

        # 3. 检索支撑证据
        evidence_list = self._search_evidence(fault_mode, component, symptoms)

        # 4. 计算各维度分数
        symptom_score = self._calc_symptom_score(fault_mode, symptoms)
        evidence_score = self._calc_evidence_reliability(evidence_list)
        risk_weight = matched_rule.get("风险等级权重", 0.5) if matched_rule else 0.5

        # 5. 计算优先级分数
        priority_score = round(
            symptom_score * 0.4 +
            template_score * 0.3 +
            evidence_score * 0.2 +
            risk_weight * 0.1,
            4
        )

        # 6. 构建推荐维修动作
        actions = matched_rule.get("推荐维修动作", []) if matched_rule else []
        # 也从数据库补充
        db_actions = self._get_db_actions(fault_mode, component)
        for a in db_actions:
            if a not in actions:
                actions.append(a)

        return {
            "部件": component or "未指定",
            "故障模式": fault_mode or "未指定",
            "异常状态列表": symptoms or [],
            "可能故障": matched_rule.get("可能故障", []) if matched_rule else [],
            "命中机理模板": [ch.get("模板名称", "") for ch in matched_chains[:3]],
            "匹配事件链": matched_chains[:3],
            "推荐维修动作": actions,
            "注意事项": matched_rule.get("注意事项", []) if matched_rule else [],
            "优先级分数": priority_score,
            "风险等级": matched_rule.get("风险等级", "未知") if matched_rule else "未知",
            "推荐理由": matched_rule.get("推荐理由", "") if matched_rule else "",
            "支撑证据": evidence_list[:5],
            "预计停机时间_小时": matched_rule.get("预计停机时间_小时", None) if matched_rule else None,
            "是否需要人工复核": matched_rule.get("是否需要人工复核", True) if matched_rule else True,
            "规则来源": rule_source,
        }

    # ================================================================
    # 规则匹配
    # ================================================================

    def _match_rule(self, fault_mode: Optional[str],
                     symptoms: Optional[List[str]]) -> Tuple[Optional[Dict], str]:
        """匹配维修规则"""
        # 精确匹配故障模式
        if fault_mode:
            for key, rule in self.CORE_MAINTENANCE_RULES.items():
                if key == fault_mode or key in fault_mode or fault_mode in key:
                    return rule, "内置核心维修规则（精确匹配）"

        # 症状模糊匹配
        if symptoms:
            for symptom in symptoms:
                for key, rule in self.CORE_MAINTENANCE_RULES.items():
                    if symptom in key or key in symptom:
                        return rule, "内置核心维修规则（症状匹配）"
                    # 检查可能故障列表中是否包含症状
                    for pf in rule.get("可能故障", []):
                        if symptom in pf:
                            return rule, "内置核心维修规则（可能故障匹配）"

        # 从数据库补充
        from database import fetch_all
        if fault_mode:
            rows = fetch_all(
                "SELECT * FROM maintenance_rules WHERE 故障模式 LIKE ? LIMIT 1",
                (f"%{fault_mode}%",)
            )
            if rows:
                r = dict(rows[0])
                steps_str = r.get("操作步骤JSON", "[]")
                try:
                    steps = json.loads(steps_str) if isinstance(steps_str, str) else (steps_str or [])
                except:
                    steps = []
                return {
                    "故障模式": r.get("故障模式", ""),
                    "可能故障": [r.get("故障模式", "")],
                    "推荐维修动作": steps if steps else [r.get("维修方案", "")],
                    "风险等级": "中",
                    "风险等级权重": 0.5,
                    "推荐理由": r.get("维修方案", ""),
                    "注意事项": [],
                    "预计停机时间_小时": None,
                    "是否需要人工复核": True,
                }, "数据库维修规则"

        return None, "无匹配规则"

    def _get_db_actions(self, fault_mode: Optional[str],
                         component: Optional[str]) -> List[str]:
        """从数据库获取补充维修动作"""
        from database import fetch_all
        actions = []
        if fault_mode:
            rows = fetch_all(
                "SELECT * FROM maintenance_rules WHERE 故障模式 LIKE ?",
                (f"%{fault_mode}%",)
            )
            for r in rows:
                scheme = r.get("维修方案", "")
                if scheme:
                    actions.extend(scheme.split("; "))
        if component and not actions:
            rows = fetch_all(
                "SELECT * FROM maintenance_rules WHERE 适用条件 LIKE ?",
                (f"%{component}%",)
            )
            for r in rows:
                scheme = r.get("维修方案", "")
                if scheme:
                    actions.extend(scheme.split("; "))
        return list(set(actions))[:10]

    # ================================================================
    # 模板匹配
    # ================================================================

    def _match_templates(self, fault_mode: Optional[str],
                          symptoms: Optional[List[str]]) -> Tuple[List[Dict], float]:
        """匹配机理模板"""
        matched = []
        search_terms = []
        if fault_mode:
            search_terms.append(fault_mode)
        if symptoms:
            search_terms.extend(symptoms)

        for chain in self._graph_chains:
            if not isinstance(chain, dict):
                continue
            pattern = chain.get("中文链式模式", "")
            tname = chain.get("模板名称", "")
            for term in search_terms:
                if term in pattern or term in tname:
                    if chain not in matched:
                        matched.append(chain)
                    break

        # 计算模板匹配分数
        if matched:
            scores = [ch.get("匹配分数", 0.5) for ch in matched]
            template_score = sum(scores) / len(scores)
        else:
            template_score = 0.0

        return matched, template_score

    # ================================================================
    # 证据检索
    # ================================================================

    def _search_evidence(self, fault_mode: Optional[str],
                          component: Optional[str],
                          symptoms: Optional[List[str]]) -> List[Dict]:
        """检索支撑证据"""
        from database import fetch_all
        evidence_list = []
        seen = set()

        search_terms = []
        if fault_mode:
            search_terms.append(fault_mode)
        if component:
            search_terms.append(component)
        if symptoms:
            search_terms.extend(symptoms)

        for term in search_terms[:5]:
            rows = fetch_all(
                "SELECT * FROM evidence WHERE 原文片段 LIKE ? LIMIT 5",
                (f"%{term}%",)
            )
            for r in rows:
                eid = r.get("evidence_id", "")
                if eid not in seen:
                    seen.add(eid)
                    evidence_list.append({
                        "证据编号": r.get("evidence_id", ""),
                        "事件编号": r.get("event_id", ""),
                        "来源编号": r.get("来源文件", ""),
                        "原文片段": (r.get("原文片段", "") or "")[:200],
                        "可靠度": "中",
                    })

        return evidence_list

    # ================================================================
    # 分数计算
    # ================================================================

    def _calc_symptom_score(self, fault_mode: Optional[str],
                             symptoms: Optional[List[str]]) -> float:
        """计算症状匹配度 (0~1)"""
        if not symptoms and not fault_mode:
            return 0.3

        score = 0.0
        if fault_mode:
            score += 0.5  # 有明确故障模式

        if symptoms:
            # 每个匹配症状加分
            for symptom in symptoms:
                for key, rule in self.CORE_MAINTENANCE_RULES.items():
                    # 检查症状是否与故障相关
                    for pf in rule.get("可能故障", []):
                        if symptom in pf or pf in symptom:
                            score += 0.15
                            break
        return min(score, 0.95)

    def _calc_evidence_reliability(self, evidence_list: List[Dict]) -> float:
        """计算证据可靠度 (0~1)"""
        if not evidence_list:
            return 0.3

        scores = []
        for evd in evidence_list:
            rel = evd.get("可靠度", "中")
            if rel == "高":
                scores.append(0.9)
            elif rel == "中":
                scores.append(0.6)
            else:
                scores.append(0.3)

        return sum(scores) / len(scores) if scores else 0.3


# 单例
recommend_service = RecommendService()
