"""
资料导入服务 - 处理用户上传文件的解析、分析和增量融合

可选子功能（非主流程前提）:
  用户上传新增资料（维修报告、现场图片、传感器数据表格）后进行补充分析，
  并可选择将分析结果增量加入已有知识图谱。

支持的文件类型:
  文档: txt, md, pdf, docx
  表格: csv, xlsx
  图片: png, jpg, jpeg

注意:
  主流程不依赖此功能即可完成完整的知识图谱构建与大模型问答。
  此功能是知识增长的加速器，允许用户将新资料增量融合到已有知识图谱中。
"""
import os
import re
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd


class ImportService:
    """资料导入服务 - 文件上传、分析、增量融合"""

    # 文件大小限制
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    # 支持的文件扩展名
    ALLOWED_EXTENSIONS = {
        "document": {".txt", ".md", ".pdf", ".docx"},
        "image": {".png", ".jpg", ".jpeg"},
        "table": {".csv", ".xlsx"},
    }

    def __init__(self):
        self._upload_dir: str = ""

    # ================================================================
    # 文件上传
    # ================================================================

    def get_upload_dir(self) -> str:
        """获取上传文件存储根目录"""
        if not self._upload_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self._upload_dir = os.path.join(base_dir, "uploads")
        return self._upload_dir

    def handle_upload(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """处理文件上传

        Args:
            file_content: 文件字节内容
            filename: 原始文件名

        Returns:
            上传结果字典
        """
        # 1. 验证文件大小
        if len(file_content) > self.MAX_FILE_SIZE:
            return {"状态": "失败", "错误": f"文件大小超过限制（最大 {self.MAX_FILE_SIZE // 1024 // 1024} MB）"}

        # 2. 确定文件类型
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            return {"状态": "失败", "错误": "无法识别文件类型（缺少扩展名）"}

        file_category = self._classify_file(filename, ext)

        # 3. 生成唯一文件名和保存路径
        file_id = f"UPL-{uuid.uuid4().hex[:8]}"
        saved_name = f"{file_id}{ext}"
        sub_dir = self._get_subdir(file_category)
        os.makedirs(sub_dir, exist_ok=True)

        storage_path = os.path.join(sub_dir, saved_name)

        # 4. 保存文件
        with open(storage_path, "wb") as f:
            f.write(file_content)

        # 5. 记录到数据库
        self._save_upload_record(file_id, filename, file_category, len(file_content), storage_path)

        return {
            "状态": "成功",
            "文件编号": file_id,
            "文件名称": filename,
            "文件类型": file_category,
            "原始扩展名": ext,
            "保存路径": storage_path,
            "上传时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "文件大小": len(file_content),
            "文件大小_可读": self._format_size(len(file_content)),
            "解析状态": "待分析",
            "说明": "文件已保存。请调用 POST /api/import/analyze/{file_id} 开始分析。"
                        "注意：资料导入是可选的增量功能，不是知识图谱构建主流程的前提。"
        }

    # ================================================================
    # 文件分析
    # ================================================================

    def analyze_file(self, file_id: str) -> Dict[str, Any]:
        """分析上传的文件（自动识别类型并选择合适的分析器）

        分析流程:
          文档(txt/md/docx/pdf): 解析文本→清洗段落→领域过滤→事件抽取→证据锚定
          表格(csv/xlsx): 读取数据→识别字段→异常趋势检测→状态事件生成
          图片(png/jpg): 模拟OCR→文本描述→事件抽取
        """
        # 获取文件信息
        file_info = self._get_file_info(file_id)
        if not file_info:
            return {"状态": "失败", "错误": f"文件 {file_id} 不存在"}

        file_path = file_info.get("存储路径", "")
        file_type = file_info.get("文件类型", "")
        filename = file_info.get("文件名", "")

        if not os.path.exists(file_path):
            return {"状态": "失败", "错误": f"文件已丢失: {file_path}"}

        # 根据类型选择分析器
        if file_type == "document":
            result = self._analyze_document(file_id, file_path, filename)
        elif file_type == "table":
            result = self._analyze_table(file_id, file_path, filename)
        elif file_type == "image":
            result = self._analyze_image(file_id, file_path, filename)
        else:
            return {"状态": "失败", "错误": f"不支持的文件类型: {file_type}"}

        # 更新解析状态
        self._update_file_status(file_id, "已分析")
        result["文件编号"] = file_id

        # 保存分析结果
        self._save_analysis_result(file_id, file_type, result)

        return result

    def get_analysis_result(self, file_id: str) -> Dict[str, Any]:
        """获取文件的分析结果"""
        from database import fetch_one
        row = fetch_one(
            "SELECT * FROM analysis_results WHERE file_id = ? ORDER BY 分析时间 DESC LIMIT 1",
            (file_id,)
        )
        if not row:
            return {"状态": "失败", "错误": f"文件 {file_id} 尚未分析或结果不存在"}

        row_dict = dict(row)
        result_json = row_dict.get("分析结果JSON", "{}")
        try:
            result = json.loads(result_json) if isinstance(result_json, str) else (result_json or {})
        except:
            result = {}

        # 同时获取文件信息
        file_info = self._get_file_info(file_id)
        return {
            "文件信息": file_info,
            "分析结果": result,
            "分析时间": row_dict.get("分析时间", ""),
            "是否已入图谱": bool(row_dict.get("是否加入图谱", 0)),
        }

    # ================================================================
    # 增量加入图谱
    # ================================================================

    def add_to_graph(self, file_id: str) -> Dict[str, Any]:
        """将文件分析结果增量加入已有知识图谱

        增量加入的内容:
          - 抽取的事件 → events 表
          - 证据 span → evidence 表
          - 事件关系 → event_relations 表
          - 图谱节点 → graph_nodes 表
        """
        # 获取分析结果
        result_data = self.get_analysis_result(file_id)
        if result_data.get("状态") == "失败":
            return result_data

        analysis = result_data.get("分析结果", {})
        events = analysis.get("抽取事件", [])
        evidence_list = analysis.get("证据span", [])

        if not events:
            return {
                "状态": "失败",
                "错误": "该文件分析结果中无事件可加入图谱",
                "说明": "请确保文件分析已完成且包含有效的事件抽取结果"
            }

        # 写入数据库
        from database import get_connection, fetch_one

        conn = get_connection()
        conn.execute("PRAGMA foreign_keys = OFF")

        try:
            event_count = 0
            evd_count = 0

            # 写入事件
            for ev in events:
                event_id = ev.get("事件编号", f"EVT-IMP-{uuid.uuid4().hex[:6]}")
                existing = fetch_one("SELECT id FROM events WHERE event_id = ?", (event_id,))
                if existing:
                    continue
                conn.execute("""
                    INSERT INTO events (event_id, filtered_id, 事件类型, 事件触发词, 事件描述, 论元JSON, 发生时间, 置信度)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_id, "", ev.get("事件类型", ""), ev.get("触发词", ""),
                    ev.get("事件描述", ""), json.dumps(ev.get("论元", {}), ensure_ascii=False),
                    ev.get("有效时间", ""), ev.get("置信度", 0.5)
                ))
                event_count += 1

            # 写入证据
            for evd in evidence_list:
                evd_id = evd.get("证据编号", f"EVD-IMP-{uuid.uuid4().hex[:6]}")
                existing = fetch_one("SELECT id FROM evidence WHERE evidence_id = ?", (evd_id,))
                if existing:
                    continue
                conn.execute("""
                    INSERT INTO evidence (evidence_id, event_id, filtered_id, 来源文件, 原文片段, 起始位置, 结束位置)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    evd_id, evd.get("事件编号", ""), "", file_id,
                    evd.get("证据原文", ""), 0, len(evd.get("证据原文", ""))
                ))
                evd_count += 1

            conn.commit()

            # 标记已入图谱
            from database import execute_sql
            execute_sql(
                "UPDATE analysis_results SET 是否加入图谱 = 1 WHERE file_id = ?",
                (file_id,)
            )

            return {
                "状态": "成功",
                "文件编号": file_id,
                "加入事件数": event_count,
                "加入证据数": evd_count,
                "说明": (
                    f"已将该文件分析结果增量加入知识图谱。"
                    f"注意：此操作为增量更新，不会覆盖已有图谱数据。"
                    f"如需查看完整图谱，请访问 GET /api/kg。"
                )
            }

        finally:
            conn.execute("PRAGMA foreign_keys = ON")

    # ================================================================
    # 文档分析（txt/md/docx/pdf）
    # ================================================================

    def _analyze_document(self, file_id: str, file_path: str,
                           filename: str) -> Dict[str, Any]:
        """分析文本文档"""
        # 解析文本
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".txt", ".md"):
            text = self._read_text(file_path)
        elif ext == ".pdf":
            text = self._read_pdf(file_path)
        elif ext == ".docx":
            text = self._read_docx(file_path)
        else:
            text = self._read_text(file_path)

        if not text:
            return {"状态": "失败", "错误": "无法解析文档内容"}

        # 清洗段落
        from services.text_clean_service import text_cleaner
        clean_result = self._clean_document_text(text, file_id)

        # 领域过滤
        from services.domain_filter_service import domain_filter
        filter_result = self._filter_document(clean_result)

        # 事件抽取
        from services.event_extract_service import event_extractor
        extract_result = event_extractor.extract_from_filtered(filter_result)

        # 证据锚定
        from services.evidence_anchor_service import evidence_anchor
        anchor_result = evidence_anchor.anchor_events(extract_result)

        # 机理模板匹配
        from services.fusion_service import fusion
        events = extract_result.get("事件列表", [])
        fusion_result = fusion.normalize_events(events)

        from services.mechanism_validation_service import mechanism_validator
        validation_result = mechanism_validator.validate_all(
            fusion_result.get("事件列表", [])
        )

        # 计算置信度
        conf = self._calc_doc_confidence(extract_result, validation_result)

        return {
            "状态": "成功",
            "文件类型": "文档",
            "解析文本": text[:2000],
            "清洗段落": clean_result.get("清洗后段落", [])[:10],
            "液压相关段落": filter_result.get("过滤后段落", [])[:10],
            "抽取事件": extract_result.get("事件列表", [])[:20],
            "证据span": anchor_result.get("证据列表", [])[:20],
            "异常指标": [],
            "匹配机理模板": [
                ch.get("模板名称", "") for ch in validation_result.get("校验结果", [])
            ],
            "生成故障链": [
                {"模板编号": ch.get("模板编号",""), "模板名称": ch.get("模板名称",""),
                 "链式模式": ch.get("中文链式模式",""), "状态": ch.get("状态","")}
                for ch in validation_result.get("校验结果", [])[:5]
            ],
            "维修建议": self._get_maintenance_suggestions(extract_result),
            "置信度": conf,
            "风险等级": "中" if conf > 0.5 else "高",
            "说明": "此分析结果来自用户上传的补充资料，可选择性加入知识图谱。"
                    "注意：资料导入是可选增量功能，不是知识图谱构建主流程的前提。"
        }

    def _clean_document_text(self, text: str, source_id: str) -> Dict[str, Any]:
        """清洗文档文本"""
        # 简单的段落拆分
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip() and len(p.strip()) >= 10]
        para_list = []
        for i, para in enumerate(paragraphs, 1):
            para_list.append({
                "source_id": source_id,
                "来源类型": "用户上传资料",
                "标题": f"导入文档段落{i}",
                "段落编号": i,
                "原始文本": para,
                "清洗后文本": para,
                "字符数": len(para)
            })

        from services.domain_filter_service import domain_filter
        filtered = domain_filter.filter_cleaned_paragraphs({
            "清洗后段落": para_list
        })

        return {
            "清洗后段落": para_list,
            "过滤后段落": filtered.get("过滤后段落", []),
        }

    def _filter_document(self, clean_result: Dict[str, Any]) -> Dict[str, Any]:
        """领域过滤"""
        from services.domain_filter_service import domain_filter
        return domain_filter.filter_cleaned_paragraphs(clean_result)

    # ================================================================
    # 表格分析（csv/xlsx）
    # ================================================================

    def _analyze_table(self, file_id: str, file_path: str,
                        filename: str) -> Dict[str, Any]:
        """分析表格数据"""
        try:
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".csv":
                df = pd.read_csv(file_path, encoding="utf-8")
            elif ext == ".xlsx":
                df = pd.read_excel(file_path, engine="openpyxl")
            else:
                return {"状态": "失败", "错误": f"不支持的表格格式: {ext}"}

            columns = list(df.columns)
            row_count = len(df)

            # 识别液压相关字段
            sensor_fields = self._detect_sensor_fields(columns)

            # 检测异常趋势
            anomalies = self._detect_anomalies(df, sensor_fields)

            # 生成状态事件
            events = self._generate_table_events(anomalies, file_id)

            # 生成证据
            evidence_list = self._generate_table_evidence(events, anomalies, file_id)

            # 异常指标文本描述
            anomaly_text = self._describe_anomalies(anomalies, sensor_fields)

            conf = 0.6 if anomalies else 0.3

            return {
                "状态": "成功",
                "文件类型": "表格",
                "表格概况": {
                    "行数": row_count,
                    "列数": len(columns),
                    "列名": columns,
                },
                "传感器字段识别": sensor_fields,
                "解析文本": self._df_to_text(df, sensor_fields),
                "清洗段落": [],
                "液压相关段落": [],
                "抽取事件": events,
                "证据span": evidence_list,
                "异常指标": [
                    {"指标": k, "描述": v}
                    for k, v in (anomalies.get("指标异常", {}) or {}).items()
                ],
                "匹配机理模板": self._match_anomaly_templates(anomalies),
                "生成故障链": self._generate_anomaly_chains(anomalies),
                "维修建议": self._get_table_maintenance(anomalies),
                "置信度": conf,
                "风险等级": "中" if anomalies else "低",
                "说明": (
                    "此分析结果来自用户上传的表格数据。"
                    "系统通过识别压力、流量、油温、振动、噪声等字段，"
                    "检测异常趋势并转换为状态事件。"
                    "注意：资料导入是可选增量功能。"
                )
            }

        except Exception as e:
            return {"状态": "失败", "错误": f"表格分析失败: {str(e)}"}

    def _detect_sensor_fields(self, columns: List[str]) -> Dict[str, List[str]]:
        """检测表格中的液压传感器字段"""
        field_map = {
            "压力": ["压力", "pressure", "MPa", "bar", "泵出口压力", "系统压力"],
            "流量": ["流量", "flow", "L/min", "泵出口流量"],
            "温度": ["温度", "油温", "temperature", "℃", "油箱温度"],
            "振动": ["振动", "vibration", "加速度", "振幅"],
            "噪声": ["噪声", "噪音", "noise", "dB", "分贝"],
            "时间": ["时间", "time", "日期", "date", "时刻"],
        }

        detected = {}
        for col in columns:
            col_lower = str(col).lower()
            for field, keywords in field_map.items():
                for kw in keywords:
                    if kw.lower() in col_lower:
                        if field not in detected:
                            detected[field] = []
                        detected[field].append(str(col))
                        break

        return detected

    def _detect_anomalies(self, df, sensor_fields: Dict[str, List[str]]) -> Dict[str, Any]:
        """检测传感器数据中的异常趋势"""
        anomalies = {"指标异常": {}, "趋势分析": []}

        # 检查压力下降趋势
        if "压力" in sensor_fields:
            for col in sensor_fields["压力"]:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(values) >= 3:
                        # 简单趋势检测: 最后3个值是否呈下降趋势
                        last3 = values.tail(3).tolist()
                        if len(last3) >= 3 and last3[0] > last3[1] > last3[2]:
                            anomalies["指标异常"]["压力下降"] = (
                                f"字段 {col} 检测到持续下降趋势: "
                                f"{last3[0]:.2f} → {last3[1]:.2f} → {last3[2]:.2f}"
                            )
                            anomalies["趋势分析"].append({
                                "趋势类型": "压力下降",
                                "字段": col,
                                "趋势描述": "压力持续降低",
                                "相关状态事件": "压力下降",
                            })

        # 检查流量降低趋势
        if "流量" in sensor_fields:
            for col in sensor_fields["流量"]:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(values) >= 3:
                        last3 = values.tail(3).tolist()
                        if len(last3) >= 3 and last3[0] > last3[1] > last3[2]:
                            anomalies["指标异常"]["流量损失"] = (
                                f"字段 {col} 检测到持续下降趋势: "
                                f"{last3[0]:.2f} → {last3[1]:.2f} → {last3[2]:.2f}"
                            )
                            anomalies["趋势分析"].append({
                                "趋势类型": "流量损失",
                                "字段": col,
                                "趋势描述": "流量持续降低",
                                "相关状态事件": "流量损失",
                            })

        # 检查油温升高趋势
        if "温度" in sensor_fields:
            for col in sensor_fields["温度"]:
                if col in df.columns:
                    values = pd.to_numeric(df[col], errors="coerce").dropna()
                    if len(values) >= 3:
                        last3 = values.tail(3).tolist()
                        if len(last3) >= 3 and last3[0] < last3[1] < last3[2]:
                            anomalies["指标异常"]["油温升高"] = (
                                f"字段 {col} 检测到持续上升趋势: "
                                f"{last3[0]:.1f} → {last3[1]:.1f} → {last3[2]:.1f}"
                            )
                            anomalies["趋势分析"].append({
                                "趋势类型": "油温升高",
                                "字段": col,
                                "趋势描述": "油温持续升高",
                                "相关状态事件": "油温升高",
                            })

        return anomalies

    def _generate_table_events(self, anomalies: Dict[str, Any],
                                file_id: str) -> List[Dict[str, Any]]:
        """从表格异常生成状态事件"""
        events = []
        trend = anomalies.get("趋势分析", [])
        indicators = anomalies.get("指标异常", {})

        for i, t in enumerate(trend, 1):
            event = {
                "事件编号": f"EVT-TBL-{i:04d}",
                "事件类型": "状态事件",
                "触发词": "检测到",
                "部件": "液压系统",
                "故障模式": "",
                "异常状态": t.get("趋势类型", ""),
                "原因": "",
                "事件描述": t.get("趋势描述", ""),
                "置信度": 0.7,
                "有效时间": datetime.now().strftime("%Y-%m-%d"),
                "来源编号": file_id,
                "证据原文": indicators.get(t.get("趋势类型", ""), ""),
                "论元": {"来源": "表格数据", "字段": t.get("字段", "")},
            }
            events.append(event)

        return events

    def _generate_table_evidence(self, events: List[Dict],
                                  anomalies: Dict[str, Any],
                                  file_id: str) -> List[Dict[str, Any]]:
        """从表格异常生成证据"""
        evidence_list = []
        indicators = anomalies.get("指标异常", {})
        for i, ev in enumerate(events, 1):
            evd = {
                "证据编号": f"EVD-TBL-{i:04d}",
                "事件编号": ev.get("事件编号", ""),
                "来源编号": file_id,
                "证据原文": ev.get("证据原文", ""),
                "可靠度": "中",
                "审核状态": "待审核",
            }
            evidence_list.append(evd)
        return evidence_list

    def _describe_anomalies(self, anomalies: Dict[str, Any],
                             sensor_fields: Dict[str, List[str]]) -> str:
        """生成异常指标的文字描述"""
        parts = []
        parts.append(f"检测到 {len(sensor_fields)} 类传感器字段: {', '.join(sensor_fields.keys())}")
        for name, desc in (anomalies.get("指标异常", {}) or {}).items():
            parts.append(f"  - {desc}")
        if not anomalies.get("指标异常"):
            parts.append("  未检测到明显异常趋势。")
        return "\n".join(parts)

    def _match_anomaly_templates(self, anomalies: Dict[str, Any]) -> List[str]:
        """匹配异常指标与机理模板"""
        templates = []
        indicators = anomalies.get("指标异常", {})
        if "压力下降" in indicators and "流量损失" in indicators:
            templates.append("T1-泄漏链")
        if "油温升高" in indicators:
            templates.append("T3-冷却链")
        if not templates:
            templates.append("待匹配")
        return templates

    def _generate_anomaly_chains(self, anomalies: Dict[str, Any]) -> List[Dict]:
        """根据异常生成故障链"""
        chains = []
        indicators = list((anomalies.get("指标异常", {}) or {}).keys())
        if "压力下降" in indicators and "流量损失" in indicators:
            chains.append({
                "模板编号": "T1", "模板名称": "泄漏链",
                "链式模式": "内泄漏→流量损失→压力下降→执行机构动作迟缓",
                "状态": "部分匹配链（从表格趋势推断）"
            })
        if "油温升高" in indicators:
            chains.append({
                "模板编号": "T3", "模板名称": "冷却链",
                "链式模式": "冷却器效率下降→油温升高→黏度下降→泄漏增加",
                "状态": "部分匹配链（从表格趋势推断）"
            })
        return chains

    def _get_table_maintenance(self, anomalies: Dict[str, Any]) -> List[str]:
        """根据表格异常推荐维修方案"""
        suggestions = []
        indicators = anomalies.get("指标异常", {})
        if "压力下降" in indicators:
            suggestions.append("检测泵内泄漏量（壳体泄漏量测量）")
            suggestions.append("检查系统密封件状态")
        if "流量损失" in indicators:
            suggestions.append("测量容积效率")
            suggestions.append("检查吸油管路和过滤器")
        if "油温升高" in indicators:
            suggestions.append("检查冷却器换热效率")
            suggestions.append("监测油液粘度变化")
        return suggestions

    def _df_to_text(self, df, sensor_fields: Dict[str, List[str]]) -> str:
        """将 DataFrame 转为文本描述"""
        parts = [f"表格数据共 {len(df)} 行，{len(df.columns)} 列。"]
        parts.append(f"识别到的传感器字段: {json.dumps(sensor_fields, ensure_ascii=False)}")
        parts.append("数据样本（前5行）:")
        parts.append(df.head(5).to_string())
        return "\n".join(parts)

    # ================================================================
    # 图片分析（模拟 OCR）
    # ================================================================

    def _analyze_image(self, file_id: str, file_path: str,
                        filename: str) -> Dict[str, Any]:
        """分析图片 - 模拟OCR

        当前使用模拟OCR结构。
        可后续接入真实OCR引擎或视觉模型进行图像理解。
        """
        # 尝试使用 PIL 获取图片基本信息
        try:
            from PIL import Image
            img = Image.open(file_path)
            img_info = {
                "宽度": img.width,
                "高度": img.height,
                "格式": img.format,
                "模式": img.mode,
            }
        except:
            img_info = {"说明": "无法读取图片信息"}

        # 模拟 OCR 文本 —— 基于文件名和液压常见场景
        simulated_text = self._simulate_ocr_text(filename)

        # 从模拟文本中提取事件
        events = self._extract_from_simulated_ocr(simulated_text, file_id)

        # 生成证据
        evidence_list = []
        for i, ev in enumerate(events, 1):
            evidence_list.append({
                "证据编号": f"EVD-IMG-{i:04d}",
                "事件编号": ev.get("事件编号", ""),
                "来源编号": file_id,
                "证据原文": simulated_text[:200],
                "可靠度": "低",
                "审核状态": "待审核",
            })

        return {
            "状态": "成功",
            "文件类型": "图片",
            "图片信息": img_info,
            "图片解析文本": simulated_text,
            "清洗段落": [],
            "液压相关段落": [],
            "抽取事件": events,
            "证据span": evidence_list,
            "异常指标": [
                {"指标": "压力下降", "描述": simulated_text[:100]},
            ],
            "匹配机理模板": ["T1-泄漏链"],
            "生成故障链": [{
                "模板编号": "T1", "模板名称": "泄漏链",
                "链式模式": "内泄漏→流量损失→压力下降→执行机构动作迟缓",
                "状态": "部分匹配链（从图片模拟OCR推断）"
            }],
            "维修建议": [
                "检查泵体和管路密封状态",
                "测量壳体泄漏量",
                "采集油样进行光谱分析",
            ],
            "置信度": 0.35,
            "风险等级": "中",
            "OCR说明": (
                "当前使用模拟OCR，返回的是基于液压系统常见故障模式的模拟文本。"
                "模拟文本从图片文件名和液压领域知识推断生成。"
                "如需真实OCR分析，请接入OCR引擎（如Tesseract、PaddleOCR）"
                "或视觉大模型进行图像理解。"
            ),
            "说明": (
                "此分析结果来自用户上传的现场图片（模拟OCR解析）。"
                "建议后续接入真实OCR引擎以获得准确的图片文本提取。"
                "注意：资料导入是可选增量功能。"
            )
        }

    def _simulate_ocr_text(self, filename: str) -> str:
        """模拟 OCR 文本生成

        基于文件名关键词和液压常见场景推断图片内容描述。
        """
        name_lower = filename.lower()
        texts = []

        # 基于文件名推断场景
        if any(w in name_lower for w in ["泵", "pump"]):
            texts.append("液压泵外观检查图。")
            texts.append("泵体表面可见渗油痕迹，疑似密封件老化导致外泄漏。")
            texts.append("泵出口压力表读数偏低，指针位于18MPa，正常应为25MPa。")
        elif any(w in name_lower for w in ["阀", "valve"]):
            texts.append("液压阀拆检图。")
            texts.append("阀芯表面可见划痕和沉积物，疑似油液污染导致阀芯卡滞。")
        elif any(w in name_lower for w in ["过滤器", "filter"]):
            texts.append("过滤器滤芯检查图。")
            texts.append("滤芯表面覆盖大量黑色沉积物和金属粉末，过滤器堵塞严重。")
        elif any(w in name_lower for w in ["油", "oil"]):
            texts.append("液压油样对比图。")
            texts.append("左侧为新油（淡黄色透明），右侧为旧油（深褐色浑浊）。")
            texts.append("旧油颜色显著变深且有异味，表明液压油已严重劣化。")
        elif any(w in name_lower for w in ["冷却", "cool"]):
            texts.append("冷却器管束检查图。")
            texts.append("管束内部可见明显水垢层（厚度约1-2mm），冷却效率下降。")
        else:
            texts.append("液压系统现场检查图。")
            texts.append("观察到以下异常现象：")
            texts.append("1. 液压泵出口压力持续下降，系统无法维持额定压力。")
            texts.append("2. 执行机构动作迟缓，伸出速度明显降低。")
            texts.append("3. 油箱温度异常升高，触感明显高于正常工况。")
            texts.append("4. 系统存在内泄漏可能，需进一步拆检确认。")

        texts.append(f"\n[模拟OCR说明] 以上内容基于文件名 '{filename}' 的液压领域知识推断生成。")
        texts.append("建议接入真实OCR引擎（Tesseract/PaddleOCR）或视觉大模型以获得准确的图像文本。")

        return "\n".join(texts)

    def _extract_from_simulated_ocr(self, text: str, file_id: str) -> List[Dict[str, Any]]:
        """从模拟OCR文本中抽取事件"""
        events = []
        patterns = [
            ("压力下降", "压力下降", "状态事件", "系统压力低于额定值"),
            ("流量损失", "流量损失", "状态事件", "执行机构速度降低"),
            ("油温升高", "油温升高", "状态事件", "油箱温度异常升高"),
            ("内泄漏", "内泄漏", "故障事件", "泵内部存在泄漏"),
            ("密封件老化", "密封件老化", "故障事件", "密封件因老化导致泄漏"),
            ("阀芯卡滞", "阀芯卡滞", "故障事件", "阀芯因污染导致卡滞"),
            ("过滤器堵塞", "过滤器堵塞", "故障事件", "滤芯表面沉积物严重"),
            ("冷却器效率下降", "冷却器效率下降", "故障事件", "管束结垢导致换热效率降低"),
            ("油液污染", "油液污染", "故障事件", "液压油严重劣化"),
            ("执行机构动作迟缓", "执行机构动作迟缓", "状态事件", "执行机构运动速度降低"),
        ]

        for i, (keyword, state, etype, desc) in enumerate(patterns, 1):
            if keyword in text:
                events.append({
                    "事件编号": f"EVT-IMG-{i:04d}",
                    "事件类型": etype,
                    "触发词": "观察到" if etype == "状态事件" else "疑似",
                    "部件": "液压系统",
                    "故障模式": state if etype == "故障事件" else "",
                    "异常状态": state if etype == "状态事件" else "",
                    "原因": "",
                    "事件描述": desc,
                    "置信度": 0.3,
                    "有效时间": datetime.now().strftime("%Y-%m-%d"),
                    "来源编号": file_id,
                    "证据原文": text[:300],
                    "论元": {"来源": "图片模拟OCR", "文件名": file_id},
                })

        return events

    # ================================================================
    # 辅助方法
    # ================================================================

    def _classify_file(self, filename: str, ext: str) -> str:
        """分类文件类型"""
        for category, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext.lower() in extensions:
                return category
        return "document"  # 默认按文档处理

    def _get_subdir(self, category: str) -> str:
        """根据文件类型获取保存子目录"""
        upload_dir = self.get_upload_dir()
        return os.path.join(upload_dir, {
            "document": "documents",
            "image": "images",
            "table": "tables",
        }.get(category, "documents"))

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / 1024 / 1024:.1f} MB"

    def _save_upload_record(self, file_id: str, filename: str,
                             file_type: str, file_size: int, storage_path: str):
        """保存上传记录到数据库"""
        from database import execute_sql
        execute_sql(
            "INSERT INTO uploaded_files (file_id, 文件名, 文件类型, 文件大小, 上传时间, 处理状态, 存储路径) "
            "VALUES (?, ?, ?, ?, datetime('now','localtime'), '待分析', ?)",
            (file_id, filename, file_type, file_size, storage_path)
        )

    def _update_file_status(self, file_id: str, status: str):
        """更新文件处理状态"""
        from database import execute_sql
        execute_sql(
            "UPDATE uploaded_files SET 处理状态 = ? WHERE file_id = ?",
            (status, file_id)
        )

    def _get_file_info(self, file_id: str) -> Optional[Dict]:
        """获取文件信息"""
        from database import fetch_one
        row = fetch_one("SELECT * FROM uploaded_files WHERE file_id = ?", (file_id,))
        return dict(row) if row else None

    def _save_analysis_result(self, file_id: str, analysis_type: str,
                               result: Dict[str, Any]):
        """保存分析结果到数据库"""
        from database import execute_sql
        result_id = f"ANR-{uuid.uuid4().hex[:8]}"
        execute_sql(
            "INSERT INTO analysis_results (result_id, file_id, 分析类型, 分析结果JSON, 是否加入图谱, 分析时间) "
            "VALUES (?, ?, ?, ?, 0, datetime('now','localtime'))",
            (result_id, file_id, analysis_type, json.dumps(result, ensure_ascii=False))
        )

    def _read_text(self, filepath: str) -> str:
        """读取文本文件"""
        for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
            try:
                with open(filepath, encoding=enc) as f:
                    return f.read()
            except:
                continue
        with open(filepath, encoding="utf-8", errors="replace") as f:
            return f.read()

    def _read_pdf(self, filepath: str) -> str:
        """读取PDF"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except:
            return ""

    def _read_docx(self, filepath: str) -> str:
        """读取DOCX"""
        try:
            from docx import Document
            doc = Document(filepath)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except:
            return ""

    def _calc_doc_confidence(self, extract_result: Dict,
                              validation_result: Dict) -> float:
        """计算文档分析置信度"""
        events = extract_result.get("事件列表", [])
        chains = validation_result.get("校验结果", [])
        if not events:
            return 0.3
        event_conf = sum(e.get("置信度", 0.5) for e in events[:10]) / min(len(events[:10]), 1)
        chain_score = sum(c.get("匹配分数", 0.5) for c in chains[:5]) / max(len(chains[:5]), 1)
        return round(event_conf * 0.6 + chain_score * 0.4, 4)

    def _get_maintenance_suggestions(self, extract_result: Dict) -> List[str]:
        """从抽取结果中提取维修建议"""
        events = extract_result.get("事件列表", [])
        suggestions = set()
        for ev in events:
            action = ev.get("维修动作", "")
            if action:
                suggestions.add(action)
        if not suggestions:
            suggestions = {"检查系统整体状态", "采集油样进行分析", "测量关键运行参数"}
        return list(suggestions)[:10]


# 单例
import_service = ImportService()
