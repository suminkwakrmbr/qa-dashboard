"""
앱 설정 및 상수 관리 모듈
"""

# 페이지 설정
PAGE_CONFIG = {
    "page_title": "Quality Hub - Premium QA Management",
    "page_icon": "🎯",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# API 설정
API_BASE_URL = "http://localhost:8003/api/v1"
HEALTH_CHECK_URL = "http://localhost:8003/health"

# 지라 설정
JIRA_SERVER = "https://dramancompany.atlassian.net"

# 캐시 설정 (초 단위)
CACHE_TTL = {
    "dashboard_stats": 30,
    "projects": 60,
    "tasks": 30,
    "jira_projects": 300  # 5분
}

# 페이지네이션 설정
PAGINATION = {
    "items_per_page": 20,
    "sync_modal_items_per_page": 10
}

# 기본 자주 사용하는 프로젝트
DEFAULT_FREQUENT_PROJECTS = ['Remember_Android', 'Remember_iOS', 'RB']

# 상태 옵션
QA_STATUS_OPTIONS = ["미시작", "QA 시작", "QA 진행중", "QA 완료"]
REQUEST_STATUS_OPTIONS = ["요청", "진행중", "완료", "보류"]

# 우선순위 옵션
PRIORITY_OPTIONS = ["Highest", "High", "Medium", "Low", "Lowest"]

# 플랫폼 옵션
PLATFORM_OPTIONS = ["android", "ios", "web", "api"]

# 색상 테마
COLORS = {
    "priority": {
        'Highest': '#dc3545',
        'High': '#fd7e14',
        'Medium': '#ffc107',
        'Low': '#28a745',
        'Lowest': '#6c757d'
    },
    "qa_status": {
        'QA 완료': '#28a745',
        'QA 진행중': '#17a2b8',
        'QA 시작': '#ffc107',
        '미시작': '#6c757d'
    },
    "request_status": {
        "요청": "#6c757d",
        "대기중": "#ffc107",
        "진행중": "#17a2b8",
        "완료": "#28a745",
        "취소": "#dc3545",
        "보류": "#ffc107"
    }
}

# 플랫폼 이모지
PLATFORM_EMOJIS = {
    "android": "📱 Android",
    "ios": "📱 iOS",
    "web": "🌐 Web",
    "api": "🔌 API"
}

# 프로젝트 타입 이모지
PROJECT_TYPE_EMOJIS = {
    'software': '💻',
    'business': '📊',
    'service_desk': '🎧',
    'ops': '⚙️'
}

# 상태 이모지
STATUS_EMOJIS = {
    'Done': '✅',
    'In Progress': '🔄',
    'QA Ready': '🎯',
    'To Do': '📝'
}

# 파일 경로
CONFIG_FILES = {
    "frequent_projects": "frequent_projects.json"
}
