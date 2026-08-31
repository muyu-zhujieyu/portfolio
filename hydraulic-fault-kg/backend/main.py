"""
液压故障演化过程的机理约束事件知识图谱与大模型问答系统
FastAPI 后端入口

系统主流程：
  文档解析 → 段落清洗 → 领域过滤 → 事件抽取 → 证据锚定 →
  双时态记录 → 机理模板校验 → 事件归一与增量融合 →
  图谱节点边生成 → SQLite入库 → 中文知识图谱展示 →
  大模型图谱问答 → 维修方案推荐 → 后台管理与构建质量评价

大模型不能直接编造事实，必须基于知识图谱、事件链、证据span、
机理模板和维修规则组织回答。
"""
import sys
import os

# 确保 backend 目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_all_tables, get_table_count
from schemas import HealthResponse

# 导入所有路由
from routers.source_router import router as source_router
from routers.extraction_router import router as extraction_router
from routers.build_router import router as build_router
from routers.graph_router import router as graph_router
from routers.qa_router import router as qa_router
from routers.llm_router import router as llm_router
from routers.recommend_router import router as recommend_router
from routers.admin_router import router as admin_router
from routers.metrics_router import router as metrics_router
from routers.advantage_router import router as advantage_router
from routers.import_router import router as import_router
from routers.sample_analysis_router import router as sample_analysis_router
from routers.pipeline_router import router as pipeline_router
from routers.pipeline_audit_router import router as pipeline_audit_router
from routers.dashboard_router import router as dashboard_router

# ================================================================
# FastAPI 应用实例
# ================================================================

app = FastAPI(
    title="液压故障演化过程的机理约束事件知识图谱与大模型问答系统",
    description=(
        "围绕液压系统故障演化过程，构建机理约束的事件知识图谱平台。\n\n"
        "核心思想：事件化建模 + 机理约束 + 证据可追溯 + "
        "双时态增量融合 + 构建质量评价。\n\n"
        "大模型回答基于知识图谱、事件链、证据span和维修规则，不编造事实。"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ================================================================
# 启动事件
# ================================================================

@app.on_event("startup")
def startup():
    """启动时自动初始化数据库"""
    print("=" * 60)
    print("  液压故障演化事件知识图谱与大模型问答系统")
    print("  Hydraulic Fault KG & Intelligent QA Backend")
    print("=" * 60)

    # 初始化数据库（创建表）
    init_db()

    # 检查数据库状态
    tables = get_all_tables()
    print(f"\n  数据库路径: backend/kg.db")
    print(f"  数据表数量: {len(tables)}")
    for t in tables:
        count = get_table_count(t)
        print(f"    - {t}: {count} 行")

    print(f"\n  API 文档: http://127.0.0.1:8000/docs")
    print(f"  健康检查: http://127.0.0.1:8000/api/health")
    print("=" * 60)


@app.on_event("shutdown")
def shutdown():
    """关闭时的清理工作"""
    from database import close_connection
    close_connection()
    print("  后端服务已停止")


# ================================================================
# CORS 中间件
# ================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# 注册路由
# ================================================================

app.include_router(source_router)
app.include_router(extraction_router)
app.include_router(build_router)
app.include_router(graph_router)
app.include_router(qa_router)
app.include_router(llm_router)
app.include_router(recommend_router)
app.include_router(admin_router)
app.include_router(metrics_router)
app.include_router(advantage_router)
app.include_router(import_router)
app.include_router(sample_analysis_router)
app.include_router(pipeline_router)
app.include_router(pipeline_audit_router)
app.include_router(dashboard_router)


@app.get("/api/dashboard/summary_legacy", tags=["系统"])
def dashboard_summary():
    """首页统计摘要"""
    from database import get_all_tables, get_table_count
    tables = get_all_tables()
    counts = {t: get_table_count(t) for t in sorted(tables)}
    import json, os
    # 从 registry 读来源数
    reg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "source_registry.json"
    )
    src_count = 0
    if os.path.exists(reg_path):
        with open(reg_path, encoding="utf-8") as f:
            src_count = len(json.load(f).get("sources", []))

    return {
        "公开资料": src_count or counts.get("sources", 0),
        "液压段落": counts.get("filtered_paragraphs", 0),
        "原始抽取事件数": counts.get("events", 0),
        "归一融合后事件数": counts.get("events", 0),  # 简化：events表已是融合后
        "证据数量": counts.get("evidence", 0),
        "机理模板": counts.get("mechanism_templates", 0),
        "图谱节点": counts.get("graph_nodes", 0),
        "图谱边": counts.get("graph_links", 0),
        "问答记录": counts.get("qa_records", 0),
        "说明": "融合后事件经过同义归一和重复合并，因此数量可能低于原始抽取事件。图谱节点为归一后的可视化节点，少于事件数是正常现象。",
    }


# ================================================================
# 健康检查接口
# ================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["系统"])
def health_check():
    """系统健康检查 - 返回中文状态信息"""
    return HealthResponse(
        状态="正常",
        系统名称="液压故障演化过程的机理约束事件知识图谱与大模型问答系统",
        说明="后端服务已启动"
    )


@app.get("/api/health/detail", tags=["系统"])
def health_check_detail():
    """详细健康检查 - 包含数据库状态"""
    tables = get_all_tables()
    return {
        "状态": "正常",
        "系统名称": "液压故障演化过程的机理约束事件知识图谱与大模型问答系统",
        "数据库": {
            "路径": "backend/kg.db",
            "数据表数量": len(tables),
            "数据表列表": tables,
            "各表行数": {t: get_table_count(t) for t in tables}
        }
    }


# ================================================================
# 知识图谱总览接口（/api/kg）
# ================================================================

@app.get("/api/kg", tags=["知识图谱"])
def get_kg_overview():
    """获取 ECharts 可视化知识图谱数据（中文节点+中文边+中文图例）

    此路由位于 /api/kg，与 /api/graph 并行，
    直接返回 ECharts 可用的 nodes/links/categories 格式。
    """
    import json, os

    graph_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "data", "graph"
    )
    nodes_path = os.path.join(graph_dir, "nodes.json")
    links_path = os.path.join(graph_dir, "links.json")

    nodes = []
    links = []
    if os.path.exists(nodes_path):
        with open(nodes_path, encoding="utf-8") as f:
            nodes = json.load(f)
    if os.path.exists(links_path):
        with open(links_path, encoding="utf-8") as f:
            links = json.load(f)

    categories = [
        {"name": "故障模式", "itemStyle": {"color": "#E74C3C"}},
        {"name": "异常状态", "itemStyle": {"color": "#F39C12"}},
        {"name": "检测方式", "itemStyle": {"color": "#3498DB"}},
        {"name": "维修动作", "itemStyle": {"color": "#2ECC71"}},
        {"name": "部件",     "itemStyle": {"color": "#9B59B6"}},
        {"name": "机理模板", "itemStyle": {"color": "#1ABC9C"}},
    ]

    return {
        "图谱名称": "液压故障演化事件知识图谱",
        "节点总数": len(nodes),
        "边总数": len(links),
        "nodes": nodes,
        "links": links,
        "categories": categories,
    }


# ================================================================
# 入口
# ================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
