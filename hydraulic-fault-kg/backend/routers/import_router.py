"""
资料导入路由 - 可选子功能：文件上传、分析、增量加入图谱

注意:
  资料导入是可选增量功能，不是知识图谱构建主流程的前提。
  主流程基于 data/raw_sources/ 中的公开维修手册、论文、教材、说明书和案例。

API:
  POST /api/import/upload             上传文件（图片/文档/表格）
  POST /api/import/analyze/{file_id}  分析已上传的文件
  GET  /api/import/result/{file_id}   查看分析结果
  POST /api/import/add-to-kg/{file_id}将分析结果增量加入知识图谱
  GET  /api/import/files              获取已上传文件列表
  GET  /api/import/results            获取分析结果列表
"""
import os
from typing import Optional, Dict
from fastapi import APIRouter, UploadFile, File, Form

from services.import_service import import_service

router = APIRouter(prefix="/api/import", tags=["资料导入"])


# ================================================================
# POST /api/import/upload - 上传文件
# ================================================================

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件（图片/文档/表格）

    支持的文件类型:
      - 图片: png, jpg, jpeg（当前使用模拟OCR）
      - 文档: pdf, docx, txt, md
      - 表格: csv, xlsx

    文件大小限制: 最大 50 MB

    上传后文件保存在 uploads 目录下对应类型子目录，
    并返回文件编号用于后续分析和加入图谱。

    注意：此功能是可选增量功能，不是知识图谱构建主流程的前提。
    """
    # 读取文件内容
    content = await file.read()

    if not content:
        return {"状态": "失败", "错误": "上传的文件为空"}

    filename = file.filename or "unknown_file"

    result = import_service.handle_upload(content, filename)
    return result


# ================================================================
# POST /api/import/analyze/{file_id} - 分析文件
# ================================================================

@router.post("/analyze/{file_id}")
def analyze_file(file_id: str):
    """分析已上传的文件（点击"开始分析"时调用）

    分析逻辑:
      - 文档(txt/md/docx/pdf): 解析文本→清洗段落→领域过滤→事件抽取→证据锚定→机理模板匹配
      - 表格(csv/xlsx): 读取数据→识别压力/流量/油温/振动/噪声字段→趋势检测→状态事件生成
      - 图片(png/jpg): 模拟OCR→液压场景推断→事件抽取

    返回完整的分析结果，包括:
      - 解析文本、清洗段落、液压相关段落
      - 抽取事件、证据span
      - 异常指标、匹配机理模板、生成故障链
      - 维修建议、置信度、风险等级
    """
    result = import_service.analyze_file(file_id)
    return result


# ================================================================
# GET /api/import/result/{file_id} - 查看分析结果
# ================================================================

@router.get("/result/{file_id}")
def get_analysis_result(file_id: str):
    """查看指定文件的分析结果

    返回字段:
      - 文件信息（名称、类型、大小、上传时间）
      - 解析文本、清洗段落、液压相关段落
      - 抽取事件、证据span
      - 异常指标、匹配机理模板、生成故障链
      - 维修建议、置信度、风险等级
      - 是否已入图谱
    """
    result = import_service.get_analysis_result(file_id)
    return result


# ================================================================
# POST /api/import/add-to-kg/{file_id} - 加入知识图谱
# ================================================================

@router.post("/add-to-kg/{file_id}")
def add_to_knowledge_graph(file_id: str):
    """将该文件分析出的事件、证据作为增量知识加入已有知识图谱

    增量加入的内容:
      - 抽取的事件 → events 表
      - 证据 span → evidence 表
      - 事件关系 → event_relations 表
      - 图谱节点 → graph_nodes 表

    注意:
      1. 此操作为增量更新，不会覆盖已有图谱数据
      2. 只有已完成分析的文件才能加入图谱
      3. 加入后可在 GET /api/kg 查看包含新数据的完整图谱
      4. 此功能是可选增量功能，主流程不依赖此功能
    """
    result = import_service.add_to_graph(file_id)
    return result


# ================================================================
# GET /api/import/files - 文件列表
# ================================================================

@router.get("/files")
def list_uploaded_files():
    """获取已上传文件列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM uploaded_files ORDER BY 上传时间 DESC")
    return {
        "总数": len(rows),
        "说明": "资料导入是可选增量功能，不是知识图谱构建主流程的前提。",
        "文件列表": [dict(r) for r in rows]
    }


# ================================================================
# GET /api/import/results - 分析结果列表
# ================================================================

@router.get("/results")
def list_analysis_results():
    """获取所有分析结果列表"""
    from database import fetch_all
    rows = fetch_all("SELECT * FROM analysis_results ORDER BY 分析时间 DESC")
    return {
        "总数": len(rows),
        "分析结果列表": [dict(r) for r in rows]
    }
