"""
机理模板校验服务 - 用液压伺服阀故障机理模板校验三元组的物理合理性

T1-T6 不是原始知识来源，而是机理约束模板。
template_source = 机理约束模板
template_role = 校验抽取三元组、组织故障演化路径、必要时补全缺失关系

T1-T6 模板的作用：
  1. 对抽取三元组进行链条匹配
  2. 给相关三元组打 template_id
  3. 检查链条是否完整
  4. 找出缺失环节
  5. 在必要时补充缺失边（标注为"机理模板补全"）
  6. 为问答提供机理解释顺序

T1 污染卡滞链: 油液污染 → 污染颗粒进入伺服阀 → 阀芯阀套污染 → 阀芯卡滞 → 流量控制异常 → 压力波动 → 响应迟缓
T2 喷嘴堵塞链: 油液污染 → 喷嘴污染 → 喷嘴堵塞 → 压差异常 → 阀芯偏移异常 → 流量输出异常 → 输出偏差
T3 气隙偏差链: 气隙垫片厚度不一致 → 气隙不对称 → 力矩马达磁路不平衡 → 零位漂移 → 伺服阀输出偏差
T4 力矩马达异常链: 力矩马达异常 → 电磁力矩异常 → 衔铁偏转异常 → 阀芯偏移 → 零位漂移 → 输出不对称
T5 密封内泄漏链: 密封组件磨损 → 内泄漏 → 压力下降 → 流量损失 → 响应迟缓
T6 线圈发热链: 线圈发热异常 → 电流异常 → 电磁力矩波动 → 输出不稳定 → 响应异常
"""
import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MechanismValidationService:
    """机理模板校验器 - 校验三元组链条完整性，必要时补全缺失关系"""

    # ================================================================
    # T1-T6 液压伺服阀故障演化机理模板
    # ================================================================

    MECHANISM_TEMPLATES = [
        {
            "template_id": "T1",
            "template_name": "污染卡滞链",
            "description": "油液污染 → 污染颗粒进入伺服阀 → 阀芯阀套污染 → 阀芯卡滞 → 流量控制异常 → 压力波动 → 响应迟缓",
            "chain_steps": [
                "油液污染", "污染颗粒进入伺服阀", "阀芯阀套污染",
                "阀芯卡滞", "流量控制异常", "压力波动", "响应迟缓",
            ],
            "expected_triples": [
                {"subject": "油液污染", "predicate": "导致", "object": "污染颗粒进入伺服阀"},
                {"subject": "污染颗粒进入伺服阀", "predicate": "导致", "object": "阀芯阀套污染"},
                {"subject": "阀芯阀套污染", "predicate": "导致", "object": "阀芯卡滞"},
                {"subject": "阀芯卡滞", "predicate": "导致", "object": "流量控制异常"},
                {"subject": "流量控制异常", "predicate": "导致", "object": "压力波动"},
                {"subject": "压力波动", "predicate": "导致", "object": "响应迟缓"},
                {"subject": "阀芯卡滞", "predicate": "由检测确认", "object": "响应曲线检测"},
                {"subject": "油液污染", "predicate": "由检测确认", "object": "污染度检测"},
                {"subject": "阀芯卡滞", "predicate": "由维修处理", "object": "清洗阀芯"},
                {"subject": "油液污染", "predicate": "由维修处理", "object": "更换液压油"},
            ],
            "physical_constraint": "污染是卡滞的根本原因，颗粒进入阀芯阀套间隙导致摩擦力增大，顺序不可逆",
        },
        {
            "template_id": "T2",
            "template_name": "喷嘴堵塞链",
            "description": "油液污染 → 喷嘴污染 → 喷嘴堵塞 → 压差异常 → 阀芯偏移异常 → 流量输出异常 → 输出偏差",
            "chain_steps": [
                "油液污染", "喷嘴污染", "喷嘴堵塞",
                "压差异常", "阀芯偏移异常", "流量输出异常", "输出偏差",
            ],
            "expected_triples": [
                {"subject": "油液污染", "predicate": "导致", "object": "喷嘴污染"},
                {"subject": "喷嘴污染", "predicate": "导致", "object": "喷嘴堵塞"},
                {"subject": "喷嘴堵塞", "predicate": "导致", "object": "压差异常"},
                {"subject": "压差异常", "predicate": "导致", "object": "阀芯偏移异常"},
                {"subject": "阀芯偏移异常", "predicate": "导致", "object": "流量输出异常"},
                {"subject": "流量输出异常", "predicate": "导致", "object": "输出偏差"},
                {"subject": "喷嘴堵塞", "predicate": "由检测确认", "object": "压差检测"},
                {"subject": "喷嘴堵塞", "predicate": "由维修处理", "object": "清洗喷嘴挡板"},
            ],
            "physical_constraint": "颗粒在喷嘴孔处积聚导致堵塞，引起控制腔压差异常，不可逆",
        },
        {
            "template_id": "T3",
            "template_name": "气隙偏差链",
            "description": "气隙垫片厚度不一致 → 气隙不对称 → 力矩马达磁路不平衡 → 零位漂移 → 伺服阀输出偏差",
            "chain_steps": [
                "气隙垫片厚度不一致", "气隙不对称",
                "力矩马达磁路不平衡", "零位漂移", "伺服阀输出偏差",
            ],
            "expected_triples": [
                {"subject": "气隙垫片厚度不一致", "predicate": "导致", "object": "气隙不对称"},
                {"subject": "气隙不对称", "predicate": "导致", "object": "力矩马达磁路不平衡"},
                {"subject": "力矩马达磁路不平衡", "predicate": "导致", "object": "零位漂移"},
                {"subject": "零位漂移", "predicate": "导致", "object": "伺服阀输出偏差"},
                {"subject": "气隙不对称", "predicate": "由检测确认", "object": "气隙检测"},
                {"subject": "零位漂移", "predicate": "由检测确认", "object": "零位检测"},
                {"subject": "气隙不对称", "predicate": "由维修处理", "object": "检查气隙垫片"},
                {"subject": "零位漂移", "predicate": "由维修处理", "object": "调整零位"},
            ],
            "physical_constraint": "气隙垫片厚度不一致是气隙不对称的直接原因，进而导致磁路不平衡",
        },
        {
            "template_id": "T4",
            "template_name": "力矩马达异常链",
            "description": "力矩马达异常 → 电磁力矩异常 → 衔铁偏转异常 → 阀芯偏移 → 零位漂移 → 输出不对称",
            "chain_steps": [
                "力矩马达异常", "电磁力矩异常", "衔铁偏转异常",
                "阀芯偏移", "零位漂移", "输出不对称",
            ],
            "expected_triples": [
                {"subject": "力矩马达异常", "predicate": "导致", "object": "电磁力矩异常"},
                {"subject": "电磁力矩异常", "predicate": "导致", "object": "衔铁偏转异常"},
                {"subject": "衔铁偏转异常", "predicate": "导致", "object": "阀芯偏移"},
                {"subject": "阀芯偏移", "predicate": "导致", "object": "零位漂移"},
                {"subject": "零位漂移", "predicate": "导致", "object": "输出不对称"},
                {"subject": "力矩马达异常", "predicate": "由检测确认", "object": "线圈电阻检测"},
                {"subject": "力矩马达异常", "predicate": "由维修处理", "object": "检查力矩马达"},
                {"subject": "零位漂移", "predicate": "由维修处理", "object": "重新标定"},
            ],
            "physical_constraint": "力矩马达是伺服阀的驱动源，其异常会导致衔铁偏转异常，不可逆",
        },
        {
            "template_id": "T5",
            "template_name": "密封内泄漏链",
            "description": "密封组件磨损 → 内泄漏 → 压力下降 → 流量损失 → 响应迟缓",
            "chain_steps": [
                "密封组件磨损", "内泄漏", "压力下降", "流量损失", "响应迟缓",
            ],
            "expected_triples": [
                {"subject": "密封组件磨损", "predicate": "导致", "object": "内泄漏"},
                {"subject": "内泄漏", "predicate": "导致", "object": "压力下降"},
                {"subject": "压力下降", "predicate": "导致", "object": "流量损失"},
                {"subject": "流量损失", "predicate": "导致", "object": "响应迟缓"},
                {"subject": "内泄漏", "predicate": "由检测确认", "object": "泄漏检测"},
                {"subject": "内泄漏", "predicate": "由维修处理", "object": "更换密封组件"},
            ],
            "physical_constraint": "密封组件磨损导致内部泄漏增大，压力下降和流量损失是必然结果",
        },
        {
            "template_id": "T6",
            "template_name": "线圈发热链",
            "description": "线圈发热异常 → 电流异常 → 电磁力矩波动 → 输出不稳定 → 响应异常",
            "chain_steps": [
                "线圈发热异常", "电流异常", "电磁力矩波动", "输出不稳定", "响应异常",
            ],
            "expected_triples": [
                {"subject": "线圈发热异常", "predicate": "导致", "object": "电流异常"},
                {"subject": "电流异常", "predicate": "导致", "object": "电磁力矩波动"},
                {"subject": "电磁力矩波动", "predicate": "导致", "object": "输出不稳定"},
                {"subject": "输出不稳定", "predicate": "导致", "object": "响应异常"},
                {"subject": "线圈发热异常", "predicate": "由检测确认", "object": "线圈电阻检测"},
                {"subject": "线圈发热异常", "predicate": "由维修处理", "object": "检查线圈电阻"},
            ],
            "physical_constraint": "线圈发热导致电阻变化，引起电流和电磁力矩异常，不可逆",
        },
    ]

    def __init__(self):
        pass

    # ================================================================
    # 公开接口
    # ================================================================

    def validate_all(self, merged_triples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """对所有融合三元组执行机理模板校验

        Args:
            merged_triples: 融合后的三元组列表

        Returns:
            {
                "模板总数": 6,
                "校验结果": [...],
                "chains": [...],
                "completed_triples": [...],
                "统计": {...}
            }
        """
        all_results = []
        all_chain_data = []
        all_completed_triples = []  # 模板补全的三元组

        for template in self.MECHANISM_TEMPLATES:
            result = self._validate_template(merged_triples, template)
            all_results.append(result)

            # 构建链条数据 - 确保 chain_links 包含所有预期三元组的边
            chain_nodes = list(template["chain_steps"])
            chain_links = []
            for et in template["expected_triples"]:
                link_id = f"LINK-{et['subject']}-{et['predicate']}-{et['object']}"[:80]
                chain_links.append(link_id)

            chain_info = {
                "template_id": template["template_id"],
                "template_name": template["template_name"],
                "chain_text": " → ".join(template["chain_steps"]),
                "chain_nodes": chain_nodes,
                "chain_links": chain_links,
                "evidence_coverage": result.get("evidence_coverage", 0),
                "template_match_score": result.get("template_match_score", 0),
            }
            all_chain_data.append(chain_info)

            # 收集模板补全的三元组
            for ct in result.get("completed_triples", []):
                all_completed_triples.append(ct)

        # 统计
        stats = {
            "模板总数": len(self.MECHANISM_TEMPLATES),
            "总预期三元组数": sum(len(t["expected_triples"]) for t in self.MECHANISM_TEMPLATES),
            "总命中三元组数": sum(len(r["matched_triples"]) for r in all_results),
            "总缺失三元组数": sum(len(r["missing_triples"]) for r in all_results),
            "总补全三元组数": len(all_completed_triples),
            "平均证据覆盖率": round(
                sum(r.get("evidence_coverage", 0) for r in all_results) /
                max(len(all_results), 1), 2
            ),
        }

        # 保存结果
        gdir = os.path.join(BASE, "data", "graph")
        os.makedirs(gdir, exist_ok=True)

        with open(os.path.join(gdir, "chains.json"), "w", encoding="utf-8") as f:
            json.dump(all_chain_data, f, ensure_ascii=False, indent=2)

        report = {
            "模板总数": len(self.MECHANISM_TEMPLATES),
            "校验结果": all_results,
            "统计": stats,
            "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(os.path.join(gdir, "mechanism_validation_report.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return {
            "模板总数": len(self.MECHANISM_TEMPLATES),
            "校验结果": all_results,
            "chains": all_chain_data,
            "completed_triples": all_completed_triples,
            "统计": stats,
        }

    def _validate_template(
        self, merged_triples: List[Dict], template: Dict
    ) -> Dict[str, Any]:
        """将融合三元组与单个模板进行匹配校验"""
        tid = template["template_id"]
        tname = template["template_name"]
        expected = template["expected_triples"]
        constraint = template["physical_constraint"]

        # 构建已存在的三元组索引
        triple_index = {}
        for t in merged_triples:
            key = f"{t.get('subject','')}|{t.get('predicate','')}|{t.get('object','')}"
            triple_index[key] = t
            # 也加入归一化键
            from services.fusion_service import fusion as fusion_svc
            subj = fusion_svc.normalize_term(t.get("subject", ""))
            obj = fusion_svc.normalize_term(t.get("object", ""))
            pred = t.get("predicate", "")
            norm_key = f"{subj}|{pred}|{obj}"
            if norm_key != key:
                triple_index[norm_key] = t

        matched_triples = []
        missing_triples = []
        evidence_texts = []

        for et in expected:
            et_key = f"{et['subject']}|{et['predicate']}|{et['object']}"
            # 同时检查归一化后的key
            from services.fusion_service import fusion as fusion_svc
            norm_subj = fusion_svc.normalize_term(et["subject"])
            norm_obj = fusion_svc.normalize_term(et["object"])
            norm_key = f"{norm_subj}|{et['predicate']}|{norm_obj}"

            found = triple_index.get(et_key) or triple_index.get(norm_key)
            if found:
                matched_triples.append({
                    "triple_text": f"{et['subject']} — {et['predicate']} — {et['object']}",
                    "merged_triple_id": found.get("merged_triple_id", ""),
                    "source": found.get("triple_source", ""),
                    "evidence_texts": found.get("evidence_texts", []),
                })
                evidence_texts.extend(found.get("evidence_texts", []))
            else:
                missing_triples.append({
                    "triple_text": f"{et['subject']} — {et['predicate']} — {et['object']}",
                })

        # 计算覆盖率
        total_expected = len(expected)
        matched_count = len(matched_triples)
        match_score = round(matched_count / max(total_expected, 1), 4)
        evidence_coverage = round(
            len([e for e in evidence_texts if e]) / max(total_expected, 1), 4
        )

        # 补全缺失的三元组（标注为机理模板补全）
        completed_triples = []
        for mt in missing_triples:
            parts = mt["triple_text"].split(" — ")
            if len(parts) == 3:
                completed_triples.append({
                    "subject": parts[0],
                    "predicate": parts[1],
                    "object": parts[2],
                    "subject_type": self._infer_type(parts[0]),
                    "object_type": self._infer_type(parts[2]),
                    "relation_type": parts[1],
                    "triple_source": "机理模板补全",
                    "template_id": tid,
                    "template_name": tname,
                    "说明": f"由{tid} {tname}机理模板补全，暂无直接原始证据",
                })

        return {
            "template_id": tid,
            "template_name": tname,
            "expected_triples": [f"{et['subject']} — {et['predicate']} — {et['object']}" for et in expected],
            "matched_triples": matched_triples,
            "missing_triples": missing_triples,
            "completed_triples": completed_triples,
            "evidence_coverage": evidence_coverage,
            "template_match_score": match_score,
            "physical_constraint": constraint,
            "说明": f"{tid} {tname}：命中{matched_count}/{total_expected}条预期三元组，补全{len(completed_triples)}条缺失关系",
        }

    def _infer_type(self, name: str) -> str:
        """推断实体类型"""
        from services.event_extract_service import (
            COMPONENTS, FAULT_MODES, ABNORMAL_STATES, DETECTIONS, ACTIONS,
        )
        if name in COMPONENTS:
            return "部件"
        if name in FAULT_MODES:
            return "故障模式"
        if name in ABNORMAL_STATES:
            return "异常状态"
        if name in DETECTIONS:
            return "检测方式"
        if name in ACTIONS:
            return "维修动作"
        if "T1" in name or "T2" in name or "T3" in name or "T4" in name or "T5" in name or "T6" in name:
            return "机理模板"
        # 推断规则
        if any(w in name for w in ["检测", "测试", "复测", "比对", "试验"]):
            return "检测方式"
        if any(w in name for w in ["更换", "清洗", "检查", "调整", "标定", "维修"]):
            return "维修动作"
        if any(w in name for w in ["异常", "卡滞", "堵塞", "磨损", "失效", "污染", "泄漏", "偏差"]):
            return "故障模式"
        if any(w in name for w in ["波动", "漂移", "迟缓", "下降", "损失", "不稳定"]):
            return "异常状态"
        return "故障模式"


# 单例
mechanism_validator = MechanismValidationService()
