"""
지라 연동 관리 페이지
"""

import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from streamlit_app.api.client import test_jira_connection

def show_jira_management():
    """지라 연동 관리 페이지 표시"""
    st.title("🔗 지라 연동 관리")
    
    # 지라 연결 상태 확인
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("연결 상태")
    
    with col2:
        if st.button("연결 테스트", type="primary"):
            with st.spinner("지라 연결을 확인하는 중..."):
                result = test_jira_connection()
                if result and result.get("success"):
                    st.success("✅ 지라 연결 성공!")
                else:
                    st.error("❌ 지라 연결 실패")
    
    # 연결 상태 정보 표시
    st.markdown("---")
    st.subheader("📋 지라 연동 정보")
    
    st.info("""
    **지라 연동 관리**
    
    이 페이지에서는 지라 서버와의 연결 상태를 확인할 수 있습니다.
    
    - **연결 테스트**: 지라 서버와의 연결 상태를 확인합니다.
    - **프로젝트 관리**: 지라 프로젝트 관련 작업은 '지라 프로젝트 관리' 메뉴를 이용해주세요.
    """)
    
    # 연결 테스트 결과 상세 정보
    with st.expander("🔧 연결 설정 정보"):
        st.markdown("""
        **지라 연결 설정**
        
        지라 연동을 위해서는 다음 설정이 필요합니다:
        - 지라 서버 URL
        - 인증 정보 (API 토큰 또는 사용자 계정)
        - 적절한 권한 설정
        
        연결에 문제가 있는 경우 시스템 관리자에게 문의하세요.
        """)
