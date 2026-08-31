"""知识图谱查询路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import kg_service
from schemas import KGGraphResponse, KGEventDetailResponse, KGEvidenceResponse, KGChainResponse

router = APIRouter(prefix="/api/kg", tags=["知识图谱"])


@router.get("", response_model=KGGraphResponse)
def get_full_graph(db: Session = Depends(get_db)):
    """获取完整知识图谱（ECharts graph 格式）"""
    return kg_service.get_kg_graph(db)


@router.get("/nodes")
def get_nodes(db: Session = Depends(get_db)):
    """获取所有图谱节点"""
    graph = kg_service.get_kg_graph(db)
    return {"nodes": graph["nodes"]}


@router.get("/edges")
def get_edges(db: Session = Depends(get_db)):
    """获取所有图谱边"""
    graph = kg_service.get_kg_graph(db)
    return {"links": graph["links"]}


@router.get("/event/{event_id}", response_model=KGEventDetailResponse)
def get_event_detail(event_id: str, db: Session = Depends(get_db)):
    """获取事件详情（含证据和关系）"""
    return kg_service.get_event_detail(db, event_id)


@router.get("/evidence/{event_id}", response_model=KGEvidenceResponse)
def get_event_evidence(event_id: str, db: Session = Depends(get_db)):
    """获取某事件的证据锚定信息"""
    return kg_service.get_evidence_for_event(db, event_id)


@router.get("/chain/{template_id}", response_model=KGChainResponse)
def get_chain_by_template(template_id: str, db: Session = Depends(get_db)):
    """按机理模板ID获取事件演化链"""
    return kg_service.get_chain_by_template(db, template_id)
