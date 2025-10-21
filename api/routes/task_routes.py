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


@router.get("/{task_id}/linked-cycles")
async def get_task_linked_cycles(task_id: int, db: Session = Depends(get_db)):
    """Task에 연결된 Zephyr 테스트 사이클 목록 조회"""
    try:
        from models.database_models import TaskCycleLink, ZephyrTestCycle
        from sqlalchemy.orm import joinedload
        from sqlalchemy import and_
        
        # Task 존재 확인
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        # 연결된 사이클 조회
        active_links = db.query(TaskCycleLink).filter(
            and_(
                TaskCycleLink.task_id == task_id,
                TaskCycleLink.is_active == True
            )
        ).all()
        
        # 응답 데이터 구성
        result = []
        for link in active_links:
            # 외부 Zephyr ID를 사용하는 새로운 연결 방식
            if link.zephyr_cycle_external_id:
                # 외부 ID를 사용한 연결 (새로운 방식)
                cycle_data = {
                    "id": link.zephyr_cycle_external_id,  # 외부 Zephyr ID 사용
                    "zephyr_cycle_id": link.zephyr_cycle_external_id,
                    "cycle_name": link.cycle_name or f"Cycle {link.zephyr_cycle_external_id}",
                    "description": "외부 Zephyr 사이클",
                    "version": "N/A",
                    "environment": "N/A", 
                    "build": "N/A",
                    "status": "Connected",
                    "created_by": "N/A",
                    "assigned_to": "N/A",
                    "start_date": "N/A",
                    "end_date": "N/A",
                    "total_test_cases": 0,
                    "executed_test_cases": 0,
                    "passed_test_cases": 0,
                    "failed_test_cases": 0,
                    "blocked_test_cases": 0,
                    "created_at": "N/A",
                    "last_sync": "N/A",
                    # 연결 정보
                    "linked_by": link.linked_by or "N/A",
                    "link_reason": link.link_reason or "",
                    "linked_at": link.created_at.isoformat() if link.created_at else "N/A"
                }
                result.append(cycle_data)
            elif link.zephyr_cycle_id:
                # 기존 DB 연결 방식 (하위 호환성)
                cycle = db.query(ZephyrTestCycle).filter(ZephyrTestCycle.id == link.zephyr_cycle_id).first()
                
                if cycle:
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
                        "last_sync": cycle.last_sync.isoformat() if cycle.last_sync else "N/A",
                        # 연결 정보
                        "linked_by": link.linked_by or "N/A",
                        "link_reason": link.link_reason or "",
                        "linked_at": link.created_at.isoformat() if link.created_at else "N/A"
                    }
                    result.append(cycle_data)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"연결된 사이클 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결된 사이클 조회 실패: {str(e)}")


@router.post("/link-cycle", response_model=BaseResponse)
async def link_task_to_cycle(
    task_id: int = Query(..., description="Task ID"),
    cycle_id: str = Query(..., description="Cycle ID"),
    cycle_name: str = Query("", description="Cycle Name"),
    linked_by: str = Query("QA팀", description="연결한 사용자"),
    link_reason: str = Query("", description="연결 이유"),
    db: Session = Depends(get_db)
):
    """Task와 Zephyr 테스트 사이클 연결"""
    try:
        from models.database_models import TaskCycleLink, ZephyrTestCycle
        
        # Task 존재 확인
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        # 프론트엔드에서 전달받은 사이클 정보로 직접 연결 (데이터베이스 의존성 제거)
        logger.info(f"사이클 ID '{cycle_id}' (이름: '{cycle_name}') 직접 연결 시도...")
        
        # 이미 연결되어 있는지 확인 (Zephyr 사이클 ID로 직접 확인)
        existing_link = db.query(TaskCycleLink).filter(
            TaskCycleLink.task_id == task_id,
            TaskCycleLink.zephyr_cycle_external_id == cycle_id,
            TaskCycleLink.is_active == True
        ).first()
        
        if existing_link:
            raise HTTPException(status_code=400, detail="이미 연결된 사이클입니다.")
        
        # 새로운 연결 생성 (외부 Zephyr ID 직접 저장)
        new_link = TaskCycleLink(
            task_id=task_id,
            zephyr_cycle_id=None,  # 기존 DB 연결은 None으로 설정
            zephyr_cycle_external_id=cycle_id,  # 외부 Zephyr ID 직접 저장
            cycle_name=cycle_name or f"Cycle {cycle_id}",  # 사이클 이름 저장
            linked_by=linked_by,
            link_reason=link_reason,
            is_active=True
        )
        
        db.add(new_link)
        db.commit()
        db.refresh(new_link)
        
        return BaseResponse(
            success=True,
            message=f"Task '{task.jira_key}'와 Cycle '{cycle_name or cycle_id}'이(가) 성공적으로 연결되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Task-Cycle 연결 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task-Cycle 연결 실패: {str(e)}")


@router.delete("/{task_id}/unlink-cycle/{cycle_id}", response_model=BaseResponse)
async def unlink_task_from_cycle(
    task_id: int,
    cycle_id: str,
    db: Session = Depends(get_db)
):
    """Task와 Zephyr 테스트 사이클 연결 해제"""
    try:
        from models.database_models import TaskCycleLink, ZephyrTestCycle
        
        # Task 존재 확인
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        # 연결 정보 조회 (외부 ID 우선, 기존 DB ID 후순위)
        link = db.query(TaskCycleLink).filter(
            TaskCycleLink.task_id == task_id,
            TaskCycleLink.zephyr_cycle_external_id == cycle_id,
            TaskCycleLink.is_active == True
        ).first()
        
        # 외부 ID로 찾지 못한 경우 기존 DB ID로 시도
        if not link:
            try:
                cycle_id_int = int(cycle_id)
                link = db.query(TaskCycleLink).filter(
                    TaskCycleLink.task_id == task_id,
                    TaskCycleLink.zephyr_cycle_id == cycle_id_int,
                    TaskCycleLink.is_active == True
                ).first()
            except ValueError:
                pass  # 정수 변환 실패 시 무시
        
        if not link:
            raise HTTPException(status_code=404, detail="연결된 사이클을 찾을 수 없습니다.")
        
        # 사이클 이름 결정
        cycle_name = link.cycle_name or f"ID {cycle_id}"
        
        # 기존 DB 사이클인 경우 추가 정보 조회
        if link.zephyr_cycle_id:
            zephyr_cycle = db.query(ZephyrTestCycle).filter(
                ZephyrTestCycle.id == link.zephyr_cycle_id
            ).first()
            if zephyr_cycle:
                cycle_name = zephyr_cycle.cycle_name
        
        # 연결 해제 (소프트 삭제 - is_active를 False로 설정)
        link.is_active = False
        db.commit()
        
        return BaseResponse(
            success=True,
            message=f"Task '{task.jira_key}'와 Cycle '{cycle_name}'의 연결이 해제되었습니다."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Task-Cycle 연결 해제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Task-Cycle 연결 해제 실패: {str(e)}")


@router.get("/{task_id}/available-cycles")
async def get_available_cycles_for_task(task_id: int, db: Session = Depends(get_db)):
    """Task에 연결 가능한 Zephyr 테스트 사이클 목록 조회 (데이터베이스에 동기화된 사이클에서 조회)"""
    try:
        from models.database_models import TaskCycleLink, ZephyrTestCycle
        from sqlalchemy import and_, not_
        
        # Task 존재 확인
        task = task_service.get_task_by_id(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
        
        # 이미 연결된 사이클 ID 목록 조회 (외부 ID와 내부 ID 모두 고려)
        linked_external_cycle_ids = set()
        linked_internal_cycle_ids = set()
        
        active_links = db.query(TaskCycleLink).filter(
            and_(
                TaskCycleLink.task_id == task_id,
                TaskCycleLink.is_active == True
            )
        ).all()
        
        for link in active_links:
            if link.zephyr_cycle_external_id:
                linked_external_cycle_ids.add(str(link.zephyr_cycle_external_id))
            if link.zephyr_cycle_id:
                linked_internal_cycle_ids.add(link.zephyr_cycle_id)
        
        # 데이터베이스에 동기화된 모든 사이클 조회 (연결되지 않은 것만)
        query = db.query(ZephyrTestCycle)
        
        # 내부 ID로 연결된 사이클 제외
        if linked_internal_cycle_ids:
            query = query.filter(not_(ZephyrTestCycle.id.in_(linked_internal_cycle_ids)))
        
        available_cycles = query.all()
        
        # 응답 데이터 구성
        result = []
        for cycle in available_cycles:
            try:
                cycle_id = str(cycle.id)
                
                # 외부 ID로도 연결 확인 (Zephyr Scale의 실제 ID와 비교)
                # cycle.zephyr_cycle_id는 Zephyr Scale의 실제 사이클 ID일 수 있음
                if cycle.zephyr_cycle_id and str(cycle.zephyr_cycle_id) in linked_external_cycle_ids:
                    continue
                
                # ZephyrProject 정보 조회
                project_key = "N/A"
                if cycle.zephyr_project:
                    project_key = cycle.zephyr_project.project_key
                
                cycle_data = {
                    "id": cycle_id,
                    "zephyr_cycle_id": cycle.zephyr_cycle_id,
                    "cycle_name": cycle.cycle_name,
                    "description": cycle.description or "",
                    "version": cycle.version or "N/A",
                    "environment": cycle.environment or "N/A",
                    "build": cycle.build or "N/A",
                    "status": cycle.status,
                    "project_key": project_key,
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
                
            except Exception as e:
                logger.warning(f"테스트 사이클 처리 중 오류: {str(e)}")
                continue
        
        # 생성일 기준으로 최신순 정렬
        result.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"Task {task_id}에 연결 가능한 동기화된 사이클 개수: {len(result)}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"연결 가능한 사이클 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"연결 가능한 사이클 조회 실패: {str(e)}")
