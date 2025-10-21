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
    update_qa_status, update_task_memo, get_task_memo, get_sync_status, reset_all_tasks,
    get_cycles_for_project, get_zephyr_projects, get_task_linked_cycles, 
    get_available_cycles_for_task, link_task_to_cycle, unlink_task_from_cycle,
    sync_zephyr_cycles_from_api, get_zephyr_test_cycles, get_cycle_test_results_summary
)
from streamlit_app.utils.helpers import get_jira_issue_url

def load_zephyr_projects_for_task_management():
    """작업 관리용 Zephyr 프로젝트 목록 로드 (Zephyr 관리와 동일한 방식)"""
    try:
        projects_data = get_zephyr_projects()
        
        if projects_data and isinstance(projects_data, list):
            st.session_state.zephyr_projects = projects_data
        else:
            st.session_state.zephyr_projects = []
    except Exception as e:
        st.error(f"프로젝트 로드 실패: {str(e)}")
        st.session_state.zephyr_projects = []

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
        
        # Zephyr 테스트 사이클 연동 정보 표시
        show_related_cycles_section(task, task_id, index, task_type)
        
        # 컨테이너 종료
        st.markdown("</div></div>", unsafe_allow_html=True)


def show_related_cycles_section(task, task_id, index, task_type):
    """Task와 관련된 Zephyr 테스트 사이클 정보 표시 및 관리 - 항상 표시"""
    
    # 프로젝트 키 추출 (Jira 키에서 프로젝트 부분 추출)
    jira_key = task.get('jira_key', '')
    if not jira_key or jira_key == 'N/A':
        return
    
    # Jira 키에서 프로젝트 키 추출 (예: KAN-123 -> KAN)
    project_key = jira_key.split('-')[0] if '-' in jira_key else jira_key
    
    # 사이클 정보 항상 표시
    st.markdown("""
    <div style="
        padding: 20px;
        background: linear-gradient(135deg, #0f1419, #1a1f2e);
        border-top: 1px solid #2d3748;
        margin-top: 10px;
    ">
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="margin-bottom: 15px; color: #e2e8f0; font-weight: 600; font-size: 0.95rem;">
        ⚡ {project_key} 프로젝트의 Zephyr 테스트 사이클 관리
    </div>
    """, unsafe_allow_html=True)
    
    # 탭 상태를 세션에 저장하여 유지
    tab_key = f"cycle_tab_{task_type}_{task_id}_{index}"
    
    # 기본값은 "연결된 사이클" 탭 (인덱스 0)
    if tab_key not in st.session_state:
        st.session_state[tab_key] = 0
    
    # 버튼으로 탭 선택 - 텍스트 크기에 맞게 작은 버튼으로 왼쪽 정렬, 여백 없이 붙여서 배치
    col1, col2, col3 = st.columns([0.38, 0.35, 4.4])
    
    with col1:
        if st.button(
            "🔗 연결된 사이클",
            key=f"linked_cycles_btn_{task_type}_{task_id}_{index}",
            type="primary" if st.session_state[tab_key] == 0 else "secondary"
        ):
            st.session_state[tab_key] = 0
            st.rerun()
    
    with col2:
        if st.button(
            "➕ 사이클 추가",
            key=f"add_cycle_btn_{task_type}_{task_id}_{index}",
            type="primary" if st.session_state[tab_key] == 1 else "secondary"
        ):
            st.session_state[tab_key] = 1
            st.rerun()
    
    # 선택된 탭에 따라 내용 표시
    if st.session_state[tab_key] == 0:
        # 현재 연결된 사이클 표시
        show_linked_cycles(task_id, project_key, task_type, index)
    else:
        # 사이클 추가 인터페이스
        show_add_cycle_interface(task_id, project_key, task_type, index)
    
    st.markdown("</div>", unsafe_allow_html=True)


def show_linked_cycles(task_id, project_key, task_type, index):
    """연결된 사이클 목록 표시"""
    try:
        # 연결된 사이클 조회
        linked_cycles = None
        try:
            linked_cycles = get_task_linked_cycles(task_id)
        except Exception as api_error:
            st.error(f"연결된 사이클 API 호출 실패: {str(api_error)}")
            linked_cycles = []
        
        # 완전한 None 및 타입 체크
        if linked_cycles is None:
            linked_cycles = []
        elif not isinstance(linked_cycles, list):
            # dict 타입인 경우 처리 시도
            if isinstance(linked_cycles, dict):
                if "data" in linked_cycles:
                    linked_cycles = linked_cycles["data"]
                elif "cycles" in linked_cycles:
                    linked_cycles = linked_cycles["cycles"]
                else:
                    linked_cycles = []
            else:
                linked_cycles = []
        
        # 유효한 사이클만 필터링
        valid_linked_cycles = []
        if isinstance(linked_cycles, list):
            for cycle in linked_cycles:
                if cycle is not None and isinstance(cycle, dict):
                    # 필수 필드 확인
                    if cycle.get('id') is not None:
                        valid_linked_cycles.append(cycle)
        
        if len(valid_linked_cycles) > 0:
            st.markdown(f"""
            <div style="margin-bottom: 15px; color: #10b981; font-weight: 600; font-size: 0.9rem;">
                ✅ 현재 {len(valid_linked_cycles)}개의 사이클이 연결되어 있습니다
            </div>
            """, unsafe_allow_html=True)
            
            # 연결된 각 사이클 표시
            for i, cycle in enumerate(valid_linked_cycles):
                try:
                    show_linked_cycle_card(cycle, i, task_id, task_type, index)
                except Exception as card_error:
                    st.error(f"사이클 카드 표시 중 오류 (사이클 {i+1}): {str(card_error)}")
                    # 간단한 텍스트로라도 표시
                    cycle_name = cycle.get('cycle_name', '이름 없음') if isinstance(cycle, dict) else '알 수 없음'
                    st.text(f"🔗 {cycle_name} (카드 표시 오류)")
        else:
            # 연결된 사이클이 없는 경우
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #2d3748, #4a5568);
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                color: #e2e8f0;
                margin: 15px 0;
            ">
                <div style="font-size: 1.2rem; margin-bottom: 10px;">🔗</div>
                <div style="font-weight: 600; margin-bottom: 8px;">연결된 사이클이 없습니다</div>
                <div style="font-size: 0.875rem; color: #a0aec0;">
                    '사이클 추가' 탭에서 테스트 사이클을 연결해보세요.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"연결된 사이클 조회 실패: {str(e)}")


def show_add_cycle_interface(task_id, project_key, task_type, index):
    """사이클 추가 인터페이스"""
    try:
        # 프로젝트 키 선택 옵션 추가
        st.markdown("""
        <div style="margin-bottom: 15px; color: #3b82f6; font-weight: 600; font-size: 0.9rem;">
            📋 Zephyr 테스트 사이클 연결
        </div>
        """, unsafe_allow_html=True)
        
        # Zephyr 프로젝트 로드 - 강제 새로고침
        try:
            # 항상 최신 프로젝트 목록을 가져오도록 강제 로드
            load_zephyr_projects_for_task_management()
            zephyr_projects = st.session_state.get('zephyr_projects', [])
            
            # 프로젝트가 없으면 다시 한 번 시도
            if not zephyr_projects:
                st.info("🔄 Zephyr 프로젝트를 다시 조회하는 중...")
                projects_data = get_zephyr_projects()
                if projects_data and isinstance(projects_data, list):
                    st.session_state.zephyr_projects = projects_data
                    zephyr_projects = projects_data
                    st.success(f"✅ {len(zephyr_projects)}개 Zephyr 프로젝트를 로드했습니다!")
                else:
                    st.error("❌ Zephyr 프로젝트 조회에 실패했습니다.")
                    zephyr_projects = []
                
        except Exception as e:
            st.error(f"Zephyr 프로젝트 로드 실패: {str(e)}")
            zephyr_projects = []
        
        # 프로젝트 옵션 생성
        project_options = {}
        
        if isinstance(zephyr_projects, list) and len(zephyr_projects) > 0:
            for project in zephyr_projects:
                if isinstance(project, dict):
                    project_key_val = project.get('key')
                    project_name_val = project.get('name')
                    
                    if project_key_val:  # key만 있어도 추가
                        display_name = f"{project_key_val}"
                        if project_name_val:
                            display_name += f" - {project_name_val}"
                        project_options[display_name] = project_key_val
        
        if not project_options:
            st.warning("⚠️ 사용 가능한 Zephyr 프로젝트가 없습니다.")
            st.info("💡 Zephyr 관리 페이지에서 먼저 연결을 확인해주세요.")
            return  # 프로젝트가 없으면 여기서 종료
        
        # 기본 선택값 설정 (KAN 프로젝트 우선)
        default_project = None
        # KAN 프로젝트가 있으면 기본 선택
        for display_name, key in project_options.items():
            if key == 'KAN':
                default_project = display_name
                break
        # KAN이 없으면 첫 번째 프로젝트 선택
        if not default_project:
            default_project = list(project_options.keys())[0]
        
        selected_project_display = st.selectbox(
            "Zephyr 프로젝트 선택",
            options=list(project_options.keys()),
            index=list(project_options.keys()).index(default_project) if default_project else 0,
            key=f"zephyr_project_{task_type}_{task_id}_{index}",
            help="연결할 테스트 사이클이 있는 Zephyr 프로젝트를 선택하세요"
        )
        
        selected_project_key = project_options.get(selected_project_display)
        
        # 글로벌 사이클 저장소에서 사이클 데이터 조회
        available_cycles = []
        project_id = None
        
        # 프로젝트 ID 찾기
        if zephyr_projects and isinstance(zephyr_projects, list):
            for project in zephyr_projects:
                if project.get('key') == selected_project_key:
                    project_id = project.get('id')
                    break
        
        # 1. 글로벌 저장소에서 먼저 확인
        if 'global_zephyr_cycles' in st.session_state and selected_project_key in st.session_state.global_zephyr_cycles:
            available_cycles = st.session_state.global_zephyr_cycles[selected_project_key]
            if not isinstance(available_cycles, list) or len(available_cycles) == 0:
                available_cycles = []
        
        # 2. 글로벌 저장소에 없으면 세션 상태에서 확인
        if not available_cycles and project_id:
            cycles_key = f"test_cycles_{project_id}"
            if cycles_key in st.session_state:
                zephyr_cycles = st.session_state[cycles_key]
                if isinstance(zephyr_cycles, list) and len(zephyr_cycles) > 0:
                    available_cycles = zephyr_cycles
                    st.success(f"✅ 세션에서 조회된 {len(available_cycles)}개 사이클을 가져왔습니다!")
                    
                    # 글로벌 저장소에도 저장 (다음번 사용을 위해)
                    if 'global_zephyr_cycles' not in st.session_state:
                        st.session_state.global_zephyr_cycles = {}
                    st.session_state.global_zephyr_cycles[selected_project_key] = available_cycles
                    st.info(f"📦 글로벌 저장소에 {selected_project_key} 프로젝트 사이클을 저장했습니다.")
        
        # 3. 둘 다 없으면 직접 API 조회
        if not available_cycles and project_id:
            try:
                with st.spinner(f"{selected_project_key} 프로젝트의 사이클을 조회하는 중..."):
                    available_cycles = get_zephyr_test_cycles(project_id, limit=100)
                    
                if isinstance(available_cycles, list) and len(available_cycles) > 0:
                    # 동기화 시간 기록
                    import datetime
                    sync_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for cycle in available_cycles:
                        cycle['last_sync'] = sync_time
                    
                    # 세션과 글로벌 저장소 모두에 저장
                    cycles_key = f"test_cycles_{project_id}"
                    st.session_state[cycles_key] = available_cycles
                    
                    if 'global_zephyr_cycles' not in st.session_state:
                        st.session_state.global_zephyr_cycles = {}
                    st.session_state.global_zephyr_cycles[selected_project_key] = available_cycles
                else:
                    available_cycles = []
                    
            except Exception as e:
                st.error(f"❌ 사이클 직접 조회 실패: {str(e)}")
                available_cycles = []
        
        # 4. 여전히 없으면 안내 메시지
        if not available_cycles:
            st.warning("⚠️ 사용 가능한 사이클이 없습니다.")
            st.info("💡 Zephyr 관리 페이지에서 먼저 사이클을 조회하거나, 위의 '실제 사이클 동기화' 버튼을 사용해주세요.")
        
        # 3. 이미 연결된 사이클 제외
        valid_cycles = []
        if isinstance(available_cycles, list):
            # 연결된 사이클 목록 조회
            linked_cycles = get_task_linked_cycles(task_id)
            linked_cycle_ids = []
            
            if isinstance(linked_cycles, list):
                for linked_cycle in linked_cycles:
                    if isinstance(linked_cycle, dict) and linked_cycle.get('id'):
                        linked_cycle_ids.append(str(linked_cycle.get('id')))
            
            # 연결되지 않은 사이클만 필터링
            for cycle in available_cycles:
                if cycle is not None and isinstance(cycle, dict):
                    cycle_id = cycle.get('id')
                    if cycle_id is not None and str(cycle_id) not in linked_cycle_ids:
                        valid_cycles.append(cycle)
        
        if len(valid_cycles) > 0:
            st.markdown(f"""
            <div style="margin-bottom: 15px; color: #3b82f6; font-weight: 600; font-size: 0.9rem;">
                📋 연결 가능한 사이클 ({len(valid_cycles)}개)
            </div>
            """, unsafe_allow_html=True)
            
            # 사이클 선택 드롭다운 - 안전한 처리 및 KAN-R 번호 기준 최신순 정렬
            cycle_options = {}
            try:
                # KAN-R 번호 추출 함수
                def extract_kan_r_number(cycle):
                    cycle_name = cycle.get('cycle_name', '') if isinstance(cycle, dict) else ''
                    if cycle_name:
                        try:
                            # KAN-R-123 형식에서 마지막 숫자 추출
                            import re
                            match = re.search(r'KAN-R-(\d+)', cycle_name)
                            if match:
                                return int(match.group(1))
                        except (ValueError, AttributeError):
                            pass
                    return 0  # KAN-R 번호가 없으면 0 (가장 낮은 우선순위)
                
                # KAN-R 번호 기준으로 내림차순 정렬 (높은 번호가 최신)
                sorted_cycles = sorted(valid_cycles, key=extract_kan_r_number, reverse=True)
                
                for cycle in sorted_cycles:
                    # 각 필드를 안전하게 추출
                    cycle_name = "이름 없음"
                    cycle_status = "N/A"
                    cycle_env = "N/A"
                    cycle_version = "N/A"
                    
                    try:
                        if isinstance(cycle, dict):
                            cycle_name = str(cycle.get('cycle_name', '이름 없음'))
                            cycle_status = str(cycle.get('status', 'N/A'))
                            cycle_env = str(cycle.get('environment', 'N/A'))
                            cycle_version = str(cycle.get('version', 'N/A'))
                    except Exception:
                        # 개별 필드 추출 실패 시 기본값 사용
                        pass
                    
                    display_name = f"{cycle_name} ({cycle_status}) - {cycle_env} v{cycle_version}"
                    cycle_options[display_name] = cycle.get('id')
                
                if len(cycle_options) > 0:
                    selected_cycle_name = st.selectbox(
                        "연결할 사이클 선택",
                        options=list(cycle_options.keys()),
                        key=f"select_cycle_{task_type}_{task_id}_{index}",
                        help="Task에 연결할 Zephyr 테스트 사이클을 선택하세요"
                    )
                    
                    # 연결 이유 입력
                    link_reason = st.text_area(
                        "연결 이유 (선택사항)",
                        placeholder="이 사이클을 연결하는 이유를 간단히 설명해주세요...",
                        key=f"link_reason_{task_type}_{task_id}_{index}",
                        height=80
                    )
                    
                    # 연결 버튼
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        if st.button(
                            "🔗 사이클 연결",
                            key=f"link_cycle_{task_type}_{task_id}_{index}",
                            help="선택한 사이클을 이 Task에 연결합니다",
                            use_container_width=True,
                            type="primary"
                        ):
                            try:
                                cycle_id = cycle_options.get(selected_cycle_name)
                                
                                if cycle_id:
                                    with st.spinner("사이클을 연결하는 중..."):
                                        # 사이클 이름 추출
                                        extracted_cycle_name = selected_cycle_name.split(' (')[0] if selected_cycle_name else f"Cycle {cycle_id}"
                                        final_link_reason = link_reason.strip() if link_reason and link_reason.strip() else "Task 관리에서 연결"
                                        
                                        result = link_task_to_cycle(
                                            task_id=task_id,
                                            cycle_id=cycle_id,
                                            cycle_name=extracted_cycle_name,
                                            linked_by="QA팀",
                                            link_reason=final_link_reason
                                        )
                                    
                                    if result and result.get("success", True):
                                        st.success(f"✅ 선택한 사이클이 성공적으로 연결되었습니다!")
                                        
                                        # 폼 초기화 - 안전한 세션 상태 제거
                                        keys_to_remove = []
                                        try:
                                            for key in list(st.session_state.keys()):
                                                if (f"select_cycle_{task_type}_{task_id}_{index}" in str(key) or 
                                                    f"link_reason_{task_type}_{task_id}_{index}" in str(key)):
                                                    keys_to_remove.append(key)
                                            
                                            for key in keys_to_remove:
                                                if key in st.session_state:
                                                    del st.session_state[key]
                                        except Exception:
                                            # 세션 상태 정리 실패 시 무시
                                            pass
                                        
                                        # 캐시 무효화 (Streamlit 방식)
                                        st.cache_data.clear()
                                        
                                        # 성공 메시지 표시 후 즉시 페이지 새로고침
                                        st.rerun()
                                    else:
                                        error_msg = "알 수 없는 오류"
                                        if result and isinstance(result, dict):
                                            error_msg = result.get("message", error_msg)
                                        st.error(f"❌ 사이클 연결 실패: {error_msg}")
                                else:
                                    st.error("❌ 선택한 사이클의 ID를 찾을 수 없습니다.")
                            except Exception as link_error:
                                st.error(f"❌ 사이클 연결 중 오류: {str(link_error)}")
                    
                else:
                    st.warning("⚠️ 표시할 수 있는 사이클이 없습니다.")
                    
            except Exception as options_error:
                st.error(f"사이클 옵션 생성 중 오류: {str(options_error)}")
                
        else:
            # 연결 가능한 사이클이 없는 경우
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #2d3748, #4a5568);
                border: 1px solid #4a5568;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                color: #e2e8f0;
                margin: 15px 0;
            ">
                <div style="font-size: 1.2rem; margin-bottom: 10px;">📋</div>
                <div style="font-weight: 600; margin-bottom: 8px;">연결 가능한 사이클이 없습니다</div>
                <div style="font-size: 0.875rem; color: #a0aec0;">
                    모든 사이클이 이미 연결되었거나, 프로젝트에 사이클이 없습니다.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 실제 Zephyr 사이클 동기화 및 Zephyr 관리 페이지로 이동 버튼
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button(
                    "🔄 실제 사이클 동기화",
                    key=f"sync_zephyr_cycles_{task_type}_{task_id}_{index}",
                    help="Zephyr Scale API에서 실제 테스트 사이클 데이터를 가져옵니다",
                    use_container_width=True,
                    type="primary"
                ):
                    with st.spinner(f"{project_key} 프로젝트의 Zephyr 사이클을 동기화하는 중..."):
                        # 실제 Zephyr API에서 테스트 사이클 조회 (Zephyr 관리 로직 사용)
                        try:
                            # 프로젝트 ID 찾기 (프로젝트 키로부터)
                            projects = get_zephyr_projects()
                            project_id = None
                            
                            if projects and isinstance(projects, list):
                                for project in projects:
                                    if project.get('key') == project_key:
                                        project_id = project.get('id')
                                        break
                            
                            if project_id:
                                # 실제 Zephyr Scale API에서 테스트 사이클 조회
                                cycles = get_zephyr_test_cycles(project_id, limit=100)
                                
                                if cycles and isinstance(cycles, list):
                                    # 동기화 시간 기록
                                    import datetime
                                    sync_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    
                                    # 각 사이클에 동기화 시간 추가
                                    for cycle in cycles:
                                        cycle['last_sync'] = sync_time
                                    
                                    st.success(f"✅ {len(cycles)}개 Zephyr 테스트 사이클 동기화 완료!")
                                    
                                    if len(cycles) == 0:
                                        st.info("ℹ️ 이 프로젝트에는 테스트 사이클이 없습니다.")
                                else:
                                    st.warning("⚠️ 테스트 사이클을 찾을 수 없습니다.")
                            else:
                                st.error(f"❌ 프로젝트 '{project_key}'를 Zephyr에서 찾을 수 없습니다.")
                                
                        except Exception as e:
                            st.error(f"❌ Zephyr 사이클 동기화 실패: {str(e)}")
                        
                        # 동기화 후 캐시 클리어하고 페이지 새로고침
                        st.cache_data.clear()
                        st.rerun()
            
            with col3:
                if st.button(
                    "🔗 Zephyr 관리로 이동",
                    key=f"goto_zephyr_add_{task_type}_{task_id}_{index}",
                    help="Zephyr 연동 관리 페이지에서 새 사이클 생성",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.info("📍 상단 메뉴에서 'Zephyr 연동 관리' 페이지를 선택해주세요.")
                    
    except Exception as e:
        st.error(f"사이클 추가 인터페이스 로드 실패: {str(e)}")


def show_linked_cycle_card(cycle, cycle_index, task_id, task_type, task_index):
    """연결된 사이클 카드 (해제 버튼 포함) - 실제 테스트 결과 표시"""
    
    cycle_name = cycle.get('cycle_name', '이름 없음')
    status = cycle.get('status', 'Not Started')
    environment = cycle.get('environment', 'N/A')
    version = cycle.get('version', 'N/A')
    linked_at = cycle.get('linked_at', 'N/A')
    link_reason = cycle.get('link_reason', '')
    cycle_id = cycle.get('id')
    
    # 실제 테스트 결과 조회
    test_results_summary = None
    if cycle_id:
        try:
            test_results_summary = get_cycle_test_results_summary(cycle_id)
        except Exception as e:
            st.warning(f"테스트 결과 조회 중 오류: {str(e)}")
    
    # 테스트 통계 (실제 데이터 우선, 없으면 기본값)
    if test_results_summary and test_results_summary.get('total_tests', 0) > 0:
        total_cases = test_results_summary.get('total_tests', 0)
        executed_cases = test_results_summary.get('executed_tests', 0)
        passed_cases = test_results_summary.get('passed_tests', 0)
        failed_cases = test_results_summary.get('failed_tests', 0)
        blocked_cases = test_results_summary.get('blocked_tests', 0)
        not_executed_cases = test_results_summary.get('not_executed_tests', 0)
        pass_rate = test_results_summary.get('pass_rate', 0.0)
        execution_rate = test_results_summary.get('execution_rate', 0.0)
        test_results = test_results_summary.get('test_results', [])
    else:
        # 기본값 사용
        total_cases = cycle.get('total_test_cases', 0)
        executed_cases = cycle.get('executed_test_cases', 0)
        passed_cases = cycle.get('passed_test_cases', 0)
        failed_cases = cycle.get('failed_test_cases', 0)
        blocked_cases = cycle.get('blocked_test_cases', 0)
        not_executed_cases = total_cases - executed_cases
        pass_rate = (passed_cases / executed_cases * 100) if executed_cases > 0 else 0.0
        execution_rate = (executed_cases / total_cases * 100) if total_cases > 0 else 0.0
        test_results = []
    
    # 연결된 사이클 정보를 expander로 표시
    with st.expander(f"🔗 {cycle_name} ({status})", expanded=True):
        # 기본 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"🌐 **환경:** {environment}")
        with col2:
            st.write(f"📦 **버전:** {version}")
        with col3:
            st.write(f"📅 **연결일:** {linked_at[:10] if linked_at != 'N/A' else 'N/A'}")
        
        # 연결 이유 (있는 경우)
        if link_reason:
            st.info(f"💬 **연결 이유:** {link_reason}")
        
        # 테스트 진행률 (테스트 케이스가 있는 경우만)
        if total_cases > 0:
            st.markdown("### 📊 테스트 실행 현황")
            
            # 실행률 표시
            st.write(f"**실행률:** {executed_cases}/{total_cases} ({execution_rate:.1f}%)")
            normalized_execution_rate = min(execution_rate / 100, 1.0)
            st.progress(normalized_execution_rate, text=f"실행률: {execution_rate:.1f}%")
            
            # 테스트 결과 통계 (실행된 케이스가 있는 경우)
            if executed_cases > 0:
                st.write(f"**통과율:** {passed_cases}/{executed_cases} ({pass_rate:.1f}%)")
                
                # 상세 통계
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("✅ 통과", passed_cases, delta=None)
                with col2:
                    st.metric("❌ 실패", failed_cases, delta=None)
                with col3:
                    st.metric("🚫 차단", blocked_cases, delta=None)
                with col4:
                    st.metric("⏸️ 미실행", not_executed_cases, delta=None)
                with col5:
                    st.metric("📈 통과율", f"{pass_rate:.1f}%", delta=None)
                
                # 실제 테스트 결과 상세 표시 (최대 10개)
                if test_results and len(test_results) > 0:
                    st.markdown("### 🔍 최근 테스트 결과")
                    
                    # 상태별 필터링 옵션
                    status_filter = st.selectbox(
                        "상태 필터",
                        ["전체", "Pass", "Fail", "Blocked", "Not Executed"],
                        key=f"status_filter_{task_type}_{task_id}_{task_index}_{cycle_index}"
                    )
                    
                    # 필터링된 결과
                    filtered_results = test_results
                    if status_filter != "전체":
                        filtered_results = [r for r in test_results if r.get('status', '').startswith(status_filter)]
                    
                    # 최대 10개만 표시
                    display_results = filtered_results[:10]
                    
                    if display_results:
                        for i, result in enumerate(display_results):
                            test_case_key = result.get('test_case_key', 'N/A')
                            test_case_name = result.get('test_case_name', 'Unknown Test')
                            result_status = result.get('status', 'Unknown')
                            executed_by = result.get('executed_by', 'Unknown')
                            executed_on = result.get('executed_on', 'N/A')
                            comment = result.get('comment', '')
                            
                            # 상태별 색상
                            status_color = {
                                'Pass': '🟢',
                                'Passed': '🟢',
                                'Fail': '🔴',
                                'Failed': '🔴',
                                'Blocked': '🟡',
                                'Not Executed': '⚪'
                            }.get(result_status, '⚫')
                            
                            # 테스트 결과 카드
                            with st.container():
                                st.markdown(f"""
                                <div style="
                                    background: linear-gradient(135deg, #1e293b, #334155);
                                    border-left: 4px solid {'#10b981' if 'Pass' in result_status else '#ef4444' if 'Fail' in result_status else '#f59e0b' if 'Blocked' in result_status else '#6b7280'};
                                    border-radius: 8px;
                                    padding: 12px;
                                    margin: 8px 0;
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                        <div style="font-weight: 600; color: #f1f5f9; font-size: 0.9rem;">
                                            {status_color} {test_case_key} - {test_case_name[:50]}{'...' if len(test_case_name) > 50 else ''}
                                        </div>
                                        <div style="
                                            background: {'#10b981' if 'Pass' in result_status else '#ef4444' if 'Fail' in result_status else '#f59e0b' if 'Blocked' in result_status else '#6b7280'};
                                            color: white;
                                            padding: 4px 8px;
                                            border-radius: 12px;
                                            font-size: 0.75rem;
                                            font-weight: 600;
                                        ">
                                            {result_status}
                                        </div>
                                    </div>
                                    <div style="display: flex; gap: 20px; font-size: 0.8rem; color: #cbd5e1;">
                                        <div>👤 {executed_by}</div>
                                        <div>📅 {executed_on[:10] if executed_on != 'N/A' else 'N/A'}</div>
                                    </div>
                                    {f'<div style="margin-top: 8px; font-size: 0.8rem; color: #94a3b8; font-style: italic;">💬 {comment}</div>' if comment else ''}
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if len(filtered_results) > 10:
                            st.info(f"📋 {len(filtered_results) - 10}개의 추가 테스트 결과가 있습니다.")
                    else:
                        st.info("선택한 상태의 테스트 결과가 없습니다.")
            else:
                st.info("아직 실행된 테스트가 없습니다.")
        else:
            st.write("📋 테스트 케이스가 없습니다.")
        
        # 연결 해제 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(
                "🔓 연결 해제",
                key=f"unlink_cycle_{task_type}_{task_id}_{task_index}_{cycle_index}",
                help="이 사이클과의 연결을 해제합니다",
                use_container_width=True,
                type="secondary"
            ):
                if cycle_id:
                    with st.spinner("사이클 연결을 해제하는 중..."):
                        result = unlink_task_from_cycle(task_id, cycle_id)
                    
                    if result and result.get("success", True):
                        st.success(f"✅ '{cycle_name}' 연결이 해제되었습니다!")
                        
                        # 캐시 무효화 (Streamlit 방식)
                        st.cache_data.clear()
                        
                        st.rerun()
                    else:
                        error_msg = result.get("message", "알 수 없는 오류") if result else "연결 해제 실패"
                        st.error(f"❌ 연결 해제 실패: {error_msg}")
                else:
                    st.error("❌ 사이클 ID를 찾을 수 없습니다.")


def show_cycle_preview_card(cycle):
    """사이클 미리보기 카드"""
    
    cycle_name = cycle.get('cycle_name', '이름 없음')
    status = cycle.get('status', 'Not Started')
    environment = cycle.get('environment', 'N/A')
    version = cycle.get('version', 'N/A')
    description = cycle.get('description', '설명이 없습니다.')
    
    # 테스트 통계
    total_cases = cycle.get('total_test_cases', 0)
    executed_cases = cycle.get('executed_test_cases', 0)
    
    # 상태별 색상
    status_colors = {
        'Not Started': '#6b7280',
        'In Progress': '#3b82f6',
        'Completed': '#10b981',
        'Cancelled': '#ef4444'
    }
    status_color = status_colors.get(status, '#6b7280')
    
    # 미리보기 카드
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="
                font-weight: 600;
                color: #3b82f6;
                font-size: 0.95rem;
            ">
                👁️ {cycle_name}
            </div>
            <div style="
                background: {status_color};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            ">
                {status}
            </div>
        </div>
        
        <div style="display: flex; gap: 20px; margin-bottom: 12px; font-size: 0.85rem; color: #cbd5e1;">
            <div>🌐 {environment}</div>
            <div>📦 {version}</div>
            <div>📊 {total_cases}개 테스트</div>
        </div>
        
        <div style="
            font-size: 0.85rem;
            color: #94a3b8;
            line-height: 1.4;
            margin-top: 8px;
        ">
            {description[:100]}{'...' if len(description) > 100 else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_cycle_summary_card(cycle, cycle_index, task_id, task_type, task_index):
    """테스트 사이클 요약 카드 표시"""
    
    cycle_name = cycle.get('cycle_name', '이름 없음')
    status = cycle.get('status', 'Not Started')
    environment = cycle.get('environment', 'N/A')
    version = cycle.get('version', 'N/A')
    
    # 테스트 통계
    total_cases = cycle.get('total_test_cases', 0)
    executed_cases = cycle.get('executed_test_cases', 0)
    passed_cases = cycle.get('passed_test_cases', 0)
    failed_cases = cycle.get('failed_test_cases', 0)
    
    # 진행률 계산
    progress_rate = (executed_cases / total_cases * 100) if total_cases > 0 else 0
    pass_rate = (passed_cases / executed_cases * 100) if executed_cases > 0 else 0
    
    # 상태별 색상
    status_colors = {
        'Not Started': '#6b7280',
        'In Progress': '#3b82f6',
        'Completed': '#10b981',
        'Cancelled': '#ef4444'
    }
    status_color = status_colors.get(status, '#6b7280')
    
    # 사이클 카드
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid #475569;
        border-radius: 8px;
        padding: 16px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="
                font-weight: 600;
                color: #f1f5f9;
                font-size: 0.95rem;
            ">
                � {cycle_name}
            </div>
            <div style="
                background: {status_color};
                color: white;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            ">
                {status}
            </div>
        </div>
        
        <div style="display: flex; gap: 20px; margin-bottom: 12px; font-size: 0.85rem; color: #cbd5e1;">
            <div>🌐 {environment}</div>
            <div>📦 {version}</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 진행률 표시 (테스트 케이스가 있는 경우만)
    if total_cases > 0:
        # Streamlit의 progress bar 사용
        st.markdown(f"""
        <div style="margin-bottom: 8px; font-size: 0.8rem; color: #94a3b8;">
            📊 테스트 진행률: {executed_cases}/{total_cases} ({progress_rate:.1f}%)
        </div>
        """, unsafe_allow_html=True)
        
        # 정규화된 진행률 (0-1 사이)
        normalized_progress = min(progress_rate / 100, 1.0)
        st.progress(normalized_progress)
        
        # 테스트 결과 통계 (실행된 케이스가 있는 경우)
        if executed_cases > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div style="text-align: center; font-size: 0.75rem; color: #10b981;">
                    <div style="font-weight: 600;">{passed_cases}</div>
                    <div>통과</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="text-align: center; font-size: 0.75rem; color: #ef4444;">
                    <div style="font-weight: 600;">{failed_cases}</div>
                    <div>실패</div>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                st.markdown(f"""
                <div style="text-align: center; font-size: 0.75rem; color: #f59e0b;">
                    <div style="font-weight: 600;">{cycle.get('blocked_test_cases', 0)}</div>
                    <div>차단</div>
                </div>
                """, unsafe_allow_html=True)
            with col4:
                st.markdown(f"""
                <div style="text-align: center; font-size: 0.75rem; color: #3b82f6;">
                    <div style="font-weight: 600;">{pass_rate:.1f}%</div>
                    <div>통과율</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 10px; color: #94a3b8; font-size: 0.85rem;">
            📋 테스트 케이스가 없습니다
        </div>
        """, unsafe_allow_html=True)
    
    # 날짜 정보
    start_date = cycle.get('start_date', 'N/A')
    end_date = cycle.get('end_date', 'N/A')
    if start_date != 'N/A' or end_date != 'N/A':
        st.markdown(f"""
        <div style="margin-top: 8px; font-size: 0.75rem; color: #94a3b8; text-align: center;">
            📅 {start_date} ~ {end_date}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
