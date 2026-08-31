"""
Pydantic 请求/响应 Schema 定义

所有字段使用中文名称，遵循项目中文规范。
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ================================================================
# 通用
# ================================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    状态: str = Field(..., description="系统运行状态")
    系统名称: str = Field(..., description="本系统名称")
    说明: str = Field(..., description="状态说明")


# ================================================================
# 来源资料
# ================================================================

class SourceCreate(BaseModel):
    """创建来源资料"""
    source_id: str
    来源类型: str
    标题: str
    作者: Optional[str] = None
    年份: Optional[int] = None
    出版方: Optional[str] = None
    文件路径: Optional[str] = None
    文档类型: Optional[str] = None
    公开说明: Optional[str] = None
    资料描述: Optional[str] = None


class SourceResponse(BaseModel):
    """来源资料响应"""
    source_id: str
    来源类型: str
    标题: str
    作者: Optional[str] = None
    年份: Optional[int] = None
    出版方: Optional[str] = None
    文件路径: Optional[str] = None
    文档类型: Optional[str] = None
    公开说明: Optional[str] = None
    资料描述: Optional[str] = None
    录入时间: Optional[str] = None


# ================================================================
# 段落
# ================================================================

class ParagraphResponse(BaseModel):
    paragraph_id: str
    source_id: str
    段落序号: int
    段落内容: str
    字符数: Optional[int] = None
    解析时间: Optional[str] = None


class FilteredParagraphResponse(BaseModel):
    filtered_id: str
    paragraph_id: str
    source_id: str
    过滤后内容: str
    相关度评分: Optional[float] = None
    过滤原因: Optional[str] = None
    过滤时间: Optional[str] = None


# ================================================================
# 事件
# ================================================================

class EventCreate(BaseModel):
    event_id: str
    filtered_id: Optional[str] = None
    事件类型: str
    事件触发词: Optional[str] = None
    事件描述: str
    论元JSON: Optional[str] = None
    发生时间: Optional[str] = None
    置信度: Optional[float] = None


class EventResponse(BaseModel):
    event_id: str
    filtered_id: Optional[str] = None
    事件类型: str
    事件触发词: Optional[str] = None
    事件描述: str
    论元JSON: Optional[str] = None
    发生时间: Optional[str] = None
    录入时间: Optional[str] = None
    置信度: Optional[float] = None


# ================================================================
# 证据
# ================================================================

class EvidenceResponse(BaseModel):
    evidence_id: str
    event_id: str
    filtered_id: Optional[str] = None
    来源文件: Optional[str] = None
    原文片段: str
    起始位置: Optional[int] = None
    结束位置: Optional[int] = None
    锚定时间: Optional[str] = None


# ================================================================
# 机理模板
# ================================================================

class MechanismTemplateResponse(BaseModel):
    template_id: str
    模板名称: str
    模板描述: Optional[str] = None
    前件条件JSON: Optional[str] = None
    后件结果JSON: Optional[str] = None
    物理约束: Optional[str] = None
    适用事件类型: Optional[str] = None


# ================================================================
# 事件关系
# ================================================================

class EventRelationResponse(BaseModel):
    relation_id: str
    source_event_id: str
    target_event_id: str
    关系类型: str
    关系描述: Optional[str] = None
    置信度: Optional[float] = None


# ================================================================
# 图谱
# ================================================================

class GraphNodeResponse(BaseModel):
    node_id: str
    节点名称: str
    节点类型: str
    节点属性JSON: Optional[str] = None
    来源event_id: Optional[str] = None
    创建时间: Optional[str] = None


class GraphLinkResponse(BaseModel):
    link_id: str
    source_node_id: str
    target_node_id: str
    边类型: str
    边属性JSON: Optional[str] = None
    来源relation_id: Optional[str] = None


class KGGraphResponse(BaseModel):
    """知识图谱完整响应 - 前端可视化用"""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    links: List[Dict[str, Any]] = Field(default_factory=list)
    stats: Dict[str, Any] = Field(default_factory=dict)


class KGEventDetailResponse(BaseModel):
    """图谱事件详情"""
    event: Dict[str, Any] = Field(default_factory=dict)
    evidence_list: List[Dict[str, Any]] = Field(default_factory=list)
    relations_as_source: List[Dict[str, Any]] = Field(default_factory=list)
    relations_as_target: List[Dict[str, Any]] = Field(default_factory=list)


# ================================================================
# 版本日志
# ================================================================

class VersionLogResponse(BaseModel):
    log_id: str
    实体类型: str
    实体ID: str
    操作类型: str
    旧值JSON: Optional[str] = None
    新值JSON: Optional[str] = None
    操作时间: Optional[str] = None
    操作说明: Optional[str] = None


# ================================================================
# 问答
# ================================================================

class QARequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题", min_length=1)


class QAResponse(BaseModel):
    """问答响应"""
    question: str
    answer: str
    answer_type: str = "图谱问答"
    related_events: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_sources: List[Dict[str, Any]] = Field(default_factory=list)
    maintenance_suggestion: Optional[Dict[str, Any]] = None
    subgraph: Optional[Dict[str, Any]] = None


class QASessionResponse(BaseModel):
    session_id: str
    会话标题: Optional[str] = None
    创建时间: Optional[str] = None
    更新时间: Optional[str] = None
    状态: Optional[str] = None


class QARecordResponse(BaseModel):
    record_id: str
    session_id: str
    用户问题: str
    模型回答: str
    检索证据JSON: Optional[str] = None
    引用来源JSON: Optional[str] = None
    创建时间: Optional[str] = None


# ================================================================
# 维修推荐
# ================================================================

class RecommendRequest(BaseModel):
    """维修方案推荐请求"""
    component: Optional[str] = Field(None, description="部件名称")
    fault_mode: Optional[str] = Field(None, description="故障模式")
    symptoms: Optional[List[str]] = Field(None, description="症状列表")


class RecommendResponse(BaseModel):
    component: Optional[str] = None
    fault_mode: Optional[str] = None
    symptoms: Optional[List[str]] = None
    matched_rules: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    estimated_downtime_hours: Optional[float] = None
    evidence_chain: List[Dict[str, Any]] = Field(default_factory=list)


class MaintenanceRuleResponse(BaseModel):
    rule_id: str
    规则名称: str
    故障模式: str
    适用条件: Optional[str] = None
    维修方案: str
    所需工具: Optional[str] = None
    所需材料: Optional[str] = None
    操作步骤JSON: Optional[str] = None
    参考来源: Optional[str] = None


# ================================================================
# 评价指标
# ================================================================

class MetricResponse(BaseModel):
    metric_id: str
    指标名称: str
    指标值: Optional[float] = None
    指标单位: Optional[str] = None
    评估时间: Optional[str] = None
    说明: Optional[str] = None


class MetricsSummaryResponse(BaseModel):
    evaluation_date: str
    total_metrics: int
    metrics: List[MetricResponse] = Field(default_factory=list)


# ================================================================
# 构建流程
# ================================================================

class BuildStepInfo(BaseModel):
    step_id: int
    name: str
    description: str


class BuildStepsResponse(BaseModel):
    total_steps: int
    steps: List[BuildStepInfo]


# ================================================================
# 导入
# ================================================================

class UploadedFileResponse(BaseModel):
    file_id: str
    文件名: str
    文件类型: str
    文件大小: Optional[int] = None
    上传时间: Optional[str] = None
    处理状态: str
    存储路径: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    result_id: str
    file_id: str
    分析类型: str
    分析结果JSON: Optional[str] = None
    是否加入图谱: bool = False
    分析时间: Optional[str] = None


# ================================================================
# 大模型
# ================================================================

class LLMRequest(BaseModel):
    """大模型调用请求"""
    prompt: str = Field(..., description="提示词")
    context: Optional[str] = Field(None, description="上下文")
    max_tokens: Optional[int] = Field(2048, description="最大输出token数")


class LLMResponse(BaseModel):
    """大模型调用响应"""
    answer: str
    model: str
    usage: Dict[str, Any] = Field(default_factory=dict)


# ================================================================
# 优势分析
# ================================================================

class AdvantageResponse(BaseModel):
    """系统优势分析响应"""
    categories: List[Dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
