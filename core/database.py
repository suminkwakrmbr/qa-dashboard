"""
데이터베이스 연결 및 세션 관리
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config.settings import settings

logger = logging.getLogger(__name__)

# SQLite 설정 최적화
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {
        "check_same_thread": False,
        "timeout": 20,
        "isolation_level": None
    }

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
    pool_pre_ping=True,
    echo=False  # 프로덕션에서는 False
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스
Base = declarative_base()


def get_db() -> Session:
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"데이터베이스 세션 오류: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise


def check_db_connection() -> bool:
    """데이터베이스 연결 상태 확인"""
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False
