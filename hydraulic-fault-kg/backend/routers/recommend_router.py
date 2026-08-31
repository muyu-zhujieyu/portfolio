"""
维修方案推荐路由 - 基于故障模式、部件、症状推荐维修方案

API:
  POST /api/recommend           根据故障信息推荐维修方案
  GET  /api/recommend/rules     获取所有维修规则
  GET  /api/recommend/rules/{id}获取单条维修规则详情
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, List

from services.recommend_service import recommend_service

router = APIRouter(prefix="/api/recommend", tags=["维修方案推荐"])


class RecommendRequestModel(BaseModel):
    """维修推荐请求体"""
    部件: Optional[str] = Field(None, description="部件名称，如：液压泵、溢流阀、过滤器")
    故障模式: Optional[str] = Field(None, description="故障模式，如：内泄漏、过滤器堵塞、阀芯卡滞")
    异常状态列表: Optional[List[str]] = Field(None, description="异常状态列表，如：压力下降、油温升高")


# ================================================================
# POST /api/recommend - 核心推荐接口
# ================================================================

@router.post("")
def recommend(req: RecommendRequestModel):
    """根据故障信息推荐维修方案

    推荐算法:
      优先级分数 = 症状匹配度×0.4 + 机理模板匹配度×0.3
                 + 证据可靠度×0.2 + 风险等级权重×0.1

    支持 6 类核心故障:
      - 内泄漏: 推荐检查密封件、更换密封组件、复测系统压力
      - 过滤器堵塞: 推荐清洗过滤器、更换滤芯、检查吸油管路
      - 阀芯卡滞: 推荐清洗阀芯、检查污染物、更换液压油
      - 冷却器效率下降: 推荐检查冷却器、清理散热通道、监测油温
      - 蓄能器预充压力不足: 推荐检测预充压力、补充氮气、更换蓄能器
      - 溢流阀异常: 推荐调整溢流阀、检查阀芯磨损、复测系统压力

    返回字段:
      - 可能故障、命中机理模板、匹配事件链
      - 推荐维修动作、注意事项
      - 优先级分数、风险等级、推荐理由
      - 支撑证据
      - 预计停机时间、是否需要人工复核
    """
    result = recommend_service.recommend(
        component=req.部件,
        fault_mode=req.故障模式,
        symptoms=req.异常状态列表,
    )
    return result


# ================================================================
# GET /api/recommend/rules - 获取所有维修规则
# ================================================================

@router.get("/rules")
def list_rules():
    """获取所有维修规则列表

    返回所有已注册的维修规则（包括内置核心规则和数据库规则）。
    """
    from database import fetch_all
    rows = fetch_all("SELECT * FROM maintenance_rules ORDER BY rule_id")

    # 添加内置规则标记
    builtin_keys = set(recommend_service.CORE_MAINTENANCE_RULES.keys())
    rules_list = []
    for r in rows:
        d = dict(r)
        fm = d.get("故障模式", "")
        if fm in builtin_keys:
            d["来源"] = "内置核心维修规则"
        else:
            d["来源"] = "数据库维修规则"
        rules_list.append(d)

    return {
        "总数": len(rules_list),
        "内置核心规则数": len(builtin_keys),
        "维修规则列表": rules_list
    }


# ================================================================
# GET /api/recommend/rules/{id} - 获取单条规则详情
# ================================================================

@router.get("/rules/{rule_id}")
def get_rule(rule_id: str):
    """获取单条维修规则详情"""
    from database import fetch_one
    row = fetch_one("SELECT * FROM maintenance_rules WHERE rule_id = ?", (rule_id,))
    if row is None:
        return {"错误": f"维修规则 {rule_id} 不存在"}
    return dict(row)
