"""
Jira 관련 API 라우트
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from core.database import get_db
from models.pydantic_models import (
    JiraConnectionTest, JiraProjectsResponse, JiraIssuesResponse,
    SyncRequest, SyncResponse, SyncStatus
)
from services.jira_service import jira_service
from services.task_service import task_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jira", tags=["jira"])

# 동기화 상태 저장용 딕셔너리
sync_status_store = {}


@router.post("/test-connection", response_model=JiraConnectionTest)
async def test_jira_connection():
    """Jira 연결 테스트"""
    try:
        success, message = jira_service.test_connection()
        
        return JiraConnectionTest(
            success=success,
            message=message,
            server=jira_service.server_url if success else None,
            username=jira_service.username if success else None
        )
    except Exception as e:
        logger.error(f"Jira 연결 테스트 오류: {str(e)}")
        return JiraConnectionTest(
            success=False,
            message=f"연결 테스트 오류: {str(e)}"
        )


@router.get("/projects", response_model=JiraProjectsResponse)
async def get_jira_projects(include_issue_count: bool = False):
    """Jira 프로젝트 목록 조회 (선택적으로 이슈 수 포함)"""
    try:
        projects = jira_service.get_projects()
        
        # 각 프로젝트의 이슈 수 확인 (요청 시에만, 처음 20개만)
        enhanced_projects = []
        for i, project in enumerate(projects):
            project_key = project.get('key', '')
            
            # include_issue_count가 True이고 처음 20개 프로젝트만 이슈 수 조회
            if include_issue_count and i < 20 and project_key:
                try:
                    issue_count = jira_service.get_project_issue_count(project_key)
                    project["issue_count"] = issue_count
                    project["is_active"] = issue_count > 0
                    
                    if issue_count > 0:
                        logger.info(f"프로젝트 {project_key}: {issue_count}개 이슈 확인됨")
                except Exception as count_error:
                    logger.warning(f"프로젝트 {project_key} 이슈 수 조회 실패: {str(count_error)}")
                    project["issue_count"] = None
                    project["is_active"] = None
            else:
                # 기본적으로는 이슈 수를 조회하지 않음
                project["issue_count"] = None
                project["is_active"] = None
            
            # API v3 응답 구조에 맞게 필드 정리
            if 'self' in project:
                del project['self']  # self URL은 응답에서 제거
            
            enhanced_projects.append(project)
        
        # include_issue_count가 True인 경우에만 활성 프로젝트 기준으로 정렬
        if include_issue_count:
            enhanced_projects.sort(key=lambda x: (
                x.get("is_active", False) is False,
                -(x.get("issue_count", 0) or 0),
                x.get("key", "")
            ))
        else:
            # 기본적으로는 프로젝트 키 순으로 정렬
            enhanced_projects.sort(key=lambda x: x.get("key", ""))
        
        return JiraProjectsResponse(
            success=True,
            projects=enhanced_projects,
            count=len(enhanced_projects)
        )
    except Exception as e:
        logger.error(f"Jira 프로젝트 조회 오류: {str(e)}")
        return JiraProjectsResponse(
            success=False,
            message=f"프로젝트 조회 오류: {str(e)}",
            projects=[],
            count=0
        )


@router.get("/projects/{project_key}/issues")
async def get_jira_project_issues(project_key: str, limit: int = None, quick: bool = False):
    """Jira 프로젝트의 이슈 목록 가져오기 (빠른 모드 지원)"""
    try:
        issues = jira_service.get_issues(project_key, limit=limit, quick_mode=quick)
        
        if issues:
            logger.info(f"프로젝트 {project_key}: {len(issues)}개 이슈 조회 성공")
            return {
                "success": True,
                "project_key": project_key,
                "issues": issues,
                "count": len(issues),
                "message": f"{len(issues)}개 이슈 조회 성공"
            }
        else:
            logger.warning(f"프로젝트 {project_key}: 이슈가 없거나 조회 실패")
            
            # 더 구체적인 에러 메시지 제공
            error_message = _get_detailed_error_message(project_key)
            
            return {
                "success": False,
                "project_key": project_key,
                "issues": [],
                "count": 0,
                "message": error_message
            }
    except Exception as e:
        logger.error(f"프로젝트 {project_key} 이슈 조회 오류: {str(e)}")
        return {
            "success": False,
            "project_key": project_key,
            "issues": [],
            "count": 0,
            "message": f"이슈 조회 오류: {str(e)}"
        }


def _get_detailed_error_message(project_key: str) -> str:
    """프로젝트 키에 대한 상세한 에러 메시지 생성"""
    # 프로젝트 존재 여부 확인
    project_exists = jira_service._check_project_exists(project_key)
    
    if not project_exists:
        return (
            f"프로젝트 '{project_key}'에 접근할 수 없습니다.\n\n"
            "가능한 원인:\n"
            "• 프로젝트가 비활성화되었거나 삭제됨 (HTTP 410)\n"
            "• 프로젝트 키가 잘못됨\n"
            "• 해당 프로젝트에 대한 접근 권한이 없음\n\n"
            "해결 방법:\n"
            "1. Jira 관리자에게 프로젝트 상태 확인 요청\n"
            "2. 올바른 프로젝트 키 확인\n"
            "3. 프로젝트 접근 권한 요청"
        )
    else:
        return (
            f"프로젝트 '{project_key}'의 이슈를 조회할 수 없습니다.\n\n"
            "가능한 원인:\n"
            "• 프로젝트에 이슈가 없음\n"
            "• JQL 쿼리 권한 제한\n"
            "• 네트워크 또는 서버 문제\n\n"
            "해결 방법:\n"
            "1. Jira 웹에서 직접 프로젝트 확인\n"
            "2. 다른 프로젝트로 테스트\n"
            "3. 네트워크 연결 상태 확인"
        )


@router.post("/sync/{project_key}", response_model=SyncResponse)
async def sync_jira_project(
    project_key: str,
    background_tasks: BackgroundTasks,
    sync_request: Optional[SyncRequest] = None,
    db: Session = Depends(get_db)
):
    """Jira 프로젝트 동기화"""
    try:
        selected_issues = None
        if sync_request and sync_request.selected_issues:
            selected_issues = sync_request.selected_issues
        
        # 동기화 상태 초기화
        sync_status_store[project_key] = SyncStatus(
            status="starting",
            progress=0,
            message="동기화를 시작합니다...",
            total_issues=0,
            processed_issues=0,
            selected_issues=selected_issues
        )
        
        # 백그라운드 작업으로 동기화 실행
        background_tasks.add_task(
            background_sync_project,
            project_key,
            db,
            selected_issues
        )
        
        if selected_issues:
            return SyncResponse(
                success=True,
                message=f"프로젝트 {project_key}의 선택된 {len(selected_issues)}개 이슈 동기화를 시작했습니다.",
                project_key=project_key,
                selected_issues_count=len(selected_issues)
            )
        else:
            return SyncResponse(
                success=True,
                message=f"프로젝트 {project_key} 전체 동기화를 시작했습니다.",
                project_key=project_key
            )
    except Exception as e:
        logger.error(f"동기화 시작 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"동기화 시작 실패: {str(e)}")


@router.get("/sync-status/{project_key}", response_model=SyncStatus)
async def get_sync_status(project_key: str):
    """동기화 상태 조회"""
    if project_key in sync_status_store:
        return sync_status_store[project_key]
    else:
        return SyncStatus(
            status="not_found",
            message="동기화 상태를 찾을 수 없습니다."
        )


@router.get("/diagnose/{project_key}")
async def diagnose_project(project_key: str):
    """프로젝트 문제 진단 및 해결책 제시"""
    try:
        diagnosis = jira_service.diagnose_project_issue(project_key)
        
        return {
            "success": True,
            "project_key": project_key,
            "diagnosis": diagnosis,
            "timestamp": "2025-09-25T15:44:00+09:00"
        }
    except Exception as e:
        logger.error(f"프로젝트 {project_key} 진단 오류: {str(e)}")
        return {
            "success": False,
            "project_key": project_key,
            "error": f"진단 중 오류 발생: {str(e)}",
            "timestamp": "2025-09-25T15:44:00+09:00"
        }


@router.get("/alternatives/{project_key}")
async def get_alternative_projects(project_key: str):
    """실패한 프로젝트의 대안 프로젝트 찾기"""
    try:
        alternatives = jira_service.get_alternative_projects(project_key)
        
        return {
            "success": True,
            "original_project": project_key,
            "alternatives": alternatives,
            "count": len(alternatives),
            "message": f"'{project_key}'와 유사한 {len(alternatives)}개의 대안 프로젝트를 찾았습니다." if alternatives else f"'{project_key}'와 유사한 프로젝트를 찾을 수 없습니다."
        }
    except Exception as e:
        logger.error(f"대안 프로젝트 검색 오류: {str(e)}")
        return {
            "success": False,
            "original_project": project_key,
            "alternatives": [],
            "count": 0,
            "error": f"대안 프로젝트 검색 중 오류 발생: {str(e)}"
        }


async def background_sync_project(
    project_key: str,
    db: Session,
    selected_issues: Optional[List[str]] = None
):
    """백그라운드 동기화 함수 - 새로운 DB 세션 사용"""
    from core.database import SessionLocal
    
    # 백그라운드 작업용 새로운 DB 세션 생성
    db_session = SessionLocal()
    
    try:
        # 상태 업데이트: 연결 중
        sync_status_store[project_key].status = "connecting"
        sync_status_store[project_key].progress = 10
        sync_status_store[project_key].message = "Jira 서버에 연결 중..."
        
        # Jira 연결 테스트
        success, message = jira_service.test_connection()
        if not success:
            raise Exception(f"Jira 연결 실패: {message}")
        
        # 상태 업데이트: 이슈 조회 중
        sync_status_store[project_key].status = "fetching_issues"
        sync_status_store[project_key].progress = 30
        sync_status_store[project_key].message = "Jira 이슈 목록 조회 중..."
        
        # 이슈 목록 가져오기
        if selected_issues:
            # 선택된 이슈만 처리 - 개별 이슈 조회로 최적화
            issues = []
            sync_status_store[project_key].total_issues = len(selected_issues)
            
            for i, issue_key in enumerate(selected_issues):
                try:
                    # 진행률 업데이트
                    progress = 30 + int((i / len(selected_issues)) * 10)  # 30-40% 구간
                    sync_status_store[project_key].progress = progress
                    sync_status_store[project_key].message = f"선택된 이슈 조회 중: {issue_key} ({i+1}/{len(selected_issues)})"
                    
                    issue = jira_service.get_issue(issue_key)
                    if issue:
                        issues.append(issue)
                        logger.info(f"선택된 이슈 조회 성공: {issue_key}")
                    else:
                        logger.warning(f"이슈 {issue_key} 조회 실패: 이슈를 찾을 수 없음")
                except Exception as e:
                    logger.warning(f"이슈 {issue_key} 조회 실패: {str(e)}")
            
            logger.info(f"선택된 이슈 {len(selected_issues)}개 중 {len(issues)}개 조회 성공")
        else:
            # 전체 이슈 조회 (무제한)
            logger.info(f"프로젝트 {project_key} 전체 이슈 조회 시작 (무제한)")
            issues = jira_service.get_issues(project_key)  # limit 제거
            logger.info(f"프로젝트 {project_key} 전체 이슈 {len(issues)}개 조회 완료")
        
        if not issues:
            raise Exception(f"조회된 이슈가 없습니다. 프로젝트 {project_key}에 이슈가 있는지 확인해주세요.")
        
        # 총 이슈 수 업데이트
        sync_status_store[project_key].total_issues = len(issues)
        sync_status_store[project_key].progress = 40
        sync_status_store[project_key].message = f"{len(issues)}개 이슈 조회 완료, 동기화 시작..."
        
        # 상태 업데이트: 처리 중
        sync_status_store[project_key].status = "processing"
        
        # 동기화 실행 (진행률 콜백 포함)
        def progress_callback(processed: int, total: int, current_issue: str = ""):
            """동기화 진행률 콜백"""
            if project_key in sync_status_store:
                progress = 40 + int((processed / total) * 50) if total > 0 else 90
                sync_status_store[project_key].progress = progress
                sync_status_store[project_key].processed_issues = processed
                
                if current_issue:
                    sync_status_store[project_key].message = f"이슈 처리 중: {current_issue} ({processed}/{total})"
                else:
                    sync_status_store[project_key].message = f"이슈 동기화 중... ({processed}/{total})"
                
                logger.info(f"동기화 진행률: {progress}% ({processed}/{total})")
        
        # 동기화 실행 (새로운 DB 세션과 콜백 함수 사용)
        logger.info(f"프로젝트 {project_key} 동기화 시작: {len(issues)}개 이슈")
        result = task_service.sync_jira_issues_with_progress(
            db_session, project_key, selected_issues, progress_callback
        )
        
        # 상태 업데이트: 완료
        sync_status_store[project_key].status = "completed"
        sync_status_store[project_key].progress = 100
        sync_status_store[project_key].message = result["message"]
        sync_status_store[project_key].total_issues = result.get("total_issues", len(issues))
        sync_status_store[project_key].processed_issues = result.get("synced_count", 0)
        
        logger.info(f"프로젝트 {project_key}: 백그라운드 동기화 완료 - {result.get('synced_count', 0)}개 처리됨")
        
    except Exception as e:
        # 상태 업데이트: 오류
        if project_key in sync_status_store:
            sync_status_store[project_key].status = "error"
            sync_status_store[project_key].progress = 0
            sync_status_store[project_key].message = f"동기화 실패: {str(e)}"
        
        logger.error(f"프로젝트 {project_key} 백그라운드 동기화 실패: {str(e)}")
        
    finally:
        # DB 세션 정리
        db_session.close()
