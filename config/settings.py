"""
애플리케이션 설정 관리
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from decouple import config


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스 설정
    DATABASE_URL: str = config("DATABASE_URL", default="sqlite:///./qa_dashboard.db")
    
    # JWT 설정
    SECRET_KEY: str = config("SECRET_KEY", default="your-secret-key-here")
    ALGORITHM: str = config("ALGORITHM", default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)
    
    # Jira 설정
    JIRA_SERVER: str = config("JIRA_SERVER", default="")
    JIRA_USERNAME: str = config("JIRA_USERNAME", default="")
    JIRA_API_TOKEN: str = config("JIRA_API_TOKEN", default="")
    
    # Zephyr 설정
    ZEPHYR_SERVER: str = config("ZEPHYR_SERVER", default="https://remember-qa.atlassian.net")
    ZEPHYR_USERNAME: str = config("ZEPHYR_USERNAME", default="")
    ZEPHYR_API_TOKEN: str = config("ZEPHYR_API_TOKEN", default="")
    ZEPHYR_ENCRYPTION_KEY: str = config("ZEPHYR_ENCRYPTION_KEY", default="zephyr-32-character-encryption-key-here")
    
    # 암호화 설정
    ENCRYPTION_KEY: str = config("ENCRYPTION_KEY", default="your-32-character-encryption-key")
    
    # GPT API 설정
    CUSTOM_GPT_API_KEY: str = config("CUSTOM_GPT_API_KEY", default="")
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "QA Dashboard"
    PROJECT_VERSION: str = "2.0.0"
    
    # CORS 설정
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # 로깅 설정
    LOG_LEVEL: str = config("LOG_LEVEL", default="INFO")
    
    # 캐시 설정
    CACHE_TTL: int = config("CACHE_TTL", default=300, cast=int)  # 5분
    
    # Jira API 설정
    JIRA_API_VERSION: str = config("JIRA_API_VERSION", default="3")  # API v3 사용
    JIRA_MAX_RESULTS: int = config("JIRA_MAX_RESULTS", default=100, cast=int)
    JIRA_TIMEOUT: int = config("JIRA_TIMEOUT", default=20, cast=int)  # timeout을 20초로 단축
    JIRA_EXPAND_FIELDS: str = config("JIRA_EXPAND_FIELDS", default="description,lead,issueTypes,url,projectKeys")
    
    # 연결 및 조회 timeout 세분화
    JIRA_CONNECTION_TIMEOUT: int = config("JIRA_CONNECTION_TIMEOUT", default=15, cast=int)  # 연결 테스트용
    JIRA_QUICK_TIMEOUT: int = config("JIRA_QUICK_TIMEOUT", default=10, cast=int)  # 빠른 조회용 (이슈 수 등)
    JIRA_SYNC_TIMEOUT: int = config("JIRA_SYNC_TIMEOUT", default=30, cast=int)  # 동기화용 (더 긴 시간)
    
    # 동기화 설정
    SYNC_BATCH_SIZE: int = config("SYNC_BATCH_SIZE", default=50, cast=int)
    
    # API v3 특화 설정
    JIRA_USE_SEARCH_API: bool = config("JIRA_USE_SEARCH_API", default=True, cast=bool)  # v3 search API 사용 여부
    JIRA_FALLBACK_TO_V2: bool = config("JIRA_FALLBACK_TO_V2", default=False, cast=bool)  # v2 폴백 허용 여부
    
    @property
    def is_jira_configured(self) -> bool:
        """Jira 설정 완료 여부 확인"""
        return bool(self.JIRA_SERVER and self.JIRA_USERNAME and self.JIRA_API_TOKEN)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()
