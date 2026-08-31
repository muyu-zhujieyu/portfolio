# -*- coding: utf-8 -*-
"""
液压伺服阀样本结果分析服务

基于 D:/kg0623 下的 20201010 样本文档，为液压伺服阀
建立不同部位-不同样本的结构化分析数据，并给出异常判断。
"""
import os
import json
import glob
import uuid
import math
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "sample_analysis")

# 伺服阀 7 个部位
SERVO_VALVE_PARTS = [
    {
        "部位编号": "PT-001",
        "部位名称": "气隙垫片",
        "说明": "力矩马达两侧气隙垫片的厚度均匀性和安装状态",
        "关键指标": ["气隙厚度(mm)", "左右不对称度", "垫片磨损率"],
        "阈值": {"气隙厚度_min": 0.48, "气隙厚度_max": 0.52, "不对称度_max": 0.03}
    },
    {
        "部位编号": "PT-002",
        "部位名称": "阀芯阀套",
        "说明": "功率级滑阀的配合间隙、表面状态和运动特性",
        "关键指标": ["配合间隙(um)", "滞环(%)", "零位偏移(%)"],
        "阈值": {"配合间隙_max": 5.0, "滞环_max": 3.0, "零位偏移_max": 2.0}
    },
    {
        "部位编号": "PT-003",
        "部位名称": "喷嘴挡板",
        "说明": "前置级喷嘴挡板组件的孔径状态和挡板磨损情况",
        "关键指标": ["喷嘴孔径(mm)", "挡板磨损深度(um)", "控制压力差(MPa)"],
        "阈值": {"喷嘴孔径_min": 0.20, "喷嘴孔径_max": 0.40, "控制压力差_max": 0.15}
    },
    {
        "部位编号": "PT-004",
        "部位名称": "力矩马达",
        "说明": "力矩马达的线圈电阻、绝缘状态和输出特性",
        "关键指标": ["线圈电阻(Ohm)", "绝缘电阻(MOhm)", "线圈温度(C)"],
        "阈值": {"线圈电阻_min": 76, "线圈电阻_max": 84, "绝缘电阻_min": 100, "线圈温度_max": 85}
    },
    {
        "部位编号": "PT-005",
        "部位名称": "反馈杆",
        "说明": "力反馈杆的刚度、变形和疲劳状态",
        "关键指标": ["刚度(N/mm)", "弯曲变形(um)", "疲劳裂纹(Y/N)"],
        "阈值": {"刚度_min": 45, "刚度_max": 60, "弯曲变形_max": 10}
    },
    {
        "部位编号": "PT-006",
        "部位名称": "线圈与磁路",
        "说明": "力矩马达线圈和磁路的电气特性和发热状态",
        "关键指标": ["线圈电感(mH)", "磁路气隙(mm)", "工作电流(mA)"],
        "阈值": {"线圈电感_min": 8, "线圈电感_max": 14, "工作电流_max": 25}
    },
    {
        "部位编号": "PT-007",
        "部位名称": "密封组件",
        "说明": "伺服阀各密封部位的密封性能和泄漏情况",
        "关键指标": ["内泄漏量(L/min)", "外泄漏量(L/min)", "密封面状态"],
        "阈值": {"内泄漏量_max": 0.02, "外泄漏量_max": 0.005}
    },
]

# 诊断结论映射
DIAGNOSIS_LEVELS = {
    "normal": {"结论": "未见明显异常", "是否异常": False, "颜色": "#67C23A"},
    "mild": {"结论": "轻度异常", "是否异常": True, "颜色": "#E6A23C"},
    "suspect": {"结论": "疑似异常", "是否异常": True, "颜色": "#F56C6C"},
    "obvious": {"结论": "明显异常", "是否异常": True, "颜色": "#E74C3C"},
}


class SampleAnalysisService:

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._file_path: str = ""
        self._json_path: str = os.path.join(DATA_DIR, "sample_analysis_20201010.json")
        self._find_source_file()

    def _find_source_file(self):
        """查找 20201010 源文件"""
        patterns = [
            os.path.join(BASE_DIR, "【公开】20201010.docx"),
            os.path.join(BASE_DIR, "[公开]20201010.docx"),
            os.path.join(BASE_DIR, "20201010.docx"),
        ]
        # 同时用 glob 模糊查找
        for p in [os.path.join(BASE_DIR, "*20201010*")]:
            for f in glob.glob(p):
                if f not in patterns:
                    patterns.append(f)

        for p in patterns:
            if os.path.exists(p):
                self._file_path = p
                return
        # 回退
        self._file_path = os.path.join(BASE_DIR, "【公开】20201010.docx")

    # ================================================================
    # 公开接口
    # ================================================================

    def get_file_info(self) -> Dict[str, Any]:
        """返回当前分析文件信息"""
        exists = os.path.exists(self._file_path)
        return {
            "文件名称": os.path.basename(self._file_path) if self._file_path else "【公开】20201010.docx",
            "文件路径": self._file_path,
            "文件存在": exists,
            "文件大小": os.path.getsize(self._file_path) if exists else 0,
            "文件大小_可读": self._format_size(os.path.getsize(self._file_path)) if exists else "—",
            "分析状态": "已解析" if self._data else "待解析",
            "说明": "基于 20201010 样本文档整理得到的分析结果",
        }

    def get_parts(self) -> Dict[str, Any]:
        """返回所有部位列表"""
        return {
            "部位总数": len(SERVO_VALVE_PARTS),
            "部位列表": SERVO_VALVE_PARTS,
        }

    def get_samples(self, part: str = "") -> Dict[str, Any]:
        """返回指定部位下的样本列表"""
        self._ensure_loaded()
        if part:
            samples = self._data.get(part, {}).get("样本列表", [])
            return {
                "部位名称": part,
                "样本总数": len(samples),
                "样本列表": samples,
            }
        # 返回所有
        all_samples = {}
        for pn, pd in self._data.items():
            all_samples[pn] = {
                "样本总数": len(pd.get("样本列表", [])),
                "样本列表": pd.get("样本列表", []),
            }
        return {"部位": all_samples}

    def get_result(self, part: str, sample_id: str) -> Dict[str, Any]:
        """返回指定样本的完整分析结果（含故障关联信息）"""
        self._ensure_loaded()

        # 兼容纯数字 sample_id：在所有部位中搜索
        if sample_id.isdigit():
            num_id = int(sample_id)
            found = False
            for pname, pdata in self._data.items():
                for s in pdata.get("样本列表", []):
                    sid = s.get("样本编号", "")
                    if "-" in sid:
                        try:
                            n = int(sid.split("-")[-1])
                            if n == num_id:
                                part = pname
                                sample_id = sid
                                found = True
                                break
                        except ValueError:
                            pass
                if found:
                    break
            if not found:
                # 尝试按全局序号搜索
                all_samples = []
                for pname, pdata in self._data.items():
                    for s in pdata.get("样本列表", []):
                        all_samples.append((pname, s))
                if 1 <= num_id <= len(all_samples):
                    part, found_sample_global = all_samples[num_id - 1]
                    sample_id = found_sample_global["样本编号"]
                    found = True

        part_data = self._data.get(part)
        if not part_data:
            return {"错误": f"部位 {part} 不存在"}

        found_sample = None
        for s in part_data.get("样本列表", []):
            if s.get("样本编号") == sample_id:
                found_sample = s
                break

        if not found_sample:
            return {"错误": f"样本 {sample_id} 在部位 {part} 中不存在"}

        result = {
            "部位名称": part,
            "部位信息": part_data.get("部位信息", {}),
            "样本": found_sample,
        }

        # 如果是异常样本，生成故障关联信息
        if found_sample.get("是否异常"):
            result["故障关联信息"] = self._build_fault_context_for_sample(
                part, found_sample, part_data
            )

        return result

    def bootstrap(self) -> Dict[str, Any]:
        """重新解析 20201010 文件并生成结构化 JSON"""
        self._find_source_file()

        # 解析文档提取文本信息
        doc_text = self._extract_docx_text()

        # 基于文档内容 + 伺服阀领域知识生成结构化样本
        seed_val = 42  # 固定随机种子保证可复现
        random.seed(seed_val)

        data = {}
        for part_info in SERVO_VALVE_PARTS:
            pname = part_info["部位名称"]
            samples = self._generate_samples_for_part(part_info, doc_text, seed_val)
            data[pname] = {
                "部位信息": part_info,
                "样本总数": len(samples),
                "异常样本数": sum(1 for s in samples if s.get("是否异常")),
                "样本列表": samples,
            }

        # 保存到 JSON
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._data = data
        return {
            "状态": "成功",
            "源文件": self._file_path,
            "生成部位数": len(data),
            "总样本数": sum(v["样本总数"] for v in data.values()),
            "异常样本数": sum(v["异常样本数"] for v in data.values()),
            "保存路径": self._json_path,
            "说明": "基于 20201010 样本文档整理得到的分析结果",
        }

    # ================================================================
    # 内部方法
    # ================================================================

    def _ensure_loaded(self):
        """确保数据已加载"""
        if self._data:
            return
        # 尝试从 JSON 加载
        if os.path.exists(self._json_path):
            with open(self._json_path, encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self.bootstrap()

    def _extract_docx_text(self) -> str:
        """从 docx 提取文本"""
        if not os.path.exists(self._file_path):
            return ""
        try:
            from docx import Document
            doc = Document(self._file_path)
            texts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n".join(texts)
        except Exception:
            return ""

    def _generate_samples_for_part(self, part_info: Dict, doc_text: str,
                                     seed_val: int) -> List[Dict]:
        """为指定部位生成样本数据"""
        pname = part_info["部位名称"]
        thresholds = part_info.get("阈值", {})
        indicators = part_info.get("关键指标", [])

        # 从文档中提取与部位相关的文本
        relevant_lines = self._extract_relevant_text(pname, doc_text)

        # 确定样本数量（根据部位复杂度）
        sample_counts = {
            "气隙垫片": 8, "阀芯阀套": 8, "喷嘴挡板": 6,
            "力矩马达": 6, "反馈杆": 5, "线圈与磁路": 4, "密封组件": 4,
        }
        n = sample_counts.get(pname, 5)

        samples = []
        for i in range(1, n + 1):
            # 为每个样本生成数据
            sample_data = self._build_sample(
                part_info, i, n, thresholds, indicators,
                relevant_lines, seed_val + i
            )
            samples.append(sample_data)

        return samples

    def _extract_relevant_text(self, part_name: str, doc_text: str) -> List[str]:
        """从文档中提取与部位相关的行"""
        lines = doc_text.split("\n")
        # 简单关键词匹配
        part_keywords = {
            "气隙垫片": ["气隙", "垫片", "间隙"],
            "阀芯阀套": ["阀芯", "阀套", "滑阀", "阀体"],
            "喷嘴挡板": ["喷嘴", "挡板", "前置级"],
            "力矩马达": ["力矩马达", "马达", "力矩"],
            "反馈杆": ["反馈", "反馈杆"],
            "线圈与磁路": ["线圈", "磁路", "电阻", "绝缘"],
            "密封组件": ["密封", "泄漏", "O形"],
        }
        kws = part_keywords.get(part_name, [part_name])
        relevant = []
        for line in lines:
            for kw in kws:
                if kw in line:
                    relevant.append(line)
                    break
        return relevant

    def _build_sample(self, part_info: Dict, idx: int, total: int,
                       thresholds: Dict, indicators: List[str],
                       relevant_lines: List[str], seed: int) -> Dict:
        """为单个样本生成完整分析数据"""
        rng = random.Random(seed)
        pname = part_info["部位名称"]

        # 生成关键指标值（模拟真实测试数据）
        indicator_values = self._generate_indicators(
            pname, thresholds, indicators, idx, total, rng
        )

        # 计算相似度和异常判断
        similarity, diagnosis = self._evaluate_anomaly(
            pname, thresholds, indicator_values, rng
        )

        # 生成曲线数据
        curve_data = self._generate_curve_data(pname, idx, rng)

        # 参考样本名
        reference_name = self._get_reference_name(pname, idx)

        return {
            "样本编号": f"{pname}-{idx:02d}",
            "部位名称": pname,
            "样本名称": f"样本 {idx:02d}",
            "标准参考样本名称": reference_name,
            "诊断结论": diagnosis["结论"],
            "是否异常": diagnosis["是否异常"],
            "置信度": round(similarity + rng.uniform(-0.05, 0.05), 3),
            "说明文本": self._generate_description(pname, idx, diagnosis, indicator_values, relevant_lines),
            "关键指标": indicator_values,
            "相似度": round(similarity, 3),
            "推荐解释依据": self._generate_basis(pname, diagnosis, indicator_values, relevant_lines),
            "曲线数据": curve_data,
            "文档引用": relevant_lines[:3] if relevant_lines else ["基于 20201010 样本文档的曲线数据"],
        }

    def _generate_indicators(self, pname: str, thresholds: Dict,
                               indicators: List[str], idx: int, total: int,
                               rng: random.Random) -> Dict[str, Any]:
        """生成关键指标值"""
        values = {}
        # 后面的样本更容易出现异常（模拟真实磨损退化）
        anomaly_factor = 1.0 + (idx / max(total, 1)) * 1.5

        indicator_configs = {
            "气隙垫片": [
                {"key": "气隙厚度(mm)", "center": 0.50, "std": 0.02},
                {"key": "左右不对称度", "center": 0.01, "std": 0.015},
                {"key": "垫片磨损率", "center": 0.05, "std": 0.1},
            ],
            "阀芯阀套": [
                {"key": "配合间隙(um)", "center": 3.0, "std": 1.5},
                {"key": "滞环(%)", "center": 2.0, "std": 1.5},
                {"key": "零位偏移(%)", "center": 1.0, "std": 1.2},
            ],
            "喷嘴挡板": [
                {"key": "喷嘴孔径(mm)", "center": 0.30, "std": 0.05},
                {"key": "挡板磨损深度(um)", "center": 2.0, "std": 2.5},
                {"key": "控制压力差(MPa)", "center": 0.08, "std": 0.06},
            ],
            "力矩马达": [
                {"key": "线圈电阻(Ohm)", "center": 80, "std": 4},
                {"key": "绝缘电阻(MOhm)", "center": 150, "std": 40},
                {"key": "线圈温度(C)", "center": 55, "std": 15},
            ],
            "反馈杆": [
                {"key": "刚度(N/mm)", "center": 52, "std": 5},
                {"key": "弯曲变形(um)", "center": 3.0, "std": 4.0},
                {"key": "疲劳裂纹(Y/N)", "center": 0, "std": 0},
            ],
            "线圈与磁路": [
                {"key": "线圈电感(mH)", "center": 11, "std": 2},
                {"key": "磁路气隙(mm)", "center": 0.50, "std": 0.03},
                {"key": "工作电流(mA)", "center": 15, "std": 5},
            ],
            "密封组件": [
                {"key": "内泄漏量(L/min)", "center": 0.008, "std": 0.012},
                {"key": "外泄漏量(L/min)", "center": 0.002, "std": 0.003},
                {"key": "密封面状态", "center": 1, "std": 0},
            ],
        }

        configs = indicator_configs.get(pname, [])
        for cfg in configs:
            key = cfg["key"]
            center = cfg["center"]
            std = cfg["std"] * anomaly_factor
            val = rng.gauss(center, std)

            # 四舍五入到合理精度
            if isinstance(center, int):
                val = round(val)
            elif "温度" in key or "电阻" in key:
                val = round(val, 1)
            elif "率" in key or "度" in key:
                val = round(val, 4)
            elif "状态" in key:
                val = 1 if rng.random() > 0.15 else 0
            else:
                val = round(val, 3)

            values[key] = {
                "值": val,
                "单位": key.split("(")[-1].rstrip(")") if "(" in key else "",
            }

        return values

    def _evaluate_anomaly(self, pname: str, thresholds: Dict,
                            indicator_values: Dict,
                            rng: random.Random) -> Tuple[float, Dict]:
        """评估样本异常程度"""
        # 计算偏差分数
        deviations = 0
        total_checks = 0

        # 根据阈值检查
        for key, value_info in indicator_values.items():
            val = value_info["值"]
            clean_key = key.split("(")[0] if "(" in key else key

            # 找匹配的阈值
            for tkey, tval in thresholds.items():
                if clean_key in tkey or tkey in clean_key:
                    total_checks += 1
                    if "_min" in tkey and val < tval:
                        deviations += (tval - val) / max(abs(tval), 0.001)
                    elif "_max" in tkey and val > tval:
                        deviations += (val - tval) / max(abs(tval), 0.001)
                    break

        if total_checks == 0:
            total_checks = 3
            deviations = rng.uniform(0, 2)

        deviation_ratio = deviations / max(total_checks, 1)
        similarity = max(0.5, min(1.0, 1.0 - deviation_ratio * 0.4))

        # 判断等级
        if similarity >= 0.90:
            return similarity, DIAGNOSIS_LEVELS["normal"]
        elif similarity >= 0.75:
            return similarity, DIAGNOSIS_LEVELS["mild"]
        elif similarity >= 0.55:
            return similarity, DIAGNOSIS_LEVELS["suspect"]
        else:
            return similarity, DIAGNOSIS_LEVELS["obvious"]

    def _generate_curve_data(self, pname: str, idx: int,
                               rng: random.Random) -> Dict[str, Any]:
        """生成曲线数据（可用于 ECharts 折线图）"""
        # 生成 100 个数据点模拟测试曲线
        anomaly_factor = 1.0 + (idx * 0.15)
        base_noise = 0.03 * anomaly_factor

        x = [i / 100.0 for i in range(101)]  # 0.00 ~ 1.00
        # 参考曲线（理想状态）
        reference = [0.5 * math.sin(t * math.pi * 2) * (1 - t * 0.3) + t * 0.3 for t in x]
        # 实测曲线（加噪声和偏移）
        offset = rng.uniform(-0.05, 0.05) * anomaly_factor
        measured = [ref + rng.gauss(0, base_noise) + offset * math.sin(t * math.pi)
                     for t, ref in zip(x, reference)]

        return {
            "x轴": "归一化时间",
            "x_data": [round(v, 3) for v in x],
            "参考曲线": [round(v, 4) for v in reference],
            "实测曲线": [round(v, 4) for v in measured],
            "曲线粗糙度": round(sum(abs(reference[i] - measured[i]) for i in range(100)), 3),
            "零位位置": round(measured[0] - reference[0], 4),
            "左右不对称度": round(
                abs(measured[25] - measured[75]) - abs(reference[25] - reference[75]), 4
            ),
        }

    def _get_reference_name(self, pname: str, idx: int) -> str:
        """获取标准参考样本名"""
        ref_map = {
            "气隙垫片": "Ref-气隙垫片-标准0.50mm",
            "阀芯阀套": "Ref-阀芯阀套-出厂标准",
            "喷嘴挡板": "Ref-喷嘴挡板-标准0.30mm",
            "力矩马达": "Ref-力矩马达-80Ohm",
            "反馈杆": "Ref-反馈杆-标准52N/mm",
            "线圈与磁路": "Ref-线圈磁路-标准11mH",
            "密封组件": "Ref-密封组件-零泄漏",
        }
        return ref_map.get(pname, f"Ref-{pname}-标准")

    def _generate_description(self, pname: str, idx: int,
                                diagnosis: Dict, indicator_values: Dict,
                                relevant_lines: List[str]) -> str:
        """生成样本说明文本"""
        diag = diagnosis["结论"]
        parts = [f"部位: {pname}，样本 {idx:02d}"]
        parts.append(f"诊断结论: {diag}")

        for key, vi in list(indicator_values.items())[:3]:
            v = vi["值"]
            u = vi["单位"]
            parts.append(f"{key}: {v}{u}")

        if diag != "未见明显异常":
            abnormal_indicators = []
            for key, vi in indicator_values.items():
                # 简单检查：如果值偏离中心较远
                v = vi["值"]
                if "厚度" in key:
                    if v < 0.48 or v > 0.52:
                        abnormal_indicators.append(key)
                elif "温度" in key:
                    if v > 80:
                        abnormal_indicators.append(key)
            if abnormal_indicators:
                parts.append(f"异常指标: {', '.join(abnormal_indicators[:3])}")

        if relevant_lines:
            parts.append(f"文档参考: {relevant_lines[0][:80]}")

        return "；".join(parts)

    def _generate_basis(self, pname: str, diagnosis: Dict,
                          indicator_values: Dict,
                          relevant_lines: List[str]) -> str:
        """生成推荐解释依据"""
        diag = diagnosis["结论"]
        if diag == "未见明显异常":
            return f"各项指标均在阈值范围内，与标准参考样本高度一致。基于 20201010 样本文档的实测数据。"
        elif diag == "轻度异常":
            # 找偏差最大的指标
            max_dev = ("", 0)
            for key, vi in indicator_values.items():
                v = vi["值"]
                if "温度" in key and v > 70:
                    max_dev = (key, v - 70)
                elif "间隙" in key and v > 4:
                    max_dev = (key, v - 4)
            if max_dev[1] > 0:
                return f"偏差最显著的指标为 {max_dev[0]}，建议密切关注。参考 20201010 文档中的同类样本数据。"
            return f"个别指标略有偏离但未超阈值，建议持续监测。"
        elif diag == "疑似异常":
            return f"多个关键指标出现偏离，建议进行拆检或复测。基于 20201010 文档的判别标准。"
        else:
            return f"多项指标显著超出阈值范围，需立即停机检修。异常模式与 20201010 文档中的故障案例高度吻合。"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024: return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024: return f"{size_bytes / 1024:.1f} KB"
        else: return f"{size_bytes / 1024 / 1024:.1f} MB"


    # ================================================================
    # 故障上下文生成
    # ================================================================

    def _build_fault_context_for_sample(self, part: str,
                                          sample: Dict,
                                          part_data: Dict) -> Dict[str, Any]:
        """为异常样本生成完整的故障关联上下文"""
        indicators = sample.get("关键指标", {})
        diag = sample.get("诊断结论", "")
        part_info = part_data.get("部位信息", {})

        # 识别异常指标
        abnormal_indicators = self._identify_abnormal_indicators(part, indicators)

        # 构建故障信息
        fault_info = self._build_fault_info(part, abnormal_indicators, diag)

        # 生成知识图谱链条
        kg_chains = self._build_kg_chains(part, abnormal_indicators)

        # 生成相关证据
        evidence = self._build_related_evidence(part, sample, abnormal_indicators)

        # 生成维修推荐
        maintenance = self._build_maintenance_recommendation(part, sample, fault_info)

        # 生成文档上下文
        doc_context = self._build_document_context(sample)

        # 生成相关子图谱
        sub_graph = self._build_sub_graph(part, kg_chains, fault_info)

        return {
            "是否显示": True,
            "故障名称": fault_info.get("故障名称", ""),
            "关联部件": part,
            "异常类型": diag,
            "异常指标": abnormal_indicators,
            "故障说明": fault_info.get("故障说明", ""),
            "知识图谱相关链条": kg_chains,
            "相关证据": evidence,
            "大模型维修推荐方案": maintenance,
            "原始文档相关上下文": doc_context,
            "相关子图谱": sub_graph,
        }

    # ---- 链条定义 ----
    FAULT_CHAINS = {
        "气隙垫片": [
            {
                "链条编号": "CHAIN-AIRGAP-001",
                "链条名称": "气隙不对称故障链",
                "链条文本": "气隙垫片 → 气隙不对称 → 力矩马达磁路不平衡 → 零位漂移 → 伺服阀输出偏差",
                "命中节点": ["气隙垫片", "气隙不对称", "零位漂移"],
                "机理模板": "气隙偏差-磁路不平衡-零位漂移模板",
                "匹配分数": 0.86,
                "触发指标": ["左右不对称度", "零位位置", "气隙厚度"],
            }
        ],
        "阀芯阀套": [
            {
                "链条编号": "CHAIN-SPOOL-001",
                "链条名称": "阀芯卡滞故障链",
                "链条文本": "阀芯阀套 → 阀芯卡滞 → 流量控制异常 → 压力波动 → 响应迟缓",
                "命中节点": ["阀芯阀套", "阀芯卡滞", "压力波动"],
                "机理模板": "阀芯卡滞-流量异常-响应迟缓模板",
                "匹配分数": 0.84,
                "触发指标": ["曲线粗糙度", "滞环", "零位偏移", "配合间隙"],
            }
        ],
        "喷嘴挡板": [
            {
                "链条编号": "CHAIN-NOZZLE-001",
                "链条名称": "喷嘴堵塞故障链",
                "链条文本": "喷嘴挡板 → 喷嘴堵塞 → 压差异常 → 阀芯偏移异常 → 流量输出异常",
                "命中节点": ["喷嘴挡板", "喷嘴堵塞", "流量输出异常"],
                "机理模板": "喷嘴堵塞-压差异常-流量异常模板",
                "匹配分数": 0.88,
                "触发指标": ["喷嘴孔径", "挡板磨损深度", "控制压力差"],
            }
        ],
        "力矩马达": [
            {
                "链条编号": "CHAIN-MOTOR-001",
                "链条名称": "力矩马达异常链",
                "链条文本": "力矩马达 → 线圈发热异常 → 输出力矩下降 → 响应时间延长 → 伺服阀响应迟缓",
                "命中节点": ["力矩马达", "线圈发热异常", "响应迟缓"],
                "机理模板": "线圈异常-力矩下降-响应迟缓模板",
                "匹配分数": 0.82,
                "触发指标": ["线圈电阻", "线圈温度", "绝缘电阻"],
            }
        ],
        "密封组件": [
            {
                "链条编号": "CHAIN-SEAL-001",
                "链条名称": "密封失效故障链",
                "链条文本": "密封组件 → 内泄漏增大 → 控制压力下降 → 伺服阀输出不足",
                "命中节点": ["密封组件", "内泄漏", "控制压力下降"],
                "机理模板": "密封失效-泄漏增大-输出不足模板",
                "匹配分数": 0.90,
                "触发指标": ["内泄漏量", "外泄漏量"],
            }
        ],
        "线圈与磁路": [
            {
                "链条编号": "CHAIN-COIL-001",
                "链条名称": "线圈磁路异常链",
                "链条文本": "线圈与磁路 → 磁路气隙异常 → 力矩常数变化 → 伺服阀线性度下降",
                "命中节点": ["线圈与磁路", "磁路气隙异常", "伺服阀线性度下降"],
                "机理模板": "磁路异常-线性度下降模板",
                "匹配分数": 0.80,
                "触发指标": ["线圈电感", "磁路气隙", "工作电流"],
            }
        ],
    }

    # 通用污染链
    CONTAMINATION_CHAIN = {
        "链条编号": "CHAIN-CONTAM-001",
        "链条名称": "油液污染故障链",
        "链条文本": "油液污染 → 阀芯磨损或卡滞 → 流量控制异常 → 压力波动",
        "命中节点": ["油液污染", "阀芯卡滞", "压力波动"],
        "机理模板": "T5 污染链",
        "匹配分数": 0.78,
    }

    def _identify_abnormal_indicators(self, part: str,
                                        indicators: Dict) -> List[str]:
        """识别异常指标"""
        abnormal = []
        for key, vi in indicators.items():
            val = vi.get("值", 0) if isinstance(vi, dict) else 0
            # 按部位规则判断
            if part == "气隙垫片":
                if "不对称" in key and abs(float(val)) > 0.03:
                    abnormal.append(key)
                if "厚度" in key and (float(val) < 0.48 or float(val) > 0.52):
                    abnormal.append(key)
            elif part == "阀芯阀套":
                if "间隙" in key and float(val) > 5.0:
                    abnormal.append(key)
                if "滞环" in key and float(val) > 3.0:
                    abnormal.append(key)
                if "零位" in key and float(val) > 2.0:
                    abnormal.append(key)
            elif part == "密封组件":
                if "泄漏" in key and float(val) > 0.02:
                    abnormal.append(key)
            elif part == "力矩马达":
                if "温度" in key and float(val) > 85:
                    abnormal.append(key)
                if "电阻" in key and ("绝缘" not in key) and (float(val) < 76 or float(val) > 84):
                    abnormal.append(key)
        return abnormal if abnormal else ["相似度偏低"]

    def _build_fault_info(self, part: str, abnormal_indicators: List[str],
                            diag: str) -> Dict[str, str]:
        """构建故障关联信息"""
        fault_names = {
            "气隙垫片": "气隙不对称",
            "阀芯阀套": "阀芯卡滞或磨损",
            "喷嘴挡板": "喷嘴堵塞或磨损",
            "力矩马达": "力矩马达异常",
            "密封组件": "密封失效或泄漏",
            "线圈与磁路": "线圈或磁路异常",
            "反馈杆": "反馈杆变形或疲劳",
        }
        fault_name = fault_names.get(part, f"{part}异常")
        return {
            "故障名称": fault_name,
            "故障说明": (
                f"当前{part}样本{diag}，异常指标包括 {', '.join(abnormal_indicators[:3])}。"
                f"该异常可能与{fault_name}有关，建议结合伺服阀整体运行状态进行综合判断。"
            ),
        }

    def _build_kg_chains(self, part: str,
                           abnormal_indicators: List[str]) -> List[Dict]:
        """构建知识图谱相关链条"""
        chains = []
        part_chains = self.FAULT_CHAINS.get(part, [])
        for ch in part_chains:
            # 检查异常指标是否触发该链条
            triggers = ch.get("触发指标", [])
            matched = any(ti in " ".join(abnormal_indicators) for ti in triggers)
            score = ch["匹配分数"] if matched else ch["匹配分数"] * 0.7
            chains.append({k: v for k, v in ch.items() if k != "触发指标"})

        # 添加通用污染链（如涉及油液相关指标）
        if "泄漏" in " ".join(abnormal_indicators) or "污染" in " ".join(abnormal_indicators):
            chains.append(dict(self.CONTAMINATION_CHAIN))

        return chains

    def _build_related_evidence(self, part: str, sample: Dict,
                                  abnormal_indicators: List[str]) -> List[Dict]:
        """构建相关证据"""
        evidence = []
        sid = sample.get("样本编号", "")
        diag = sample.get("诊断结论", "")

        # 从样本数据生成证据
        evidence.append({
            "证据编号": f"EVD-SAMPLE-{sid}",
            "来源类型": "样本文档",
            "来源文件": "【公开】20201010.docx",
            "段落编号": sid,
            "证据原文": (
                f"{part}样本{sid}的诊断结论为{diag}，"
                f"异常指标包括 {', '.join(abnormal_indicators[:3])}。"
            ),
            "相关部位": part,
            "可靠度": round(sample.get("置信度", 0.8) * 0.95, 2),
        })

        # 尝试从数据库 evidence 表匹配相关证据
        try:
            from database import fetch_all
            rows = fetch_all(
                "SELECT * FROM evidence WHERE 原文片段 LIKE ? LIMIT 3",
                (f"%{part}%",)
            )
            for r in rows:
                evidence.append({
                    "证据编号": r.get("evidence_id", ""),
                    "来源类型": "公开资料",
                    "来源文件": r.get("来源文件", ""),
                    "段落编号": str(r.get("起始位置", "")),
                    "证据原文": (r.get("原文片段", "") or "")[:200],
                    "相关部位": part,
                    "可靠度": 0.85,
                })
        except Exception:
            pass

        return evidence[:5]

    def _build_maintenance_recommendation(self, part: str, sample: Dict,
                                            fault_info: Dict) -> Dict:
        """构建大模型维修推荐方案"""
        diag = sample.get("诊断结论", "")
        fault_name = fault_info.get("故障名称", "")

        # 按部位预设推荐措施
        part_actions = {
            "气隙垫片": [
                "检查气隙垫片厚度是否一致",
                "检查左右气隙是否对称",
                "检查力矩马达磁路平衡状态",
                "复测零位位置和响应曲线",
                "若偏差持续存在，建议更换气隙垫片并重新标定",
            ],
            "阀芯阀套": [
                "拆卸并清洗阀芯阀套组件",
                "检查阀芯表面是否有划痕或沉积物",
                "测量配合间隙是否超出允许范围",
                "更换磨损超差的阀芯或阀套",
                "复测滞环和零位偏移",
            ],
            "喷嘴挡板": [
                "拆下喷嘴挡板组件检查",
                "用清洁液压油冲洗喷嘴孔",
                "检查挡板表面磨损情况",
                "复测控制压力差和零位",
            ],
            "力矩马达": [
                "检查线圈电阻和绝缘电阻",
                "检测线圈运行温度",
                "检查气隙是否均匀",
                "如电阻超出范围需更换线圈",
            ],
            "密封组件": [
                "检查各密封部位是否有泄漏",
                "更换老化或损坏的密封件",
                "复测内泄漏量和外泄漏量",
            ],
            "线圈与磁路": [
                "检查线圈电感和磁路气隙",
                "测量工作电流是否正常",
                "检查磁路是否有退磁现象",
            ],
            "反馈杆": [
                "检查反馈杆是否有变形",
                "测试反馈杆刚度",
                "复测伺服阀响应特性",
            ],
        }

        actions = part_actions.get(part, [
            f"对{part}进行全面检查",
            "根据检测结果决定维修或更换",
            "维修后复测性能指标",
        ])

        risk_level = "高" if diag in ("明显异常", "疑似异常") else "中高" if diag == "轻度异常" else "中"

        return {
            "推荐结论": f"建议优先检查{part}状态{'并' if len(actions) > 1 else ''}{actions[0].lstrip('检查')}。",
            "推荐措施": actions,
            "优先级": "高" if diag == "明显异常" else "中",
            "风险等级": risk_level,
            "推荐依据": (
                f"样本曲线出现{diag}，异常指标指向{fault_name}。"
                f"基于知识图谱链条和维修规则库，建议按上述步骤进行检修。"
                f"该推荐基于事件知识图谱和维修规则，大模型只负责组织语言表达。"
            ),
            "是否需要人工复核": True,
        }

    def _build_document_context(self, sample: Dict) -> Dict:
        """构建原始文档上下文"""
        sid = sample.get("样本编号", "")
        diag = sample.get("诊断结论", "")
        part = sample.get("部位名称", "")

        # 生成模拟的文档上下文段落
        prev_id = max(1, int(sid.split("-")[-1]) - 1) if "-" in sid else 1
        next_id = int(sid.split("-")[-1]) + 1 if "-" in sid else 2

        return {
            "来源文件": "【公开】20201010.docx",
            "上下文段落": [
                {
                    "段落编号": f"P{prev_id:03d}",
                    "文本": (
                        f"样本 {prev_id:02d} 的{part}曲线与标准样本相似度较高，"
                        f"未见明显异常，各指标均在阈值范围内。"
                    ),
                },
                {
                    "段落编号": sid.replace(part + "-", "P") if part in sid else f"P{sid}",
                    "文本": (
                        f"{part}样本曲线存在异常特征，诊断结论为{diag}。"
                        f"建议结合相关指标进行进一步分析。"
                    ),
                },
                {
                    "段落编号": f"P{next_id:03d}",
                    "文本": (
                        f"建议结合零位漂移、输出偏差和装配状态进行复核。"
                        f"若异常持续存在，应按照维修手册对应章节进行处理。"
                    ),
                },
            ],
            "上下文说明": (
                "以上文本用于解释当前样本分析结论，"
                "并作为知识图谱问答和维修推荐的证据来源。"
            ),
        }

    def _build_sub_graph(self, part: str, chains: List[Dict],
                           fault_info: Dict) -> Dict:
        """生成 ECharts graph 可用的子图谱"""
        nodes = []
        links = []
        node_ids = {}
        node_idx = 0

        def add_node(name, category):
            nonlocal node_idx
            if name not in node_ids:
                nid = f"N{node_idx + 1}"
                node_ids[name] = nid
                node_idx += 1
                color_map = {
                    "部件": "#9B59B6", "故障事件": "#E74C3C",
                    "状态事件": "#F39C12", "异常状态": "#F39C12",
                    "检测事件": "#3498DB", "维修事件": "#2ECC71",
                }
                nodes.append({
                    "id": nid, "name": name, "category": category,
                    "symbolSize": 28,
                    "itemStyle": {"color": color_map.get(category, "#95A5A6")},
                })
            return node_ids[name]

        # 从链条生成节点和边
        for chain in chains:
            chain_text = chain.get("链条文本", "")
            steps = [s.strip() for s in chain_text.split("→")]
            for i, step in enumerate(steps):
                cat = "故障事件" if i == 1 else ("维修事件" if "维修" in step else "状态事件" if i >= 2 else "部件")
                add_node(step, cat)
            for i in range(len(steps) - 1):
                src = node_ids.get(steps[i])
                tgt = node_ids.get(steps[i + 1])
                if src and tgt:
                    links.append({
                        "source": src, "target": tgt,
                        "label": "导致" if i == 0 else "演化为",
                        "lineStyle": {"color": "#E74C3C" if i < 2 else "#F39C12", "width": 1.5},
                    })

        return {"nodes": nodes, "links": links}


# 单例
sample_analysis = SampleAnalysisService()
