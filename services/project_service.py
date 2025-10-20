"""
프로젝트 관리 서비스
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.database_models import Project, Task
from models.pydantic_models import ProjectCreate, ProjectUpdate, ProjectResponse

logger = logging.getLogger(__name__)


class ProjectService:
    """프로젝트 관리 서비스 클래스"""
    
    @staticmethod
    def get_projects(
        db: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """프로젝트 목록 조회"""
        query = db.query(Project)
        
        if is_active is not None:
            query = query.filter(Project.is_active == is_active)
        
        return query.order_by(desc(Project.updated_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
        """ID로 프로젝트 조회"""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_project_by_key(db: Session, jira_project_key: str) -> Optional[Project]:
        """Jira 프로젝트 키로 조회"""
        return db.query(Project).filter(Project.jira_project_key == jira_project_key).first()
    
    @staticmethod
    def create_project(db: Session, project_data: ProjectCreate) -> Project:
        """프로젝트 생성"""
        # 중복 키 확인
        existing = db.query(Project).filter(
            Project.jira_project_key == project_data.jira_project_key
        ).first()
        
        if existing:
            raise ValueError(f"프로젝트 키 '{project_data.jira_project_key}'가 이미 존재합니다.")
        
        project = Project(**project_data.dict())
        db.add(project)
        db.commit()
        db.refresh(project)
        logger.info(f"프로젝트 생성: {project.name} ({project.jira_project_key})")
        return project
    
    @staticmethod
    def update_project(db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """프로젝트 업데이트"""
        project = ProjectService.get_project_by_id(db, project_id)
        if not project:
            return None
        
        update_data = project_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
        
        project.updated_at = datetime.now()
        db.commit()
        db.refresh(project)
        logger.info(f"프로젝트 업데이트: {project.name}")
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """프로젝트 삭제 (관련 작업도 함께 삭제)"""
        project = ProjectService.get_project_by_id(db, project_id)
        if not project:
            return False
        
        # 관련 작업 수 확인
        task_count = db.query(Task).filter(Task.project_id == project_id).count()
        
        # 관련 작업 삭제
        if task_count > 0:
            db.query(Task).filter(Task.project_id == project_id).delete()
            logger.info(f"프로젝트 {project.name}의 관련 작업 {task_count}개 삭제")
        
        project_name = project.name
        db.delete(project)
        db.commit()
        logger.info(f"프로젝트 삭제: {project_name}")
        return True
    
    @staticmethod
    def get_project_stats(db: Session, project_id: int) -> Dict[str, Any]:
        """프로젝트 통계 조회"""
        project = ProjectService.get_project_by_id(db, project_id)
        if not project:
            return {}
        
        total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
        completed_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "Done"
        ).count()
        qa_ready_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "QA Ready"
        ).count()
        in_progress_tasks = db.query(Task).filter(
            Task.project_id == project_id,
            Task.status == "In Progress"
        ).count()
        
        completion_rate = 0.0
        if total_tasks > 0:
            completion_rate = round((completed_tasks / total_tasks) * 100, 1)
        
        return {
            "project_id": project_id,
            "project_name": project.name,
            "jira_project_key": project.jira_project_key,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "qa_ready_tasks": qa_ready_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": completion_rate,
            "last_sync": project.last_sync
        }
    
    @staticmethod
    def update_last_sync(db: Session, project_id: int) -> Optional[Project]:
        """프로젝트 마지막 동기화 시간 업데이트"""
        project = ProjectService.get_project_by_id(db, project_id)
        if not project:
            return None
        
        project.last_sync = datetime.now()
        project.updated_at = datetime.now()
        db.commit()
        db.refresh(project)
        
        logger.info(f"프로젝트 동기화 시간 업데이트: {project.name}")
        return project
    
    @staticmethod
    def get_or_create_project(db: Session, jira_project_key: str, project_name: str) -> Project:
        """프로젝트 조회 또는 생성"""
        project = ProjectService.get_project_by_key(db, jira_project_key)
        
        if not project:
            # 새 프로젝트 생성
            project_data = ProjectCreate(
                name=project_name,
                jira_project_key=jira_project_key,
                description=f"Jira 프로젝트 {jira_project_key}에서 자동 생성됨"
            )
            project = ProjectService.create_project(db, project_data)
            logger.info(f"새 프로젝트 자동 생성: {project_name} ({jira_project_key})")
        
        return project


# 전역 프로젝트 서비스 인스턴스
project_service = ProjectService()
