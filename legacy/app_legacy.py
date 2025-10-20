import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

# 페이지 설정
st.set_page_config(
    page_title="Quality Hub - Premium QA Management",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 기본 URL
API_BASE_URL = "http://localhost:8003/api/v1"

# 고급 스타일링 - 현대적이고 전문적인 디자인
st.markdown("""
<style>
    /* Google Fonts 임포트 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* 전체 앱 스타일링 */
    .stApp {
        background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1400px;
    }
    
    /* 사이드바 스타일링 */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e2329 0%, #2d3748 100%);
        border-right: 1px solid #4a5568;
    }
    
    /* 헤더 스타일 */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        letter-spacing: -0.025em;
        color: #f7fafc !important;
    }
    
    h1 {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        font-size: 1.875rem;
        color: #e2e8f0 !important;
        border-bottom: 2px solid #4a5568;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    
    h3 {
        font-size: 1.5rem;
        color: #cbd5e0 !important;
        margin-bottom: 1rem;
    }
    
    /* 텍스트 스타일 */
    .stMarkdown, .stText, p, div, span {
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
        line-height: 1.6;
    }
    
    /* 버튼 스타일링 */
    .stButton > button {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        border-radius: 8px;
        border: none;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        letter-spacing: 0.025em;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
        color: #e2e8f0;
        border: 1px solid #4a5568;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border-color: #667eea;
        transform: translateY(-1px);
    }
    
    /* 입력 필드 스타일링 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
        padding: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        outline: none;
    }
    
    /* 메트릭 카드 스타일링 */
    .css-1r6slb0 {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border: 1px solid #4a5568;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* 탭 스타일링 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #1a202c;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #a0aec0;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* 사이드바 버튼 스타일링 */
    .css-1d391kg .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: 1px solid transparent;
        color: #cbd5e0;
        font-weight: 500;
        padding: 0.875rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        transition: all 0.2s ease;
    }
    
    .css-1d391kg .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        font-weight: 600;
    }
    
    .css-1d391kg .stButton > button:hover {
        background-color: #2d3748;
        border-color: #4a5568;
        transform: translateX(4px);
    }
    
    /* 알림 박스 스타일링 */
    .success-box { 
        background: linear-gradient(135deg, #065f46 0%, #047857 100%);
        border: 1px solid #10b981;
        color: #d1fae5;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(16, 185, 129, 0.1);
        font-weight: 500;
    }
    
    .error-box { 
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 1px solid #ef4444;
        color: #fecaca;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(239, 68, 68, 0.1);
        font-weight: 500;
    }
    
    .info-box { 
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
        border: 1px solid #3b82f6;
        color: #dbeafe;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
        font-weight: 500;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #92400e 0%, #b45309 100%);
        border: 1px solid #f59e0b;
        color: #fef3c7;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(245, 158, 11, 0.1);
        font-weight: 500;
    }
    
    /* 코드 스타일링 */
    code {
        font-family: 'JetBrains Mono', monospace;
        background-color: #1a202c;
        color: #e2e8f0;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
    }
    
    /* 체크박스 스타일링 */
    .stCheckbox > label {
        color: #e2e8f0 !important;
        font-weight: 500;
    }
    
    /* 라벨 스타일링 */
    .stSelectbox > label,
    .stTextInput > label,
    .stTextArea > label {
        color: #cbd5e0 !important;
        font-weight: 600;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    /* 데이터프레임 스타일링 */
    .dataframe {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 8px;
    }
    
    /* 확장 가능한 섹션 스타일링 */
    .streamlit-expanderHeader {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        color: #e2e8f0;
        font-weight: 600;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
    }
    
    .streamlit-expanderContent {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
        margin-top: -0.5rem;
    }
    
    /* 컨테이너 간격 개선 */
    .stContainer > div {
        padding: 0.5rem 0;
    }
    
    /* 메트릭 카드 간격 개선 */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border: 1px solid #4a5568;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* 컬럼 간격 개선 */
    .stColumns > div {
        padding: 0 0.5rem;
    }
    
    /* 텍스트와 보더 간격 개선 */
    .stMarkdown p {
        margin-bottom: 1rem;
        line-height: 1.7;
    }
    
    /* 입력 필드 라벨 간격 개선 */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label {
        margin-bottom: 0.75rem !important;
        display: block;
    }
    
    /* 버튼 간격 개선 */
    .stButton {
        margin: 0.25rem 0;
    }
    
    /* 알림 박스 내부 간격 개선 */
    .success-box p,
    .error-box p,
    .info-box p,
    .warning-box p {
        margin: 0.5rem 0;
        line-height: 1.5;
    }
    
    /* 스피너 스타일링 */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* 진행률 바 스타일링 */
    .stProgress .st-bo {
        background-color: #667eea;
    }
    
    /* 커스텀 카드 스타일 */
    .premium-card {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        border: 1px solid #4a5568;
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .premium-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        border-color: #667eea;
    }
    
    /* 그라데이션 텍스트 */
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    /* 상태 배지 */
    .status-badge {
        display: inline-block;
        padding: 0.375rem 0.875rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-success { background: linear-gradient(135deg, #065f46, #047857); color: #d1fae5; }
    .status-warning { background: linear-gradient(135deg, #92400e, #b45309); color: #fef3c7; }
    .status-error { background: linear-gradient(135deg, #7f1d1d, #991b1b); color: #fecaca; }
    .status-info { background: linear-gradient(135deg, #1e3a8a, #1d4ed8); color: #dbeafe; }
    
    /* 애니메이션 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        h1 {
            font-size: 2rem;
        }
        
        .premium-card {
            padding: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def api_call(endpoint, method="GET", data=None):
    """API 호출 공통 함수"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=15)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=15)
        elif method == "PATCH":
            response = requests.patch(url, json=data, timeout=15)
        elif method == "DELETE":
            response = requests.delete(url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 오류: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"연결 오류: {str(e)}")
        return None

def check_api_connection():
    """API 서버 연결 확인"""
    # 헬스 체크는 루트 레벨에 있음
    try:
        url = "http://localhost:8003/health"
        response = requests.get(url, timeout=15)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=30)
def get_dashboard_stats():
    """대시보드 통계 데이터 가져오기"""
    # 레거시 엔드포인트는 루트 레벨에 있음
    try:
        url = "http://localhost:8003/stats/dashboard"
        response = requests.get(url, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=60)
def get_projects():
    """프로젝트 목록 가져오기"""
    # 레거시 엔드포인트는 루트 레벨에 있음
    try:
        url = "http://localhost:8003/projects"
        response = requests.get(url, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=30)
def get_tasks(project_id=None, status=None):
    """작업 목록 가져오기"""
    # 레거시 엔드포인트는 루트 레벨에 있음
    try:
        params = []
        if project_id:
            params.append(f"project_id={project_id}")
        if status:
            params.append(f"status={status}")
        
        url = "http://localhost:8003/tasks"
        if params:
            url += "?" + "&".join(params)
        
        response = requests.get(url, timeout=15)
        return response.json() if response.status_code == 200 else None
    except:
        return None

def test_jira_connection():
    """지라 연결 테스트"""
    return api_call("/jira/test-connection", method="POST")

@st.cache_data(ttl=300)  # 5분 캐시
def get_jira_projects():
    """지라 프로젝트 목록 가져오기"""
    return api_call("/jira/projects")

def sync_jira_project(project_key, selected_issues=None):
    """지라 프로젝트 동기화"""
    if selected_issues:
        # 선택된 이슈만 동기화
        data = {"selected_issues": selected_issues}
        result = api_call(f"/jira/sync/{project_key}", method="POST", data=data)
    else:
        # 전체 동기화
        result = api_call(f"/jira/sync/{project_key}", method="POST")
    
    # 동기화 시작 후 캐시 클리어
    if result:
        st.cache_data.clear()
    
    return result

def get_jira_project_issues(project_key):
    """지라 프로젝트의 이슈 목록 가져오기"""
    return api_call(f"/jira/projects/{project_key}/issues")

def show_sync_modal(project_key, project_name):
    """동기화 모달 표시 - 개선된 UI"""
    # 모달 스타일링
    st.markdown("""
    <style>
    .sync-modal {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    .sync-modal h3 {
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 1.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .issue-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #2E86AB;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    .issue-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .priority-high { border-left-color: #dc3545; }
    .priority-medium { border-left-color: #ffc107; }
    .priority-low { border-left-color: #28a745; }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .status-todo { background: #e9ecef; color: #495057; }
    .status-progress { background: #cce5ff; color: #0066cc; }
    .status-done { background: #d4edda; color: #155724; }
    .status-qa { background: #fff3cd; color: #856404; }
    </style>
    """, unsafe_allow_html=True)
    
    # 모달 헤더
    st.markdown(f"""
    <div class="sync-modal">
        <h3>🔄 {project_name} ({project_key}) 동기화</h3>
        <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0;">
            동기화할 이슈를 선택하고 QA 대시보드로 가져오세요
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 이슈 목록 가져오기
    with st.spinner(f"🔍 {project_key} 프로젝트의 이슈 목록을 가져오는 중..."):
        issues_data = get_jira_project_issues(project_key)
    
    if issues_data and issues_data.get("issues"):
        issues = issues_data["issues"]
        
        # 페이지 배너 (전체 이슈 갯수) - 테스크 목록 위에 표시
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        ">
            <h2 style="color: white; margin: 0 0 1rem 0; font-size: 1.8rem;">
                📊 {project_name} ({project_key}) 이슈 현황
            </h2>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem;">
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; min-width: 120px;">
                    <div style="color: white; font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">
                        {len(issues)}
                    </div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        📋 전체 이슈
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; min-width: 120px;">
                    <div style="color: white; font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">
                        {sum(1 for issue in issues if issue.get("fields", {}).get("status", {}).get("name", "") in ["To Do", "Open"])}
                    </div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        📝 할 일
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; min-width: 120px;">
                    <div style="color: white; font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">
                        {sum(1 for issue in issues if issue.get("fields", {}).get("status", {}).get("name", "") in ["In Progress", "In Review"])}
                    </div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        🔄 진행중
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 8px; min-width: 120px;">
                    <div style="color: white; font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;">
                        {sum(1 for issue in issues if issue.get("fields", {}).get("status", {}).get("name", "") in ["Done", "Closed"])}
                    </div>
                    <div style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">
                        ✅ 완료
                    </div>
                </div>
            </div>
            <div style="margin-top: 1rem; color: rgba(255,255,255,0.8); font-size: 0.9rem;">
                📅 최근 3개월간의 이슈를 표시합니다
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "상태 필터", 
                ["전체"] + list(set([issue.get("fields", {}).get("status", {}).get("name", "") for issue in issues if issue.get("fields", {}).get("status", {}).get("name")])),
                key=f"status_filter_{project_key}"
            )
        with col2:
            priority_filter = st.selectbox(
                "우선순위 필터",
                ["전체"] + list(set([issue.get("fields", {}).get("priority", {}).get("name", "") for issue in issues if issue.get("fields", {}).get("priority", {}).get("name")])),
                key=f"priority_filter_{project_key}"
            )
        with col3:
            assignee_filter = st.selectbox(
                "담당자 필터",
                ["전체"] + list(set([issue.get("fields", {}).get("assignee", {}).get("displayName", "미할당") if issue.get("fields", {}).get("assignee") else "미할당" for issue in issues])),
                key=f"assignee_filter_{project_key}"
            )
        
        # 필터링 적용
        filtered_issues = issues
        if status_filter != "전체":
            filtered_issues = [issue for issue in filtered_issues if issue.get("fields", {}).get("status", {}).get("name", "") == status_filter]
        if priority_filter != "전체":
            filtered_issues = [issue for issue in filtered_issues if issue.get("fields", {}).get("priority", {}).get("name", "") == priority_filter]
        if assignee_filter != "전체":
            assignee_name = lambda issue: issue.get("fields", {}).get("assignee", {}).get("displayName", "미할당") if issue.get("fields", {}).get("assignee") else "미할당"
            filtered_issues = [issue for issue in filtered_issues if assignee_name(issue) == assignee_filter]
        
        if len(filtered_issues) != len(issues):
            st.info(f"🔍 필터 적용: {len(filtered_issues)}개 이슈 표시 (전체 {len(issues)}개)")
        
        # 전체 선택/해제 버튼
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("✅ 전체 선택", key=f"select_all_{project_key}", use_container_width=True):
                for i, issue in enumerate(filtered_issues):
                    st.session_state[f"issue_selected_{project_key}_{issue.get('key')}"] = True
                st.rerun()
        
        with col2:
            if st.button("❌ 전체 해제", key=f"deselect_all_{project_key}", use_container_width=True):
                for i, issue in enumerate(filtered_issues):
                    st.session_state[f"issue_selected_{project_key}_{issue.get('key')}"] = False
                st.rerun()
        
        with col3:
            if st.button("🎯 QA 대상만", key=f"select_qa_{project_key}", use_container_width=True, help="QA Ready, In Review 상태 이슈만 선택"):
                qa_statuses = ["QA Ready", "In Review", "Ready for QA", "Testing"]
                for i, issue in enumerate(filtered_issues):
                    issue_status = issue.get("fields", {}).get("status", {}).get("name", "")
                    st.session_state[f"issue_selected_{project_key}_{issue.get('key')}"] = issue_status in qa_statuses
                st.rerun()
        
        with col4:
            if st.button("🔥 높은 우선순위", key=f"select_high_{project_key}", use_container_width=True, help="High, Highest 우선순위 이슈만 선택"):
                high_priorities = ["High", "Highest", "Critical"]
                for i, issue in enumerate(filtered_issues):
                    issue_priority = issue.get("fields", {}).get("priority", {}).get("name", "")
                    st.session_state[f"issue_selected_{project_key}_{issue.get('key')}"] = issue_priority in high_priorities
                st.rerun()
        
        st.markdown("---")
        
        # 이슈 목록 표시 (카드 형태)
        selected_issues = []
        
        # 페이지네이션
        items_per_page = 10
        total_pages = (len(filtered_issues) + items_per_page - 1) // items_per_page
        
        if total_pages > 1:
            # 현재 페이지 번호 가져오기
            page_key = f"sync_page_{project_key}"
            if page_key not in st.session_state:
                st.session_state[page_key] = 1
            
            current_page = st.session_state[page_key]
            
            
            page_num = current_page - 1
        else:
            page_num = 0
        
        start_idx = page_num * items_per_page
        end_idx = start_idx + items_per_page
        page_issues = filtered_issues[start_idx:end_idx]
        
        for i, issue in enumerate(page_issues):
            issue_key = issue.get("key", "")
            issue_summary = issue.get("fields", {}).get("summary", "")
            issue_status = issue.get("fields", {}).get("status", {}).get("name", "")
            issue_assignee = issue.get("fields", {}).get("assignee", {}).get("displayName", "미할당") if issue.get("fields", {}).get("assignee") else "미할당"
            issue_priority = issue.get("fields", {}).get("priority", {}).get("name", "Medium")
            issue_created = issue.get("fields", {}).get("created", "")[:10]
            issue_updated = issue.get("fields", {}).get("updated", "")[:10]
            
            # 체크박스 기본값 설정 (처음에는 모두 선택)
            checkbox_key = f"issue_selected_{project_key}_{issue_key}"
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = True
            
            # 우선순위별 스타일 클래스
            priority_class = {
                "Highest": "priority-high",
                "High": "priority-high", 
                "Medium": "priority-medium",
                "Low": "priority-low",
                "Lowest": "priority-low"
            }.get(issue_priority, "priority-medium")
            
            # 상태별 배지 스타일
            status_class = {
                "To Do": "status-todo",
                "Open": "status-todo",
                "In Progress": "status-progress",
                "In Review": "status-progress",
                "QA Ready": "status-qa",
                "Done": "status-done",
                "Closed": "status-done"
            }.get(issue_status, "status-todo")
            
            # 이슈 카드
            col1, col2 = st.columns([1, 20])
            
            with col1:
                is_selected = st.checkbox(
                    "선택",
                    value=st.session_state[checkbox_key],
                    key=checkbox_key,
                    label_visibility="hidden"
                )
            
            with col2:
                st.markdown(f"""
                <div class="issue-card {priority_class}" style="background: #2d3748; border: 1px solid #4a5568; color: #e2e8f0;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
                        <div style="flex: 1;">
                            <div style="margin-bottom: 0.3rem;">
                                <strong style="color: #63b3ed; font-size: 1.1rem;">{issue_key}</strong>
                                <span class="status-badge {status_class}" style="margin-left: 0.5rem;">{issue_status}</span>
                            </div>
                            <div style="color: #cbd5e0; font-size: 1rem; font-weight: 500; line-height: 1.4; margin-bottom: 0.5rem;">
                                {issue_summary}
                            </div>
                        </div>
                        <div style="text-align: right; font-size: 0.8rem; color: #a0aec0; margin-left: 1rem;">
                            <div style="margin-bottom: 0.2rem;">우선순위: <strong style="color: #fbb6ce;">{issue_priority}</strong></div>
                            <div>담당자: <strong style="color: #9ae6b4;">{issue_assignee}</strong></div>
                        </div>
                    </div>
                    <div style="font-size: 0.75rem; color: #718096; border-top: 1px solid #4a5568; padding-top: 0.5rem;">
                        생성: {issue_created} | 수정: {issue_updated}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if is_selected:
                selected_issues.append(issue_key)
        
        # 페이지네이션 (목록 하단)
        if total_pages > 1:
            st.markdown("---")
            current_page = st.session_state[page_key]
            
            # 간단한 페이지네이션
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # 페이지 번호 버튼들을 한 줄로 표시
                page_buttons = []
                
                # 이전 버튼
                if current_page > 1:
                    page_buttons.append("◀")
                
                # 페이지 번호들 (최대 5개)
                start_page = max(1, current_page - 2)
                end_page = min(total_pages, start_page + 4)
                
                if end_page - start_page < 4:
                    start_page = max(1, end_page - 4)
                
                for page in range(start_page, end_page + 1):
                    if page == current_page:
                        page_buttons.append(f"**{page}**")
                    else:
                        page_buttons.append(str(page))
                
                # 다음 버튼
                if current_page < total_pages:
                    page_buttons.append("▶")
                
                # 버튼들을 한 줄로 표시 (간격 최소화)
                button_cols = st.columns(len(page_buttons), gap="small")
                for i, button_text in enumerate(page_buttons):
                    with button_cols[i]:
                        if button_text == "◀":
                            if st.button("◀", key=f"prev_sync_simple_{project_key}"):
                                st.session_state[page_key] = current_page - 1
                                st.rerun()
                        elif button_text == "▶":
                            if st.button("▶", key=f"next_sync_simple_{project_key}"):
                                st.session_state[page_key] = current_page + 1
                                st.rerun()
                        elif button_text.startswith("**"):
                            # 현재 페이지 (텍스트만 표시, 버튼과 동일한 크기)
                            st.markdown(f"<div style='text-align: center; color: #0066cc; font-weight: bold; font-size: 1rem; padding: 0.375rem 0.75rem; line-height: 1.5;'>{current_page}</div>", unsafe_allow_html=True)
                        else:
                            # 다른 페이지 번호
                            if st.button(button_text, key=f"sync_page_simple_{button_text}_{project_key}"):
                                st.session_state[page_key] = int(button_text)
                                st.rerun()
            
            # 페이지 정보
            st.info(f"📄 {current_page} / {total_pages} 페이지 (전체 {len(filtered_issues)}개 이슈)")
        
        st.markdown("---")
        
        # 선택된 이슈 수 표시
        if selected_issues:
            st.success(f"✅ 선택된 이슈: **{len(selected_issues)}개** / 전체 {len(filtered_issues)}개")
        else:
            st.warning(f"⚠️ 선택된 이슈: **0개** / 전체 {len(filtered_issues)}개")
        
        # 동기화 실행 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            sync_disabled = len(selected_issues) == 0
            if st.button("🔄 선택된 이슈 동기화", type="primary", key=f"sync_selected_{project_key}", disabled=sync_disabled, use_container_width=True):
                if selected_issues:
                    with st.spinner(f"선택된 {len(selected_issues)}개 이슈를 동기화하는 중..."):
                        sync_result = sync_jira_project(project_key, selected_issues)
                        if sync_result:
                            st.success(f"✅ {len(selected_issues)}개 이슈 동기화 시작!")
                            st.cache_data.clear()
                            # 모달 닫기
                            del st.session_state[f'show_sync_modal_{project_key}']
                            # 동기화 완료 후 작업 관리 페이지로 이동
                            st.session_state.current_page = "작업 관리"
                            st.info("🔄 동기화가 완료되면 작업 관리 페이지에서 확인하실 수 있습니다.")
                            st.rerun()
                        else:
                            st.error("❌ 동기화 시작 실패")
        
        with col2:
            if st.button("🔄 전체 동기화", type="secondary", key=f"sync_all_{project_key}", use_container_width=True):
                with st.spinner(f"전체 {len(filtered_issues)}개 이슈를 동기화하는 중..."):
                    sync_result = sync_jira_project(project_key)
                    if sync_result:
                        st.success(f"✅ 전체 이슈 동기화 시작!")
                        st.cache_data.clear()
                        # 모달 닫기
                        del st.session_state[f'show_sync_modal_{project_key}']
                        # 동기화 완료 후 작업 관리 페이지로 이동
                        st.session_state.current_page = "작업 관리"
                        st.info("🔄 동기화가 완료되면 작업 관리 페이지에서 확인하실 수 있습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 동기화 시작 실패")
        
        with col3:
            if st.button("❌ 취소", key=f"cancel_sync_{project_key}", use_container_width=True):
                # 모달 닫기
                del st.session_state[f'show_sync_modal_{project_key}']
                st.rerun()
    
    else:
        st.error(f"❌ {project_key} 프로젝트의 이슈를 가져올 수 없습니다.")
        st.info("💡 프로젝트가 비활성화되었거나 이슈가 없을 수 있습니다.")
        
        # 취소 버튼만 표시
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("❌ 닫기", key=f"close_modal_{project_key}", type="primary", use_container_width=True):
                del st.session_state[f'show_sync_modal_{project_key}']
                st.rerun()

def get_sync_status(project_key):
    """동기화 상태 조회"""
    return api_call(f"/jira/sync-status/{project_key}")

def reset_all_tasks():
    """모든 작업 데이터 초기화"""
    return api_call("/tasks/reset", method="DELETE")

def delete_task(task_id):
    """개별 작업 삭제"""
    return api_call(f"/tasks/{task_id}", method="DELETE")

def update_qa_status(task_id, qa_status):
    """작업의 QA 상태 업데이트"""
    return api_call(f"/tasks/{task_id}/qa-status?qa_status={qa_status}", method="PUT")

def update_task_memo(task_id, memo):
    """작업의 메모 업데이트"""
    data = {"memo": memo}
    return api_call(f"/tasks/{task_id}/memo", method="PUT", data=data)

def get_task_memo(task_id):
    """작업의 메모 조회"""
    return api_call(f"/tasks/{task_id}/memo")

def get_jira_issue_url(jira_key):
    """지라 이슈 URL 생성"""
    # 환경변수에서 지라 서버 URL 가져오기 (기본값 설정)
    jira_server = "https://dramancompany.atlassian.net"  # 실제 지라 서버 URL
    return f"{jira_server}/browse/{jira_key}"

def create_jira_link(jira_key):
    """지라 이슈 링크 HTML 생성"""
    if not jira_key or jira_key == 'N/A':
        return jira_key
    
    jira_url = get_jira_issue_url(jira_key)
    return f'<a href="{jira_url}" target="_blank" style="color: #0066cc; text-decoration: none; font-weight: bold;">{jira_key} 🔗</a>'

def clear_work_states():
    """모든 작업 상태 초기화 (사이드바 클릭 시 호출)"""
    # 동기화 모달 관련 상태 초기화
    keys_to_remove = []
    for key in st.session_state.keys():
        if (key.startswith('show_sync_modal_') or 
            key.startswith('sync_modal_project_name_') or
            key.startswith('issue_selected_') or
            key.startswith('confirm_delete_') or
            key.startswith('confirm_reset') or
            key.startswith('page_') or
            key.startswith('status_filter_') or
            key.startswith('priority_filter_') or
            key.startswith('assignee_filter_')):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]


def main():
    # API 연결 상태 확인
    if not check_api_connection():
        st.error("⚠️ 백엔드 서버에 연결할 수 없습니다.")
        st.info("백엔드 서버 실행: `python3 backend/server.py`")
        return
    
    # 고급스러운 사이드바 디자인
    st.sidebar.markdown("""
    <div style="text-align: left; padding: 1.5rem 0; margin-bottom: 1rem;">
        <h2 style="color: #ffffff; font-size: 1.8rem; margin: 0; font-weight: 600;">
            🎯 QA Hub
        </h2>
        <div style="width: 80px; height: 2px; background: linear-gradient(90deg, #ffffff, #e0e0e0); margin: 0.5rem 0; border-radius: 1px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 페이지 선택을 세션 상태로 관리
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "대시보드 홈"
    
    # 현재 페이지 표시를 위한 스타일
    current_page = st.session_state.current_page
    
    # 메인 메뉴 버튼들 (카테고리명 없이)
    # 대시보드 홈 버튼
    home_style = "primary" if current_page == "대시보드 홈" else "secondary"
    if st.sidebar.button("🏠 대시보드 홈", use_container_width=True, type=home_style):
        # 모든 작업 상태 초기화
        clear_work_states()
        st.session_state.current_page = "대시보드 홈"
        st.rerun()
    
    # 작업 관리 버튼
    task_style = "primary" if current_page == "작업 관리" else "secondary"
    if st.sidebar.button("📋 작업 관리", use_container_width=True, type=task_style):
        # 모든 작업 상태 초기화
        clear_work_states()
        st.session_state.current_page = "작업 관리"
        st.rerun()
    
    # 테스트 케이스 버튼
    test_style = "primary" if current_page == "테스트 케이스" else "secondary"
    if st.sidebar.button("🧪 테스트 케이스", use_container_width=True, type=test_style):
        # 모든 작업 상태 초기화
        clear_work_states()
        st.session_state.current_page = "테스트 케이스"
        st.rerun()
    
    # QA 요청서 버튼
    qa_request_style = "primary" if current_page == "QA 요청서" else "secondary"
    if st.sidebar.button("📝 QA 요청서", use_container_width=True, type=qa_request_style):
        # 모든 작업 상태 초기화
        clear_work_states()
        st.session_state.current_page = "QA 요청서"
        st.rerun()
    
    
    # 지라 프로젝트 관리 버튼
    project_style = "primary" if current_page == "지라 프로젝트 관리" else "secondary"
    if st.sidebar.button("📂 지라 프로젝트 관리", use_container_width=True, type=project_style):
        # 모든 작업 상태 초기화
        clear_work_states()
        st.session_state.current_page = "지라 프로젝트 관리"
        st.rerun()
    
    # 구분선
    st.sidebar.markdown("""
    <div style="margin: 2rem 0 1.5rem 0;">
        <div style="height: 1px; background: linear-gradient(90deg, transparent, #DEE2E6, transparent); margin: 1rem 0;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 상태 표시 섹션
    st.sidebar.markdown("""
    <div style="margin: 1rem 0;">
        <h4 style="color: #ffffff; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
            📡 상태
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # API 상태 표시 (더 고급스럽게)
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, #D4EDDA, #C3E6CB); padding: 0.8rem; border-radius: 8px; border-left: 4px solid #28A745; margin-bottom: 1rem;">
        <div style="display: flex; align-items: center;">
            <span style="color: #155724; font-weight: 600; font-size: 0.9rem;">
                ✅ API 서버 연결됨
            </span>
        </div>
        <div style="color: #155724; font-size: 0.75rem; margin-top: 0.2rem; opacity: 0.8;">
            모든 시스템 정상 작동
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 하단 여백
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    # 지라 연동 관리 (데이터 새로고침 포함)
    st.sidebar.markdown("""
    <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #DEE2E6;">
        <h4 style="color: #ffffff; font-size: 0.8rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.8rem;">
            🔗 연동 관리
        </h4>
    </div>
    """, unsafe_allow_html=True)
    
    # 데이터 새로고침 버튼 (연동 관리 하위로 이동)
    if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True, help="캐시를 지우고 최신 데이터를 불러옵니다"):
        st.cache_data.clear()
        st.rerun()
    
    jira_style = "primary" if current_page == "지라 연동 관리" else "secondary"
    if st.sidebar.button("⚙️ 지라 설정", use_container_width=True, type=jira_style, help="지라 연동 설정 및 프로젝트 동기화"):
        st.session_state.current_page = "지라 연동 관리"
        st.rerun()
    
    # 현재 선택된 페이지 표시
    current_page = st.session_state.current_page
    
    # 페이지별 내용
    if current_page == "대시보드 홈":
        show_dashboard_home()
    elif current_page == "지라 연동 관리":
        show_jira_management()
    elif current_page == "작업 관리":
        show_task_management()
    elif current_page == "테스트 케이스":
        show_test_cases()
    elif current_page == "QA 요청서":
        show_qa_requests()
    elif current_page == "지라 프로젝트 관리":
        show_jira_project_management()

def show_dashboard_home():
    """대시보드 홈 화면"""
    # 제목 - 대시보드 홈에서만 표시
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-bottom: 2rem;">
        <h1 style="color: #2E86AB; font-size: 3rem; margin: 0; font-weight: 700;">
            🎯 Quality Hub
        </h1>
        <p style="color: #6C757D; font-size: 1.2rem; margin: 0.5rem 0 0 0; font-weight: 300;">
            Quality Assurance Management Platform
        </p>
        <div style="width: 100px; height: 3px; background: linear-gradient(90deg, #2E86AB, #A23B72); margin: 1rem auto; border-radius: 2px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.header("📊 QA 현황 대시보드")
    
    # 통계 데이터 가져오기
    stats = get_dashboard_stats()
    jira_projects_data = get_jira_projects()
    
    if not stats:
        st.error("통계 데이터를 불러올 수 없습니다.")
        return
    
    # 상단 메트릭 카드
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📋 전체 작업", 
            value=stats.get("total_tasks", 0),
            delta=f"+{stats.get('qa_ready_tasks', 0)} QA 대기"
        )
    
    with col2:
        st.metric(
            label="✅ 완료된 작업", 
            value=stats.get("completed_tasks", 0),
            delta=f"{stats.get('completion_rate', 0)}% 완료율"
        )
    
    with col3:
        st.metric(
            label="🔍 진행 중", 
            value=stats.get("in_progress_tasks", 0),
            delta="활성 작업"
        )
    
    with col4:
        st.metric(
            label="🎯 QA 대기", 
            value=stats.get("qa_ready_tasks", 0),
            delta="테스트 준비"
        )
    
    with col5:
        # 지라 프로젝트 수 표시
        project_count = 0
        if jira_projects_data and jira_projects_data.get("projects"):
            project_count = len(jira_projects_data["projects"])
        
        st.metric(
            label="🔗 지라 프로젝트", 
            value=project_count,
            delta="연동됨" if project_count > 0 else "미연동"
        )
    
    st.markdown("---")
    
    # 실시간 작업 목록
    st.subheader("📋 최근 동기화된 작업")
    tasks = get_tasks()
    
    if tasks:
        # 최근 동기화된 작업들만 표시
        recent_tasks = [t for t in tasks if t.get('last_sync')]
        
        if recent_tasks:
            task_df = pd.DataFrame(recent_tasks)
            
            # 표시할 컬럼 선택
            display_columns = ['jira_key', 'title', 'status', 'assignee', 'priority']
            if all(col in task_df.columns for col in display_columns):
                display_df = task_df[display_columns].copy()
                
                # 지라 키를 클릭 가능한 링크로 변환
                if 'jira_key' in display_df.columns:
                    display_df['jira_key'] = display_df['jira_key'].apply(create_jira_link)
                
                # 상태별 이모지 추가
                status_emoji = {
                    'Done': '✅',
                    'In Progress': '🔄', 
                    'QA Ready': '🎯',
                    'To Do': '📝'
                }
                
                if 'status' in display_df.columns:
                    display_df['status'] = display_df['status'].apply(
                        lambda x: f"{status_emoji.get(x, '⚪')} {x}"
                    )
                
                display_df.columns = ['지라 키', '제목', '상태', '담당자', '우선순위']
                
                # HTML 렌더링을 위해 st.markdown 사용
                st.markdown("**📋 최근 동기화된 작업 목록**")
                
                # 테이블 형태로 HTML 생성 (다크 테마에 맞는 고급스러운 색상)
                html_table = "<table style='width: 100%; border-collapse: collapse; background-color: #1e1e1e; border-radius: 8px; overflow: hidden;'>"
                html_table += "<tr style='background-color: #2d3748; font-weight: bold;'>"
                for col in display_df.columns:
                    html_table += f"<th style='padding: 14px; border: 1px solid #4a5568; text-align: left; color: #e2e8f0; font-size: 14px;'>{col}</th>"
                html_table += "</tr>"
                
                for i, (_, row) in enumerate(display_df.iterrows()):
                    # 교대로 다른 배경색 적용 (어두운 톤)
                    bg_color = "#2d3748" if i % 2 == 0 else "#1a202c"
                    html_table += f"<tr style='background-color: {bg_color}; border-bottom: 1px solid #4a5568; transition: background-color 0.2s;' onmouseover='this.style.backgroundColor=\"#374151\"' onmouseout='this.style.backgroundColor=\"{bg_color}\"'>"
                    for col in display_df.columns:
                        value = row[col] if row[col] != 'N/A' else ''
                        html_table += f"<td style='padding: 14px; border: 1px solid #4a5568; color: #cbd5e0; font-size: 13px;'>{value}</td>"
                    html_table += "</tr>"
                
                html_table += "</table>"
                st.markdown(html_table, unsafe_allow_html=True)
            else:
                st.dataframe(task_df, width='stretch')
                
            # 동기화 정보
            if recent_tasks:
                last_sync = max([t.get('last_sync', '') for t in recent_tasks if t.get('last_sync')])
                if last_sync:
                    st.info(f"🕐 마지막 동기화: {last_sync}")
        else:
            st.info("동기화된 작업이 없습니다. '지라 연동 관리' 페이지에서 동기화를 실행해주세요.")
    else:
        st.info("작업 데이터가 없습니다.")

def show_jira_management():
    """지라 연동 관리 화면"""
    st.header("🔗 지라 연동 관리")
    
    # 연결 테스트 섹션
    st.subheader("1️⃣ 지라 연결 테스트")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔍 지라 연결 테스트", type="primary"):
            with st.spinner("지라 연결 확인 중..."):
                jira_status = test_jira_connection()
                
                if jira_status and jira_status.get("success"):
                    st.markdown(f"""
                    <div style="background-color: #e8ede8; padding: 1rem; border-radius: 0.5rem; border-left: 0.25rem solid #5a6b5a; color: #3a4a3a;">
                        <h4 style="color: #3a4a3a; margin-top: 0;">✅ 지라 연결 성공</h4>
                        <p><strong>서버:</strong> {jira_status.get('server')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    error_msg = jira_status.get('message') if jira_status else '연결 실패'
                    st.markdown(f"""
                    <div class="error-box">
                        <h4>❌ 지라 연결 실패</h4>
                        <p><strong>오류:</strong> {error_msg}</p>
                        <p>API 토큰과 서버 설정을 확인해주세요.</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        ### 📋 연결 확인 항목
        - ✅ API 토큰 유효성
        - ✅ 서버 접근 가능성
        - ✅ 사용자 인증
        - ✅ 권한 확인
        """)
    
    st.markdown("---")
    
    # 지라 설정 정보
    st.subheader("2️⃣ 지라 설정 정보")
    
    # 설정 정보 표시
    st.markdown("""
    ### 📂 프로젝트 관리
    지라 프로젝트 목록 조회 및 동기화는 **'📂 지라 프로젝트 관리'** 메뉴에서 이용하실 수 있습니다.
    """)
    
    # 빠른 액세스 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📂 지라 프로젝트 관리로 이동", type="primary", use_container_width=True):
            st.session_state.current_page = "지라 프로젝트 관리"
            st.rerun()
    
    with col2:
        if st.button("🔄 캐시 초기화", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ 캐시가 초기화되었습니다.")
            st.rerun()

def show_task_management():
    """작업 관리 화면"""
    st.header("📋 작업 관리")
    
    # 상단 액션 버튼들
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        projects = get_projects()
        project_options = ["전체"] + [p["name"] for p in projects] if projects else ["전체"]
        selected_project = st.selectbox("프로젝트", project_options)
    
    with col2:
        status_filter = st.selectbox("상태 필터", ["전체", "QA Ready", "In Progress", "Done", "To Do"])
    
    with col3:
        assignee_filter = st.selectbox("담당자 필터", ["전체"])
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)  # 버튼 위치 맞추기
        if st.button("🗑️ 초기화", type="secondary", help="모든 작업 데이터를 삭제합니다"):
            # 확인 대화상자
            if 'confirm_reset' not in st.session_state:
                st.session_state.confirm_reset = False
            
            if not st.session_state.confirm_reset:
                st.session_state.confirm_reset = True
                st.rerun()
    
    # 초기화 확인 대화상자
    if st.session_state.get('confirm_reset', False):
        st.warning("⚠️ **데이터 초기화 확인**")
        st.markdown("""
        **다음 데이터가 모두 삭제됩니다:**
        - 모든 동기화된 작업 데이터
        - 프로젝트 동기화 기록
        - 작업 상태 및 할당 정보
        
        **이 작업은 되돌릴 수 없습니다!**
        """)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ 확인", type="primary"):
                with st.spinner("데이터 초기화 중..."):
                    result = reset_all_tasks()
                    
                    if result and result.get("success"):
                        st.success(f"✅ {result.get('message')}")
                        st.info(f"📊 삭제된 작업: {result.get('deleted_tasks', 0)}개")
                        st.cache_data.clear()  # 캐시 클리어
                        st.session_state.confirm_reset = False
                        st.rerun()
                    else:
                        st.error("❌ 데이터 초기화에 실패했습니다.")
                        st.session_state.confirm_reset = False
        
        with col2:
            if st.button("❌ 취소"):
                st.session_state.confirm_reset = False
                st.rerun()
        
        with col3:
            st.empty()  # 공간 확보
        
        st.markdown("---")
    
    # 작업 목록
    project_id = None
    if selected_project != "전체" and projects:
        project_id = next((p["id"] for p in projects if p["name"] == selected_project), None)
    
    status = status_filter if status_filter != "전체" else None
    tasks = get_tasks(project_id=project_id, status=status)
    
    if tasks:
        st.subheader(f"📊 작업 목록 ({len(tasks)}개)")
        
        # 우선순위별 정렬 옵션
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("정렬 기준", ["우선순위", "상태", "업데이트 시간"])
        with col2:
            sort_order = st.selectbox("정렬 순서", ["높은 순", "낮은 순"])
        
        # 우선순위 매핑
        priority_order = {"Highest": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
        qa_status_order = {"QA 완료": 4, "QA 진행중": 3, "QA 시작": 2, "미시작": 1}
        
        # 정렬 적용
        if sort_by == "우선순위":
            tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'Medium'), 3), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "상태":
            tasks.sort(key=lambda x: qa_status_order.get(x.get('status', '미시작'), 1), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "업데이트 시간":
            tasks.sort(key=lambda x: x.get('updated_at', ''), 
                      reverse=(sort_order == "높은 순"))
        
        # 동기화된 작업과 일반 작업 구분
        synced_tasks = [t for t in tasks if t.get('last_sync')]
        manual_tasks = [t for t in tasks if not t.get('last_sync')]
        
        if synced_tasks:
            st.markdown("### 🔗 지라 동기화 작업")
            
            # 컴팩트한 카드 형태로 표시
            for i, task in enumerate(synced_tasks):
                # 우선순위별 색상 설정
                priority = task.get('priority', 'Medium')
                priority_colors = {
                    'Highest': '#dc3545',  # 빨간색
                    'High': '#fd7e14',     # 주황색
                    'Medium': '#ffc107',   # 노란색
                    'Low': '#28a745',      # 초록색
                    'Lowest': '#6c757d'    # 회색
                }
                priority_color = priority_colors.get(priority, '#ffc107')
                
                # QA 상태별 색상
                qa_status = task.get('status', '미시작')
                qa_colors = {
                    'QA 완료': '#28a745',
                    'QA 진행중': '#17a2b8', 
                    'QA 시작': '#ffc107',
                    '미시작': '#6c757d'
                }
                qa_color = qa_colors.get(qa_status, '#6c757d')
                
                # 컴팩트한 카드 UI
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                        border-left: 4px solid {priority_color};
                        border-radius: 8px;
                        padding: 1rem;
                        margin: 0.5rem 0;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1; min-width: 0;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                    <span style="
                                        background: {priority_color}; 
                                        color: white; 
                                        padding: 0.2rem 0.5rem; 
                                        border-radius: 12px; 
                                        font-size: 0.7rem; 
                                        font-weight: bold;
                                    ">{priority}</span>
                                    <span style="color: #63b3ed; font-weight: bold; font-size: 0.9rem;">
                                        {task.get('jira_key', 'N/A')}
                                    </span>
                                </div>
                                <h4 style="color: #e2e8f0; margin: 0 0 0.5rem 0; font-size: 1rem; line-height: 1.3;">
                                    {task.get('title', 'N/A')[:80]}{'...' if len(task.get('title', '')) > 80 else ''}
                                </h4>
                                <div style="display: flex; gap: 1rem; font-size: 0.8rem; color: #a0aec0;">
                                    <span>👤 {task.get('assignee', 'N/A')}</span>
                                    <span>📊 {task.get('status', 'N/A')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # QA 상태 변경을 위한 인라인 컨트롤
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        # 지라 링크 버튼
                        jira_key = task.get('jira_key', 'N/A')
                        if jira_key and jira_key != 'N/A':
                            jira_url = get_jira_issue_url(jira_key)
                            st.markdown(f'<a href="{jira_url}" target="_blank"><button style="background: #0066cc; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer;">🔗 지라 보기</button></a>', unsafe_allow_html=True)
                    
                    with col2:
                        # QA 상태 변경 (컴팩트) - 라벨 추가
                        current_status = task.get('status', '미시작')
                        qa_statuses = ["미시작", "QA 시작", "QA 진행중", "QA 완료"]
                        
                        st.markdown("<small style='color: #a0aec0;'>검수 상태 :</small>", unsafe_allow_html=True)
                        new_status = st.selectbox(
                            "검수 상태", 
                            qa_statuses, 
                            index=qa_statuses.index(current_status) if current_status in qa_statuses else 0,
                            key=f"qa_status_{task.get('id')}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        # 상태가 변경되면 자동으로 저장
                        if new_status != current_status:
                            result = update_qa_status(task.get('id'), new_status)
                            if result and result.get("success"):
                                st.success(f"✅ QA 상태 변경: {new_status}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ 상태 변경 실패")
                    
                    with col3:
                        # 상세 보기 버튼
                        if st.button("📋", key=f"detail_{task.get('id')}_{i}", help="상세 정보 보기"):
                            # 상세 정보 토글
                            detail_key = f"show_detail_{task.get('id')}"
                            if detail_key not in st.session_state:
                                st.session_state[detail_key] = False
                            st.session_state[detail_key] = not st.session_state[detail_key]
                            st.rerun()
                    
                    with col4:
                        # 삭제 버튼
                        if st.button("🗑️", key=f"delete_synced_{task.get('id')}_{i}", help="작업 삭제"):
                            if f'confirm_delete_{task.get("id")}' not in st.session_state:
                                st.session_state[f'confirm_delete_{task.get("id")}'] = True
                                st.rerun()
                    
                    # 메모 기능 추가
                    with st.expander("📝 메모", expanded=False):
                        # 현재 메모 불러오기
                        current_memo = ""
                        memo_data = get_task_memo(task.get('id'))
                        if memo_data and memo_data.get('memo'):
                            current_memo = memo_data['memo']
                        
                        # 메모 입력 필드
                        memo_text = st.text_area(
                            "메모 내용",
                            value=current_memo,
                            height=100,
                            key=f"memo_synced_{task.get('id')}_{i}",
                            placeholder="QA 진행 상황, 발견된 이슈, 특이사항 등을 기록하세요..."
                        )
                        
                        # 메모 저장 버튼
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("💾 저장", key=f"save_memo_synced_{task.get('id')}_{i}"):
                                result = update_task_memo(task.get('id'), memo_text)
                                if result and result.get("success"):
                                    st.success("✅ 메모가 저장되었습니다.")
                                else:
                                    st.error("❌ 메모 저장에 실패했습니다.")
                        
                        with col2:
                            if current_memo:
                                st.info(f"📅 마지막 수정: {memo_data.get('updated_at', '알 수 없음')}")
                    
                    # 상세 정보 표시 (토글)
                    detail_key = f"show_detail_{task.get('id')}"
                    if st.session_state.get(detail_key, False):
                        st.markdown(f"""
                        <div style="background: #1a202c; padding: 1rem; border-radius: 6px; margin-top: 0.5rem; border-left: 2px solid {qa_color};">
                            <div style="color: #cbd5e0; font-size: 0.9rem; line-height: 1.5;">
                                <strong style="color: #e2e8f0;">📝 설명:</strong><br>
                                {task.get('description', '설명이 없습니다.')[:300]}{'...' if len(task.get('description', '')) > 300 else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 개별 삭제 확인 대화상자
                    if st.session_state.get(f'confirm_delete_{task.get("id")}', False):
                        st.warning(f"⚠️ **작업 삭제 확인**")
                        st.write(f"**{task.get('jira_key')} - {task.get('title')}** 작업을 삭제하시겠습니까?")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ 삭제 확인", key=f"confirm_del_{task.get('id')}"):
                                result = delete_task(task.get('id'))
                                if result and result.get("success"):
                                    st.success("✅ 작업이 삭제되었습니다.")
                                    st.cache_data.clear()
                                    del st.session_state[f'confirm_delete_{task.get("id")}']
                                    st.rerun()
                                else:
                                    st.error("❌ 작업 삭제에 실패했습니다.")
                        
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_del_{task.get('id')}"):
                                del st.session_state[f'confirm_delete_{task.get("id")}']
                                st.rerun()
        
        if manual_tasks:
            st.markdown("### 📝 수동 생성 작업")
            
            # 컴팩트한 카드 형태로 표시
            for i, task in enumerate(manual_tasks):
                # 우선순위별 색상 설정
                priority = task.get('priority', 'Medium')
                priority_colors = {
                    'Highest': '#dc3545',  # 빨간색
                    'High': '#fd7e14',     # 주황색
                    'Medium': '#ffc107',   # 노란색
                    'Low': '#28a745',      # 초록색
                    'Lowest': '#6c757d'    # 회색
                }
                priority_color = priority_colors.get(priority, '#ffc107')
                
                # QA 상태별 색상
                qa_status = task.get('status', '미시작')
                qa_colors = {
                    'QA 완료': '#28a745',
                    'QA 진행중': '#17a2b8', 
                    'QA 시작': '#ffc107',
                    '미시작': '#6c757d'
                }
                qa_color = qa_colors.get(qa_status, '#6c757d')
                
                # 컴팩트한 카드 UI
                with st.container():
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                        border-left: 4px solid {priority_color};
                        border-radius: 8px;
                        padding: 1rem;
                        margin: 0.5rem 0;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    ">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1; min-width: 0;">
                                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                    <span style="
                                        background: {priority_color}; 
                                        color: white; 
                                        padding: 0.2rem 0.5rem; 
                                        border-radius: 12px; 
                                        font-size: 0.7rem; 
                                        font-weight: bold;
                                    ">{priority}</span>
                                    <span style="color: #63b3ed; font-weight: bold; font-size: 0.9rem;">
                                        {task.get('jira_key', 'N/A')}
                                    </span>
                                </div>
                                <h4 style="color: #e2e8f0; margin: 0 0 0.5rem 0; font-size: 1rem; line-height: 1.3;">
                                    {task.get('title', 'N/A')[:80]}{'...' if len(task.get('title', '')) > 80 else ''}
                                </h4>
                                <div style="display: flex; gap: 1rem; font-size: 0.8rem; color: #a0aec0;">
                                    <span>👤 {task.get('assignee', 'N/A')}</span>
                                    <span>📊 {task.get('status', 'N/A')}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # QA 상태 변경을 위한 인라인 컨트롤
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        # 지라 링크 버튼
                        jira_key = task.get('jira_key', 'N/A')
                        if jira_key and jira_key != 'N/A':
                            jira_url = get_jira_issue_url(jira_key)
                            st.markdown(f'<a href="{jira_url}" target="_blank"><button style="background: #0066cc; color: white; border: none; padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer;">🔗 지라 보기</button></a>', unsafe_allow_html=True)
                    
                    with col2:
                        # QA 상태 변경 (컴팩트) - 라벨 추가
                        current_status = task.get('status', '미시작')
                        qa_statuses = ["미시작", "QA 시작", "QA 진행중", "QA 완료"]
                        
                        st.markdown("<small style='color: #a0aec0;'>검수 상태 :</small>", unsafe_allow_html=True)
                        new_status = st.selectbox(
                            "검수 상태", 
                            qa_statuses, 
                            index=qa_statuses.index(current_status) if current_status in qa_statuses else 0,
                            key=f"qa_status_manual_{task.get('id')}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        # 상태가 변경되면 자동으로 저장
                        if new_status != current_status:
                            result = update_qa_status(task.get('id'), new_status)
                            if result and result.get("success"):
                                st.success(f"✅ QA 상태 변경: {new_status}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ 상태 변경 실패")
                    
                    with col3:
                        # 상세 보기 버튼
                        if st.button("📋", key=f"detail_manual_{task.get('id')}_{i}", help="상세 정보 보기"):
                            # 상세 정보 토글
                            detail_key = f"show_detail_manual_{task.get('id')}"
                            if detail_key not in st.session_state:
                                st.session_state[detail_key] = False
                            st.session_state[detail_key] = not st.session_state[detail_key]
                            st.rerun()
                    
                    with col4:
                        # 삭제 버튼
                        if st.button("🗑️", key=f"delete_manual_{task.get('id')}_{i}", help="작업 삭제"):
                            if f'confirm_delete_{task.get("id")}' not in st.session_state:
                                st.session_state[f'confirm_delete_{task.get("id")}'] = True
                                st.rerun()
                    
                    # 메모 기능 추가 (수동 작업)
                    with st.expander("📝 메모", expanded=False):
                        # 현재 메모 불러오기
                        current_memo = ""
                        memo_data = get_task_memo(task.get('id'))
                        if memo_data and memo_data.get('memo'):
                            current_memo = memo_data['memo']
                        
                        # 메모 입력 필드
                        memo_text = st.text_area(
                            "메모 내용",
                            value=current_memo,
                            height=100,
                            key=f"memo_manual_{task.get('id')}_{i}",
                            placeholder="QA 진행 상황, 발견된 이슈, 특이사항 등을 기록하세요..."
                        )
                        
                        # 메모 저장 버튼
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            if st.button("💾 저장", key=f"save_memo_manual_{task.get('id')}_{i}"):
                                result = update_task_memo(task.get('id'), memo_text)
                                if result and result.get("success"):
                                    st.success("✅ 메모가 저장되었습니다.")
                                else:
                                    st.error("❌ 메모 저장에 실패했습니다.")
                        
                        with col2:
                            if current_memo:
                                st.info(f"📅 마지막 수정: {memo_data.get('updated_at', '알 수 없음')}")
                    
                    # 상세 정보 표시 (토글)
                    detail_key = f"show_detail_manual_{task.get('id')}"
                    if st.session_state.get(detail_key, False):
                        st.markdown(f"""
                        <div style="background: #1a202c; padding: 1rem; border-radius: 6px; margin-top: 0.5rem; border-left: 2px solid {qa_color};">
                            <div style="color: #cbd5e0; font-size: 0.9rem; line-height: 1.5;">
                                <strong style="color: #e2e8f0;">📝 설명:</strong><br>
                                {task.get('description', '설명이 없습니다.')[:300]}{'...' if len(task.get('description', '')) > 300 else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # 개별 삭제 확인 대화상자
                    if st.session_state.get(f'confirm_delete_{task.get("id")}', False):
                        st.warning(f"⚠️ **작업 삭제 확인**")
                        st.write(f"**{task.get('jira_key')} - {task.get('title')}** 작업을 삭제하시겠습니까?")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ 삭제 확인", key=f"confirm_del_manual_{task.get('id')}"):
                                result = delete_task(task.get('id'))
                                if result and result.get("success"):
                                    st.success("✅ 작업이 삭제되었습니다.")
                                    st.cache_data.clear()
                                    del st.session_state[f'confirm_delete_{task.get("id")}']
                                    st.rerun()
                                else:
                                    st.error("❌ 작업 삭제에 실패했습니다.")
                        
                        with col2:
                            if st.button("❌ 취소", key=f"cancel_del_manual_{task.get('id')}"):
                                del st.session_state[f'confirm_delete_{task.get("id")}']
                                st.rerun()
    else:
        st.info("작업이 없습니다. 지라에서 프로젝트를 동기화해주세요.")

def show_jira_project_management():
    """지라 프로젝트 관리 화면"""
    st.header("📂 지라 프로젝트 관리")
    
    # 동기화 모달 표시 확인
    for key in list(st.session_state.keys()):
        if key.startswith('show_sync_modal_'):
            project_key = key.replace('show_sync_modal_', '')
            project_name = st.session_state.get(f'sync_modal_project_name_{project_key}', project_key)
            show_sync_modal(project_key, project_name)
            return  # 모달이 표시되면 다른 내용은 표시하지 않음
    
    # 자주 사용하는 프로젝트 관리 (영구 저장)
    def load_frequent_projects():
        """자주 사용하는 프로젝트 목록을 파일에서 로드"""
        try:
            import os
            config_file = "frequent_projects.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return ['Remember_Android', 'Remember_iOS', 'RB']  # 기본값
    
    def save_frequent_projects(projects):
        """자주 사용하는 프로젝트 목록을 파일에 저장"""
        try:
            with open("frequent_projects.json", 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    if 'frequent_projects' not in st.session_state:
        st.session_state.frequent_projects = load_frequent_projects()
    
    # 자동으로 지라 프로젝트 목록 로드
    with st.spinner("지라 프로젝트 목록 로드 중..."):
        jira_projects_data = get_jira_projects()
        
        if jira_projects_data and jira_projects_data.get("projects"):
            projects = jira_projects_data["projects"]
            
            # 상단에 통계 정보 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📂 전체 프로젝트", len(projects))
            with col2:
                if st.button("🔄 목록 새로고침"):
                    st.cache_data.clear()
                    st.rerun()
            with col3:
                # 검색 기능
                search_term = st.text_input("🔍 프로젝트 검색", placeholder="프로젝트명 또는 키 입력")
            
            # 자주 사용하는 프로젝트와 일반 프로젝트 분리
            frequent_projects = []
            other_projects = []
            
            for project in projects:
                project_key = project.get('key', '')
                project_name = project.get('name', '')
                
                # 자주 사용하는 프로젝트 키워드 매칭 (세션 상태 기반) - 정확한 매칭
                is_frequent = False
                for keyword in st.session_state.frequent_projects:
                    # 프로젝트 키가 정확히 일치하는 경우만
                    if keyword.lower() == project_key.lower():
                        is_frequent = True
                        break
                
                if is_frequent:
                    frequent_projects.append(project)
                else:
                    other_projects.append(project)
            
            # 검색 필터링
            if search_term:
                filtered_frequent = [
                    p for p in frequent_projects 
                    if search_term.lower() in p.get('name', '').lower() 
                    or search_term.lower() in p.get('key', '').lower()
                ]
                filtered_other = [
                    p for p in other_projects 
                    if search_term.lower() in p.get('name', '').lower() 
                    or search_term.lower() in p.get('key', '').lower()
                ]
                filtered_projects = filtered_frequent + filtered_other
            else:
                filtered_frequent = frequent_projects
                filtered_other = other_projects
                filtered_projects = frequent_projects + other_projects
            
            # 통계 표시
            if search_term:
                st.success(f"✅ {len(filtered_projects)}개 프로젝트 표시 중 (전체 {len(projects)}개)")
            else:
                st.success(f"✅ 자주 사용: {len(frequent_projects)}개, 기타: {len(other_projects)}개 (전체 {len(projects)}개)")
            
            # 프로젝트 목록을 테이블 형태로 표시
            if filtered_projects:
                # 자주 사용하는 프로젝트 먼저 표시
                if not search_term and frequent_projects:
                    st.markdown("### ⭐ 자주 사용하는 프로젝트")
                    
                    # 자주 사용하는 프로젝트만 표시
                    for i, project in enumerate(frequent_projects):
                        project_key = project.get('key', 'Unknown')
                        project_name = project.get('name', 'Unknown')
                        issue_count = project.get('issue_count')
                        is_active = project.get('is_active')
                        
                        # 프로젝트 타입에 따른 이모지
                        project_type = project.get('projectTypeKey', 'software')
                        type_emoji = {
                            'software': '💻',
                            'business': '📊', 
                            'service_desk': '🎧',
                            'ops': '⚙️'
                        }
                        emoji = type_emoji.get(project_type, '📁')
                        
                        # 활성 프로젝트 표시 (이슈 수 기반)
                        if is_active is True:
                            title_prefix = "🟢 "  # 활성 프로젝트
                            issue_info = f" ({issue_count}개 이슈)"
                        elif is_active is False:
                            title_prefix = "🔴 "  # 비활성 프로젝트
                            issue_info = " (이슈 없음)"
                        else:
                            title_prefix = "⭐ "  # 자주 사용하는 프로젝트
                            issue_info = ""
                        
                        with st.expander(f"{title_prefix}{emoji} {project_key} - {project_name}{issue_info}"):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**프로젝트 키:** {project_key}")
                                st.write(f"**프로젝트명:** {project_name}")
                                if project.get('description'):
                                    st.write(f"**설명:** {project.get('description')}")
                                st.write(f"**프로젝트 타입:** {project.get('projectTypeKey', 'Unknown')}")
                                st.success("⭐ 자주 사용하는 프로젝트")
                            
                            with col2:
                                # 자주 사용하는 프로젝트에서 해제 버튼
                                if st.button(f"❌ 해제", key=f"remove_frequent_{project.get('key')}_{i}", type="secondary", help="자주 사용하는 프로젝트에서 제거"):
                                    # 프로젝트 키워드 찾아서 제거 - 정확한 매칭
                                    project_key = project.get('key', '')
                                    project_name = project.get('name', '')
                                    
                                    # 매칭되는 키워드 찾기 (정확한 매칭 로직)
                                    matching_keywords = []
                                    for keyword in st.session_state.frequent_projects:
                                        # 프로젝트 키가 정확히 일치하는 경우만
                                        if keyword.lower() == project_key.lower():
                                            matching_keywords.append(keyword)
                                            break
                                    
                                    if matching_keywords:
                                        # 첫 번째 매칭 키워드 제거
                                        keyword_to_remove = matching_keywords[0]
                                        st.session_state.frequent_projects.remove(keyword_to_remove)
                                        # 파일에 저장
                                        save_frequent_projects(st.session_state.frequent_projects)
                                        st.success(f"✅ '{project_key}' 프로젝트가 자주 사용하는 프로젝트에서 제거되었습니다.")
                                        st.rerun()
                                
                                if st.button(f"🔄 동기화", key=f"sync_frequent_{project.get('key')}_{i}"):
                                    project_key = project.get('key')
                                    project_name = project.get('name', project_key)
                                    
                                    # 이슈 선택 모달 표시
                                    st.session_state[f'show_sync_modal_{project_key}'] = True
                                    st.session_state[f'sync_modal_project_name_{project_key}'] = project_name
                                    st.rerun()
                            
                    
                    # 구분선
                    if other_projects:
                        st.markdown("---")
                        st.markdown("### 📂 기타 프로젝트")
                
                # 기타 프로젝트 또는 검색 결과 표시
                display_projects = filtered_other if not search_term else filtered_projects
                
                # 페이지네이션 (기타 프로젝트 영역)
                items_per_page = 20
                total_pages = (len(display_projects) + items_per_page - 1) // items_per_page
                
                if total_pages > 1:
                    # 현재 페이지 번호 가져오기
                    if "other_projects_page" not in st.session_state:
                        st.session_state.other_projects_page = 1
                    
                    current_page = st.session_state.other_projects_page
                    page_num = current_page - 1
                else:
                    page_num = 0
                
                start_idx = page_num * items_per_page
                end_idx = start_idx + items_per_page
                page_projects = display_projects[start_idx:end_idx]
                
                for i, project in enumerate(page_projects):
                    project_key = project.get('key', 'Unknown')
                    project_name = project.get('name', 'Unknown')
                    issue_count = project.get('issue_count')
                    is_active = project.get('is_active')
                    
                    # 프로젝트 타입에 따른 이모지
                    project_type = project.get('projectTypeKey', 'software')
                    type_emoji = {
                        'software': '💻',
                        'business': '📊', 
                        'service_desk': '🎧',
                        'ops': '⚙️'
                    }
                    emoji = type_emoji.get(project_type, '📁')
                    
                    # 활성 프로젝트 표시 (이슈 수 기반)
                    if is_active is True:
                        title_prefix = "🟢 "  # 활성 프로젝트
                        issue_info = f" ({issue_count}개 이슈)"
                    elif is_active is False:
                        title_prefix = "🔴 "  # 비활성 프로젝트
                        issue_info = " (이슈 없음)"
                    else:
                        # 키워드 기반 추천 (이슈 수 미확인)
                        title_prefix = ""
                        issue_info = ""
                    
                    # 키워드 기반 추천 여부 확인
                    is_recommended = any(keyword in project_key.upper() for keyword in ['DRAMA', 'MOBILE', 'WEB', 'TEST', 'DEV'])
                    if is_recommended:
                        title_prefix = "⭐ "
                    
                    with st.expander(f"{title_prefix}{emoji} {project_key} - {project_name}{issue_info}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**프로젝트 키:** {project_key}")
                            st.write(f"**프로젝트명:** {project_name}")
                            if project.get('description'):
                                st.write(f"**설명:** {project.get('description')}")
                            st.write(f"**프로젝트 타입:** {project.get('projectTypeKey', 'Unknown')}")
                            
                            if is_recommended:
                                st.success("⭐ 추천 프로젝트 - 최근 활동 가능성이 높습니다")
                        
                        with col2:
                            # 기타 프로젝트에서 자주 사용하는 프로젝트로 추가 버튼
                            if st.button(f"⭐ 추가", key=f"add_frequent_{project.get('key')}_{i}", type="primary", help="자주 사용하는 프로젝트에 추가"):
                                project_key = project.get('key', '')
                                
                                # 프로젝트 키를 자주 사용하는 프로젝트에 추가
                                if project_key and project_key not in st.session_state.frequent_projects:
                                    st.session_state.frequent_projects.append(project_key)
                                    # 파일에 저장
                                    save_frequent_projects(st.session_state.frequent_projects)
                                    st.success(f"✅ '{project_key}' 프로젝트가 자주 사용하는 프로젝트에 추가되었습니다.")
                                    st.rerun()
                                else:
                                    st.warning(f"⚠️ '{project_key}' 프로젝트는 이미 자주 사용하는 프로젝트에 포함되어 있습니다.")
                            
                            if st.button(f"🔄 동기화", key=f"sync_{project.get('key')}_{i}"):
                                project_key = project.get('key')
                                project_name = project.get('name', project_key)
                                
                                # 이슈 선택 모달 표시
                                st.session_state[f'show_sync_modal_{project_key}'] = True
                                st.session_state[f'sync_modal_project_name_{project_key}'] = project_name
                                st.rerun()
                
                # 페이지네이션 (목록 하단)
                if total_pages > 1:
                    st.markdown("---")
                    current_page = st.session_state.other_projects_page
                    
                    # 간단한 페이지네이션
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        # 페이지 번호 버튼들을 한 줄로 표시
                        page_buttons = []
                        
                        # 이전 버튼
                        if current_page > 1:
                            page_buttons.append("◀")
                        
                        # 페이지 번호들 (최대 5개)
                        start_page = max(1, current_page - 2)
                        end_page = min(total_pages, start_page + 4)
                        
                        if end_page - start_page < 4:
                            start_page = max(1, end_page - 4)
                        
                        for page in range(start_page, end_page + 1):
                            if page == current_page:
                                page_buttons.append(f"**{page}**")
                            else:
                                page_buttons.append(str(page))
                        
                        # 다음 버튼
                        if current_page < total_pages:
                            page_buttons.append("▶")
                        
                        # 버튼들을 한 줄로 표시 (간격 최소화)
                        button_cols = st.columns(len(page_buttons), gap="small")
                        for i, button_text in enumerate(page_buttons):
                            with button_cols[i]:
                                if button_text == "◀":
                                    if st.button("◀", key="prev_projects_simple"):
                                        st.session_state.other_projects_page = current_page - 1
                                        st.rerun()
                                elif button_text == "▶":
                                    if st.button("▶", key="next_projects_simple"):
                                        st.session_state.other_projects_page = current_page + 1
                                        st.rerun()
                                elif button_text.startswith("**"):
                                    # 현재 페이지 (텍스트만 표시, 버튼과 동일한 크기)
                                    st.markdown(f"<div style='text-align: center; color: #0066cc; font-weight: bold; font-size: 1rem; padding: 0.375rem 0.75rem; line-height: 1.5;'>{current_page}</div>", unsafe_allow_html=True)
                                else:
                                    # 다른 페이지 번호
                                    if st.button(button_text, key=f"page_simple_{button_text}"):
                                        st.session_state.other_projects_page = int(button_text)
                                        st.rerun()
                    
                    # 페이지 정보
                    st.info(f"📄 {current_page} / {total_pages} 페이지 (전체 {len(display_projects)}개 프로젝트)")
            else:
                st.info("검색 조건에 맞는 프로젝트가 없습니다.")
                
        else:
            st.error("❌ 지라 프로젝트를 조회할 수 없습니다. 연결 상태를 확인해주세요.")
            
            # 수동 새로고침 버튼 제공
            if st.button("🔄 다시 시도"):
                st.cache_data.clear()
                st.rerun()


def show_qa_requests():
    """QA 요청서 화면"""
    st.header("📝 QA 요청서 관리")
    
    # 탭으로 구분
    tab1, tab2 = st.tabs(["📝 QA 요청서 작성", "📋 QA 요청서 목록"])
    
    with tab1:
        show_qa_request_form()
    
    with tab2:
        show_qa_request_list()

def show_qa_request_form():
    """QA 요청서 작성 폼"""
    st.subheader("📝 QA 요청서 작성")
    
    # 세션 상태로 폼 데이터 관리
    if 'qa_form_data' not in st.session_state:
        st.session_state.qa_form_data = {
            'requester': '',
            'assignee': '',
            'project_name': '',
            'qa_content': '',
            'platforms': [],
            'build_link': '',
            'deployment_date': None,
            'doc_link_1': '',
            'doc_link_2': '',
            'doc_link_3': ''
        }
    
    # 작성자, 담당자 필드
    col1, col2 = st.columns(2)
    with col1:
        requester = st.text_input(
            "작성자 *", 
            value=st.session_state.qa_form_data['requester'],
            placeholder="예: 홍길동",
            help="QA를 요청하는 담당자 이름을 입력하세요",
            key="qa_requester"
        )
        st.session_state.qa_form_data['requester'] = requester
    
    with col2:
        assignee = st.text_input(
            "담당자", 
            value=st.session_state.qa_form_data['assignee'],
            placeholder="예: 김QA",
            help="QA를 담당할 사람 이름을 입력하세요 (선택사항)",
            key="qa_assignee"
        )
        st.session_state.qa_form_data['assignee'] = assignee
    
    # 프로젝트명
    project_name = st.text_input(
        "프로젝트명 *", 
        value=st.session_state.qa_form_data['project_name'],
        placeholder="예: Remember 앱 v2.1.0",
        help="QA를 요청할 프로젝트의 이름을 입력하세요",
        key="qa_project_name"
    )
    st.session_state.qa_form_data['project_name'] = project_name
    
    # 검수 희망 내용
    qa_content = st.text_area(
        "검수 희망 내용 *",
        value=st.session_state.qa_form_data['qa_content'],
        height=150,
        placeholder="예:\n- 로그인 기능 테스트\n- 회원가입 플로우 검증\n- UI/UX 개선사항 확인\n- 성능 테스트",
        help="구체적인 QA 요청 사항을 작성해주세요",
        key="qa_content"
    )
    st.session_state.qa_form_data['qa_content'] = qa_content
    
    # 플랫폼 선택
    st.markdown("**플랫폼 *")
    col1, col2, col3, col4 = st.columns(4)
    
    platforms = []
    with col1:
        if st.checkbox("📱 Android", key="platform_android"):
            platforms.append("android")
    with col2:
        if st.checkbox("📱 iOS", key="platform_ios"):
            platforms.append("ios")
    with col3:
        if st.checkbox("🌐 Web", key="platform_web"):
            platforms.append("web")
    with col4:
        if st.checkbox("🔌 API", key="platform_api"):
            platforms.append("api")
    
    st.session_state.qa_form_data['platforms'] = platforms
    
    # 빌드 링크
    build_link = st.text_input(
        "빌드 링크",
        value=st.session_state.qa_form_data['build_link'],
        placeholder="https://example.com/build/app.apk",
        help="테스트할 빌드 파일의 다운로드 링크를 입력하세요",
        key="qa_build_link"
    )
    st.session_state.qa_form_data['build_link'] = build_link
    
    # 희망 배포 날짜
    deployment_date = st.date_input(
        "희망 배포 날짜",
        value=st.session_state.qa_form_data['deployment_date'],
        help="QA 완료 후 배포를 희망하는 날짜를 선택하세요 (선택사항)",
        key="qa_deployment_date"
    )
    st.session_state.qa_form_data['deployment_date'] = deployment_date
    
    # 기획서/디자인문서 링크 관리 (폼 하단으로 이동)
    st.markdown("**기획서/디자인문서 링크**")
    
    # 링크 입력 필드들
    doc_link_1 = st.text_input(
        "문서 링크 1",
        value=st.session_state.qa_form_data['doc_link_1'],
        placeholder="https://example.com/document1",
        help="기획서나 디자인 문서 링크를 입력하세요",
        key="qa_doc_link_1"
    )
    st.session_state.qa_form_data['doc_link_1'] = doc_link_1
    
    doc_link_2 = st.text_input(
        "문서 링크 2 (선택사항)",
        value=st.session_state.qa_form_data['doc_link_2'],
        placeholder="https://example.com/document2",
        help="추가 문서 링크가 있다면 입력하세요",
        key="qa_doc_link_2"
    )
    st.session_state.qa_form_data['doc_link_2'] = doc_link_2
    
    doc_link_3 = st.text_input(
        "문서 링크 3 (선택사항)",
        value=st.session_state.qa_form_data['doc_link_3'],
        placeholder="https://example.com/document3",
        help="추가 문서 링크가 있다면 입력하세요",
        key="qa_doc_link_3"
    )
    st.session_state.qa_form_data['doc_link_3'] = doc_link_3
    
    # 폼 밖에서 실제 제출 버튼 (초록색)
    st.markdown("---")
    
    # 제출 버튼을 초록색으로 스타일링
    st.markdown("""
    <style>
    .stButton > button[kind="primary"] {
        background-color: #28a745 !important;
        border-color: #28a745 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #218838 !important;
        border-color: #1e7e34 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 QA 요청서 제출", type="primary", use_container_width=True):
        # 세션 상태에서 데이터 가져오기
        form_data = st.session_state.qa_form_data
        
        # 필수 필드 검증
        if not form_data['requester']:
            st.error("❌ 작성자를 입력해주세요.")
            return
        
        if not form_data['project_name']:
            st.error("❌ 프로젝트명을 입력해주세요.")
            return
        
        if not form_data['qa_content']:
            st.error("❌ 검수 희망 내용을 입력해주세요.")
            return
        
        if not form_data['platforms']:
            st.error("❌ 플랫폼을 하나 이상 선택해주세요.")
            return
        
        # 문서 링크 수집 (빈 링크 제거)
        doc_links = [link for link in [form_data['doc_link_1'], form_data['doc_link_2'], form_data['doc_link_3']] if link.strip()]
        
        # 문서 링크를 백엔드 형식으로 변환
        documents = []
        for i, link in enumerate(doc_links):
            documents.append({
                "document_type": "기획서/디자인문서",
                "document_name": f"문서 {i+1}",
                "document_link": link
            })
        
        # QA 요청서 데이터 구성 (백엔드 API 형식에 맞춤)
        qa_request_data = {
            "requester": form_data['requester'],
            "project_name": form_data['project_name'],
            "test_content": form_data['qa_content'],
            "platform": ",".join(form_data['platforms']),
            "build_link": form_data['build_link'] if form_data['build_link'].strip() else None,
            "desired_deploy_date": form_data['deployment_date'].isoformat() if form_data['deployment_date'] else None,
            "assignee": form_data['assignee'] if form_data['assignee'].strip() else None,
            "documents": documents
        }
        
        # API 호출
        with st.spinner("QA 요청서를 제출하는 중..."):
            result = api_call("/qa-requests", method="POST", data=qa_request_data)
            
            if result and result.get("success"):
                st.success("✅ QA 요청서가 성공적으로 제출되었습니다!")
                st.info(f"📋 요청서 ID: {result.get('qa_request_id', result.get('id', 'N/A'))}")
                st.balloons()  # 축하 애니메이션
                
                # 폼 데이터 초기화
                st.session_state.qa_form_data = {
                    'requester': '',
                    'assignee': '',
                    'project_name': '',
                    'qa_content': '',
                    'platforms': [],
                    'build_link': '',
                    'deployment_date': None,
                    'doc_link_1': '',
                    'doc_link_2': '',
                    'doc_link_3': ''
                }
                
                st.info("💡 폼이 초기화되었습니다. 새로운 요청서를 작성할 수 있습니다.")
                st.rerun()
            else:
                st.error("❌ QA 요청서 제출에 실패했습니다.")
                if result and result.get("message"):
                    st.error(f"오류 메시지: {result.get('message')}")
        

def show_delete_modal_qa(request_id, project_name):
    """QA 요청서 삭제 확인 모달"""
    # 모달 스타일링
    st.markdown("""
    <style>
    .delete-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .delete-modal-content {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        max-width: 500px;
        width: 90%;
        text-align: center;
        animation: modalFadeIn 0.3s ease-out;
    }
    .delete-modal h3 {
        color: white;
        margin-bottom: 1rem;
        font-size: 1.8rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .delete-modal p {
        color: rgba(255,255,255,0.9);
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    .password-input {
        background: rgba(255,255,255,0.2);
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 8px;
        padding: 0.75rem;
        color: white;
        font-size: 1rem;
        width: 100%;
        margin-bottom: 1.5rem;
        text-align: center;
        font-weight: bold;
    }
    .password-input::placeholder {
        color: rgba(255,255,255,0.7);
    }
    @keyframes modalFadeIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 모달 헤더
    st.markdown(f"""
    <div class="delete-modal-content">
        <h3>🗑️ QA 요청서 삭제 확인</h3>
        <p><strong>{project_name} (ID: {request_id})</strong> 요청서를 삭제하시겠습니까?</p>
        <p style="color: #ffeb3b; font-weight: bold;">⚠️ 이 작업은 되돌릴 수 없습니다!</p>
        <p style="font-size: 0.9rem;">보안을 위해 비밀번호를 입력해주세요.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 비밀번호 입력
    password = st.text_input(
        "비밀번호",
        type="password",
        placeholder="qa2025",
        help="삭제 확인을 위한 비밀번호를 입력하세요",
        key=f"delete_password_{request_id}",
        label_visibility="collapsed"
    )
    
    # 버튼들
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 삭제 확인", key=f"confirm_delete_modal_{request_id}", type="primary", use_container_width=True):
            if password == "qa2025":
                # QA 요청서 삭제 API 호출
                result = api_call(f"/qa-requests/{request_id}", method="DELETE")
                
                if result and result.get("success"):
                    st.success("✅ QA 요청서가 삭제되었습니다.")
                    st.cache_data.clear()
                    # 모달 닫기
                    del st.session_state[f'show_delete_modal_qa_{request_id}']
                    st.rerun()
                else:
                    st.error("❌ QA 요청서 삭제에 실패했습니다.")
                    if result and result.get("message"):
                        st.error(f"오류: {result.get('message')}")
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다. (힌트: qa2025)")
    
    with col2:
        if st.button("❌ 취소", key=f"cancel_delete_modal_{request_id}", use_container_width=True):
            # 모달 닫기
            del st.session_state[f'show_delete_modal_qa_{request_id}']
            st.rerun()

def show_qa_request_detail(request_id):
    """QA 요청서 상세 페이지"""
    # 뒤로가기 버튼
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← 뒤로가기", key="back_to_list"):
            if 'qa_request_detail_id' in st.session_state:
                del st.session_state['qa_request_detail_id']
            st.rerun()
    
    with col2:
        st.subheader(f"📋 QA 요청서 상세 정보 (ID: {request_id})")
    
    # 요청서 상세 정보 가져오기
    request_detail = api_call(f"/qa-requests/{request_id}")
    
    if request_detail:
        # API 응답이 직접 데이터인 경우와 success 래퍼가 있는 경우 모두 처리
        if request_detail.get("success"):
            request = request_detail
        else:
            # 직접 데이터가 반환된 경우
            request = request_detail
        
        # 상태별 색상 설정
        status = request.get("status", "대기중")
        status_colors = {
            "요청": "#6c757d",
            "대기중": "#ffc107",
            "진행중": "#17a2b8",
            "완료": "#28a745",
            "취소": "#dc3545"
        }
        status_color = status_colors.get(status, "#6c757d")
        
        # 플랫폼 정보 처리
        platform_str = request.get("platform", "")
        platforms = platform_str.split(",") if platform_str else []
        platform_emojis = {
            "android": "📱 Android",
            "ios": "📱 iOS",
            "web": "🌐 Web",
            "api": "🔌 API"
        }
        
        # 상세 정보 카드
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border-left: 6px solid {status_color};
            border-radius: 12px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem;">
                <div>
                    <h2 style="color: #e2e8f0; margin: 0 0 0.5rem 0; font-size: 1.8rem;">
                        {request.get('project_name', 'N/A')}
                    </h2>
                    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                        <span style="
                            background: {status_color}; 
                            color: white; 
                            padding: 0.5rem 1rem; 
                            border-radius: 20px; 
                            font-size: 0.9rem; 
                            font-weight: bold;
                        ">{status}</span>
                        <span style="color: #a0aec0; font-size: 0.9rem;">
                            ID: {request.get('id')}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 기본 정보 섹션
        st.markdown("### 📋 기본 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **👤 작성자:** {request.get('requester', 'N/A')}  
            **👨‍💼 담당자:** {request.get('assignee', '미할당')}  
            **📅 요청일:** {request.get('created_at', 'N/A')[:10]}  
            **🚀 희망 배포일:** {request.get('desired_deploy_date', '미정')}
            """)
        
        with col2:
            st.markdown("**🖥️ 플랫폼:**")
            if platforms:
                for platform in platforms:
                    platform_name = platform_emojis.get(platform.strip(), f"📋 {platform}")
                    st.markdown(f"- {platform_name}")
            else:
                st.markdown("- 플랫폼 정보 없음")
        
        st.markdown("---")
        
        # 검수 내용 섹션
        st.markdown("### 📝 검수 희망 내용")
        st.markdown(f"""
        <div style="
            background: #1a202c; 
            padding: 1.5rem; 
            border-radius: 8px; 
            border-left: 4px solid #4299e1;
            margin: 1rem 0;
        ">
            <div style="color: #e2e8f0; line-height: 1.6; white-space: pre-wrap;">
{request.get('test_content', '내용이 없습니다.')}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 빌드 링크 섹션
        if request.get('build_link'):
            st.markdown("### 🔗 빌드 링크")
            st.markdown(f"[📦 빌드 다운로드]({request.get('build_link')})")
            st.markdown("---")
        
        # 문서 링크 섹션
        documents = request.get('documents', [])
        if documents:
            st.markdown("### 📄 관련 문서")
            for i, doc in enumerate(documents):
                doc_name = doc.get('document_name', f'문서 {i+1}')
                doc_link = doc.get('document_link', '')
                doc_type = doc.get('document_type', '문서')
                
                if doc_link:
                    st.markdown(f"🔗 [{doc_type}: {doc_name}]({doc_link})")
            st.markdown("---")
        
        # 관리 섹션
        st.markdown("### ⚙️ 관리")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 상태 변경
            st.markdown("**상태 변경**")
            status_options = ["요청", "대기중", "진행중", "완료", "취소"]
            try:
                current_index = status_options.index(status)
            except ValueError:
                current_index = 0
            
            new_status = st.selectbox(
                "새 상태",
                status_options,
                index=current_index,
                key=f"detail_status_change_{request_id}"
            )
            
            if st.button("💾 상태 저장", key=f"detail_save_status_{request_id}", use_container_width=True):
                update_data = {"status": new_status}
                result = api_call(f"/qa-requests/{request_id}", method="PUT", data=update_data)
                
                if result and result.get("success"):
                    st.success(f"✅ 상태가 '{new_status}'로 변경되었습니다.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ 상태 변경에 실패했습니다.")
        
        with col2:
            # 담당자 변경
            st.markdown("**담당자 변경**")
            new_assignee = st.text_input(
                "새 담당자",
                value=request.get('assignee', ''),
                key=f"detail_assignee_change_{request_id}"
            )
            
            if st.button("👤 담당자 저장", key=f"detail_save_assignee_{request_id}", use_container_width=True):
                update_data = {"assignee": new_assignee}
                result = api_call(f"/qa-requests/{request_id}", method="PUT", data=update_data)
                
                if result and result.get("success"):
                    st.success(f"✅ 담당자가 '{new_assignee}'로 변경되었습니다.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ 담당자 변경에 실패했습니다.")
        
        with col3:
            # 삭제
            st.markdown("**요청서 삭제**")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ 요청서 삭제", key=f"detail_delete_{request_id}", type="secondary", use_container_width=True):
                st.session_state[f'show_delete_modal_qa_{request_id}'] = True
                st.rerun()
        
        # 삭제 모달 표시
        if st.session_state.get(f'show_delete_modal_qa_{request_id}', False):
            show_delete_modal_qa(request_id, request.get('project_name', 'Unknown'))
        
        # 수정 이력 (향후 구현 예정)
        st.markdown("---")
        st.markdown("### 📊 요청서 정보")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📅 생성일: {request.get('created_at', 'N/A')}")
        with col2:
            st.info(f"🔄 수정일: {request.get('updated_at', 'N/A')}")
    
    else:
        st.error("❌ 요청서를 찾을 수 없습니다.")
        if st.button("← 목록으로 돌아가기"):
            if 'qa_request_detail_id' in st.session_state:
                del st.session_state['qa_request_detail_id']
            st.rerun()

def show_qa_request_list():
    """QA 요청서 목록"""
    # 상세 페이지 표시 확인
    if 'qa_request_detail_id' in st.session_state:
        show_qa_request_detail(st.session_state['qa_request_detail_id'])
        return
    
    st.subheader("📋 QA 요청서 목록")
    
    # 삭제 모달 표시 확인
    for key in list(st.session_state.keys()):
        if key.startswith('show_delete_modal_qa_'):
            request_id = key.replace('show_delete_modal_qa_', '')
            # 해당 요청서 정보 찾기
            qa_requests = api_call("/qa-requests")
            if qa_requests and qa_requests.get("requests"):
                for request in qa_requests["requests"]:
                    if str(request.get('id')) == str(request_id):
                        show_delete_modal_qa(request_id, request.get('project_name', 'Unknown'))
                        return  # 모달이 표시되면 다른 내용은 표시하지 않음
    
    # 필터링 옵션 (개선된 버전)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status_filter = st.selectbox(
            "📊 상태 필터",
            ["전체", "요청", "진행중", "완료", "보류"]
        )
    
    with col2:
        platform_filter = st.selectbox(
            "🖥️ 플랫폼 필터",
            ["전체", "android", "ios", "web", "api"]
        )
    
    with col3:
        assignee_filter = st.selectbox(
            "👤 담당자 필터",
            ["전체"]  # 동적으로 담당자 목록을 가져올 수 있도록 개선 가능
        )
    
    with col4:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # QA 요청서 목록 가져오기
    params = {}
    if status_filter != "전체":
        params["status"] = status_filter
    if platform_filter != "전체":
        params["platform"] = platform_filter
    if assignee_filter != "전체":
        params["assignee"] = assignee_filter
    
    # API 호출 (쿼리 파라미터 포함)
    endpoint = "/qa-requests"
    if params:
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint += f"?{query_string}"
    
    qa_requests = api_call(endpoint)
    
    if qa_requests and qa_requests.get("requests"):
        requests_list = qa_requests["requests"]
        
        # 통계 정보 표시
        total_count = len(requests_list)
        status_counts = {}
        for req in requests_list:
            status = req.get("status", "요청")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 상단 통계 카드
        st.markdown("### 📊 QA 요청서 현황")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📋 전체", total_count)
        with col2:
            st.metric("⏳ 요청", status_counts.get("요청", 0))
        with col3:
            st.metric("🔄 진행중", status_counts.get("진행중", 0))
        with col4:
            st.metric("✅ 완료", status_counts.get("완료", 0))
        with col5:
            st.metric("⏸️ 보류", status_counts.get("보류", 0))
        
        st.markdown("---")
        
        # 요청서 목록을 개선된 카드 형태로 표시
        for i, request in enumerate(requests_list):
            # 상태별 색상 설정
            status = request.get("status", "요청")
            status_colors = {
                "요청": "#6c757d",
                "진행중": "#17a2b8", 
                "완료": "#28a745",
                "보류": "#ffc107"
            }
            status_color = status_colors.get(status, "#6c757d")
            
            # 플랫폼 정보 처리 (문자열을 배열로 변환)
            platform_str = request.get("platform", "")
            platforms = platform_str.split(",") if platform_str else []
            platform_emojis = {
                "android": "📱 Android",
                "ios": "📱 iOS", 
                "web": "🌐 Web",
                "api": "🔌 API"
            }
            platform_display = " | ".join([platform_emojis.get(p.strip(), f"📋 {p}") for p in platforms if p.strip()])
            
            # 우선순위 계산 (배포일 기준)
            priority_icon = "🔥"
            desired_date = request.get('desired_deploy_date')
            if desired_date:
                from datetime import datetime, timedelta
                try:
                    deploy_date = datetime.fromisoformat(desired_date.replace('Z', '+00:00'))
                    days_left = (deploy_date - datetime.now()).days
                    if days_left <= 3:
                        priority_icon = "🚨"
                    elif days_left <= 7:
                        priority_icon = "⚡"
                    else:
                        priority_icon = "📅"
                except:
                    priority_icon = "📅"
            
            with st.container():
                # 개선된 카드 디자인
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
                    border-left: 6px solid {status_color};
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin: 1rem 0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transition: transform 0.2s ease;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.8rem;">
                                <span style="
                                    background: {status_color}; 
                                    color: white; 
                                    padding: 0.4rem 1rem; 
                                    border-radius: 20px; 
                                    font-size: 0.85rem; 
                                    font-weight: bold;
                                    text-transform: uppercase;
                                    letter-spacing: 0.5px;
                                ">{status}</span>
                                <span style="color: #a0aec0; font-size: 0.9rem; font-weight: 500;">
                                    ID: {request.get('id')}
                                </span>
                                <span style="font-size: 1.2rem;">{priority_icon}</span>
                            </div>
                            
                            <h3 style="color: #e2e8f0; margin: 0 0 1rem 0; font-size: 1.4rem; font-weight: 600; line-height: 1.3;">
                                {request.get('project_name', 'N/A')}
                            </h3>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; margin-bottom: 1rem;">
                                <div style="color: #cbd5e0; font-size: 0.9rem;">
                                    <strong style="color: #9ae6b4;">👤 요청자:</strong> {request.get('requester', 'N/A')}
                                </div>
                                <div style="color: #cbd5e0; font-size: 0.9rem;">
                                    <strong style="color: #fbb6ce;">👨‍💼 담당자:</strong> {request.get('assignee', '미할당')}
                                </div>
                                <div style="color: #cbd5e0; font-size: 0.9rem;">
                                    <strong style="color: #90cdf4;">📅 요청일:</strong> {request.get('created_at', 'N/A')[:10]}
                                </div>
                                <div style="color: #cbd5e0; font-size: 0.9rem;">
                                    <strong style="color: #f6ad55;">🚀 배포 희망일:</strong> {request.get('desired_deploy_date', '미정')[:10] if request.get('desired_deploy_date') else '미정'}
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 1rem;">
                                <div style="color: #cbd5e0; font-size: 0.9rem; margin-bottom: 0.3rem;">
                                    <strong style="color: #c6f6d5;">🖥️ 플랫폼:</strong>
                                </div>
                                <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 500;">
                                    {platform_display if platform_display else '플랫폼 정보 없음'}
                                </div>
                            </div>
                            
                            <div style="
                                background: rgba(255,255,255,0.05); 
                                padding: 1rem; 
                                border-radius: 8px; 
                                border-left: 3px solid #4299e1;
                                margin-bottom: 1rem;
                            ">
                                <div style="color: #cbd5e0; font-size: 0.85rem; margin-bottom: 0.3rem;">
                                    <strong style="color: #90cdf4;">📝 검수 내용:</strong>
                                </div>
                                <div style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5;">
                                    {request.get('test_content', '내용이 없습니다.')[:150]}{'...' if len(request.get('test_content', '')) > 150 else ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 상세 카드 내 상태변경 메뉴 및 액션 버튼들
                with st.expander("⚙️ 관리 메뉴", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown("**📊 상태 변경**")
                        status_options = ["요청", "진행중", "완료", "보류"]
                        try:
                            current_index = status_options.index(status)
                        except ValueError:
                            current_index = 0
                        
                        new_status = st.selectbox(
                            "새 상태",
                            status_options,
                            index=current_index,
                            key=f"status_change_{request.get('id')}_{i}",
                            label_visibility="collapsed"
                        )
                        
                        if st.button("💾 상태 저장", key=f"save_status_{request.get('id')}_{i}", use_container_width=True):
                            status_update_data = {
                                "status": new_status
                            }
                            result = api_call(f"/qa-requests/{request.get('id')}/status", method="PATCH", data=status_update_data)
                            
                            if result and result.get("success"):
                                st.success(f"✅ 상태가 '{new_status}'로 변경되었습니다.")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ 상태 변경에 실패했습니다.")
                    
                    with col2:
                        st.markdown("**👤 담당자 변경**")
                        current_assignee = request.get('assignee', '')
                        new_assignee = st.text_input(
                            "새 담당자",
                            value=current_assignee,
                            key=f"assignee_change_{request.get('id')}_{i}",
                            placeholder="담당자 이름 입력",
                            label_visibility="collapsed"
                        )
                        
                        if st.button("👤 담당자 저장", key=f"save_assignee_{request.get('id')}_{i}", use_container_width=True):
                            assignee_update_data = {
                                "status": status,  # 현재 상태 유지
                                "assignee": new_assignee
                            }
                            result = api_call(f"/qa-requests/{request.get('id')}/status", method="PATCH", data=assignee_update_data)
                            
                            if result and result.get("success"):
                                st.success(f"✅ 담당자가 '{new_assignee}'로 변경되었습니다.")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ 담당자 변경에 실패했습니다.")
                    
                    with col3:
                        st.markdown("**📋 상세 정보**")
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("📋 상세 보기", key=f"view_detail_{request.get('id')}_{i}", type="primary", use_container_width=True):
                            # 상세 페이지로 이동
                            st.session_state['qa_request_detail_id'] = request.get('id')
                            st.rerun()
                    
                    with col4:
                        st.markdown("**🗑️ 삭제**")
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🗑️ 삭제", key=f"delete_qa_{request.get('id')}_{i}", type="secondary", use_container_width=True):
                            # 삭제 확인 모달 표시
                            st.session_state[f'show_delete_modal_qa_{request.get("id")}'] = True
                            st.rerun()
                
                # 빌드 링크가 있는 경우 표시
                if request.get('build_link'):
                    st.markdown(f"🔗 [빌드 다운로드]({request.get('build_link')})")
                
                # 문서 링크가 있는 경우 표시
                documents = request.get('documents', [])
                if documents:
                    st.markdown("**📄 관련 문서:**")
                    for doc in documents:
                        doc_name = doc.get('document_name', '문서')
                        doc_link = doc.get('document_link', '')
                        if doc_link:
                            st.markdown(f"• [📎 {doc_name}]({doc_link})")
    else:
        st.info("📝 등록된 QA 요청서가 없습니다.")
        st.markdown("""
        ### 💡 QA 요청서를 작성해보세요!
        
        **'📝 QA 요청서 작성'** 탭에서 새로운 QA 요청서를 작성할 수 있습니다.
        
        **포함 정보:**
        - 👤 요청자 및 담당자 정보
        - 📱 플랫폼 선택 (Android, iOS, Web, API)
        - 📝 상세한 검수 내용
        - 🔗 빌드 링크 및 관련 문서
        - 📅 희망 배포 일정
        """)

def show_test_cases():
    """테스트 케이스 화면"""
    st.header("🧪 테스트 케이스 관리")
    st.info("테스트 케이스 기능을 개발 중입니다.")

        
if __name__ == "__main__":
    main()
