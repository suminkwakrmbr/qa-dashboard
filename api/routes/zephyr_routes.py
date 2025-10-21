"""
Zephyr 연동 API 라우트
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from models.pydantic_models import (
    BaseResponse, ZephyrConnectionCreate, ZephyrConnectionUpdate, ZephyrConnectionResponse,
    ZephyrConnectionTest, ZephyrProjectResponse, ZephyrTestCaseResponse,
    ZephyrTestExecutionResponse, ZephyrSyncRequest, ZephyrSyncResponse,
    ZephyrSyncStatus, ZephyrSyncHistoryResponse, ZephyrDashboardStats
)
from services.zephyr_service import zephyr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zephyr", tags=["zephyr"])


# Zephyr 연결 설정 관련 엔드포인트
@router.post("/connection", response_model=ZephyrConnectionResponse)
async def create_zephyr_connection(
    connection_data: ZephyrConnectionCreate,
    db: Session = Depends(get_db)
):
    """Zephyr 연결 설정 생성"""
    try:
        connection = zephyr_service.create_connection(db, connection_data)
        return connection
    except Exception as e:
        logger.error(f"Zephyr 연결 설정 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 설정 생성 실패: {str(e)}")


@router.get("/connection", response_model=ZephyrConnectionResponse)
async def get_zephyr_connection(db: Session = Depends(get_db)):
    """현재 Zephyr 연결 설정 조회"""
    try:
        connection = zephyr_service.get_connection(db)
        if not connection:
            raise HTTPException(status_code=404, detail="연결 설정을 찾을 수 없습니다.")
        return ZephyrConnectionResponse.from_orm(connection)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 연결 설정 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 설정 조회 실패: {str(e)}")


@router.put("/connection/{connection_id}", response_model=ZephyrConnectionResponse)
async def update_zephyr_connection(
    connection_id: int,
    connection_data: ZephyrConnectionUpdate,
    db: Session = Depends(get_db)
):
    """Zephyr 연결 설정 업데이트"""
    try:
        connection = zephyr_service.update_connection(db, connection_id, connection_data)
        return connection
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Zephyr 연결 설정 업데이트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 설정 업데이트 실패: {str(e)}")


@router.post("/connection/test", response_model=ZephyrConnectionTest)
async def test_zephyr_connection(db: Session = Depends(get_db)):
    """Zephyr 연결 테스트"""
    try:
        result = zephyr_service.test_connection(db)
        return ZephyrConnectionTest(
            success=result["success"],
            message=result["message"],
            server_url=result.get("server_url"),
            username=result.get("username"),
            connection_time=result.get("connection_time")
        )
    except Exception as e:
        logger.error(f"Zephyr 연결 테스트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 테스트 실패: {str(e)}")


# Zephyr 프로젝트 관련 엔드포인트
@router.get("/projects", response_model=List[ZephyrProjectResponse])
async def get_zephyr_projects(db: Session = Depends(get_db)):
    """Zephyr 프로젝트 목록 조회"""
    try:
        projects = zephyr_service.get_projects(db)
        return projects
    except Exception as e:
        logger.error(f"Zephyr 프로젝트 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 조회 실패: {str(e)}")


@router.post("/projects/{project_id}/sync", response_model=ZephyrSyncResponse)
async def sync_zephyr_project(
    project_id: int,
    sync_request: ZephyrSyncRequest,
    db: Session = Depends(get_db)
):
    """Zephyr 프로젝트 동기화"""
    try:
        result = zephyr_service.sync_project(db, project_id, sync_request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Zephyr 프로젝트 동기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 동기화 실패: {str(e)}")


@router.get("/projects/{project_id}", response_model=ZephyrProjectResponse)
async def get_zephyr_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 프로젝트 상세 조회"""
    try:
        from models.database_models import ZephyrProject
        
        project = db.query(ZephyrProject).filter(
            ZephyrProject.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
        
        return ZephyrProjectResponse.from_orm(project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 프로젝트 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 조회 실패: {str(e)}")


# Zephyr 테스트 케이스 관련 엔드포인트
@router.get("/projects/{project_id}/test-cases", response_model=List[ZephyrTestCaseResponse])
async def get_zephyr_test_cases(
    project_id: int,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10000, ge=1, le=10000, description="가져올 항목 수"),
    status: Optional[str] = Query(None, description="상태 필터"),
    priority: Optional[str] = Query(None, description="우선순위 필터"),
    db: Session = Depends(get_db)
):
    """Zephyr 테스트 케이스 목록 조회"""
    try:
        from models.database_models import ZephyrTestCase
        
        query = db.query(ZephyrTestCase).filter(
            ZephyrTestCase.zephyr_project_id == project_id
        )
        
        # 필터 적용
        if status:
            query = query.filter(ZephyrTestCase.status == status)
        if priority:
            query = query.filter(ZephyrTestCase.priority == priority)
        
        # 페이지네이션
        test_cases = query.offset(skip).limit(limit).all()
        
        return [ZephyrTestCaseResponse.from_orm(tc) for tc in test_cases]
    except Exception as e:
        logger.error(f"Zephyr 테스트 케이스 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 케이스 조회 실패: {str(e)}")


@router.get("/test-cases/{test_case_id}", response_model=ZephyrTestCaseResponse)
async def get_zephyr_test_case(
    test_case_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 테스트 케이스 상세 조회"""
    try:
        from models.database_models import ZephyrTestCase
        
        test_case = db.query(ZephyrTestCase).filter(
            ZephyrTestCase.id == test_case_id
        ).first()
        
        if not test_case:
            raise HTTPException(status_code=404, detail="테스트 케이스를 찾을 수 없습니다.")
        
        return ZephyrTestCaseResponse.from_orm(test_case)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 테스트 케이스 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 케이스 조회 실패: {str(e)}")


# Zephyr 테스트 실행 관련 엔드포인트
@router.get("/test-cases/{test_case_id}/executions", response_model=List[ZephyrTestExecutionResponse])
async def get_zephyr_test_executions(
    test_case_id: int,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=500, description="가져올 항목 수"),
    status: Optional[str] = Query(None, description="실행 상태 필터"),
    db: Session = Depends(get_db)
):
    """Zephyr 테스트 실행 결과 목록 조회"""
    try:
        from models.database_models import ZephyrTestExecution
        
        query = db.query(ZephyrTestExecution).filter(
            ZephyrTestExecution.test_case_id == test_case_id
        )
        
        # 필터 적용
        if status:
            query = query.filter(ZephyrTestExecution.execution_status == status)
        
        # 최신 순으로 정렬
        executions = query.order_by(
            ZephyrTestExecution.executed_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [ZephyrTestExecutionResponse.from_orm(exec) for exec in executions]
    except Exception as e:
        logger.error(f"Zephyr 테스트 실행 결과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"실행 결과 조회 실패: {str(e)}")


@router.get("/executions/{execution_id}", response_model=ZephyrTestExecutionResponse)
async def get_zephyr_test_execution(
    execution_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 테스트 실행 결과 상세 조회"""
    try:
        from models.database_models import ZephyrTestExecution
        
        execution = db.query(ZephyrTestExecution).filter(
            ZephyrTestExecution.id == execution_id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="실행 결과를 찾을 수 없습니다.")
        
        return ZephyrTestExecutionResponse.from_orm(execution)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 테스트 실행 결과 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"실행 결과 조회 실패: {str(e)}")


# Zephyr 동기화 이력 관련 엔드포인트
@router.get("/sync-history", response_model=List[ZephyrSyncHistoryResponse])
async def get_zephyr_sync_history(
    project_id: Optional[int] = Query(None, description="프로젝트 ID 필터"),
    sync_direction: Optional[str] = Query(None, description="동기화 방향 필터"),
    sync_status: Optional[str] = Query(None, description="동기화 상태 필터"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=500, description="가져올 항목 수"),
    db: Session = Depends(get_db)
):
    """Zephyr 동기화 이력 조회"""
    try:
        from models.database_models import ZephyrSyncHistory
        
        query = db.query(ZephyrSyncHistory)
        
        # 필터 적용
        if project_id:
            query = query.filter(ZephyrSyncHistory.zephyr_project_id == project_id)
        if sync_direction:
            query = query.filter(ZephyrSyncHistory.sync_direction == sync_direction)
        if sync_status:
            query = query.filter(ZephyrSyncHistory.sync_status == sync_status)
        
        # 최신 순으로 정렬
        histories = query.order_by(
            ZephyrSyncHistory.started_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [ZephyrSyncHistoryResponse.from_orm(history) for history in histories]
    except Exception as e:
        logger.error(f"Zephyr 동기화 이력 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"동기화 이력 조회 실패: {str(e)}")


@router.get("/sync-history/{sync_id}", response_model=ZephyrSyncHistoryResponse)
async def get_zephyr_sync_history_detail(
    sync_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 동기화 이력 상세 조회"""
    try:
        from models.database_models import ZephyrSyncHistory
        
        history = db.query(ZephyrSyncHistory).filter(
            ZephyrSyncHistory.id == sync_id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="동기화 이력을 찾을 수 없습니다.")
        
        return ZephyrSyncHistoryResponse.from_orm(history)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 동기화 이력 상세 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"동기화 이력 조회 실패: {str(e)}")


@router.get("/sync-status/{sync_id}", response_model=ZephyrSyncStatus)
async def get_zephyr_sync_status(
    sync_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 동기화 상태 조회"""
    try:
        from models.database_models import ZephyrSyncHistory
        
        history = db.query(ZephyrSyncHistory).filter(
            ZephyrSyncHistory.id == sync_id
        ).first()
        
        if not history:
            raise HTTPException(status_code=404, detail="동기화 이력을 찾을 수 없습니다.")
        
        # 진행률 계산
        progress = 0
        if history.total_items > 0:
            progress = int((history.processed_items / history.total_items) * 100)
        
        return ZephyrSyncStatus(
            sync_id=sync_id,
            status=history.sync_status,
            progress=progress,
            message=history.error_message or "동기화 진행 중",
            total_items=history.total_items,
            processed_items=history.processed_items,
            success_items=history.success_items,
            failed_items=history.failed_items,
            start_time=history.started_at,
            end_time=history.completed_at,
            error_message=history.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Zephyr 동기화 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"동기화 상태 조회 실패: {str(e)}")


# Zephyr 통계 관련 엔드포인트
@router.get("/stats/dashboard", response_model=ZephyrDashboardStats)
async def get_zephyr_dashboard_stats(db: Session = Depends(get_db)):
    """Zephyr 대시보드 통계 조회"""
    try:
        stats = zephyr_service.get_dashboard_stats(db)
        return stats
    except Exception as e:
        logger.error(f"Zephyr 대시보드 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


# 유틸리티 엔드포인트
@router.delete("/projects/{project_id}/reset", response_model=BaseResponse)
async def reset_zephyr_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Zephyr 프로젝트 데이터 초기화"""
    try:
        from models.database_models import ZephyrProject, ZephyrTestCase, ZephyrTestExecution, ZephyrSyncHistory
        
        # 프로젝트 확인
        project = db.query(ZephyrProject).filter(
            ZephyrProject.id == project_id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")
        
        # 관련 데이터 삭제
        # 실행 결과 삭제
        db.query(ZephyrTestExecution).filter(
            ZephyrTestExecution.test_case_id.in_(
                db.query(ZephyrTestCase.id).filter(
                    ZephyrTestCase.zephyr_project_id == project_id
                )
            )
        ).delete(synchronize_session=False)
        
        # 테스트 케이스 삭제
        deleted_test_cases = db.query(ZephyrTestCase).filter(
            ZephyrTestCase.zephyr_project_id == project_id
        ).count()
        
        db.query(ZephyrTestCase).filter(
            ZephyrTestCase.zephyr_project_id == project_id
        ).delete()
        
        # 동기화 이력 삭제
        db.query(ZephyrSyncHistory).filter(
            ZephyrSyncHistory.zephyr_project_id == project_id
        ).delete()
        
        # 프로젝트 상태 초기화
        project.is_synced = False
        project.sync_status = "not_synced"
        project.test_case_count = 0
        project.last_sync = None
        project.sync_error = None
        
        db.commit()
        
        return BaseResponse(
            success=True,
            message=f"프로젝트 '{project.project_name}' 데이터가 초기화되었습니다. (테스트 케이스 {deleted_test_cases}개 삭제)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Zephyr 프로젝트 초기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 초기화 실패: {str(e)}")


@router.get("/cycles/available-for-task/{task_id}")
async def get_available_cycles_for_task(
    task_id: int,
    project_key: str = Query(..., description="프로젝트 키"),
    db: Session = Depends(get_db)
):
    """Task에 연결 가능한 Zephyr 테스트 사이클 목록 조회"""
    try:
        from models.database_models import ZephyrTestCycle, ZephyrProject, TaskCycleLink
        from sqlalchemy.orm import joinedload
        
        # 프로젝트 키로 Zephyr 프로젝트 조회
        zephyr_project = db.query(ZephyrProject).filter(
            ZephyrProject.project_key == project_key
        ).first()
        
        if not zephyr_project:
            # 프로젝트가 없으면 빈 배열 반환
            return []
        
        # 해당 프로젝트의 모든 사이클 조회
        all_cycles = db.query(ZephyrTestCycle).filter(
            ZephyrTestCycle.zephyr_project_id == zephyr_project.id
        ).all()
        
        # 이미 연결된 사이클 ID 목록 조회
        linked_cycle_ids = db.query(TaskCycleLink.zephyr_cycle_id).filter(
            TaskCycleLink.task_id == task_id,
            TaskCycleLink.is_active == True
        ).all()
        
        linked_cycle_ids = [link[0] for link in linked_cycle_ids]
        
        # 연결되지 않은 사이클만 필터링
        available_cycles = [
            cycle for cycle in all_cycles 
            if cycle.id not in linked_cycle_ids
        ]
        
        # 응답 데이터 구성
        result = []
        for cycle in available_cycles:
            cycle_data = {
                "id": str(cycle.id),
                "zephyr_cycle_id": cycle.zephyr_cycle_id,
                "cycle_name": cycle.cycle_name,
                "description": cycle.description or "",
                "version": cycle.version or "N/A",
                "environment": cycle.environment or "N/A",
                "build": cycle.build or "N/A",
                "status": cycle.status,
                "created_by": cycle.created_by or "N/A",
                "assigned_to": cycle.assigned_to or "N/A",
                "start_date": cycle.start_date.isoformat() if cycle.start_date else "N/A",
                "end_date": cycle.end_date.isoformat() if cycle.end_date else "N/A",
                "total_test_cases": cycle.total_test_cases,
                "executed_test_cases": cycle.executed_test_cases,
                "passed_test_cases": cycle.passed_test_cases,
                "failed_test_cases": cycle.failed_test_cases,
                "blocked_test_cases": cycle.blocked_test_cases,
                "created_at": cycle.created_at.isoformat() if cycle.created_at else "N/A",
                "last_sync": cycle.last_sync.isoformat() if cycle.last_sync else "N/A"
            }
            result.append(cycle_data)
        
        return result
        
    except Exception as e:
        logger.error(f"연결 가능한 사이클 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 가능한 사이클 조회 실패: {str(e)}")


@router.get("/cycles")
async def get_cycles_for_project(
    project_key: str = Query(..., description="프로젝트 키"),
    db: Session = Depends(get_db)
):
    """프로젝트의 모든 Zephyr 테스트 사이클 목록 조회"""
    try:
        from models.database_models import ZephyrTestCycle, ZephyrProject
        
        # 프로젝트 키로 Zephyr 프로젝트 조회
        zephyr_project = db.query(ZephyrProject).filter(
            ZephyrProject.project_key == project_key
        ).first()
        
        if not zephyr_project:
            # 프로젝트가 없으면 빈 배열 반환
            return []
        
        # 해당 프로젝트의 모든 사이클 조회
        cycles = db.query(ZephyrTestCycle).filter(
            ZephyrTestCycle.zephyr_project_id == zephyr_project.id
        ).all()
        
        # 응답 데이터 구성
        result = []
        for cycle in cycles:
            cycle_data = {
                "id": str(cycle.id),
                "zephyr_cycle_id": cycle.zephyr_cycle_id,
                "cycle_name": cycle.cycle_name,
                "description": cycle.description or "",
                "version": cycle.version or "N/A",
                "environment": cycle.environment or "N/A",
                "build": cycle.build or "N/A",
                "status": cycle.status,
                "created_by": cycle.created_by or "N/A",
                "assigned_to": cycle.assigned_to or "N/A",
                "start_date": cycle.start_date.isoformat() if cycle.start_date else "N/A",
                "end_date": cycle.end_date.isoformat() if cycle.end_date else "N/A",
                "total_test_cases": cycle.total_test_cases,
                "executed_test_cases": cycle.executed_test_cases,
                "passed_test_cases": cycle.passed_test_cases,
                "failed_test_cases": cycle.failed_test_cases,
                "blocked_test_cases": cycle.blocked_test_cases,
                "created_at": cycle.created_at.isoformat() if cycle.created_at else "N/A",
                "last_sync": cycle.last_sync.isoformat() if cycle.last_sync else "N/A"
            }
            result.append(cycle_data)
        
        return result
        
    except Exception as e:
        logger.error(f"프로젝트 사이클 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"프로젝트 사이클 조회 실패: {str(e)}")


@router.get("/debug/cycles-count")
async def debug_cycles_count(db: Session = Depends(get_db)):
    """디버깅: 전체 사이클 개수 및 상세 정보 조회"""
    try:
        from models.database_models import ZephyrTestCycle, ZephyrProject, TaskCycleLink
        
        # 전체 사이클 개수
        total_cycles = db.query(ZephyrTestCycle).count()
        
        # 전체 프로젝트 개수
        total_projects = db.query(ZephyrProject).count()
        
        # 전체 연결 개수
        total_links = db.query(TaskCycleLink).count()
        
        # 각 프로젝트별 사이클 개수
        projects = db.query(ZephyrProject).all()
        project_details = []
        for project in projects:
            cycle_count = db.query(ZephyrTestCycle).filter(
                ZephyrTestCycle.zephyr_project_id == project.id
            ).count()
            project_details.append({
                "project_id": project.id,
                "project_key": project.project_key,
                "project_name": project.project_name,
                "cycle_count": cycle_count
            })
        
        # 모든 사이클 목록 (최대 10개)
        cycles = db.query(ZephyrTestCycle).limit(10).all()
        cycle_details = []
        for cycle in cycles:
            cycle_details.append({
                "id": cycle.id,
                "cycle_name": cycle.cycle_name,
                "project_id": cycle.zephyr_project_id,
                "status": cycle.status
            })
        
        return {
            "total_cycles": total_cycles,
            "total_projects": total_projects,
            "total_links": total_links,
            "project_details": project_details,
            "cycle_samples": cycle_details
        }
        
    except Exception as e:
        logger.error(f"디버깅 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"디버깅 정보 조회 실패: {str(e)}")


@router.get("/debug/create-test-data", response_model=BaseResponse)
async def create_test_data(
    project_key: str = Query("KAN", description="프로젝트 키"),
    db: Session = Depends(get_db)
):
    """디버깅: 테스트용 Zephyr 데이터 생성"""
    try:
        from models.database_models import ZephyrProject, ZephyrTestCycle
        from datetime import datetime, timedelta
        
        # 프로젝트 키로 Zephyr 프로젝트 찾기 또는 생성
        zephyr_project = db.query(ZephyrProject).filter(
            ZephyrProject.project_key == project_key
        ).first()
        
        if not zephyr_project:
            # 새 Zephyr 프로젝트 생성
            zephyr_project = ZephyrProject(
                zephyr_project_id=f"zephyr_{project_key.lower()}",
                project_key=project_key,
                project_name=f"{project_key} 프로젝트",
                description=f"{project_key} 프로젝트의 테스트 관리",
                is_synced=True,
                sync_status="completed",
                test_case_count=0,
                last_sync=datetime.now()
            )
            db.add(zephyr_project)
            db.commit()
            db.refresh(zephyr_project)
        
        # 기존 테스트 사이클 개수 확인
        existing_cycles = db.query(ZephyrTestCycle).filter(
            ZephyrTestCycle.zephyr_project_id == zephyr_project.id
        ).count()
        
        if existing_cycles == 0:
            # 테스트용 사이클들 생성
            test_cycles = [
                {
                    "cycle_name": "Sprint 1 테스트",
                    "description": "첫 번째 스프린트 테스트 사이클",
                    "version": "v1.0",
                    "environment": "Development",
                    "build": "build-001",
                    "status": "In Progress"
                },
                {
                    "cycle_name": "Sprint 2 테스트", 
                    "description": "두 번째 스프린트 테스트 사이클",
                    "version": "v1.1",
                    "environment": "Staging",
                    "build": "build-002",
                    "status": "Not Started"
                },
                {
                    "cycle_name": "회귀 테스트",
                    "description": "전체 기능 회귀 테스트",
                    "version": "v1.0",
                    "environment": "Production",
                    "build": "build-003",
                    "status": "Completed"
                }
            ]
            
            created_cycles = []
            for i, cycle_data in enumerate(test_cycles):
                cycle = ZephyrTestCycle(
                    zephyr_cycle_id=f"cycle_{project_key.lower()}_{i+1}",
                    zephyr_project_id=zephyr_project.id,
                    cycle_name=cycle_data["cycle_name"],
                    description=cycle_data["description"],
                    version=cycle_data["version"],
                    environment=cycle_data["environment"],
                    build=cycle_data["build"],
                    start_date=datetime.now() + timedelta(days=i*7),
                    end_date=datetime.now() + timedelta(days=(i+1)*7),
                    status=cycle_data["status"],
                    created_by="QA팀",
                    assigned_to="QA팀",
                    total_test_cases=10 + i*5,
                    executed_test_cases=i*3,
                    passed_test_cases=i*2,
                    failed_test_cases=i,
                    blocked_test_cases=0,
                    created_at=datetime.now(),
                    last_sync=datetime.now()
                )
                db.add(cycle)
                created_cycles.append(cycle_data["cycle_name"])
            
            db.commit()
            
            return BaseResponse(
                success=True,
                message=f"프로젝트 '{project_key}'에 {len(created_cycles)}개의 테스트 사이클이 생성되었습니다: {', '.join(created_cycles)}"
            )
        else:
            return BaseResponse(
                success=True,
                message=f"프로젝트 '{project_key}'에 이미 {existing_cycles}개의 사이클이 있습니다."
            )
        
    except Exception as e:
        db.rollback()
        logger.error(f"테스트 데이터 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 데이터 생성 실패: {str(e)}")


@router.post("/sync-cycles/{project_key}", response_model=BaseResponse)
async def sync_test_cycles_from_zephyr(
    project_key: str,
    db: Session = Depends(get_db)
):
    """Zephyr Scale API에서 실제 테스트 사이클 데이터를 동기화"""
    try:
        result = zephyr_service.sync_test_cycles_from_zephyr(db, project_key)
        
        return BaseResponse(
            success=result["success"],
            message=result["message"]
        )
        
    except Exception as e:
        logger.error(f"Zephyr 테스트 사이클 동기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 사이클 동기화 실패: {str(e)}")


@router.delete("/reset-all", response_model=BaseResponse)
async def reset_all_zephyr_data(db: Session = Depends(get_db)):
    """모든 Zephyr 데이터 초기화"""
    try:
        from models.database_models import (
            ZephyrConnection, ZephyrProject, ZephyrTestCase, 
            ZephyrTestExecution, ZephyrSyncHistory, TaskCycleLink, ZephyrTestCycle
        )
        
        # 모든 데이터 개수 조회
        total_executions = db.query(ZephyrTestExecution).count()
        total_test_cases = db.query(ZephyrTestCase).count()
        total_test_cycles = db.query(ZephyrTestCycle).count()
        total_sync_histories = db.query(ZephyrSyncHistory).count()
        total_projects = db.query(ZephyrProject).count()
        total_connections = db.query(ZephyrConnection).count()
        total_task_cycle_links = db.query(TaskCycleLink).count()
        
        # 모든 데이터 삭제 (외래키 순서 고려)
        db.query(TaskCycleLink).delete()  # Task-Cycle 연결 먼저 삭제
        db.query(ZephyrTestExecution).delete()
        db.query(ZephyrTestCase).delete()
        db.query(ZephyrTestCycle).delete()  # 테스트 사이클 삭제 추가
        db.query(ZephyrSyncHistory).delete()
        db.query(ZephyrProject).delete()
        db.query(ZephyrConnection).delete()
        
        db.commit()
        
        total_deleted = (
            total_executions + total_test_cases + total_test_cycles + total_sync_histories + 
            total_projects + total_connections + total_task_cycle_links
        )
        
        return BaseResponse(
            success=True,
            message=f"모든 Zephyr 데이터가 초기화되었습니다. (총 {total_deleted}개 항목 삭제)"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Zephyr 전체 데이터 초기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"전체 데이터 초기화 실패: {str(e)}")
