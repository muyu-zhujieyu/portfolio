"""机理校验路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services import validation_service
from schemas import ValidationCheckRequest, ValidationCheckResponse, ValidationReportResponse

router = APIRouter(prefix="/api/validation", tags=["机理校验"])


@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    """获取所有机理模板"""
    return {"templates": validation_service.get_all_templates(db)}


@router.post("/check-chain", response_model=ValidationCheckResponse)
def check_chain(req: ValidationCheckRequest, db: Session = Depends(get_db)):
    """校验事件链是否匹配机理模板"""
    return validation_service.check_chain(db, req.event_ids)


@router.get("/report", response_model=ValidationReportResponse)
def get_validation_report(db: Session = Depends(get_db)):
    """获取机理校验完整报告"""
    return validation_service.get_validation_report(db)
