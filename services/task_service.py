"""
작업 관리 서비스
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.database_models import Task, Project, SyncHistory
from models.pydantic_models import TaskCreate, TaskUpdate, TaskResponse
from services.jira_service import jira_service

logger = logging.getLogger(__name__)


class TaskService:
    """작업 관리 서비스 클래스"""
    
    @staticmethod
    def get_tasks(
        db: Session,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000
    ) -> List[Task]:
        """작업 목록 조회"""
        query = db.query(Task)
        
        if project_id:
            query = query.filter(Task.project_id == project_id)
        if status:
            query = query.filter(Task.status == status)
        
        return query.order_by(desc(Task.updated_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
        """ID로 작업 조회"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    @staticmethod
    def get_task_by_jira_key(db: Session, jira_key: str) -> Optional[Task]:
        """Jira 키로 작업 조회"""
        return db.query(Task).filter(Task.jira_key == jira_key).first()
    
    @staticmethod
    def create_task(db: Session, task_data: TaskCreate) -> Task:
        """작업 생성"""
        task = Task(**task_data.dict())
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info(f"작업 생성: {task.jira_key}")
        return task
    
    @staticmethod
    def update_task(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """작업 업데이트"""
        task = TaskService.get_task_by_id(db, task_id)
        if not task:
            return None
        
        update_data = task_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)
        logger.info(f"작업 업데이트: {task.jira_key}")
        return task
    
    @staticmethod
    def delete_task(db: Session, task_id: int) -> bool:
        """작업 삭제"""
        task = TaskService.get_task_by_id(db, task_id)
        if not task:
            return False
        
        jira_key = task.jira_key
        db.delete(task)
        db.commit()
        logger.info(f"작업 삭제: {jira_key}")
        return True
    
    @staticmethod
    def update_qa_status(db: Session, task_id: int, qa_status: str) -> Optional[Task]:
        """QA 상태 업데이트 - qa_status 필드만 업데이트"""
        task = TaskService.get_task_by_id(db, task_id)
        if not task:
            return None
        
        old_qa_status = task.qa_status
        task.qa_status = qa_status  # status가 아닌 qa_status 필드 업데이트
        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)
        
        logger.info(f"QA 상태 업데이트: {task.jira_key} - {old_qa_status} → {qa_status}")
        return task
    
    @staticmethod
    def update_memo(db: Session, task_id: int, memo: str) -> Optional[Task]:
        """메모 업데이트"""
        task = TaskService.get_task_by_id(db, task_id)
        if not task:
            return None
        
        task.memo = memo
        task.updated_at = datetime.now()
        db.commit()
        db.refresh(task)
        
        logger.info(f"메모 업데이트: {task.jira_key}")
        return task
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """대시보드 통계 조회"""
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == "Done").count()
        qa_ready_tasks = db.query(Task).filter(Task.status == "QA Ready").count()
        in_progress_tasks = db.query(Task).filter(Task.status == "In Progress").count()
        
        completion_rate = 0.0
        if total_tasks > 0:
            completion_rate = round((completed_tasks / total_tasks) * 100, 1)
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "qa_ready_tasks": qa_ready_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": completion_rate
        }
    
    @staticmethod
    def reset_all_tasks(db: Session) -> Dict[str, Any]:
        """모든 작업 데이터 초기화"""
        try:
            # 작업 수 카운트
            deleted_tasks = db.query(Task).count()
            deleted_sync_history = db.query(SyncHistory).count()
            
            # 관련 데이터 순서대로 삭제 (외래 키 제약 조건 고려)
            # 1. TestCase 삭제 (Task에 의존)
            from models.database_models import TestCase
            db.query(TestCase).delete()
            
            # 2. Task 삭제
            db.query(Task).delete()
            
            # 3. SyncHistory 삭제
            db.query(SyncHistory).delete()
            
            # 4. 모든 프로젝트의 last_sync 초기화
            db.query(Project).update({"last_sync": None})
            
            db.commit()
            
            logger.info(f"데이터 초기화 완료: {deleted_tasks}개 작업, {deleted_sync_history}개 동기화 이력 삭제됨")
            
            return {
                "success": True,
                "message": f"모든 작업 데이터가 초기화되었습니다. (작업: {deleted_tasks}개, 동기화 이력: {deleted_sync_history}개 삭제)",
                "deleted_tasks": deleted_tasks,
                "deleted_sync_history": deleted_sync_history
            }
        except Exception as e:
            db.rollback()
            logger.error(f"데이터 초기화 실패: {str(e)}")
            raise Exception(f"데이터 초기화 실패: {str(e)}")
    
    @staticmethod
    def sync_jira_issues(
        db: Session,
        project_key: str,
        selected_issues: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Jira 이슈 동기화"""
        return TaskService.sync_jira_issues_with_progress(
            db, project_key, selected_issues, None
        )
    
    @staticmethod
    def sync_jira_issues_with_progress(
        db: Session,
        project_key: str,
        selected_issues: Optional[List[str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Jira 이슈 동기화 (진행률 콜백 지원)"""
        try:
            # 동기화 이력 생성
            sync_history = SyncHistory(
                project_key=project_key,
                sync_type="selected" if selected_issues else "full",
                status="started"
            )
            db.add(sync_history)
            db.commit()
            
            # 프로젝트 확인 및 생성
            project = TaskService._ensure_project_exists(db, project_key)
            
            # Jira 이슈 가져오기
            issues = jira_service.get_issues(project_key)
            total_issues = len(issues)
            
            # 선택된 이슈만 필터링
            if selected_issues:
                issues = [issue for issue in issues if issue["key"] in selected_issues]
                logger.info(f"선택된 이슈 {len(issues)}개 처리 시작 (전체 {total_issues}개 중)")
            
            synced_count = 0
            
            for i, issue in enumerate(issues):
                try:
                    jira_key = issue.get("key", "")
                    
                    # 진행률 콜백 호출
                    if progress_callback:
                        progress_callback(i, len(issues), jira_key)
                    
                    # 기존 작업 확인
                    task = db.query(Task).filter(Task.jira_key == jira_key).first()
                    
                    # Jira 서비스에서 이미 정규화된 데이터 사용
                    title = issue.get("summary", "")[:500]
                    description = issue.get("description", "")
                    status = issue.get("status", "To Do")
                    assignee = issue.get("assignee", "")
                    priority = issue.get("priority", "Medium")
                    jira_id = issue.get("id", "")
                    
                    if not task:
                        # 새 작업 생성 (프로젝트 ID 포함)
                        task = Task(
                            jira_key=jira_key,
                            jira_id=jira_id,
                            title=title,
                            description=description,
                            status=status,
                            assignee=assignee,
                            priority=priority,
                            project_id=project.id,  # 프로젝트 ID 설정
                            last_sync=datetime.now()
                        )
                        db.add(task)
                        logger.info(f"새 이슈 생성: {jira_key} - {title}")
                    else:
                        # 기존 작업 업데이트
                        task.title = title
                        task.description = description or task.description
                        task.status = status
                        task.assignee = assignee
                        task.priority = priority
                        task.project_id = project.id  # 프로젝트 ID 업데이트
                        task.last_sync = datetime.now()
                        logger.info(f"이슈 업데이트: {jira_key} - {title}")
                    
                    synced_count += 1
                    
                    # 배치 처리를 위한 중간 커밋 (50개마다로 변경하여 성능 향상)
                    if synced_count % 50 == 0:
                        db.commit()
                        logger.info(f"중간 커밋: {synced_count}개 이슈 처리 완료")
                    
                except Exception as e:
                    logger.error(f"이슈 {issue.get('key', 'Unknown')} 동기화 오류: {str(e)}")
                    continue
            
            # 최종 진행률 콜백 호출
            if progress_callback:
                progress_callback(len(issues), len(issues), "완료")
            
            # 동기화 이력 업데이트
            sync_history.status = "completed"
            sync_history.total_issues = len(issues)
            sync_history.processed_issues = synced_count
            sync_history.completed_at = datetime.now()
            
            db.commit()
            
            logger.info(f"프로젝트 {project_key}: {synced_count}개 작업 동기화 완료")
            
            return {
                "success": True,
                "message": f"동기화 완료! {synced_count}개 작업 처리됨",
                "project_key": project_key,
                "synced_count": synced_count,
                "total_issues": len(issues)
            }
            
        except Exception as e:
            db.rollback()
            # 동기화 이력 오류 업데이트
            if 'sync_history' in locals():
                sync_history.status = "failed"
                sync_history.error_message = str(e)
                sync_history.completed_at = datetime.now()
                db.commit()
            
            logger.error(f"프로젝트 {project_key} 동기화 실패: {str(e)}")
            raise
    
    @staticmethod
    def _ensure_project_exists(db: Session, project_key: str) -> Project:
        """프로젝트 존재 확인 및 생성"""
        # 기존 프로젝트 확인
        project = db.query(Project).filter(Project.jira_project_key == project_key).first()
        
        if not project:
            # Jira에서 프로젝트 정보 가져오기
            try:
                jira_projects = jira_service.get_projects()
                jira_project_info = None
                
                for jp in jira_projects:
                    if jp.get('key') == project_key:
                        jira_project_info = jp
                        break
                
                if jira_project_info:
                    project_name = jira_project_info.get('name', project_key)
                    project_description = jira_project_info.get('description', '')
                else:
                    # Jira에서 프로젝트 정보를 찾을 수 없는 경우 기본값 사용
                    project_name = project_key
                    project_description = f"Auto-created project for {project_key}"
                
                # 새 프로젝트 생성
                project = Project(
                    name=project_name,
                    jira_project_key=project_key,
                    description=project_description,
                    is_active=True,
                    last_sync=datetime.now()
                )
                
                db.add(project)
                db.commit()
                db.refresh(project)
                
                logger.info(f"새 프로젝트 생성: {project_key} - {project_name}")
                
            except Exception as e:
                logger.warning(f"Jira 프로젝트 정보 조회 실패, 기본 프로젝트 생성: {str(e)}")
                
                # Jira 조회 실패 시 기본 프로젝트 생성
                project = Project(
                    name=project_key,
                    jira_project_key=project_key,
                    description=f"Auto-created project for {project_key}",
                    is_active=True,
                    last_sync=datetime.now()
                )
                
                db.add(project)
                db.commit()
                db.refresh(project)
                
                logger.info(f"기본 프로젝트 생성: {project_key}")
        
        return project


# 전역 작업 서비스 인스턴스
task_service = TaskService()
