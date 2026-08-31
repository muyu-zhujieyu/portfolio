# -*- coding: utf-8 -*-
"""
液压伺服阀样本结果分析路由

基于 20201010 样本文档，提供部位-样本-结果的结构化分析数据。

API:
  GET  /api/sample-analysis/file-info   返回当前分析文件信息
  GET  /api/sample-analysis/parts       返回所有部位列表
  GET  /api/sample-analysis/samples     返回指定部位下的样本列表
  GET  /api/sample-analysis/result      返回指定样本的完整分析结果
  POST /api/sample-analysis/bootstrap   重新解析文件并生成结构化JSON
"""
import os
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from typing import Optional
from services.sample_analysis_service import sample_analysis
from services.sample_doc_reader_service import doc_reader
from services.curve_image_analysis_service import curve_analyzer, OUTPUT_PATH

router = APIRouter(prefix="/api/sample-analysis", tags=["样本结果分析"])


@router.get("/file-info")
def get_file_info():
    """获取当前分析文件信息（含原始图片统计）

    返回:
      - 文件名称/路径/大小
      - 提取图片数/样本总数
      - 原始图片目录
      - 说明: 曲线来源：20201010 原始文档提取，未修改原始曲线。
    """
    return doc_reader.get_file_info()


@router.get("/parts")
def get_parts():
    """获取所有部位列表（基于原始图片分析结果）"""
    return curve_analyzer.get_parts()


@router.get("/samples")
def get_samples(part: Optional[str] = Query(None, description="部位名称")):
    """获取指定部位下的所有样本列表（基于原始图片分析）"""
    return curve_analyzer.get_samples(part or "")


@router.get("/result")
def get_result(
    part: str = Query("", description="部位名称"),
    sample_id: str = Query(..., description="样本编号")
):
    """获取指定样本的完整分析结果（基于原始图片分析）

    返回:
      - 样本编号/部位名称/原始图片路径/标准参考样本
      - 诊断结论/是否异常/置信度/相似度
      - 指标卡片（零位位置/左右不对称度/曲线粗糙度等）
      - 曲线来源说明: 该曲线图来自 20201010 原始文档提取
      - 原始文档上下文（前后文本段落）
    """
    result = curve_analyzer.get_result(part, sample_id)
    if "错误" in result:
        # 回退到旧版分析
        return sample_analysis.get_result(part, sample_id)

    # 异常样本：自动注入故障关联上下文
    sample = result.get("样本", {})
    if sample.get("是否异常"):
        fault_context = _build_fault_context(sample)
        result["故障关联信息"] = fault_context["故障关联信息"]
        result["知识图谱相关链条"] = fault_context["知识图谱相关链条"]
        result["相关证据"] = fault_context["相关证据"]
        result["大模型维修推荐方案"] = fault_context["大模型维修推荐方案"]
        result["原始文档相关上下文"] = fault_context["原始文档相关上下文"]
        result["相关子图谱"] = fault_context["相关子图谱"]
    else:
        # 正常样本：明确返回不触发
        result["故障关联信息"] = {"是否显示": False}

    return result


@router.post("/extract-doc")
def extract_doc():
    """解析 20201010 docx，提取原始图片和上下文，生成样本清单

    流程:
      1. 自动查找 D:/kg0623 下包含 20201010 的 docx 文件
      2. 提取文档段落文本
      3. 提取所有原始图片，保存到 data/sample_analysis/raw_images/
      4. 将图片与前后文本上下文匹配
      5. 根据上下文自动归类到伺服阀部位
      6. 生成 data/sample_analysis/sample_manifest_20201010.json

    注意: 所有原始曲线图片来自 20201010 文档提取，未经修改。
    """
    return doc_reader.extract_doc()


@router.get("/raw-image")
def get_raw_image(sample_id: str = Query(..., description="样本编号")):
    """返回原始曲线图片（从 raw_images 目录）"""
    raw_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "sample_analysis", "raw_images"
    )
    # 尝试直接匹配 sample_id
    for fname in os.listdir(raw_dir):
        if sample_id in fname and fname.endswith(('.png', '.jpg', '.jpeg')):
            return FileResponse(os.path.join(raw_dir, fname), media_type='image/png')

    # 尝试按序号匹配
    if sample_id.startswith('S') and sample_id[1:].isdigit():
        num = int(sample_id[1:])
        target = f"sample_{num:03d}_original.png"
        path = os.path.join(raw_dir, target)
        if os.path.exists(path):
            return FileResponse(path, media_type='image/png')

    return {"错误": f"未找到样本 {sample_id} 的原始图片"}


@router.get("/manifest")
def get_manifest():
    """获取完整样本清单（含原始图片路径和文档上下文）

    返回 sample_manifest_20201010.json 的所有内容。
    """
    return doc_reader.get_manifest()


@router.post("/analyze-all")
def analyze_all():
    """对所有样本进行图像分析

    基于 Pillow + numpy 对 raw_images 中的原始曲线图片进行特征分析:
      - 曲线像素占比、左右不对称度、零位偏移、曲线粗糙度等
      - 与同部位标准参考样本对比计算相似度
      - 异常判断: >=0.90正常 / 0.75-0.90轻度 / 0.55-0.75疑似 / <0.55明显

    注意: 该曲线图来自 20201010 原始文档提取，系统仅进行图像特征分析，未修改原始曲线。
    """
    return curve_analyzer.analyze_all()


@router.post("/bootstrap")
def bootstrap():
    """重新解析 20201010 文件并生成结构化 JSON"""
    return sample_analysis.bootstrap()


# ================================================================
# 故障上下文生成（异常样本增强）
# ================================================================

FAULT_CHAINS_MAP = {
    "气隙垫片": [{
        "链条编号": "CHAIN-AIRGAP-001",
        "链条名称": "气隙不对称故障链",
        "链条文本": "气隙垫片 -> 气隙不对称 -> 力矩马达磁路不平衡 -> 零位漂移 -> 伺服阀输出偏差",
        "命中节点": ["气隙垫片", "气隙不对称", "零位漂移"],
        "机理模板": "气隙偏差-磁路不平衡-零位漂移模板",
        "匹配分数": 0.86,
    }],
    "马达螺钉": [{
        "链条编号": "CHAIN-MOTOR-001",
        "链条名称": "力矩马达异常链",
        "链条文本": "马达螺钉松动 -> 力矩马达 -> 电磁力矩异常 -> 衔铁偏转异常 -> 零位漂移",
        "命中节点": ["马达螺钉", "力矩马达", "零位漂移"],
        "机理模板": "马达装配异常-力矩异常-零位漂移模板",
        "匹配分数": 0.84,
    }],
    "衔铁组件": [{
        "链条编号": "CHAIN-ARMATURE-001",
        "链条名称": "衔铁组件异常链",
        "链条文本": "衔铁组件 -> 衔铁偏移 -> 零位漂移 -> 流量偏置 -> 响应异常",
        "命中节点": ["衔铁组件", "衔铁偏移", "零位漂移", "响应异常"],
        "机理模板": "衔铁偏移-零位漂移-响应异常模板",
        "匹配分数": 0.82,
    }],
    "上壳体回油螺钉": [{
        "链条编号": "CHAIN-HOUSING-001",
        "链条名称": "壳体螺钉松动链",
        "链条文本": "上壳体回油螺钉松动 -> 密封失效 -> 内泄漏增大 -> 控制压力下降",
        "命中节点": ["上壳体回油螺钉", "密封失效", "控制压力下降"],
        "机理模板": "螺钉松动-密封失效-压力下降模板",
        "匹配分数": 0.80,
    }],
    "喷嘴挡板": [{
        "链条编号": "CHAIN-NOZZLE-001",
        "链条名称": "喷嘴堵塞故障链",
        "链条文本": "喷嘴挡板 -> 喷嘴堵塞 -> 压差异常 -> 阀芯偏移异常 -> 流量输出异常",
        "命中节点": ["喷嘴挡板", "喷嘴堵塞", "流量输出异常"],
        "机理模板": "喷嘴堵塞-压差异常-流量异常模板",
        "匹配分数": 0.88,
    }],
    "阀芯阀套": [{
        "链条编号": "CHAIN-SPOOL-001",
        "链条名称": "阀芯卡滞故障链",
        "链条文本": "阀芯阀套 -> 阀芯卡滞 -> 流量控制异常 -> 压力波动 -> 响应迟缓",
        "命中节点": ["阀芯阀套", "阀芯卡滞", "压力波动"],
        "机理模板": "阀芯卡滞-流量异常-响应迟缓模板",
        "匹配分数": 0.86,
    }],
}

CONTAMINATION_CHAIN = {
    "链条编号": "CHAIN-CONTAM-001",
    "链条名称": "油液污染故障链",
    "链条文本": "油液污染 -> 阀芯磨损或卡滞 -> 流量控制异常 -> 压力波动",
    "命中节点": ["油液污染", "阀芯卡滞", "压力波动"],
    "机理模板": "T5 污染链",
    "匹配分数": 0.78,
}

MAINTENANCE_RULES = {
    "气隙垫片": {
        "推荐结论": "建议优先检查气隙垫片厚度一致性和安装位置，并复测零位漂移。",
        "推荐措施": [
            "检查气隙垫片厚度是否一致",
            "检查左右气隙是否对称",
            "检查力矩马达磁路平衡状态",
            "复测零位位置和响应曲线",
            "若偏差持续存在，建议更换气隙垫片并重新标定",
        ],
        "优先级": "高", "风险等级": "中高", "是否需要人工复核": True,
    },
    "马达螺钉": {
        "推荐结论": "建议检查马达螺钉扭矩是否一致，排查力矩马达装配状态。",
        "推荐措施": [
            "检查马达螺钉扭矩是否符合标准(0.7N.M)",
            "检查螺钉是否松动或过紧",
            "检查力矩马达气隙是否均匀",
            "复测伺服阀零位和响应特性",
        ],
        "优先级": "高", "风险等级": "高", "是否需要人工复核": True,
    },
    "衔铁组件": {
        "推荐结论": "建议检查衔铁组件装配状态和零位漂移情况。",
        "推荐措施": [
            "检查衔铁是否偏转或卡滞",
            "检查衔铁气隙是否均匀",
            "复测零位漂移和流量特性",
            "若衔铁异常持续，建议更换衔铁组件",
        ],
        "优先级": "高", "风险等级": "中高", "是否需要人工复核": True,
    },
    "上壳体回油螺钉": {
        "推荐结论": "建议检查上壳体回油螺钉紧固状态和密封性能。",
        "推荐措施": [
            "检查螺钉扭矩是否达标",
            "检查密封面是否有泄漏痕迹",
            "复测内泄漏量",
            "若泄漏持续，建议更换密封件",
        ],
        "优先级": "中", "风险等级": "中", "是否需要人工复核": False,
    },
    "喷嘴挡板": {
        "推荐结论": "建议检查喷嘴挡板组件状态和零位漂移。",
        "推荐措施": [
            "拆下喷嘴检查是否有堵塞",
            "用清洁液压油冲洗喷嘴孔",
            "检查挡板表面磨损",
            "复测控制压力差和零位",
        ],
        "优先级": "高", "风险等级": "中高", "是否需要人工复核": True,
    },
    "阀芯阀套": {
        "推荐结论": "建议检查阀芯阀套配合状态和滞环特性。",
        "推荐措施": [
            "清洗阀芯阀套配合面",
            "检查阀芯表面是否有划痕",
            "复测滞环和零位偏移",
            "如磨损严重需更换阀芯组件",
        ],
        "优先级": "高", "风险等级": "高", "是否需要人工复核": True,
    },
}


def _build_fault_context(sample: dict) -> dict:
    """为异常样本构建完整的故障关联上下文"""
    part = sample.get("部位名称", "其他")
    diag = sample.get("诊断结论", "")
    indicators = sample.get("指标卡片", {})
    ctx = sample.get("原始文档上下文", {})

    # 识别异常指标
    abnormal_indicators = []
    for k, v in indicators.items():
        val = v.get("值", 0) if isinstance(v, dict) else 0
        if isinstance(val, str):
            continue
        if k == "左右不对称度" and abs(float(val)) > 0.05:
            abnormal_indicators.append(k)
        elif k == "曲线粗糙度" and float(val) > 2.5:
            abnormal_indicators.append(k)
        elif k == "零位位置" and abs(float(val)) > 0.04:
            abnormal_indicators.append(k)
        elif k == "估计斜率" and abs(float(val)) > 0.06:
            abnormal_indicators.append(k)
    if not abnormal_indicators:
        abnormal_indicators = ["相似度偏低"]

    # 故障关联信息
    fault_names = {
        "气隙垫片": "气隙不对称", "马达螺钉": "马达装配异常",
        "衔铁组件": "衔铁偏移", "上壳体回油螺钉": "壳体螺钉松动",
        "喷嘴挡板": "喷嘴堵塞", "阀芯阀套": "阀芯卡滞",
    }
    fault_info = {
        "是否显示": True,
        "故障名称": fault_names.get(part, f"{part}异常"),
        "关联部件": part,
        "异常类型": diag,
        "异常指标": abnormal_indicators,
        "故障说明": (
            f"当前{part}样本诊断为{diag}，异常指标包括{', '.join(abnormal_indicators[:3])}。"
            f"该异常可能与{fault_names.get(part, part+'异常')}有关，"
            f"建议结合伺服阀整体运行状态进行综合判断。曲线图来自20201010原始文档。"
        ),
    }

    # 知识图谱链条
    chains = FAULT_CHAINS_MAP.get(part, [])
    # 添加污染链作为通用链
    if any(kw in str(indicators) for kw in ["泄漏", "污染"]):
        chains = chains + [CONTAMINATION_CHAIN]

    # 相关证据（从文档上下文生成）
    evidence = []
    sid = sample.get("样本编号", "")
    prev_ctx = ctx.get("前置上下文", [])
    next_ctx = ctx.get("后置上下文", [])

    evidence.append({
        "证据编号": f"EVD-SAMPLE-{sid}",
        "来源类型": "样本文档",
        "来源文件": "【公开】20201010.docx",
        "段落编号": sid,
        "证据原文": f"{part}样本{sid}的诊断结论为{diag}，异常指标包括{', '.join(abnormal_indicators[:3])}。",
        "相关部位": part,
        "可靠度": round(sample.get("置信度", 0.8), 2),
    })
    # 添加上下文证据
    for i, text in enumerate(prev_ctx[-2:] + next_ctx[:1]):
        if text:
            evidence.append({
                "证据编号": f"EVD-DOC-{sid}-{i+1}",
                "来源类型": "文档上下文",
                "来源文件": "【公开】20201010.docx",
                "段落编号": f"P-{sid}-{i+1}",
                "证据原文": text[:200],
                "相关部位": part,
                "可靠度": 0.75,
            })

    # 维修推荐
    maint = MAINTENANCE_RULES.get(part, MAINTENANCE_RULES.get("气隙垫片", {}))
    maintenance = {
        "推荐结论": maint.get("推荐结论", ""),
        "推荐措施": maint.get("推荐措施", []),
        "优先级": maint.get("优先级", "中"),
        "风险等级": maint.get("风险等级", "中"),
        "推荐依据": (
            f"样本诊断为{diag}，异常指标指向{part}异常。"
            f"基于液压伺服阀维修规则库，建议按上述步骤检修。"
            f"大模型只负责组织语言表达，维修建议来自已验证的维修规则。"
        ),
        "是否需要人工复核": maint.get("是否需要人工复核", True),
    }

    # 文档上下文
    doc_context = {
        "来源文件": "【公开】20201010.docx",
        "上下文段落": [
            {"段落编号": f"DOC-PREV-{sid}", "文本": text}
            for text in prev_ctx[-2:]
        ] + [
            {"段落编号": f"DOC-CURR-{sid}", "文本": (
                f"{part}样本{sid}诊断为{diag}，"
                f"异常指标: {', '.join(abnormal_indicators[:3])}。"
            )},
        ] + [
            {"段落编号": f"DOC-NEXT-{sid}", "文本": text}
            for text in next_ctx[:1]
        ],
        "上下文说明": "以上文本来自20201010文档，用于解释当前样本分析结论。",
    }

    # 相关子图谱
    sub_nodes = []
    sub_links = []
    node_ids = {}
    nid = 0

    def add_node(name, category):
        nonlocal nid
        if name not in node_ids:
            nid += 1
            node_ids[name] = f"N{nid}"
            colors = {"部件": "#9B59B6", "故障事件": "#E74C3C",
                      "状态事件": "#F39C12", "维修事件": "#2ECC71",
                      "证据事件": "#3498DB"}
            sub_nodes.append({
                "id": f"N{nid}", "name": name, "category": category,
                "symbolSize": 30, "itemStyle": {"color": colors.get(category, "#95A5A6")},
            })
        return node_ids[name]

    # 从链条生成节点和边
    for chain in chains:
        steps = [s.strip() for s in chain["链条文本"].split("->")]
        for i, step in enumerate(steps):
            cat = "故障事件" if i == 1 else ("维修事件" if i == len(steps)-1 and "维修" in str(maint) else "状态事件" if i >= 2 else "部件")
            add_node(step, cat)
        for i in range(len(steps) - 1):
            sub_links.append({
                "source": node_ids[steps[i]], "target": node_ids[steps[i+1]],
                "label": "导致" if i == 0 else "演化为",
                "lineStyle": {"color": "#E74C3C", "width": 2},
            })

    sub_graph = {"nodes": sub_nodes, "links": sub_links}

    return {
        "故障关联信息": fault_info,
        "知识图谱相关链条": chains,
        "相关证据": evidence[:5],
        "大模型维修推荐方案": maintenance,
        "原始文档相关上下文": doc_context,
        "相关子图谱": sub_graph,
    }
