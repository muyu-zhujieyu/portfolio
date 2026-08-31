"""
构建质量评价路由 - 管理构建质量评价指标

API:
  GET  /api/metrics         获取全部构建质量评价指标
  GET  /api/metrics/{id}    获取单条指标详情
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["构建质量评价"])


@router.get("")
def get_metrics():
    """获取全部构建质量评价指标"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM metrics ORDER BY metric_id")
    evaluated = [r for r in rows if r.get("指标值") is not None]
    return {
        "evaluation_date": "待评估",
        "total_metrics": len(rows),
        "evaluated_count": len(evaluated),
        "metrics": rows
    }


@router.get("/{metric_id}")
def get_metric(metric_id: str):
    """获取单条评价指标详情"""
    from database import fetch_one
    row = fetch_one("SELECT * FROM metrics WHERE metric_id = ?", (metric_id,))
    if row is None:
        return {"错误": f"指标 {metric_id} 不存在"}
    return row
