"""
작업 관리 API 라우트
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.pydantic_models import (
    TaskResponse, TaskCreate, TaskUpdate, DashboardStats,
    MemoRequest, MemoResponse, DeleteResponse, QAStatusResponse,
    BaseResponse
)
from services.task_service import task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    project_id: Optional[int] = Query(None, description="프로젝트 ID 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(1000, ge=1, le=5000, description="가져올 항목 수"),
    db: Session = Depends(get_db)
):
    """작업 목록 조회"""
    try:
        tasks = task_service.get_tasks(
            db=db,
            project_id=project_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return tasks
    except Exception as e:
        logger.error(f"작업 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 목록 조회 실패: {str(e)}")




@router.delete("/reset", response_model=DeleteResponse)
async def reset_all_tasks(db: Session = Depends(get_db)):
    """모든 작업 데이터 초기화"""
    try:
        result = task_service.reset_all_tasks(db)
        
        return DeleteResponse(
            success=True,
            message=result["message"],
            deleted_count=result["deleted_tasks"]
        )
    except Exception as e:
        logger.error(f"데이터 초기화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"데이터 초기화 실패: {str(e)}")


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """작업 상세 조회"""
    try:
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 조회 실패: {str(e)}")


@router.post("/", response_model=TaskResponse)
async def create_task(task_data: TaskCreate, db: Session = Depends(get_db)):
    """작업 생성"""
    try:
        # 중복 Jira 키 확인
        existing_task = task_service.get_task_by_jira_key(db, task_data.jira_key)
        if existing_task:
            raise HTTPException(
                status_code=400,
                detail=f"Jira 키 '{task_data.jira_key}'가 이미 존재합니다."
            )
        
        task = task_service.create_task(db, task_data)
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 생성 실패: {str(e)}")


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):
    """작업 업데이트"""
    try:
        task = task_service.update_task(db, task_id, task_data)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 업데이트 실패: {str(e)}")


@router.delete("/{task_id}", response_model=DeleteResponse)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """작업 삭제"""
    try:
        # 작업 정보 조회 (삭제 전)
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        task_info = {
            "id": task.id,
            "jira_key": task.jira_key,
            "title": task.title
        }
        
        # 작업 삭제
        success = task_service.delete_task(db, task_id)
        if not success:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        return DeleteResponse(
            success=True,
            message="작업이 삭제되었습니다.",
            deleted_count=1,
            deleted_items=[task_info]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"작업 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"작업 삭제 실패: {str(e)}")


@router.put("/{task_id}/qa-status", response_model=QAStatusResponse)
async def update_qa_status(
    task_id: int,
    qa_status: str = Query(..., pattern="^(미시작|QA 시작|QA 진행중|QA 완료)$"),
    db: Session = Depends(get_db)
):
    """QA 상태 업데이트 - qa_status 필드만 업데이트"""
    try:
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        old_qa_status = task.qa_status
        updated_task = task_service.update_qa_status(db, task_id, qa_status)
        
        return QAStatusResponse(
            success=True,
            message=f"QA 상태가 '{qa_status}'로 업데이트되었습니다.",
            task_id=task_id,
            jira_key=updated_task.jira_key,
            old_status=old_qa_status,
            new_status=qa_status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QA 상태 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QA 상태 업데이트 실패: {str(e)}")


@router.put("/{task_id}/memo", response_model=MemoResponse)
async def update_task_memo(
    task_id: int,
    memo_request: MemoRequest,
    db: Session = Depends(get_db)
):
    """작업 메모 업데이트"""
    try:
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        updated_task = task_service.update_memo(db, task_id, memo_request.memo)
        
        return MemoResponse(
            success=True,
            message="메모가 업데이트되었습니다.",
            task_id=task_id,
            jira_key=updated_task.jira_key,
            memo=memo_request.memo,
            updated_at=updated_task.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메모 업데이트 실패: {str(e)}")


@router.get("/{task_id}/memo", response_model=MemoResponse)
async def get_task_memo(task_id: int, db: Session = Depends(get_db)):
    """작업 메모 조회"""
    try:
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        return MemoResponse(
            success=True,
            message="메모 조회 성공",
            task_id=task_id,
            jira_key=task.jira_key,
            memo=task.memo or "",
            updated_at=task.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"메모 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메모 조회 실패: {str(e)}")


@router.get("/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """대시보드 통계 조회"""
    try:
        stats = task_service.get_dashboard_stats(db)
        return DashboardStats(**stats)
    except Exception as e:
        logger.error(f"대시보드 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")
