"""
QA 요청서 API 라우트
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from services.qa_request_service import qa_request_service
from models.pydantic_models import (
    QARequestCreate, QARequestUpdate, QARequestResponse,
    QARequestListResponse, QARequestStatusUpdate, BaseResponse
)

router = APIRouter(prefix="/qa-requests", tags=["QA 요청서"])


@router.post("/", response_model=QARequestResponse)
async def create_qa_request(
    qa_request_data: QARequestCreate,
    db: Session = Depends(get_db)
):
    """QA 요청서 생성"""
    try:
        result = qa_request_service.create_qa_request(db, qa_request_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 생성 실패: {str(e)}")


@router.get("/", response_model=QARequestListResponse)
async def get_qa_requests(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[str] = Query(None, description="상태 필터"),
    platform: Optional[str] = Query(None, description="플랫폼 필터"),
    assignee: Optional[str] = Query(None, description="담당자 필터"),
    db: Session = Depends(get_db)
):
    """QA 요청서 목록 조회"""
    try:
        result = qa_request_service.get_qa_requests(
            db, page=page, size=size, status=status, platform=platform, assignee=assignee
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 목록 조회 실패: {str(e)}")


@router.get("/{qa_request_id}", response_model=QARequestResponse)
async def get_qa_request(
    qa_request_id: int,
    db: Session = Depends(get_db)
):
    """QA 요청서 상세 조회"""
    try:
        result = qa_request_service.get_qa_request(db, qa_request_id)
        if not result:
            raise HTTPException(status_code=404, detail="QA 요청서를 찾을 수 없습니다")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 조회 실패: {str(e)}")


@router.put("/{qa_request_id}", response_model=QARequestResponse)
async def update_qa_request(
    qa_request_id: int,
    update_data: QARequestUpdate,
    db: Session = Depends(get_db)
):
    """QA 요청서 업데이트"""
    try:
        result = qa_request_service.update_qa_request(db, qa_request_id, update_data)
        if not result:
            raise HTTPException(status_code=404, detail="QA 요청서를 찾을 수 없습니다")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 업데이트 실패: {str(e)}")


@router.patch("/{qa_request_id}/status", response_model=QARequestResponse)
async def update_qa_request_status(
    qa_request_id: int,
    status_data: QARequestStatusUpdate,
    db: Session = Depends(get_db)
):
    """QA 요청서 상태 업데이트"""
    try:
        result = qa_request_service.update_qa_request_status(db, qa_request_id, status_data)
        if not result:
            raise HTTPException(status_code=404, detail="QA 요청서를 찾을 수 없습니다")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 상태 업데이트 실패: {str(e)}")


@router.delete("/{qa_request_id}", response_model=BaseResponse)
async def delete_qa_request(
    qa_request_id: int,
    db: Session = Depends(get_db)
):
    """QA 요청서 삭제"""
    try:
        success = qa_request_service.delete_qa_request(db, qa_request_id)
        if not success:
            raise HTTPException(status_code=404, detail="QA 요청서를 찾을 수 없습니다")
        
        return BaseResponse(
            success=True,
            message="QA 요청서가 성공적으로 삭제되었습니다"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 삭제 실패: {str(e)}")


@router.get("/stats/summary")
async def get_qa_request_stats(db: Session = Depends(get_db)):
    """QA 요청서 통계"""
    try:
        stats = qa_request_service.get_qa_request_stats(db)
        return {
            "success": True,
            "message": "QA 요청서 통계 조회 성공",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA 요청서 통계 조회 실패: {str(e)}")
