"""
事件抽取模块
从过滤后的段落中抽取：
部件、故障模式、异常状态、原因、检测方式、维修动作、事件触发词、时间表达、证据span。
"""
import re
import uuid
from typing import List, Dict, Optional, Set
from datetime import datetime

# ── 中文事件类型定义 ──
EVENT_TYPE_MAP = {
    "故障事件": "故障事件",
    "状态事件": "状态事件",
    "检测事件": "检测事件",
    "维修事件": "维修事件",
    "传播事件": "传播事件",
    "证据事件": "证据事件",
}

# ── 部件词典 ──
COMPONENT_DICT = {
    "液压泵": ["液压泵", "柱塞泵", "齿轮泵", "叶片泵", "变量泵", "定量泵"],
    "液压缸": ["液压缸", "油缸", "活塞缸", "柱塞缸", "动臂液压缸", "铲斗液压缸"],
    "方向阀": ["方向阀", "换向阀", "电磁换向阀", "比例方向阀", "电液换向阀"],
    "溢流阀": ["溢流阀", "安全阀", "先导溢流阀", "电磁溢流阀"],
    "减压阀": ["减压阀", "定值减压阀", "定比减压阀"],
    "过滤器": ["过滤器", "滤芯", "高压过滤器", "回油过滤器", "吸油过滤器", "入口过滤器"],
    "蓄能器": ["蓄能器", "皮囊式蓄能器", "活塞式蓄能器"],
    "冷却器": ["冷却器", "散热器", "风冷冷却器", "水冷冷却器"],
    "密封件": ["密封件", "密封圈", "格莱圈", "O形圈", "U形圈", "油封", "防尘圈"],
    "管路": ["管路", "软管", "钢管", "接头"],
    "泵": ["泵", "液压泵", "主泵", "先导泵"],
    "比例阀": ["比例阀", "比例方向阀", "比例溢流阀"],
    "液压油": ["液压油", "油液", "矿物油", "合成油"],
}

# ── 故障模式词典 ──
FAULT_MODE_DICT = {
    "内泄漏": ["内泄漏", "内部泄漏", "内泄", "泵内泄"],
    "外泄漏": ["外泄漏", "外部泄漏", "外泄", "漏油", "渗漏"],
    "密封失效": ["密封失效", "密封损坏", "密封圈破损", "密封件磨损", "油封老化"],
    "堵塞": ["堵塞", "滤芯堵塞", "过滤器堵塞", "管路堵塞"],
    "卡滞": ["卡滞", "阀芯卡滞", "卡住", "卡死", "滑阀卡滞"],
    "磨损": ["磨损", "磨粒磨损", "摩擦磨损", "柱塞磨损", "配流盘磨损"],
    "气蚀": ["气蚀", "穴蚀", "空化"],
    "弹簧疲劳": ["弹簧疲劳", "弹簧失效", "弹簧断裂"],
    "皮囊破裂": ["皮囊破裂", "皮囊损坏", "皮囊老化"],
    "油液污染": ["油液污染", "液压油污染", "清洁度超标", "颗粒污染"],
    "油温过高": ["油温过高", "过热", "温度升高", "油液过热"],
    "压力不足": ["压力不足", "压力下降", "压力降低", "压力偏低"],
    "噪声异常": ["噪声", "噪音", "高频噪声"],
    "振动异常": ["振动", "震动", "抖动"],
    "爬行": ["爬行", "爬行现象"],
    "冷却失效": ["冷却失效", "冷却不足", "散热不良", "冷却器效率下降"],
}

# ── 异常状态词典 ──
STATE_DICT = {
    "压力下降": ["压力下降", "压力不足", "压力降低", "系统压力偏低"],
    "压力波动": ["压力波动", "压力脉动", "压力振荡", "压力不稳"],
    "流量损失": ["流量损失", "流量不足", "流量下降", "流量降低"],
    "油温升高": ["油温升高", "油液温度上升", "油温上升", "温度异常"],
    "黏度下降": ["黏度下降", "黏度降低", "油液变稀"],
    "动作缓慢": ["动作缓慢", "速度下降", "动作迟滞", "无力"],
    "噪声增大": ["噪声增大", "噪声升高", "异响"],
    "振动增大": ["振动加剧", "振动增大"],
    "效率下降": ["效率下降", "容积效率降低", "工作效率降低"],
    "泄漏增大": ["泄漏增大", "泄漏加剧"],
    "容积效率下降": ["容积效率下降", "容积效率低"],
}

# ── 检测方式词典 ──
INSPECTION_DICT = {
    "压力检测": ["压力检测", "测量压力", "压力表", "压力传感器"],
    "流量检测": ["流量检测", "测量流量", "流量计"],
    "温度检测": ["温度检测", "测温", "红外测温", "温度传感器"],
    "振动检测": ["振动检测", "振动分析", "振动信号", "加速度传感器"],
    "油液分析": ["油液分析", "油样检测", "光谱分析", "铁谱分析", "颗粒计数"],
    "噪声检测": ["噪声检测", "噪声测量", "声级计"],
    "拆检": ["拆检", "拆解检查", "拆卸检查", "解体检查"],
    "保压试验": ["保压试验", "保压测试", "打压试验"],
    "内泄漏检测": ["内泄漏检测", "泄漏量测量", "沉降量测量"],
    "容积效率检测": ["容积效率检测", "容积效率测试"],
    "清洁度检测": ["清洁度检测", "污染度检测", "NAS"],
    "目视检查": ["目视检查", "外观检查", "目测"],
}

# ── 维修动作词典 ──
MAINTENANCE_DICT = {
    "更换密封件": ["更换密封件", "更换密封圈", "更换油封", "更换格莱圈"],
    "更换滤芯": ["更换滤芯", "更换过滤器", "更换过滤芯"],
    "更换液压油": ["更换液压油", "换油", "系统换油"],
    "清洗": ["清洗", "清洗阀芯", "清洗滤芯", "清洗管路", "超声波清洗"],
    "更换弹簧": ["更换弹簧"],
    "更换皮囊": ["更换皮囊", "更换蓄能器皮囊"],
    "更换泵组件": ["更换泵", "更换泵芯", "更换柱塞泵"],
    "研磨": ["研磨", "研磨修复", "珩磨"],
    "调整压力": ["调整压力", "重新标定压力", "设定压力"],
    "紧固": ["紧固", "拧紧"],
    "补油": ["补充液压油", "补油"],
    "冲洗系统": ["冲洗系统", "循环冲洗"],
}

# ── 时间表达式 ──
TIME_PATTERNS = [
    r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?',
    r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',
    r'\d{4}年\d{1,2}月',
    r'\d{4}-\d{2}-\d{2}',
    r'\d{2}:\d{2}(:\d{2})?',
    r'\d+小时',
    r'\d+天',
    r'\d+个月',
    r'\d+年',
]


def extract_time_expressions(text: str) -> List[str]:
    """从文本中提取时间表达式"""
    times = []
    for pat in TIME_PATTERNS:
        matches = re.findall(pat, text)
        times.extend(matches)
    return list(set(times))  # 去重


def extract_component(text: str) -> Optional[str]:
    """从文本中提取部件名称"""
    for comp_cn, patterns in COMPONENT_DICT.items():
        for pat in patterns:
            if pat in text:
                return comp_cn
    return None


def extract_fault_mode(text: str) -> Optional[str]:
    """从文本中提取故障模式"""
    for fm_cn, patterns in FAULT_MODE_DICT.items():
        for pat in patterns:
            if pat in text:
                return fm_cn
    return None


def extract_state(text: str) -> Optional[str]:
    """从文本中提取异常状态"""
    for state_cn, patterns in STATE_DICT.items():
        for pat in patterns:
            if pat in text:
                return state_cn
    return None


def extract_inspection(text: str) -> Optional[str]:
    """从文本中提取检测方式"""
    for insp_cn, patterns in INSPECTION_DICT.items():
        for pat in patterns:
            if pat in text:
                return insp_cn
    return None


def extract_maintenance_action(text: str) -> Optional[str]:
    """从文本中提取维修动作"""
    for maint_cn, patterns in MAINTENANCE_DICT.items():
        for pat in patterns:
            if pat in text:
                return maint_cn
    return None


def extract_cause(text: str) -> Optional[str]:
    """从文本中提取原因（含"因为"、"由于"、"导致"、"引起"等触发词的分句）"""
    cause_patterns = [
        r'(?:因为|由于|因为|原因[是为]|根[本源]原因[是为])[，:：\s]*(.+?)(?:[。；;]|$)',
        r'(.+?)(?:导致|引起|引发|造成|致使)(.+?)(?:[。；;]|$)',
    ]
    for pat in cause_patterns:
        match = re.search(pat, text)
        if match:
            return match.group(0)[:100]
    return None


def classify_event_type(text: str) -> str:
    """根据文本内容判断事件类型"""
    # 检查故障模式
    for patterns in FAULT_MODE_DICT.values():
        for pat in patterns:
            if pat in text:
                return "故障事件"

    # 检查维修动作
    for patterns in MAINTENANCE_DICT.values():
        for pat in patterns:
            if pat in text:
                return "维修事件"

    # 检查检测方式
    for patterns in INSPECTION_DICT.values():
        for pat in patterns:
            if pat in text:
                return "检测事件"

    # 检查异常状态
    for patterns in STATE_DICT.values():
        for pat in patterns:
            if pat in text:
                return "状态事件"

    return "状态事件"  # 默认


def extract_events_from_paragraphs(
    paragraphs: List[Dict],
    source_id: str
) -> List[Dict]:
    """
    从段落列表中抽取事件。
    每条段落可能产生多个事件。
    """
    events = []
    event_counter = 0

    for para in paragraphs:
        text = para.get("text", "")
        sentences = para.get("sentences", [text])

        for si, sentence in enumerate(sentences):
            if len(sentence) < 10:
                continue

            event_type = classify_event_type(sentence)
            component = extract_component(sentence)
            fault_mode = extract_fault_mode(sentence)
            state = extract_state(sentence)
            inspection = extract_inspection(sentence)
            action = extract_maintenance_action(sentence)
            cause = extract_cause(sentence)
            time_expressions = extract_time_expressions(sentence)

            # 如果句子中没有任何可抽取的内容，跳过
            if not any([component, fault_mode, state, inspection, action]):
                continue

            event_counter += 1
            event = {
                "event_id": f"{source_id}_EVT{event_counter:03d}",
                "event_type": event_type,
                "trigger": sentence[:120],
                "component": component,
                "fault_mode": fault_mode,
                "state": state,
                "cause": cause,
                "inspection": inspection,
                "action": action,
                "time_expressions": time_expressions,
                "valid_time": time_expressions[0] if time_expressions else "",
                "observed_time": datetime.now().isoformat(),
                "confidence": 0.75,
                "source_id": source_id,
                "paragraph_no": para.get("paragraph_no", 0),
                "sentence_id": f"{source_id}_P{para.get('paragraph_no', 0):03d}_S{si+1:02d}",
                "evidence_span": sentence,
                "matched_keywords": para.get("matched_keywords", []),
            }
            events.append(event)

    return events


def get_extraction_stats(paragraphs: List[Dict], events: List[Dict]) -> Dict:
    """获取事件抽取统计"""
    event_type_dist = {}
    component_dist = {}
    fault_mode_dist = {}
    state_dist = {}

    for ev in events:
        et = ev["event_type"]
        event_type_dist[et] = event_type_dist.get(et, 0) + 1

        comp = ev.get("component")
        if comp:
            component_dist[comp] = component_dist.get(comp, 0) + 1

        fm = ev.get("fault_mode")
        if fm:
            fault_mode_dist[fm] = fault_mode_dist.get(fm, 0) + 1

        st = ev.get("state")
        if st:
            state_dist[st] = state_dist.get(st, 0) + 1

    return {
        "原始段落数量": len(paragraphs),
        "抽取事件数量": len(events),
        "平均每段事件数": round(len(events) / max(len(paragraphs), 1), 2),
        "事件类型分布": event_type_dist,
        "部件分布": component_dist,
        "故障模式分布": fault_mode_dist,
        "异常状态分布": state_dist,
    }
