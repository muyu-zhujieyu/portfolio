# -*- coding: utf-8 -*-
"""
解析诊断与审计路由 - 审计三元组抽取/融合/证据/图谱贡献
"""
from fastapi import APIRouter
from services.pipeline_audit_service import pipeline_audit

router = APIRouter(prefix="/api/pipeline", tags=["解析诊断"])


@router.get("/audit")
def get_audit():
    """获取完整三元组抽取审计报告

    指标包括:
      - 原始三元组数量
      - 融合三元组数量
      - 证据覆盖率
      - 模板命中/补全统计
      - 各资料来源贡献
    """
    return pipeline_audit.run_audit()


@router.get("/source-contribution")
def get_source_contributions():
    """获取每份资料的三元组贡献明细"""
    return {"各资料贡献明细": pipeline_audit.get_source_contributions()}


@router.get("/filter-debug")
def get_filter_debug():
    """获取被过滤段落及原因"""
    return pipeline_audit.get_filter_debug()
