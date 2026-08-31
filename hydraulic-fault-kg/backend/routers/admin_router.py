"""
后台管理路由 - 管理所有数据实体的查看和操作

API:
  GET  /api/admin/events       管理事件列表
  GET  /api/admin/evidence     管理证据列表
  GET  /api/admin/templates    管理机理模板列表
  GET  /api/admin/version-logs 查看版本日志
  GET  /api/admin/summary      数据库概览
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["后台管理"])


@router.get("/events")
def admin_events():
    """获取所有事件列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM events ORDER BY 录入时间 DESC LIMIT 200")
    return {"总数": len(rows), "事件列表": rows}


@router.get("/evidence")
def admin_evidence():
    """获取所有证据列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM evidence ORDER BY 锚定时间 DESC LIMIT 200")
    return {"总数": len(rows), "证据列表": rows}


@router.get("/templates")
def admin_templates():
    """获取所有机理模板列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM mechanism_templates ORDER BY 创建时间 DESC")
    return {"总数": len(rows), "模板列表": rows}


@router.get("/version-logs")
def admin_version_logs():
    """查看版本日志"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM version_logs ORDER BY 操作时间 DESC LIMIT 200")
    return {"总数": len(rows), "版本日志列表": rows}


@router.get("/relations")
def admin_relations():
    """获取所有事件关系列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM event_relations ORDER BY 置信度 DESC LIMIT 200")
    return {"总数": len(rows), "关系列表": rows}


@router.get("/qa-records")
def admin_qa_records():
    """获取大模型问答记录"""
    from database import fetch_all
    records = fetch_all("SELECT * FROM qa_records ORDER BY 创建时间 DESC LIMIT 200")
    sessions = fetch_all("SELECT * FROM qa_sessions ORDER BY 更新时间 DESC LIMIT 100")
    return {
        "问答记录总数": len(records),
        "会话总数": len(sessions),
        "问答记录": records,
        "会话列表": sessions,
    }


@router.get("/summary")
def admin_summary():
    """获取数据库概览（各表行数统计）"""
    from database import get_all_tables, get_table_count
    tables = get_all_tables()
    return {
        "数据库表数量": len(tables),
        "各表行数": {t: get_table_count(t) for t in sorted(tables)}
    }
