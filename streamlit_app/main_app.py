"""
QA Dashboard - 완전히 리팩토링된 메인 애플리케이션
모든 기능을 모듈화하여 구현
"""

import streamlit as st
import sys
import os

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 모듈 임포트
from config.settings import PAGE_CONFIG
from api.client import check_api_connection

# 페이지 모듈 임포트
from page_modules.dashboard import show_dashboard_home
from page_modules.jira_management import show_jira_management
from page_modules.jira_project_management import show_jira_project_management
from streamlit_app.page_modules.task_management import show_task_management
from page_modules.qa_request import show_qa_request
from page_modules.qa_assistant import show_qa_assistant
from streamlit_app.page_modules.zephyr_project_management import show_zephyr_management
from streamlit_app.page_modules.zephyr_management import show_zephyr_project_management_page
from page_modules.admin_management import show_admin_management

# 페이지 설정
st.set_page_config(**PAGE_CONFIG)

# 커스텀 스타일 제거됨 - 기본 Streamlit 테마 사용

def main():
    """메인 애플리케이션"""
    # API 연결 상태 확인 (선택적)
    api_connected = check_api_connection()
    
    # 사이드바 제목
    st.sidebar.markdown("""
    <div style="text-align: left; padding: 1rem 0; margin-bottom: 1rem;">
        <h2 style="color: #ffffff; font-size: 1.5rem; margin: 0; font-weight: 600;">
            🎯Quality Hub
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # 페이지 선택을 세션 상태로 관리
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "대시보드"
    
    current_page = st.session_state.current_page
    
    # 일반유저 메뉴
    st.sidebar.markdown("""
    <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 600; margin: 1rem 0 0.5rem 0; padding-left: 0.5rem;">
        👤 일반유저 메뉴
    </div>
    """, unsafe_allow_html=True)
    
    general_menu_items = [
        ("🏠 대시보드", "대시보드"),
        ("📝 QA 요청서", "QA 요청서")
    ]
    
    for menu_label, menu_key in general_menu_items:
        button_type = "primary" if current_page == menu_key else "secondary"
        if st.sidebar.button(menu_label, use_container_width=True, type=button_type):
            st.session_state.current_page = menu_key
            st.rerun()
    
    # QA 전용 메뉴
    st.sidebar.markdown("""
    <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 600; margin: 1.5rem 0 0.5rem 0; padding-left: 0.5rem;">
        🔧 QA 전용 메뉴
    </div>
    """, unsafe_allow_html=True)
    
    qa_menu_items = [
        ("🤖 QA AI 어시스턴트", "QA AI 어시스턴트"),
        ("📋 작업 관리", "작업 관리"),
        ("📂 지라 프로젝트 관리", "지라 프로젝트 관리"),
        ("⚡ 제퍼 프로젝트 관리", "제퍼 프로젝트 관리")
    ]
    
    for menu_label, menu_key in qa_menu_items:
        button_type = "primary" if current_page == menu_key else "secondary"
        if st.sidebar.button(menu_label, use_container_width=True, type=button_type):
            st.session_state.current_page = menu_key
            st.rerun()
    
    # 연동관리 메뉴
    st.sidebar.markdown("""
    <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 600; margin: 1.5rem 0 0.5rem 0; padding-left: 0.5rem;">
        🔗 연동관리
    </div>
    """, unsafe_allow_html=True)
    
    integration_menu_items = [
        ("🔗 지라 연동 관리", "지라 연동 관리"),
        ("⚡ 제퍼 연동 관리", "제퍼 연동 관리")
    ]
    
    for menu_label, menu_key in integration_menu_items:
        button_type = "primary" if current_page == menu_key else "secondary"
        if st.sidebar.button(menu_label, use_container_width=True, type=button_type):
            st.session_state.current_page = menu_key
            st.rerun()
    
    # 관리자 전용 메뉴
    st.sidebar.markdown("""
    <div style="color: #e2e8f0; font-size: 0.9rem; font-weight: 600; margin: 1.5rem 0 0.5rem 0; padding-left: 0.5rem;">
        👑 관리자 전용 메뉴
    </div>
    """, unsafe_allow_html=True)
    
    admin_menu_items = [
        ("🔧 관리자 설정", "관리자 설정")
    ]
    
    for menu_label, menu_key in admin_menu_items:
        button_type = "primary" if current_page == menu_key else "secondary"
        if st.sidebar.button(menu_label, use_container_width=True, type=button_type):
            st.session_state.current_page = menu_key
            st.rerun()
    
    # 구분선
    st.sidebar.markdown("---")
    
    # API 상태 표시
    if api_connected:
        st.sidebar.success("✅ API 서버 연결됨")
    else:
        st.sidebar.warning("⚠️ API 서버 연결 안됨")
        st.sidebar.info("백엔드 서버 실행: `python main.py`")
    
    # Zephyr 연결 상태 표시
    def check_zephyr_connection():
        """Zephyr 연결 상태 확인"""
        try:
            from dotenv import load_dotenv
            import requests
            
            # .env 파일 로드
            load_dotenv()
            
            zephyr_username = os.getenv('ZEPHYR_USERNAME', '')
            zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
            
            if not zephyr_username or not zephyr_api_token:
                return False, "설정 없음"
            
            # 빠른 연결 테스트
            headers = {
                "Authorization": f"Bearer {zephyr_api_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(
                "https://api.zephyrscale.smartbear.com/v2/projects",
                headers=headers,
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                return True, "연결됨"
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, "연결 실패"
    
    # Zephyr 연결 상태 확인 (캐시 사용)
    if 'zephyr_sidebar_status' not in st.session_state:
        zephyr_connected, zephyr_status = check_zephyr_connection()
        st.session_state.zephyr_sidebar_status = (zephyr_connected, zephyr_status)
    else:
        zephyr_connected, zephyr_status = st.session_state.zephyr_sidebar_status
    
    # Zephyr 상태 표시
    if zephyr_connected:
        st.sidebar.success("⚡ Zephyr 연결됨")
    else:
        if zephyr_status == "설정 없음":
            st.sidebar.info("⚡ Zephyr 설정 필요")
        else:
            st.sidebar.warning(f"⚡ Zephyr 연결 안됨")
    
    # 페이지별 내용 표시
    if current_page == "대시보드":
        show_dashboard_home()
    elif current_page == "지라 프로젝트 관리":
        show_jira_project_management()
    elif current_page == "지라 연동 관리":
        show_jira_management()
    elif current_page == "작업 관리":
        show_task_management()
    elif current_page == "QA AI 어시스턴트":
        show_qa_assistant()
    elif current_page == "제퍼 프로젝트 관리":
        show_zephyr_management()
    elif current_page == "제퍼 연동 관리":
        show_zephyr_project_management_page()
    elif current_page == "QA 요청서":
        show_qa_request()
    elif current_page == "관리자 설정":
        show_admin_management()

if __name__ == "__main__":
    main()
