"""
유틸리티 함수 모듈
공통으로 사용되는 헬퍼 함수들을 정의합니다.
"""

import streamlit as st
import json
from datetime import datetime

def format_date(date_string):
    """날짜 문자열을 포맷팅"""
    if not date_string:
        return "N/A"
    try:
        # ISO 형식의 날짜를 파싱
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return date_string[:10] if len(date_string) >= 10 else date_string

def format_datetime(date_string):
    """날짜 문자열을 포맷팅 (format_date와 동일한 기능)"""
    return format_date(date_string)

def get_status_color(status):
    """상태에 따른 색상 반환"""
    status_colors = {
        'Done': '#28a745',
        'In Progress': '#17a2b8', 
        'QA Ready': '#ffc107',
        'To Do': '#6c757d',
        '완료': '#28a745',
        '진행중': '#17a2b8',
        'QA 완료': '#28a745',
        'QA 진행중': '#17a2b8', 
        'QA 시작': '#ffc107',
        '미시작': '#6c757d'
    }
    return status_colors.get(status, '#6c757d')

def get_priority_icon(priority):
    """우선순위에 따른 아이콘 반환"""
    priority_icons = {
        'Highest': '🚨',
        'High': '🔥',
        'Medium': '⚡',
        'Low': '📝',
        'Lowest': '📋'
    }
    return priority_icons.get(priority, '📋')

def get_priority_color(priority):
    """우선순위에 따른 색상 반환"""
    priority_colors = {
        'Highest': '#dc3545',  # 빨간색
        'High': '#fd7e14',     # 주황색
        'Medium': '#ffc107',   # 노란색
        'Low': '#28a745',      # 초록색
        'Lowest': '#6c757d',   # 회색
        '긴급': '#dc3545',
        '높음': '#fd7e14',
        '보통': '#ffc107',
        '낮음': '#28a745'
    }
    return priority_colors.get(priority, '#ffc107')

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

def get_platform_emoji(platform):
    """플랫폼에 따른 이모지 반환"""
    platform_emojis = {
        "android": "📱 Android",
        "ios": "📱 iOS",
        "web": "🌐 Web",
        "api": "🔌 API"
    }
    return platform_emojis.get(platform.lower(), f"📋 {platform}")

def format_platform_list(platform_str):
    """플랫폼 문자열을 포맷팅된 리스트로 변환"""
    if not platform_str:
        return "플랫폼 정보 없음"
    
    platforms = platform_str.split(",") if platform_str else []
    formatted_platforms = [get_platform_emoji(p.strip()) for p in platforms if p.strip()]
    return " | ".join(formatted_platforms) if formatted_platforms else "플랫폼 정보 없음"

def calculate_priority_from_date(desired_date):
    """배포 희망일로부터 우선순위 아이콘 계산"""
    if not desired_date:
        return "📅"
    
    try:
        from datetime import datetime, timedelta
        deploy_date = datetime.fromisoformat(desired_date.replace('Z', '+00:00'))
        days_left = (deploy_date - datetime.now()).days
        
        if days_left <= 3:
            return "🚨"  # 긴급
        elif days_left <= 7:
            return "⚡"  # 높음
        else:
            return "📅"  # 보통
    except:
        return "📅"

def truncate_text(text, max_length=150):
    """텍스트를 지정된 길이로 자르기"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."

def create_status_badge(status, size="normal"):
    """상태 배지 HTML 생성"""
    color = get_status_color(status)
    
    if size == "small":
        padding = "0.2rem 0.5rem"
        font_size = "0.7rem"
    else:
        padding = "0.4rem 1rem"
        font_size = "0.85rem"
    
    return f"""
    <span style="
        background: {color}; 
        color: white; 
        padding: {padding}; 
        border-radius: 20px; 
        font-size: {font_size}; 
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    ">{status}</span>
    """

def validate_url(url):
    """URL 유효성 검사"""
    if not url:
        return False
    
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def format_file_size(size_bytes):
    """파일 크기를 읽기 쉬운 형태로 포맷팅"""
    if not size_bytes:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} TB"

def create_info_card(title, content, icon="ℹ️", color="#17a2b8"):
    """정보 카드 HTML 생성"""
    return f"""
    <div style="
        background: linear-gradient(135deg, {color}20 0%, {color}10 100%);
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span style="font-size: 1.2rem;">{icon}</span>
            <strong style="color: {color}; font-size: 1rem;">{title}</strong>
        </div>
        <div style="color: #e2e8f0; line-height: 1.5;">
            {content}
        </div>
    </div>
    """
