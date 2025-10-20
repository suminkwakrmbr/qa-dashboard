"""
작업 관리 페이지 - legacy.py의 show_task_management 기능 구현
"""

import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from streamlit_app.api.client import (
    get_projects, get_tasks, delete_task,
    update_qa_status, update_task_memo, get_task_memo, get_sync_status, reset_all_tasks
)
from streamlit_app.utils.helpers import get_jira_issue_url

def show_sync_status_banner():
    """동기화 상태 배너 표시"""
    # 현재 진행 중인 동기화 작업 확인
    projects_response = get_projects()
    
    if not projects_response:
        return
    
    # 프로젝트 목록 처리
    projects = []
    if isinstance(projects_response, dict) and 'projects' in projects_response:
        projects = projects_response['projects']
    elif isinstance(projects_response, list):
        projects = projects_response
    
    if not projects:
        return
    
    # 진행 중인 동기화 작업 찾기
    active_syncs = []
    completed_syncs = []
    failed_syncs = []
    
    for project in projects:
        project_key = project.get('key')
        if not project_key:
            continue
            
        try:
            sync_status = get_sync_status(project_key)
            if sync_status:
                status = sync_status.get('status', 'unknown')
                if status in ["starting", "connecting", "fetching_issues", "processing"]:
                    active_syncs.append({
                        'project_key': project_key,
                        'project_name': project.get('name', project_key),
                        'status': status,
                        'progress': sync_status.get('progress', 0),
                        'message': sync_status.get('message', '진행 중...'),
                        'total_issues': sync_status.get('total_issues', 0),
                        'processed_issues': sync_status.get('processed_issues', 0)
                    })
                elif status == "completed":
                    completed_syncs.append({
                        'project_key': project_key,
                        'project_name': project.get('name', project_key),
                        'total_issues': sync_status.get('total_issues', 0),
                        'processed_issues': sync_status.get('processed_issues', 0)
                    })
                elif status == "error":
                    failed_syncs.append({
                        'project_key': project_key,
                        'project_name': project.get('name', project_key),
                        'message': sync_status.get('message', '동기화 실패')
                    })
        except:
            # 동기화 상태 조회 실패 시 무시
            continue
    
    # 상태 배너 표시
    if active_syncs or completed_syncs or failed_syncs:
        with st.container():
            st.markdown("### 🔄 동기화 상태")
            
            # 진행 중인 동기화
            if active_syncs:
                for sync in active_syncs:
                    with st.expander(f"🔄 {sync['project_key']} - 동기화 진행 중 ({sync['progress']}%)", expanded=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.progress(sync['progress'] / 100.0, text=f"진행률: {sync['progress']}%")
                            st.info(f"📝 {sync['message']}")
                            
                            if sync['total_issues'] > 0:
                                st.write(f"📊 처리 현황: {sync['processed_issues']}/{sync['total_issues']} 이슈")
                        
                        with col2:
                            # 상태별 아이콘
                            status_icons = {
                                "starting": "🚀",
                                "connecting": "🔗", 
                                "fetching_issues": "📥",
                                "processing": "⚙️"
                            }
                            st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{status_icons.get(sync['status'], '🔄')}</div>", unsafe_allow_html=True)
            
            # 완료된 동기화 (최근 3개만)
            if completed_syncs:
                recent_completed = completed_syncs[:3]
                for sync in recent_completed:
                    st.success(f"✅ {sync['project_key']} - 동기화 완료 ({sync['processed_issues']}/{sync['total_issues']} 이슈 처리)")
            
            # 실패한 동기화 (최근 3개만)
            if failed_syncs:
                recent_failed = failed_syncs[:3]
                for sync in recent_failed:
                    st.error(f"❌ {sync['project_key']} - {sync['message']}")
            
            st.markdown("---")

def show_task_management():
    """작업 관리 화면"""
    st.header("📋 작업 관리")
    
    # 새로고침 및 전체 초기화 버튼을 우측 끝에 배치
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col2:
        if st.button("🔄 새로고침", help="최신 데이터를 가져옵니다", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col3:
        if st.button("🗑️ 전체 초기화", help="모든 작업 데이터를 삭제합니다", type="secondary", use_container_width=True):
            st.session_state.show_reset_modal = True
            st.rerun()
    
    # 전체 초기화 모달 표시
    if st.session_state.get('show_reset_modal', False):
        show_reset_modal()
    
    # 작업 목록 가져오기 (필터 없이 전체 조회)
    project_id = None
    status = None
    
    # 작업 목록 가져오기 (에러 처리 개선)
    try:
        tasks_response = get_tasks(project_id=project_id, status=status)
        
        # API 응답 처리
        tasks = None
        if tasks_response:
            if isinstance(tasks_response, dict) and 'tasks' in tasks_response:
                tasks = tasks_response['tasks']
            elif isinstance(tasks_response, list):
                tasks = tasks_response
            else:
                st.error(f"예상하지 못한 작업 응답 형식: {type(tasks_response)}")
                tasks = []
        else:
            tasks = []
            
    except Exception as e:
        st.error(f"작업 목록을 불러오는 중 오류가 발생했습니다: {str(e)}")
        tasks = []
    
    if tasks:
        st.subheader(f"📊 작업 목록 ({len(tasks)}개)")
        
        # 정렬 및 페이지 설정 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            sort_by = st.selectbox("정렬 기준", ["전체", "우선순위", "상태", "업데이트 시간"])
        with col2:
            # '전체' 선택 시 정렬 순서 옵션 비활성화
            if sort_by != "전체":
                sort_order = st.selectbox("정렬 순서", ["높은 순", "낮은 순"])
            else:
                sort_order = st.selectbox("정렬 순서", ["미지정"], disabled=True)
        with col3:
            # 페이지당 표시 개수 선택
            items_per_page = st.selectbox(
                "페이지당 표시", 
                [10, 20, 50, 100, "전체"],
                index=1,  # 기본값 20
                help="한 페이지에 표시할 작업 개수를 선택하세요"
            )
        
        # 우선순위 매핑
        priority_order = {"Highest": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
        qa_status_order = {"QA 완료": 4, "QA 진행중": 3, "QA 시작": 2, "미시작": 1}
        
        # 정렬 적용
        if sort_by == "전체":
            # 기본 순서 유지 (데이터베이스에서 가져온 순서)
            pass
        elif sort_by == "우선순위":
            tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'Medium'), 3), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "상태":
            tasks.sort(key=lambda x: qa_status_order.get(x.get('qa_status', '미시작'), 1), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "업데이트 시간":
            # None 값 처리를 위한 안전한 정렬
            def safe_date_key(task):
                updated_at = task.get('updated_at')
                if updated_at is None or updated_at == '':
                    return '1900-01-01'  # 가장 오래된 날짜로 설정
                return str(updated_at)
            
            tasks.sort(key=safe_date_key, reverse=(sort_order == "높은 순"))
        
        # 페이지네이션 설정 - 사용자 선택에 따라 동적 처리
        if items_per_page == "전체":
            # 전체 표시 시 페이지네이션 없음
            page_tasks = tasks
            current_page = 0
            total_pages = 1
        else:
            # 선택된 개수에 따른 페이지네이션
            items_per_page = int(items_per_page)
            total_pages = (len(tasks) + items_per_page - 1) // items_per_page
            
            # 페이지 선택
            if total_pages > 1:
                current_page = st.selectbox(
                    "페이지 선택",
                    range(1, total_pages + 1),
                    key="task_page_selector",
                    help=f"총 {total_pages}페이지 중 선택"
                ) - 1
            else:
                current_page = 0
            
            # 현재 페이지의 작업들만 표시
            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, len(tasks))
            page_tasks = tasks[start_idx:end_idx]
        
        # 표시 정보
        if items_per_page == "전체":
            st.info(f"📊 전체 {len(tasks)}개 작업을 표시합니다.")
        else:
            start_num = current_page * items_per_page + 1
            end_num = min((current_page + 1) * items_per_page, len(tasks))
            st.info(f"📊 {start_num}-{end_num}번째 작업 (전체 {len(tasks)}개 중)")
        
        # 현재 페이지의 작업들 표시
        for i, task in enumerate(page_tasks):
            show_task_card(task, start_idx + i, "task")
            
            # 마지막 이슈가 아닌 경우 구분선 추가
            if i < len(page_tasks) - 1:
                st.markdown("""
                <div style="
                    border-bottom: 3px solid #444444;
                    margin: 30px 0;
                    width: 100%;
                "></div>
                """, unsafe_allow_html=True)
    else:
        st.info("작업이 없습니다. 지라에서 프로젝트를 동기화해주세요.")


@st.dialog("전체 초기화")
def show_reset_modal():
    """전체 초기화 확인 모달"""
    st.warning("⚠️ **주의: 모든 작업 데이터가 삭제됩니다!**")
    st.markdown("""
    다음 데이터가 **완전히 삭제**됩니다:
    - 모든 작업 (Task)
    - 모든 테스트 케이스 (TestCase)  
    - 모든 동기화 이력 (SyncHistory)
    - 프로젝트의 마지막 동기화 시간 초기화
    
    **이 작업은 되돌릴 수 없습니다.**
    """)
    
    # 확인 체크박스
    confirm_reset = st.checkbox("위 내용을 이해했으며, 모든 데이터를 삭제하는 것에 동의합니다.")
    
    # 버튼 영역
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 전체 초기화 실행", type="primary", use_container_width=True, disabled=not confirm_reset):
            if confirm_reset:
                with st.spinner("모든 데이터를 삭제하는 중..."):
                    result = reset_all_tasks()
                    
                if result and result.get("success"):
                    st.success("✅ 모든 데이터가 초기화되었습니다.")
                    st.cache_data.clear()
                    # 모달 닫기
                    if 'show_reset_modal' in st.session_state:
                        del st.session_state['show_reset_modal']
                    st.rerun()
                else:
                    st.error("❌ 초기화에 실패했습니다.")
            else:
                st.error("확인 체크박스를 선택해주세요.")
    
    with col2:
        if st.button("취소", use_container_width=True):
            # 모달 닫기
            if 'show_reset_modal' in st.session_state:
                del st.session_state['show_reset_modal']
            st.rerun()


@st.dialog("작업 삭제")
def delete_task_modal(task_id, jira_key, title):
    """작업 삭제 확인 모달"""
    st.markdown(f"**{jira_key}** - {title}")
    st.warning("이 작업을 삭제하시겠습니까?")
    
    # 버튼 영역
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 삭제", type="primary", use_container_width=True):
            result = delete_task(task_id)
            if result and result.get("success"):
                st.success("✅ 삭제되었습니다.")
                st.cache_data.clear()
                # 모달 닫기
                if f'show_delete_modal_{task_id}' in st.session_state:
                    del st.session_state[f'show_delete_modal_{task_id}']
                st.rerun()
            else:
                st.error("❌ 삭제에 실패했습니다.")
    
    with col2:
        if st.button("취소", use_container_width=True):
            # 모달 닫기
            if f'show_delete_modal_{task_id}' in st.session_state:
                del st.session_state[f'show_delete_modal_{task_id}']
            st.rerun()


def show_task_card(task, index, task_type):
    """실제 서비스 수준의 고급스럽고 간편한 작업 카드"""
    
    # 기본 정보 추출
    jira_key = task.get('jira_key', 'N/A')
    title = task.get('title', 'N/A')
    description = task.get('description', '설명이 없습니다.')
    priority = task.get('priority', 'Medium')
    qa_status = task.get('qa_status', '미시작')
    assignee = task.get('assignee', 'N/A')
    created_at = task.get('created_at', 'N/A')[:10] if task.get('created_at') else 'N/A'
    task_id = task.get('id')
    
    # 지라 URL
    jira_url = get_jira_issue_url(jira_key) if jira_key and jira_key != 'N/A' else None
    
    # 메모 불러오기
    current_memo = ""
    memo_data = get_task_memo(task_id)
    if memo_data and memo_data.get('memo'):
        current_memo = memo_data['memo']
    
    # 우선순위별 색상 (실제 서비스 스타일)
    priority_colors = {
        'Highest': '#dc2626',  # 빨강 (긴급)
        'High': '#ea580c',     # 주황 (높음)
        'Medium': '#ca8a04',   # 노랑 (보통)
        'Low': '#16a34a',      # 초록 (낮음)
        'Lowest': '#2563eb'    # 파랑 (최저)
    }
    priority_color = priority_colors.get(priority, '#ca8a04')
    
    # QA 상태별 색상 (실제 서비스 스타일)
    status_colors = {
        'QA 완료': '#059669',    # 초록
        'QA 진행중': '#d97706',  # 주황
        'QA 시작': '#2563eb',    # 파랑
        '미시작': '#6b7280'      # 회색
    }
    status_color = status_colors.get(qa_status, '#6b7280')
    
    # 삭제 모달 표시
    if st.session_state.get(f'show_delete_modal_{task_id}', False):
        delete_task_modal(task_id, jira_key, title)
    
    # 다크모드 실제 서비스 스타일의 카드 컨테이너
    with st.container():
        # 메인 카드 - 다크모드 고급 디자인
        st.markdown(f"""
        <div style="
            background: linear-gradient(145deg, #1f2937, #111827);
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 0;
            margin: 16px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), 0 1px 3px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        ">
        """, unsafe_allow_html=True)
        
        # 우선순위별 좌측 액센트 바
        st.markdown(f"""
        <div style="
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, {priority_color}, {priority_color}aa);
        "></div>
        """, unsafe_allow_html=True)
        
        # 헤더 영역 - 다크모드 스타일
        st.markdown(f"""
        <div style="
            padding: 16px 20px;
            border-bottom: 1px solid #374151;
            background: linear-gradient(135deg, #1f2937, #374151);
            display: flex;
            align-items: center;
            justify-content: space-between;
        ">
            <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                <div style="
                    background: linear-gradient(135deg, {priority_color}, {priority_color}dd);
                    color: white;
                    padding: 6px 12px;
                    border-radius: 6px;
                    font-size: 0.75rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">
                    {priority}
                </div>
                <div style="
                    background: linear-gradient(135deg, {status_color}, {status_color}dd);
                    color: white;
                    padding: 6px 16px;
                    border-radius: 16px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">
                    {qa_status}
                </div>
                <div style="color: #9ca3af; font-size: 0.875rem; font-weight: 500;">
                    👤 {assignee}
                </div>
                <div style="color: #9ca3af; font-size: 0.875rem; font-weight: 500;">
                    📅 {created_at}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 제목 및 지라 키
        st.markdown(f"""
        <div style="padding: 20px 20px 16px 20px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="
                    background: linear-gradient(135deg, #374151, #4b5563);
                    color: #e5e7eb;
                    padding: 4px 12px;
                    border-radius: 6px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                    border: 1px solid #4b5563;
                ">
                    {jira_key}
                </span>
                {f'<a href="{jira_url}" target="_blank" style="color: #60a5fa; text-decoration: none; font-size: 0.875rem; font-weight: 500; transition: color 0.2s;">🔗 Jira에서 보기</a>' if jira_url else ''}
            </div>
            <h3 style="
                margin: 0;
                color: #f9fafb;
                font-size: 1.25rem;
                font-weight: 700;
                line-height: 1.4;
                text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            ">
                {title}
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 작업 설명 - 가독성 개선된 다크모드 스타일
        clean_description = description.strip() if description and description.strip() else '설명이 없습니다.'
        import re
        clean_description = re.sub(r'\n\s*\n', '\n\n', clean_description)
        
        st.markdown(f"""
        <div style="padding: 0 20px 20px 20px;">
            <div style="margin-bottom: 10px; color: #f3f4f6; font-weight: 600; font-size: 0.9rem;">
                📄 작업 설명
            </div>
            <div style="
                background: linear-gradient(135deg, #1e293b, #334155);
                border: 1px solid #475569;
                border-radius: 10px;
                padding: 20px;
                color: #f1f5f9;
                font-size: 1rem;
                line-height: 1.7;
                white-space: pre-wrap;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                letter-spacing: 0.3px;
            ">
                {clean_description}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 기존 메모 (있는 경우만) - 편집/삭제 가능한 다크모드 스타일
        if current_memo:
            st.markdown(f"""
            <div style="padding: 0 20px 20px 20px;">
                <div style="margin-bottom: 10px; color: #f3f4f6; font-weight: 600; font-size: 0.875rem;">
                    📋 기존 메모
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 메모 편집 모드 체크
            edit_memo_key = f"edit_memo_{task_type}_{task_id}_{index}"
            is_editing = st.session_state.get(edit_memo_key, False)
            
            col1, col2, col3 = st.columns([6, 1, 1])
            
            # 편집 모드에서는 text_area를 별도 변수로 저장
            edited_memo_value = None
            
            with col1:
                if is_editing:
                    # 편집 모드
                    edited_memo_value = st.text_area(
                        "메모 편집",
                        value=current_memo,
                        height=100,
                        key=f"edited_memo_{task_type}_{task_id}_{index}",
                        label_visibility="collapsed"
                    )
                else:
                    # 읽기 모드
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #451a03, #78350f);
                        border: 1px solid #92400e;
                        border-radius: 8px;
                        padding: 16px;
                        color: #fbbf24;
                        font-size: 0.875rem;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
                        margin: 0 20px 20px 20px;
                    ">
                        {current_memo}
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                if is_editing:
                    # 저장 버튼 (기존 메모 편집용)
                    if st.button("💾", key=f"save_edit_memo_{task_type}_{task_id}_{index}", help="메모 저장"):
                        # 편집된 메모 텍스트 사용 - 직접 변수 사용
                        if edited_memo_value is not None and edited_memo_value.strip():
                            memo_result = update_task_memo(task_id, edited_memo_value.strip())
                            if memo_result and memo_result.get("success"):
                                st.success("✅ 메모가 수정되었습니다.")
                                # 편집 모드 종료
                                st.session_state[edit_memo_key] = False
                                # 편집된 메모 세션 상태 정리
                                edited_memo_key = f"edited_memo_{task_type}_{task_id}_{index}"
                                if edited_memo_key in st.session_state:
                                    del st.session_state[edited_memo_key]
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ 메모 수정에 실패했습니다.")
                        else:
                            st.warning("메모 내용을 입력해주세요.")
                else:
                    # 편집 버튼
                    if st.button("✏️", key=f"edit_memo_{task_type}_{task_id}_{index}", help="메모 편집"):
                        st.session_state[edit_memo_key] = True
                        st.rerun()
            
            with col3:
                if is_editing:
                    # 취소 버튼
                    if st.button("❌", key=f"cancel_memo_{task_type}_{task_id}_{index}", help="편집 취소"):
                        st.session_state[edit_memo_key] = False
                        st.rerun()
                else:
                    # 삭제 버튼
                    if st.button("🗑️", key=f"delete_memo_{task_type}_{task_id}_{index}", help="메모 삭제"):
                        memo_result = update_task_memo(task_id, "")
                        if memo_result and memo_result.get("success"):
                            st.success("✅ 메모가 삭제되었습니다.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ 메모 삭제에 실패했습니다.")
        
        st.markdown("""
        <div style="
            padding: 20px;
            background: linear-gradient(135deg, #0f172a, #1e293b);
            border-top: 1px solid #334155;
            border-radius: 0 0 12px 12px;
        ">
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns([2.5, 0.5, 2, 1, 1])
        
        with col1:
            # 새 메모 입력
            memo_text = st.text_input(
                "💬 새 메모",
                value="",
                key=f"new_memo_{task_type}_{task_id}_{index}",
                placeholder="QA 진행 상황을 간단히 기록하세요...",
                label_visibility="collapsed"
            )
        
        with col2:
            # 메모 저장 버튼 (입력 폼 바로 옆)
            if st.button("📝", key=f"save_memo_{task_type}_{task_id}_{index}", help="메모 저장", use_container_width=True):
                if memo_text.strip():
                    combined_memo = current_memo
                    if combined_memo:
                        combined_memo += f"\n\n--- {created_at} 추가 ---\n{memo_text}"
                    else:
                        combined_memo = memo_text
                    
                    memo_result = update_task_memo(task_id, combined_memo)
                    if memo_result and memo_result.get("success"):
                        st.success("✅ 메모가 저장되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 메모 저장에 실패했습니다.")
                else:
                    st.warning("메모 내용을 입력해주세요.")
        
        with col3:
            # QA 상태 변경
            current_status = task.get('qa_status', '미시작')
            qa_statuses = ["미시작", "QA 시작", "QA 진행중", "QA 완료"]
            
            new_status = st.selectbox(
                "상태",
                qa_statuses,
                index=qa_statuses.index(current_status) if current_status in qa_statuses else 0,
                key=f"qa_status_{task_type}_{task_id}_{index}",
                label_visibility="collapsed"
            )
        
        with col4:
            # QA 상태 저장 버튼
            if st.button("🔄", key=f"save_status_{task_type}_{task_id}_{index}", help="QA 상태 저장", type="primary", use_container_width=True):
                if new_status != current_status:
                    status_result = update_qa_status(task_id, new_status)
                    if status_result and status_result.get("success"):
                        st.success(f"✅ 상태가 '{new_status}'로 변경되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 상태 변경에 실패했습니다.")
                else:
                    st.info("현재 상태와 동일합니다.")
        
        with col5:
            # 작업 삭제 버튼
            if st.button("🗑️", key=f"delete_{task_type}_{task_id}_{index}", help="작업 삭제", use_container_width=True):
                st.session_state[f'show_delete_modal_{task_id}'] = True
                st.rerun()
        
        # 컨테이너 종료
        st.markdown("</div></div>", unsafe_allow_html=True)
