"""
QA Dashboard - 메인 애플리케이션
"""
import logging
import sys
import traceback
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.database import init_db, check_db_connection
from api.routes import jira_routes, task_routes, qa_request_routes, project_routes, zephyr_routes

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('qa_dashboard.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 QA Dashboard 시작")
    
    try:
        # 데이터베이스 초기화
        init_db()
        
        # 데이터베이스 연결 확인
        if check_db_connection():
            logger.info("✅ 데이터베이스 연결 성공")
        else:
            logger.error("❌ 데이터베이스 연결 실패")
            
        # Jira 설정 확인
        if settings.is_jira_configured:
            logger.info("✅ Jira 설정 완료")
        else:
            logger.warning("⚠️ Jira 설정이 불완전합니다")
            
    except Exception as e:
        logger.error(f"❌ 애플리케이션 초기화 실패: {e}")
        traceback.print_exc()
    
    yield
    
    # 종료 시 실행
    logger.info("👋 QA Dashboard 종료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description="실제 Jira와 연동된 QA 대시보드",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 미들웨어 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    
    # 라우터 등록
    app.include_router(jira_routes.router, prefix=settings.API_V1_STR)
    app.include_router(task_routes.router, prefix=settings.API_V1_STR)
    app.include_router(project_routes.router, prefix=settings.API_V1_STR)
    app.include_router(qa_request_routes.router, prefix=settings.API_V1_STR)
    app.include_router(zephyr_routes.router, prefix=settings.API_V1_STR)
    
    return app


# FastAPI 앱 인스턴스
app = create_app()

@app.get("/")
async def root():
    """루트 엔드포인트 - API 정보 반환"""
    return {
        "message": "QA Dashboard API Server",
        "description": "Streamlit 앱은 별도로 실행하세요: streamlit run streamlit_app/app_refactored.py",
        "api_docs": "/docs",
        "health": "/health"
    }


@app.get("/api", response_model=dict)
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": f"{settings.PROJECT_NAME} v{settings.PROJECT_VERSION}",
        "description": "실제 Jira와 연동된 QA 대시보드",
        "jira_configured": settings.is_jira_configured,
        "status": "running",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    db_status = check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "jira_configured": settings.is_jira_configured,
        "version": settings.PROJECT_VERSION
    }


@app.get("/stats/dashboard")
async def get_dashboard_stats_legacy():
    """레거시 대시보드 통계 엔드포인트 (하위 호환성)"""
    from core.database import get_db
    from services.task_service import task_service
    
    # 데이터베이스 세션 생성
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        stats = task_service.get_dashboard_stats(db)
        return stats
    finally:
        db.close()


@app.get("/projects")
async def get_projects_legacy():
    """레거시 프로젝트 목록 엔드포인트 (하위 호환성)"""
    from core.database import get_db
    from models.database_models import Project
    
    # 데이터베이스 세션 생성
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        projects = db.query(Project).filter(Project.is_active == True).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "jira_project_key": p.jira_project_key,
                "description": p.description,
                "is_active": p.is_active,
                "last_sync": p.last_sync
            }
            for p in projects
        ]
    finally:
        db.close()


@app.get("/tasks")
async def get_tasks_legacy():
    """레거시 작업 목록 엔드포인트 (하위 호환성)"""
    from core.database import get_db
    from services.task_service import task_service
    
    # 데이터베이스 세션 생성
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        tasks = task_service.get_tasks(db)
        return [
            {
                "id": t.id,
                "jira_key": t.jira_key,
                "title": t.title,
                "status": t.status,
                "assignee": t.assignee,
                "priority": t.priority,
                "project_id": t.project_id,
                "last_sync": t.last_sync
            }
            for t in tasks
        ]
    finally:
        db.close()


def main():
    """메인 함수"""
    try:
        print("=" * 60)
        print(f"🚀 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION} 시작")
        print(f"📊 Jira 서버: {settings.JIRA_SERVER}")
        print(f"👤 사용자: {settings.JIRA_USERNAME}")
        print(f"🔑 API 토큰: {'✅ 설정됨' if settings.JIRA_API_TOKEN else '❌ 미설정'}")
        print(f"🗄️ 데이터베이스: {settings.DATABASE_URL}")
        print("=" * 60)
        
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8002,
            reload=False,  # 프로덕션에서는 False
            log_level=settings.LOG_LEVEL.lower()
        )
        
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다.")
    except Exception as e:
        print(f"❌ 서버 실행 오류: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
