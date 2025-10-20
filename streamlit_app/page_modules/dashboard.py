"""
대시보드 홈 페이지 모듈
"""

import streamlit as st
import pandas as pd
import sys
import os
import plotly.express as px
import plotly.graph_objects as go

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from streamlit_app.api.client import api_call, get_dashboard_stats, get_projects, get_tasks
from streamlit_app.utils.helpers import create_jira_link
from streamlit_app.utils.deployment_notice import get_active_deployment_notice

def show_dashboard_home():
    """대시보드 홈 화면 - 고급 통계 포함"""
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
    
    # 배포날짜 공지 영역
    deployment_notice = get_active_deployment_notice()
    if deployment_notice:
        # 날짜 파싱 (예: "2025년 01월 15일 14:30" 형식)
        deployment_date_str = deployment_notice.get('deployment_date', '')
        
        # 날짜에서 연도, 월, 일 추출
        import re
        date_match = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', deployment_date_str)
        time_match = re.search(r'(\d{1,2}):(\d{2})', deployment_date_str)
        
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            
            time_str = ""
            if time_match:
                hour = time_match.group(1).zfill(2)
                minute = time_match.group(2)
                time_str = f"{hour}:{minute}"
        else:
            # 파싱 실패시 기본값
            year, month, day = "2025", "01", "01"
            time_str = ""
        
        # 공지 메시지 처리
        notice_message = deployment_notice.get("notice_message", "시스템 배포가 예정되어 있습니다.")
        if not notice_message.strip():
            notice_message = "시스템 배포가 예정되어 있습니다."
        
        # 캘린더 형식 배포 공지
        col1, col2 = st.columns([1, 3])
        
        with col1:
            # 배포 예정일 타이틀
            st.markdown("""
            <div style="text-align: left; margin-bottom: 0.5rem;">
                <h4 style="color: #667eea; margin: 0; font-size: 2rem; font-weight: 600;">
                    ⭐️ 배포 공지
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # 캘린더 스타일 날짜 박스
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 1.5rem;
                text-align: center;
                color: white;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                margin-bottom: 1rem;
            ">
                <div style="font-size: 1.2rem; opacity: 0.8; margin-bottom: 0.5rem; font-weight: 400;">
                    {year}년
                </div>
                <div style="font-size: 2rem; opacity: 0.95; margin-bottom: 0.8rem; font-weight: 600;">
                    {month}월 {day}일
                </div>
                {f'<div style="font-size: 1rem; opacity: 0.9;">{time_str}</div>' if time_str else ''}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # 공지 내용
            st.markdown(f"""
            <div style="
                background: rgba(102, 126, 234, 0.1);
                border-left: 4px solid #667eea;
                padding: 2rem;
                border-radius: 10px;
                margin-bottom: 2rem;
                margin-top: 4.5rem;
                height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <h3 style="color: #667eea; margin: 0 0 1rem 0; font-size: 1.3rem;">
                    🚀 배포 예정 안내
                </h3>
                <p style="margin: 0; font-size: 1.1rem; line-height: 1.5;">
                    {notice_message}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.header("📊 QA 현황 대시보드")
    
    # 통계 데이터 가져오기 (에러 처리 개선)
    try:
        stats = get_dashboard_stats()
        jira_projects_data = get_projects()
    except Exception as e:
        st.warning("⚠️ API 서버에 연결할 수 없습니다. 기본 화면을 표시합니다.")
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "qa_ready_tasks": 0,
            "completion_rate": 0,
            "qa_completed": 0,
            "qa_in_progress": 0,
            "qa_started": 0,
            "qa_not_started": 0,
            "qa_completion_rate": 0,
            "priority_highest": 0,
            "priority_high": 0,
            "priority_medium": 0,
            "priority_low": 0,
            "priority_lowest": 0,
            "top_assignees": [],
            "project_stats": [],
            "weekly_new_tasks": 0,
            "active_projects": 0
        }
        jira_projects_data = None
    
    if not stats:
        stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "qa_ready_tasks": 0,
            "completion_rate": 0,
            "qa_completed": 0,
            "qa_in_progress": 0,
            "qa_started": 0,
            "qa_not_started": 0,
            "qa_completion_rate": 0,
            "priority_highest": 0,
            "priority_high": 0,
            "priority_medium": 0,
            "priority_low": 0,
            "priority_lowest": 0,
            "top_assignees": [],
            "project_stats": [],
            "weekly_new_tasks": 0,
            "active_projects": 0
        }
    
    # 상단 메트릭 카드 - 확장된 통계
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric(
            label="📋 전체 작업", 
            value=stats.get("total_tasks", 0),
            delta=f"+{stats.get('weekly_new_tasks', 0)} 이번 주"
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
        st.metric(
            label="🧪 QA 완료", 
            value=stats.get("qa_completed", 0),
            delta=f"{stats.get('qa_completion_rate', 0)}% QA율"
        )
    
    with col6:
        # 활성 프로젝트 수 표시
        project_count = stats.get("active_projects", 0)
        
        st.metric(
            label="🔗 활성 프로젝트", 
            value=project_count,
            delta="연동됨" if project_count > 0 else "미연동"
        )
    
    st.markdown("---")
    
    # 차트 섹션
    col1, col2 = st.columns(2)
    
    with col1:
        # QA 상태별 파이 차트
        st.subheader("🧪 QA 상태 분포")
        qa_data = {
            'QA 완료': stats.get("qa_completed", 0),
            'QA 진행중': stats.get("qa_in_progress", 0),
            'QA 시작': stats.get("qa_started", 0),
            '미시작': stats.get("qa_not_started", 0)
        }
        
        if sum(qa_data.values()) > 0:
            fig_qa = px.pie(
                values=list(qa_data.values()),
                names=list(qa_data.keys()),
                color_discrete_sequence=['#28a745', '#ffc107', '#17a2b8', '#6c757d']
            )
            fig_qa.update_traces(textposition='inside', textinfo='percent+label')
            fig_qa.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig_qa, use_container_width=True)
        else:
            st.info("QA 데이터가 없습니다.")
    
    with col2:
        # 우선순위별 바 차트
        st.subheader("⚡ 우선순위별 작업")
        priority_data = {
            'Highest': stats.get("priority_highest", 0),
            'High': stats.get("priority_high", 0),
            'Medium': stats.get("priority_medium", 0),
            'Low': stats.get("priority_low", 0),
            'Lowest': stats.get("priority_lowest", 0)
        }
        
        if sum(priority_data.values()) > 0:
            fig_priority = px.bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                color=list(priority_data.values()),
                color_continuous_scale='Reds'
            )
            fig_priority.update_layout(height=300, showlegend=False)
            fig_priority.update_xaxes(title="우선순위")
            fig_priority.update_yaxes(title="작업 수")
            st.plotly_chart(fig_priority, use_container_width=True)
        else:
            st.info("우선순위 데이터가 없습니다.")
    
    # 담당자별 통계
    if stats.get("top_assignees"):
        st.subheader("👥 담당자별 작업 현황 (상위 5명)")
        assignee_df = pd.DataFrame(stats["top_assignees"])
        
        fig_assignee = px.bar(
            assignee_df,
            x='name',
            y='count',
            color='count',
            color_continuous_scale='Blues'
        )
        fig_assignee.update_layout(height=300, showlegend=False)
        fig_assignee.update_xaxes(title="담당자")
        fig_assignee.update_yaxes(title="작업 수")
        st.plotly_chart(fig_assignee, use_container_width=True)
    
    # 프로젝트별 통계
    if stats.get("project_stats"):
        st.subheader("📁 프로젝트별 작업 현황")
        project_df = pd.DataFrame(stats["project_stats"])
        
        fig_project = px.bar(
            project_df,
            x='project',
            y='count',
            color='count',
            color_continuous_scale='Greens'
        )
        fig_project.update_layout(height=300, showlegend=False)
        fig_project.update_xaxes(title="프로젝트")
        fig_project.update_yaxes(title="작업 수")
        st.plotly_chart(fig_project, use_container_width=True)
    
    # 동기화 정보
    if stats.get("last_sync_time"):
        st.subheader("🔄 최근 동기화 정보")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"🕐 마지막 동기화: {stats.get('last_sync_time')}")
        
        with col2:
            st.info(f"📁 프로젝트: {stats.get('last_sync_project', 'N/A')}")
        
        with col3:
            status_emoji = "✅" if stats.get('last_sync_status') == 'completed' else "❌"
            st.info(f"{status_emoji} 상태: {stats.get('last_sync_status', 'N/A')}")
    
    st.markdown("---")
    
    # 실시간 작업 목록
    st.subheader("📋 최근 동기화된 작업")
    
    try:
        tasks = get_tasks()
    except Exception as e:
        tasks = None
        st.info("작업 데이터를 불러올 수 없습니다.")
    
    if tasks:
        # 최근 동기화된 작업들만 표시
        recent_tasks = [t for t in tasks if t.get('last_sync')]
        
        if recent_tasks:
            task_df = pd.DataFrame(recent_tasks)
            
            # 처리 상태(지라 상태)와 검수 상태 분리 표시 - 검수 상태를 제일 끝으로 이동
            display_columns = ['jira_key', 'title', 'status', 'assignee', 'priority', 'qa_status']
            
            # 컬럼이 없는 경우 기본값 설정
            for col in display_columns:
                if col not in task_df.columns:
                    if col == 'qa_status':
                        task_df[col] = '미시작'  # qa_status 기본값
                    else:
                        task_df[col] = 'N/A'
            
            display_df = task_df[display_columns].copy()
            
            # 지라 키를 클릭 가능한 링크로 변환
            if 'jira_key' in display_df.columns:
                display_df['jira_key'] = display_df['jira_key'].apply(create_jira_link)
            
            # 지라 상태는 원본 그대로 표시 (처리 상태)
            # 지라에서 받아온 상태를 변경하지 않음
            
            # 검수 상태만 이모지 추가 (작업관리에서 설정한 값)
            qa_status_emoji = {
                'QA 완료': '✅',
                'QA 진행중': '🔄',
                'QA 시작': '🚀',
                '미시작': '⏸️'
            }
            
            if 'qa_status' in display_df.columns:
                display_df['qa_status'] = display_df['qa_status'].apply(
                    lambda x: f"{qa_status_emoji.get(x, '⏸️')} {x}" if x and x != 'N/A' else '⏸️ 미시작'
                )
            
            display_df.columns = ['지라 키', '제목', '처리 상태', '담당자', '우선순위', '검수 상태']
            
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
