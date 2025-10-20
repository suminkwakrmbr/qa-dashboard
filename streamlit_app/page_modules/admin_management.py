"""
관리자 전용 페이지 모듈
"""

import streamlit as st
import sys
import os
from datetime import datetime, date

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from streamlit_app.utils.deployment_notice import (
    load_deployment_notice, 
    save_deployment_notice, 
    deactivate_deployment_notice
)

def show_admin_management():
    """관리자 전용 페이지"""
    st.header("🔧 관리자 설정")
    
    # 탭으로 구분
    tab1, tab2 = st.tabs(["📅 배포날짜 공지 관리", "⚙️ 기타 설정"])
    
    with tab1:
        st.subheader("📅 배포날짜 공지 관리")
        
        # 현재 설정된 공지 정보 표시
        current_notice = load_deployment_notice()
        
        if current_notice.get("is_active", False):
            st.success("✅ 현재 활성화된 배포날짜 공지가 있습니다.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**배포날짜:** {current_notice.get('deployment_date', 'N/A')}")
            with col2:
                st.info(f"**마지막 업데이트:** {current_notice.get('last_updated', 'N/A')}")
            
            if current_notice.get('notice_message'):
                st.info(f"**공지 메시지:** {current_notice.get('notice_message')}")
            
            # 비활성화 버튼
            if st.button("🔴 공지 비활성화", type="secondary"):
                if deactivate_deployment_notice():
                    st.success("배포날짜 공지가 비활성화되었습니다.")
                    st.rerun()
                else:
                    st.error("공지 비활성화에 실패했습니다.")
        else:
            st.info("현재 활성화된 배포날짜 공지가 없습니다.")
        
        st.markdown("---")
        
        # 새로운 배포날짜 공지 설정
        st.subheader("🆕 새 배포날짜 공지 설정")
        
        with st.form("deployment_notice_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # 배포날짜 선택
                deployment_date = st.date_input(
                    "배포날짜 선택",
                    value=date.today(),
                    help="배포 예정일을 선택해주세요"
                )
            
            with col2:
                # 시간 선택 (선택사항)
                deployment_time = st.time_input(
                    "배포시간 (선택사항)",
                    value=None,
                    help="배포 예정 시간을 선택해주세요 (선택사항)"
                )
            
            # 공지 메시지
            notice_message = st.text_area(
                "공지 메시지 (선택사항)",
                placeholder="예: 시스템 점검으로 인해 일시적으로 서비스가 중단될 수 있습니다.",
                help="배포와 관련된 추가 안내사항을 입력해주세요"
            )
            
            # 미리보기
            if deployment_date:
                st.markdown("### 📋 미리보기")
                
                # 날짜 포맷팅
                formatted_date = deployment_date.strftime("%Y년 %m월 %d일")
                if deployment_time:
                    formatted_date += f" {deployment_time.strftime('%H:%M')}"
                
                # 미리보기 HTML
                preview_html = f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    margin: 1rem 0;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                ">
                    <div style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">
                        🚀 배포 예정 안내
                    </div>
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem;">
                        {formatted_date}
                    </div>
                    {f'<div style="font-size: 0.9rem; opacity: 0.9;">{notice_message}</div>' if notice_message else ''}
                </div>
                """
                st.markdown(preview_html, unsafe_allow_html=True)
            
            # 제출 버튼
            submitted = st.form_submit_button("💾 배포날짜 공지 저장", type="primary")
            
            if submitted:
                if deployment_date:
                    # 날짜 포맷팅
                    formatted_date = deployment_date.strftime("%Y년 %m월 %d일")
                    if deployment_time:
                        formatted_date += f" {deployment_time.strftime('%H:%M')}"
                    
                    # 저장
                    if save_deployment_notice(formatted_date, notice_message or ""):
                        st.success("✅ 배포날짜 공지가 성공적으로 저장되었습니다!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ 배포날짜 공지 저장에 실패했습니다.")
                else:
                    st.error("배포날짜를 선택해주세요.")
    
    with tab2:
        st.subheader("⚙️ 기타 설정")
        st.info("추후 추가될 관리자 설정 기능들이 여기에 표시됩니다.")
        
        # 시스템 정보
        st.markdown("### 📊 시스템 정보")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("현재 시간", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        with col2:
            # 배포 공지 파일 존재 여부
            notice_file_exists = os.path.exists(os.path.join(project_root, "deployment_notice.json"))
            st.metric("배포 공지 파일", "존재" if notice_file_exists else "없음")
