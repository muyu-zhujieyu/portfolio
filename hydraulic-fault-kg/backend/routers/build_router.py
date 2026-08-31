"""
知识图谱构建流程路由 - 管理端到端构建流水线

API:
  GET  /api/build/steps       获取构建步骤定义
  GET  /api/build/status      获取当前构建状态
  GET  /api/build/result      获取最新构建结果
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/build", tags=["知识图谱构建"])


@router.get("/steps")
def get_build_steps():
    """获取构建流水线 15 个步骤的定义"""
    steps = [
        {"步骤编号": 1,  "步骤名称": "文档解析",       "说明": "解析PDF/DOCX/TXT文档，提取文本内容"},
        {"步骤编号": 2,  "步骤名称": "段落清洗",       "说明": "去除无关格式、合并碎片、分句分段"},
        {"步骤编号": 3,  "步骤名称": "领域相关性过滤", "说明": "基于术语词典过滤非液压相关段落"},
        {"步骤编号": 4,  "步骤名称": "事件本体设计",   "说明": "定义事件类型、论元角色、关系类型"},
        {"步骤编号": 5,  "步骤名称": "事件抽取",       "说明": "从段落中抽取事件触发词、论元和关系"},
        {"步骤编号": 6,  "步骤名称": "证据span锚定",   "说明": "将抽取结果锚定回原文具体位置"},
        {"步骤编号": 7,  "步骤名称": "双时态记录",     "说明": "记录事件发生时间与录入时间"},
        {"步骤编号": 8,  "步骤名称": "机理模板校验",   "说明": "用液压机理模板验证事件链物理合理性"},
        {"步骤编号": 9,  "步骤名称": "事件归一与融合", "说明": "合并同义事件，去冗余，增量更新"},
        {"步骤编号": 10, "步骤名称": "图谱节点边生成", "说明": "生成事件节点、实体节点和关系边"},
        {"步骤编号": 11, "步骤名称": "SQLite入库",     "说明": "节点和边持久化存储"},
        {"步骤编号": 12, "步骤名称": "中文图谱展示",   "说明": "ECharts前端可视化展示图谱"},
        {"步骤编号": 13, "步骤名称": "大模型图谱问答", "说明": "基于图谱检索+大模型组织回答"},
        {"步骤编号": 14, "步骤名称": "维修方案推荐",   "说明": "基于事件链匹配维修规则推荐方案"},
        {"步骤编号": 15, "步骤名称": "构建质量评价",   "说明": "多维度评价指标计算与展示"},
    ]
    return {"总步骤数": len(steps), "构建步骤": steps}


@router.get("/status")
def get_build_status():
    """获取当前构建状态"""
    from database import get_all_tables, get_table_count
    tables = get_all_tables()
    return {
        "构建状态": "已初始化",
        "数据库路径": "backend/kg.db",
        "数据表数量": len(tables),
        "各表记录数": {t: get_table_count(t) for t in sorted(tables)}
    }


@router.get("/result")
def get_build_result():
    """获取最新构建结果摘要"""
    from database import fetch_all
    return {
        "来源资料数": len(fetch_all("SELECT * FROM sources")),
        "原始段落数": len(fetch_all("SELECT * FROM paragraphs")),
        "过滤段落数": len(fetch_all("SELECT * FROM filtered_paragraphs")),
        "事件数": len(fetch_all("SELECT * FROM events")),
        "证据数": len(fetch_all("SELECT * FROM evidence")),
        "机理模板数": len(fetch_all("SELECT * FROM mechanism_templates")),
        "事件关系数": len(fetch_all("SELECT * FROM event_relations")),
        "图谱节点数": len(fetch_all("SELECT * FROM graph_nodes")),
        "图谱边数": len(fetch_all("SELECT * FROM graph_links")),
        "维修规则数": len(fetch_all("SELECT * FROM maintenance_rules")),
        "评价指标数": len(fetch_all("SELECT * FROM metrics")),
    }
