"""
프로젝트 관리 API 라우트
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.pydantic_models import (
    ProjectCreate, ProjectUpdate, ProjectResponse, 
    BaseResponse, DeleteResponse
)
from services.project_service import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """프로젝트 목록 조회"""
    projects = project_service.get_projects(db, is_active=is_active, skip=skip, limit=limit)
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """프로젝트 상세 조회"""
    project = project_service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로젝트를 찾을 수 없습니다."
        )
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate, db: Session = Depends(get_db)):
    """프로젝트 생성"""
    try:
        project = project_service.create_project(db, project_data)
        return project
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로젝트 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, 
    project_data: ProjectUpdate, 
    db: Session = Depends(get_db)
):
    """프로젝트 업데이트"""
    project = project_service.update_project(db, project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로젝트를 찾을 수 없습니다."
        )
    return project


@router.delete("/{project_id}", response_model=DeleteResponse)
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """프로젝트 삭제"""
    success = project_service.delete_project(db, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로젝트를 찾을 수 없습니다."
        )
    
    return DeleteResponse(
        success=True,
        message="프로젝트가 성공적으로 삭제되었습니다.",
        deleted_count=1
    )


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: int, db: Session = Depends(get_db)):
    """프로젝트 통계 조회"""
    stats = project_service.get_project_stats(db, project_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로젝트를 찾을 수 없습니다."
        )
    return stats


@router.post("/{project_id}/sync", response_model=BaseResponse)
async def update_project_sync(project_id: int, db: Session = Depends(get_db)):
    """프로젝트 동기화 시간 업데이트"""
    project = project_service.update_last_sync(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="프로젝트를 찾을 수 없습니다."
        )
    
    return BaseResponse(
        success=True,
        message="프로젝트 동기화 시간이 업데이트되었습니다."
    )
