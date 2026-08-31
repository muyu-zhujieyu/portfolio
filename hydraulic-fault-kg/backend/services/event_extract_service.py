# -*- coding: utf-8 -*-
"""
液压伺服阀故障维修三元组抽取服务 - 多模式多关系抽取

支持模式:
  A: 包含关系 (X包含A、B、C)
  B: 因果关系 (A导致B)
  C: 链式因果 (A导致B，B导致C)
  D: 表现关系 (A表现为B)
  E: 检测确认 (A可通过B确认)
  F: 维修处理 (A的维修措施包括B)
  G: 复测验证 (B后应复测C)
  H: 部件故障发生 (A发生于B)
  I: 段落级共现 (故障+检测/维修词共现)
"""
import re
from typing import List, Dict, Any, Tuple

# ================================================================
# 领域词典
# ================================================================
COMPONENTS = [
    "液压伺服阀", "电液伺服阀", "伺服阀",
    "阀芯阀套", "阀芯", "阀套",
    "喷嘴挡板", "喷嘴", "挡板",
    "力矩马达", "衔铁组件", "衔铁",
    "反馈杆", "气隙垫片", "线圈与磁路", "线圈", "磁路",
    "密封组件", "过滤组件", "控制边", "节流边", "油液",
    "供油口P", "回油口T", "工作口A", "工作口B",
]

FAULT_MODES = [
    "油液污染", "阀芯卡滞", "阀芯磨损", "阀芯污染",
    "喷嘴堵塞", "喷嘴污染", "气隙不对称", "气隙垫片厚度不一致",
    "力矩马达异常", "磁路不平衡", "力矩马达磁路不平衡", "衔铁偏移",
    "零位漂移", "滞环增大", "响应迟缓", "压力波动", "流量控制异常",
    "内泄漏", "密封失效", "密封组件磨损",
    "线圈发热异常", "反馈异常",
    "输出偏差", "输出不稳定", "输出不对称",
    "压差异常", "阀芯偏移异常", "阀芯偏移",
    "流量输出异常", "电流异常", "电磁力矩波动",
    "电磁力矩异常", "衔铁偏转异常",
    "污染颗粒进入伺服阀", "阀芯阀套污染",
    "伺服阀输出偏差", "响应异常",
    "压力下降", "流量损失",
]

ABNORMAL_STATES = [
    "零位偏移", "响应变慢", "流量波动", "输出不对称", "重复性下降",
    "曲线粗糙度增大", "左右不对称", "温升异常", "内泄漏增大",
    "控制压力下降", "响应时间延长", "压力下降", "流量损失", "能量损失",
    "电流异常", "压力波动", "输出偏差", "输出不稳定", "响应迟缓",
    "电磁力矩波动", "磁路不平衡", "滞环增大",
    "伺服阀输出偏差", "压差异常", "阀芯偏移异常", "流量输出异常",
]

DETECTIONS = [
    "污染度检测", "响应曲线检测", "压力检测", "流量检测",
    "压差检测", "零位检测", "气隙检测", "样本曲线比对",
    "线圈电阻检测", "电流检测", "温升检测", "泄漏检测",
    "台架试验", "维修后复测", "复测响应曲线",
    "复测压力曲线", "复测流量响应",
    "红外测温", "拆卸检查", "目视检查",
    "绝缘电阻检测", "放大镜检查",
]

ACTIONS = [
    "更换液压油", "更换滤芯", "清洗阀芯", "清洗伺服阀",
    "清洗喷嘴挡板", "检查污染度", "检查气隙垫片", "调整零位",
    "重新标定", "检查力矩马达", "检查线圈电阻", "检查衔铁组件",
    "检查反馈杆", "更换密封组件", "复测响应曲线", "复测压力曲线",
    "复测流量响应", "排除污染颗粒", "调整气隙对称",
    "检查磁路", "检查力矩马达", "检查绝缘电阻",
    "超声波清洗", "更换密封圈", "更换密封垫",
    "更换力矩马达线圈组件",
]

# 匹配映射
PART_FAULT_MAP = {
    "阀芯阀套": ["阀芯卡滞", "阀芯磨损", "阀芯污染"],
    "阀芯": ["阀芯卡滞", "阀芯磨损"],
    "喷嘴挡板": ["喷嘴堵塞", "喷嘴污染"],
    "喷嘴": ["喷嘴堵塞", "喷嘴污染"],
    "力矩马达": ["力矩马达异常", "衔铁偏移", "衔铁偏转异常"],
    "衔铁组件": ["衔铁偏移", "衔铁偏转异常"],
    "衔铁": ["衔铁偏移"],
    "气隙垫片": ["气隙不对称", "气隙垫片厚度不一致"],
    "线圈与磁路": ["线圈发热异常", "电流异常", "磁路不平衡"],
    "线圈": ["线圈发热异常"],
    "磁路": ["磁路不平衡", "力矩马达磁路不平衡"],
    "密封组件": ["密封失效", "密封组件磨损", "内泄漏"],
    "过滤组件": ["油液污染"],
    "反馈杆": ["反馈异常"],
}

FAULT_DETECT_MAP = {
    "油液污染": "污染度检测",
    "阀芯卡滞": "响应曲线检测",
    "阀芯磨损": "响应曲线检测",
    "喷嘴堵塞": "压差检测",
    "喷嘴污染": "流量检测",
    "气隙不对称": "气隙检测",
    "力矩马达异常": "线圈电阻检测",
    "磁路不平衡": "零位检测",
    "力矩马达磁路不平衡": "零位检测",
    "零位漂移": "零位检测",
    "响应迟缓": "响应曲线检测",
    "压力波动": "压力检测",
    "流量控制异常": "流量检测",
    "内泄漏": "泄漏检测",
    "密封失效": "泄漏检测",
    "密封组件磨损": "泄漏检测",
    "线圈发热异常": "线圈电阻检测",
    "电流异常": "电流检测",
    "电磁力矩波动": "电流检测",
    "滞环增大": "响应曲线检测",
    "输出偏差": "响应曲线检测",
    "输出不稳定": "响应曲线检测",
    "压差异常": "压差检测",
    "阀芯偏移异常": "压力检测",
    "流量输出异常": "流量检测",
    "衔铁偏转异常": "线圈电阻检测",
}

FAULT_ACTION_MAP = {
    "油液污染": ["更换液压油", "更换滤芯", "检查污染度"],
    "阀芯卡滞": ["清洗阀芯", "更换液压油", "更换滤芯"],
    "阀芯磨损": ["清洗阀芯"],
    "喷嘴堵塞": ["清洗喷嘴挡板", "更换液压油"],
    "喷嘴污染": ["清洗喷嘴挡板"],
    "气隙不对称": ["检查气隙垫片", "调整气隙对称"],
    "气隙垫片厚度不一致": ["检查气隙垫片", "重新标定"],
    "力矩马达异常": ["检查力矩马达", "检查线圈电阻", "检查衔铁组件", "重新标定"],
    "力矩马达磁路不平衡": ["检查力矩马达", "重新标定"],
    "零位漂移": ["调整零位", "重新标定"],
    "响应迟缓": ["复测响应曲线"],
    "压力波动": ["复测压力曲线"],
    "流量控制异常": ["复测流量响应"],
    "内泄漏": ["更换密封组件"],
    "密封失效": ["更换密封组件"],
    "密封组件磨损": ["更换密封组件"],
    "线圈发热异常": ["检查线圈电阻", "检查力矩马达", "检查绝缘电阻"],
    "电流异常": ["检查线圈电阻", "检查绝缘电阻"],
    "电磁力矩波动": ["检查力矩马达"],
    "输出偏差": ["重新标定"],
    "输出不稳定": ["检查力矩马达"],
    "输出不对称": ["调整零位", "重新标定"],
    "衔铁偏移": ["检查衔铁组件"],
    "衔铁偏转异常": ["检查衔铁组件", "检查力矩马达"],
    "反馈异常": ["检查反馈杆"],
    "滞环增大": ["复测响应曲线"],
    "阀芯偏移异常": ["清洗阀芯"],
    "流量输出异常": ["复测流量响应"],
    "伺服阀输出偏差": ["调整零位", "重新标定"],
}

# 复测映射: 维修动作 -> 复测检测
ACTION_RETEST_MAP = {
    "清洗阀芯": "维修后复测",
    "清洗喷嘴挡板": "维修后复测",
    "更换液压油": "污染度检测",
    "更换密封组件": "维修后复测",
    "调整零位": "维修后复测",
    "重新标定": "维修后复测",
    "检查力矩马达": "维修后复测",
    "检查线圈电阻": "维修后复测",
}


class EventExtractService:
    """液压伺服阀故障维修三元组抽取器"""

    def extract_from_filtered(self, filtered_result):
        paragraphs = filtered_result.get("过滤后段落", [])
        all_triples = []
        seq = 0
        for para in paragraphs:
            text = para.get("原始文本", "")
            if not text or len(text) < 10:
                continue
            source_id = para.get("source_id", "")
            source_type = para.get("来源类型", "公开资料")
            source_title = para.get("标题", "")
            source_file = para.get("文件路径", "")
            para_id = para.get("paragraph_id", 0)
            triples = self._extract_all(text, source_id, source_type, source_title, source_file, para_id, seq)
            all_triples.extend(triples)
            seq += len(triples)
        # 去重
        seen = set()
        deduped = []
        for t in all_triples:
            key = f"{t['subject']}|{t['predicate']}|{t['object']}|{t['source_id']}|{t['paragraph_id']}"
            if key not in seen:
                seen.add(key)
                t["triple_id"] = f"TRI-{len(deduped)+1:06d}"
                deduped.append(t)
        type_stats = {}
        for t in deduped:
            rt = t.get("relation_type", "未知")
            type_stats[rt] = type_stats.get(rt, 0) + 1
        return {"状态": "成功", "三元组总数": len(deduped), "三元组列表": deduped, "类型统计": type_stats}

    def _extract_all(self, text, sid, stype, stitle, sfile, pid, start_seq):
        triples = []
        seq = start_seq
        # 分句
        sentences = re.split(r'[。！？\n；;]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 4]

        for si, sent in enumerate(sentences):
            n = len(triples)
            # 模式A: 包含
            triples.extend(self._pat_include(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))
            # 模式B/C: 导致/链式因果 + 表现为
            triples.extend(self._pat_causal_manifest(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))
            # 模式E: 检测确认
            triples.extend(self._pat_detect(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))
            # 模式F: 维修处理
            triples.extend(self._pat_repair(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))
            # 模式G: 复测验证
            triples.extend(self._pat_retest(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))
            # 模式H: 发生于
            triples.extend(self._pat_occur(sent, sid, stype, stitle, sfile, pid, si, seq + len(triples)))

        # 段落级: 共现检测/维修
        triples.extend(self._para_detect(text, sid, stype, stitle, sfile, pid, seq + len(triples)))
        triples.extend(self._para_repair(text, sid, stype, stitle, sfile, pid, seq + len(triples)))

        return triples

    # ── 模式A: 包含 ──
    def _pat_include(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        trigs = ["包括", "包含", "主要由", "组成", "由……组成", "构成"]
        has = any(t in sent for t in trigs)
        comps = self._matches(sent, COMPONENTS)
        if has and len(comps) >= 2:
            # 找第一个作为subject(最大部件)，其余作为object
            subj = comps[0][0]
            for ct in comps[1:]:
                if ct[0] != subj:
                    triples.append(self._mk(seq + len(triples) + 1, subj, "包含", ct[0], "部件", "部件", "包含",
                                            sid, stype, stitle, sfile, pid, si, sent, subj + "包含" + ct[0],
                                            [subj, ct[0]], "规则抽取"))
        return triples

    # ── 模式B/C: 因果 + 表现 (链式) ──
    def _pat_causal_manifest(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        cause_words = ["导致", "引起", "造成", "使得", "诱发", "会使", "进而", "从而", "致使",
                       "进一步导致", "会导致", "可引起", "引发", "最终导致", "直接导致"]
        manifest_words = ["表现为", "表现出", "症状为", "特征为", "出现", "呈现"]

        all_terms = self._matches(sent, FAULT_MODES) + self._matches(sent, ABNORMAL_STATES)

        for cw in cause_words:
            if cw not in sent:
                continue
            idx = sent.find(cw)
            before, after = sent[:idx].strip(), sent[idx + len(cw):].strip()
            bt = [t for t in all_terms if t[0] in before]
            at = [t for t in all_terms if t[0] in after]
            for b in bt:
                for a in at:
                    if b[0] != a[0]:
                        st = "故障模式" if b[0] in FAULT_MODES else "异常状态"
                        ot = "故障模式" if a[0] in FAULT_MODES else "异常状态"
                        triples.append(self._mk(seq + len(triples) + 1, b[0], "导致", a[0], st, ot, "导致",
                                                sid, stype, stitle, sfile, pid, si, sent, b[0] + cw + a[0],
                                                [b[0], a[0], cw], "规则抽取"))

        for mw in manifest_words:
            if mw not in sent:
                continue
            idx = sent.find(mw)
            before, after = sent[:idx].strip(), sent[idx + len(mw):].strip()
            bt = self._matches(before, FAULT_MODES) + self._matches(before, ABNORMAL_STATES)
            at = self._matches(after, ABNORMAL_STATES) + self._matches(after, FAULT_MODES)
            for b in bt:
                for a in at:
                    if b[0] != a[0]:
                        st = "故障模式" if b[0] in FAULT_MODES else "异常状态"
                        ot = "异常状态" if a[0] in ABNORMAL_STATES else "故障模式"
                        triples.append(self._mk(seq + len(triples) + 1, b[0], "表现为", a[0], st, ot, "表现为",
                                                sid, stype, stitle, sfile, pid, si, sent, b[0] + mw + a[0],
                                                [b[0], a[0], mw], "规则抽取"))
        return triples

    # ── 模式E: 检测确认 ──
    def _pat_detect(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        faults = self._matches(sent, FAULT_MODES)
        states = self._matches(sent, ABNORMAL_STATES)
        detects = self._matches(sent, DETECTIONS)
        all_subj = faults + states
        for dt in detects:
            for st in all_subj:
                if dt[0] != st[0]:
                    triples.append(self._mk(seq + len(triples) + 1, st[0], "由检测确认", dt[0],
                                            "故障模式" if st[0] in FAULT_MODES else "异常状态",
                                            "检测方式", "由检测确认",
                                            sid, stype, stitle, sfile, pid, si, sent, st[0] + "——" + dt[0],
                                            [st[0], dt[0]], "词典匹配", conf=0.72))
        return triples

    # ── 模式F: 维修处理 ──
    def _pat_repair(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        faults = self._matches(sent, FAULT_MODES)
        states = self._matches(sent, ABNORMAL_STATES)
        actions = self._matches(sent, ACTIONS)
        all_subj = faults + states
        for act in actions:
            for st in all_subj:
                if act[0] != st[0]:
                    triples.append(self._mk(seq + len(triples) + 1, st[0], "由维修处理", act[0],
                                            "故障模式" if st[0] in FAULT_MODES else "异常状态",
                                            "维修动作", "由维修处理",
                                            sid, stype, stitle, sfile, pid, si, sent, st[0] + "——" + act[0],
                                            [st[0], act[0]], "词典匹配", conf=0.72))
        return triples

    # ── 模式G: 复测验证 ──
    def _pat_retest(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        actions = self._matches(sent, ACTIONS)
        detects = self._matches(sent, DETECTIONS)
        has_retest = any(w in sent for w in ["复测", "复核", "重新测试"])
        if has_retest:
            for act in actions:
                for dt in detects:
                    if ("复测" in dt[0] or "复测" in act[0]) and act[0] != dt[0]:
                        triples.append(self._mk(seq + len(triples) + 1, act[0], "复测验证", dt[0],
                                                "维修动作", "检测方式", "复测验证",
                                                sid, stype, stitle, sfile, pid, si, sent, act[0] + "复测" + dt[0],
                                                [act[0], dt[0]], "规则抽取", conf=0.70))
        return triples

    # ── 模式H: 发生于 ──
    def _pat_occur(self, sent, sid, stype, stitle, sfile, pid, si, seq):
        triples = []
        comps = [c[0] for c in self._matches(sent, COMPONENTS)]
        faults = [f[0] for f in self._matches(sent, FAULT_MODES)]
        for comp in comps:
            for fault in PART_FAULT_MAP.get(comp, []):
                if fault in faults:
                    triples.append(self._mk(seq + len(triples) + 1, comp, "发生于", fault,
                                            "部件", "故障模式", "发生于",
                                            sid, stype, stitle, sfile, pid, si, sent, comp + "→" + fault,
                                            [comp, fault], "词典匹配", conf=0.65))
                    break
        return triples

    # ── 段落级: 检测确认共现 ──
    def _para_detect(self, text, sid, stype, stitle, sfile, pid, seq):
        triples = []
        all_terms = [t[0] for t in self._matches(text, FAULT_MODES) + self._matches(text, ABNORMAL_STATES)]
        for fault in set(all_terms):
            rec = FAULT_DETECT_MAP.get(fault, "")
            if rec and rec in text:
                triples.append(self._mk(seq + len(triples) + 1, fault, "由检测确认", rec,
                                        "故障模式" if fault in FAULT_MODES else "异常状态",
                                        "检测方式", "由检测确认",
                                        sid, stype, stitle, sfile, pid, 0, text[:200], fault + "——" + rec,
                                        [fault, rec], "词典匹配", conf=0.60))
        return triples

    # ── 段落级: 维修处理共现 ──
    def _para_repair(self, text, sid, stype, stitle, sfile, pid, seq):
        triples = []
        all_terms = [t[0] for t in self._matches(text, FAULT_MODES) + self._matches(text, ABNORMAL_STATES)]
        for fault in set(all_terms):
            for action in FAULT_ACTION_MAP.get(fault, []):
                if action in text:
                    triples.append(self._mk(seq + len(triples) + 1, fault, "由维修处理", action,
                                            "故障模式" if fault in FAULT_MODES else "异常状态",
                                            "维修动作", "由维修处理",
                                            sid, stype, stitle, sfile, pid, 0, text[:200], fault + "——" + action,
                                            [fault, action], "词典匹配", conf=0.60))
        return triples

    # ── builder ──
    def _mk(self, seq, subj, pred, obj, st, ot, rt, sid, stype, stitle, sfile, pid, si, ev, es, mt, em, tc="", conf=0.75):
        return {
            "triple_id": f"TRI-{seq:06d}", "subject": subj, "predicate": pred, "object": obj,
            "subject_type": st, "object_type": ot, "relation_type": rt,
            "source_id": sid, "source_type": stype, "source_title": stitle, "source_file": sfile,
            "paragraph_id": pid, "sentence_id": si,
            "evidence_text": ev, "evidence_span": es, "confidence": conf,
            "matched_terms": mt, "template_candidate": tc, "extraction_method": em,
        }

    def _matches(self, text, term_list):
        m = []
        for t in term_list:
            p = text.find(t)
            if p >= 0:
                m.append((t, p))
        return sorted(set(m), key=lambda x: x[1])


event_extractor = EventExtractService()
