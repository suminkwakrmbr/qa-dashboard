"""
작업 관리 페이지 - 리스트 형식 초기화면과 상세 페이지로 분리
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
    sync_zephyr_cycles_from_api, get_zephyr_test_cycles, get_cycle_test_results_summary,
    get_zephyr_cycles_from_api
)
from streamlit_app.utils.helpers import get_jira_issue_url

def show_task_management():
    """작업 관리 메인 화면 - 페이지 상태에 따라 리스트 또는 상세 표시"""
    
    # 페이지 상태 관리
    if 'task_page_state' not in st.session_state:
        st.session_state.task_page_state = 'list'  # 'list' 또는 'detail'
    
    if 'selected_task_id' not in st.session_state:
        st.session_state.selected_task_id = None
    
    # 페이지 상태에 따라 화면 표시
    if st.session_state.task_page_state == 'list':
        show_task_list()
    elif st.session_state.task_page_state == 'detail':
        show_task_detail()

def show_task_list():
    """작업 목록 화면 (리스트 형식)"""
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
    
    # 작업 목록 가져오기
    try:
        tasks_response = get_tasks()
        
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
            if sort_by != "전체":
                sort_order = st.selectbox("정렬 순서", ["높은 순", "낮은 순"])
            else:
                sort_order = st.selectbox("정렬 순서", ["미지정"], disabled=True)
        with col3:
            items_per_page = st.selectbox(
                "페이지당 표시", 
                [10, 20, 50, 100, "전체"],
                index=1,
                help="한 페이지에 표시할 작업 개수를 선택하세요"
            )
        
        # 우선순위 매핑
        priority_order = {"Highest": 5, "High": 4, "Medium": 3, "Low": 2, "Lowest": 1}
        qa_status_order = {"QA 완료": 4, "QA 진행중": 3, "QA 시작": 2, "미시작": 1}
        
        # 정렬 적용
        if sort_by == "전체":
            pass
        elif sort_by == "우선순위":
            tasks.sort(key=lambda x: priority_order.get(x.get('priority', 'Medium'), 3), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "상태":
            tasks.sort(key=lambda x: qa_status_order.get(x.get('qa_status', '미시작'), 1), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "업데이트 시간":
            def safe_date_key(task):
                updated_at = task.get('updated_at')
                if updated_at is None or updated_at == '':
                    return '1900-01-01'
                return str(updated_at)
            
            tasks.sort(key=safe_date_key, reverse=(sort_order == "높은 순"))
        
        # 페이지네이션 설정
        if items_per_page == "전체":
            page_tasks = tasks
            current_page = 0
            total_pages = 1
        else:
            items_per_page = int(items_per_page)
            total_pages = (len(tasks) + items_per_page - 1) // items_per_page
            
            if total_pages > 1:
                current_page = st.selectbox(
                    "페이지 선택",
                    range(1, total_pages + 1),
                    key="task_page_selector",
                    help=f"총 {total_pages}페이지 중 선택"
                ) - 1
            else:
                current_page = 0
            
            start_idx = current_page * items_per_page
            end_idx = min(start_idx + items_per_page, len(tasks))
            page_tasks = tasks[start_idx:end_idx]
        
        # 표시 정보 (간단하게)
        if items_per_page != "전체":
            start_num = current_page * items_per_page + 1
            end_num = min((current_page + 1) * items_per_page, len(tasks))
        
        # 게시판 형태의 테이블로 작업 목록 표시
        st.markdown("---")
        
        # 테이블 데이터 준비 (상세보기 버튼 포함)
        table_data = []
        for task in page_tasks:
            jira_key = task.get('jira_key', 'N/A')
            title = task.get('title', 'N/A')
            priority = task.get('priority', 'Medium')
            qa_status = task.get('qa_status', '미시작')
            assignee = task.get('assignee', 'N/A')
            created_at = task.get('created_at', 'N/A')[:10] if task.get('created_at') else 'N/A'
            task_id = task.get('id')
            
            # 제목 길이 제한
            display_title = title[:50] + '...' if len(title) > 50 else title
            
            # 우선순위별 아이콘
            priority_icons = {
                'Highest': '🔴',
                'High': '🟠', 
                'Medium': '🟡',
                'Low': '🟢',
                'Lowest': '🔵'
            }
            priority_display = f"{priority_icons.get(priority, '🟡')} {priority}"
            
            # QA 상태별 아이콘
            status_icons = {
                'QA 완료': '✅',
                'QA 진행중': '🔄',
                'QA 시작': '🚀',
                '미시작': '⏸️'
            }
            status_display = f"{status_icons.get(qa_status, '⏸️')} {qa_status}"
            
            table_data.append({
                'ID': task_id,
                '작업 키': jira_key,
                '제목': display_title,
                '우선순위': priority_display,
                'QA 상태': status_display,
                '담당자': assignee,
                '생성일': created_at
            })
        
        # 커스텀 스타일 적용 - 극한 압축
        st.markdown("""
        <style>
        /* 전체 앱 스타일 */
        .main .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        
        /* 마크다운 요소 간격 최소화 */
        .stMarkdown {
            margin-bottom: 0px !important;
            margin-top: 0px !important;
        }
        
        /* 컬럼 간격 최소화 */
        .stColumns {
            gap: 0.2rem !important;
        }
        
        /* 구분선 간격 최소화 */
        hr {
            margin: 0.2rem 0 !important;
        }
        
        /* 버튼 높이 최소화 */
        .stButton > button {
            height: 2rem !important;
            padding: 0.2rem 0.5rem !important;
            font-size: 14px !important;
            line-height: 1.2 !important;
        }
        
        /* 텍스트 요소 간격 최소화 및 상하 가운데 정렬 */
        p {
            margin-bottom: 0.2rem !important;
            margin-top: 0.2rem !important;
            line-height: 1.2 !important;
            display: flex !important;
            align-items: center !important;
            min-height: 2rem !important;
        }
        
        /* 컬럼 내 텍스트 상하 가운데 정렬 (좌우는 왼쪽 정렬) */
        .stColumns > div > div {
            display: flex !important;
            align-items: center !important;
            min-height: 2rem !important;
        }
        
        /* 모든 컬럼 텍스트 왼쪽 정렬 */
        .stColumns > div > div p {
            text-align: left !important;
            justify-content: flex-start !important;
        }
        
        /* 전체 데이터프레임 스타일 */
        .stDataFrame {
            font-size: 22px !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        }
        
        /* 데이터프레임 내부 테이블 */
        .stDataFrame table {
            font-size: 22px !important;
            line-height: 1.2 !important;
        }
        
        /* 헤더 스타일 */
        .stDataFrame thead th {
            font-size: 24px !important;
            font-weight: 800 !important;
            padding: 2px 4px !important;
            background-color: #f1f3f4 !important;
            border-bottom: 3px solid #dadce0 !important;
            color: #202124 !important;
            text-align: center !important;
            line-height: 1.1 !important;
        }
        
        /* 데이터 셀 스타일 */
        .stDataFrame tbody td {
            font-size: 22px !important;
            padding: 1px 4px !important;
            border-bottom: 1px solid #e8eaed !important;
            vertical-align: middle !important;
            color: #3c4043 !important;
            text-align: center !important;
            line-height: 1.1 !important;
        }
        
        /* 제목 컬럼은 왼쪽 정렬 */
        .stDataFrame tbody td:nth-child(2) {
            text-align: left !important;
            font-weight: 500 !important;
        }
        
        /* 행 호버 효과 */
        .stDataFrame tbody tr:hover {
            background-color: #f8f9fa !important;
        }
        
        /* 리사이즈 핸들 숨기기 */
        .stDataFrame [data-testid="stDataFrameResizeHandle"] {
            display: none !important;
        }
        
        /* 전체 컨테이너 스타일 */
        .stDataFrame > div {
            border-radius: 8px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
            overflow: hidden !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📋 작업 목록")
        
        # 헤더 행
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 4, 1.5, 1.5, 1.5, 1.2, 1])
        
        with col1:
            st.markdown("**작업 키**")
        with col2:
            st.markdown("**제목**")
        with col3:
            st.markdown("**우선순위**")
        with col4:
            st.markdown("**QA 상태**")
        with col5:
            st.markdown("**담당자**")
        with col6:
            st.markdown("**생성일**")
        with col7:
            st.markdown("**액션**")
        
        st.markdown("---")
        
        # 작업 목록 표시
        for i, task in enumerate(page_tasks):
            jira_key = task.get('jira_key', 'N/A')
            title = task.get('title', 'N/A')
            priority = task.get('priority', 'Medium')
            qa_status = task.get('qa_status', '미시작')
            assignee = task.get('assignee', 'N/A')
            created_at = task.get('created_at', 'N/A')[:10] if task.get('created_at') else 'N/A'
            task_id = task.get('id')
            
            # 우선순위별 아이콘
            priority_icons = {
                'Highest': '🔴',
                'High': '🟠', 
                'Medium': '🟡',
                'Low': '🟢',
                'Lowest': '🔵'
            }
            priority_display = f"{priority_icons.get(priority, '🟡')} {priority}"
            
            # QA 상태별 아이콘
            status_icons = {
                'QA 완료': '✅',
                'QA 진행중': '🔄',
                'QA 시작': '🚀',
                '미시작': '⏸️'
            }
            status_display = f"{status_icons.get(qa_status, '⏸️')} {qa_status}"
            
            # 제목 길이 제한
            display_title = title[:60] + '...' if len(title) > 60 else title
            
            # 각 작업을 행으로 표시
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.5, 4, 1.5, 1.5, 1.5, 1.2, 1])
            
            with col1:
                st.markdown(f"{jira_key}")
            
            with col2:
                st.markdown(f"{display_title}")
            
            with col3:
                st.markdown(f"{priority_display}")
            
            with col4:
                st.markdown(f"{status_display}")
            
            with col5:
                st.markdown(f"{assignee}")
            
            with col6:
                st.markdown(f"{created_at}")
            
            with col7:
                if st.button(
                    "상세보기",
                    key=f"detail_btn_{task_id}",
                    help=f"'{title}' 작업의 상세 정보를 봅니다",
                    use_container_width=True,
                    type="primary"
                ):
                    st.session_state.selected_task_id = task_id
                    st.session_state.task_page_state = 'detail'
                    st.rerun()
            
            # 작업 간 구분선 (마지막 작업 제외)
            if i < len(page_tasks) - 1:
                st.markdown("---")
    else:
        st.info("작업이 없습니다. 지라에서 프로젝트를 동기화해주세요.")

def show_task_detail():
    """작업 상세 화면"""
    # 뒤로 가기 버튼
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("← 목록으로", help="작업 목록으로 돌아갑니다"):
            st.session_state.task_page_state = 'list'
            st.session_state.selected_task_id = None
            st.rerun()
    
    # 선택된 작업 ID 확인
    task_id = st.session_state.get('selected_task_id')
    if not task_id:
        st.error("선택된 작업이 없습니다.")
        if st.button("목록으로 돌아가기"):
            st.session_state.task_page_state = 'list'
            st.rerun()
        return
    
    # 작업 정보 가져오기
    try:
        tasks_response = get_tasks()
        tasks = []
        
        if tasks_response:
            if isinstance(tasks_response, dict) and 'tasks' in tasks_response:
                tasks = tasks_response['tasks']
            elif isinstance(tasks_response, list):
                tasks = tasks_response
        
        # 선택된 작업 찾기
        selected_task = None
        for task in tasks:
            if str(task.get('id')) == str(task_id):
                selected_task = task
                break
        
        if not selected_task:
            st.error("선택된 작업을 찾을 수 없습니다.")
            if st.button("목록으로 돌아가기"):
                st.session_state.task_page_state = 'list'
                st.rerun()
            return
        
        # 작업 상세 정보 표시
        show_task_detail_card(selected_task)
        
    except Exception as e:
        st.error(f"작업 상세 정보를 불러오는 중 오류가 발생했습니다: {str(e)}")
        if st.button("목록으로 돌아가기"):
            st.session_state.task_page_state = 'list'
            st.rerun()

def show_task_detail_card(task):
    """작업 상세 정보 카드"""
    
    # 기본 정보 추출
    jira_key = task.get('jira_key', 'N/A')
    title = task.get('title', 'N/A')
    description = task.get('description', '설명이 없습니다.')
    priority = task.get('priority', 'Medium')
    qa_status = task.get('qa_status', '미시작')
    assignee = task.get('assignee', 'N/A')
    created_at = task.get('created_at', 'N/A')[:10] if task.get('created_at') else 'N/A'
    task_id = task.get('id')
    
    # 프로젝트 키 추출 - 여러 방법으로 시도
    project_key = task.get('project_key')
    if not project_key or project_key == 'N/A':
        # jira_key에서 프로젝트 키 추출 (예: RB-6494 -> RB)
        if jira_key and jira_key != 'N/A' and '-' in jira_key:
            project_key = jira_key.split('-')[0]
        else:
            project_key = None
    
    # 지라 URL
    jira_url = get_jira_issue_url(jira_key) if jira_key and jira_key != 'N/A' else None
    
    # 페이지 헤더
    st.header(f"📋 {jira_key} - 작업 상세")
    
    # 기본 정보 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("우선순위", priority)
    with col2:
        st.metric("QA 상태", qa_status)
    with col3:
        st.metric("담당자", assignee)
    with col4:
        st.metric("생성일", created_at)
    
    # 제목 및 설명
    st.subheader("📄 작업 제목")
    st.write(title)
    
    if jira_url:
        st.markdown(f"🔗 [Jira에서 보기]({jira_url})")
    
    st.subheader("📝 작업 설명")
    st.write(description)
    
    # QA 상태 변경
    st.subheader("🔄 QA 상태 변경")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_qa_status = st.selectbox(
            "상태 변경",
            ["미시작", "QA 시작", "QA 진행중", "QA 완료"],
            index=["미시작", "QA 시작", "QA 진행중", "QA 완료"].index(qa_status) if qa_status in ["미시작", "QA 시작", "QA 진행중", "QA 완료"] else 0,
            key=f"qa_status_select_{task_id}"
        )
    
    with col2:
        # 버튼을 selectbox와 같은 높이에 맞추기 위해 빈 라벨 추가
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("상태 변경", key=f"update_qa_status_{task_id}"):
            if new_qa_status != qa_status:
                result = update_qa_status(task_id, new_qa_status)
                if result and result.get("success"):
                    st.success(f"✅ QA 상태가 '{new_qa_status}'로 변경되었습니다.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ QA 상태 변경에 실패했습니다.")
            else:
                st.info("현재 상태와 동일합니다.")
    
    # 메모 관리
    st.subheader("📋 메모 관리")
    
    # 현재 메모 불러오기
    current_memo = ""
    memo_data = get_task_memo(task_id)
    if memo_data and memo_data.get('memo'):
        current_memo = memo_data['memo']
    
    # 메모 표시 및 편집
    if current_memo:
        st.write("**현재 메모:**")
        st.info(current_memo)
        
        # 메모 편집
        col1, col2 = st.columns([3, 1])
        with col1:
            edited_memo = st.text_area(
                "메모 편집",
                value=current_memo,
                height=100,
                key=f"edit_memo_{task_id}"
            )
        with col2:
            # 텍스트 영역과 버튼 정렬을 위한 여백 추가
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("메모 수정", key=f"update_memo_{task_id}"):
                if edited_memo.strip():
                    result = update_task_memo(task_id, edited_memo.strip())
                    if result and result.get("success"):
                        st.success("✅ 메모가 수정되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 메모 수정에 실패했습니다.")
                else:
                    st.warning("메모 내용을 입력해주세요.")
            
            if st.button("메모 삭제", key=f"delete_memo_{task_id}"):
                result = update_task_memo(task_id, "")
                if result and result.get("success"):
                    st.success("✅ 메모가 삭제되었습니다.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("❌ 메모 삭제에 실패했습니다.")
    else:
        # 새 메모 추가
        col1, col2 = st.columns([3, 1])
        with col1:
            new_memo = st.text_area(
                "새 메모 추가",
                height=100,
                key=f"new_memo_{task_id}",
                placeholder="메모를 입력하세요..."
            )
        with col2:
            # 텍스트 영역과 버튼 정렬을 위한 여백 추가
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("메모 추가", key=f"add_memo_{task_id}"):
                if new_memo.strip():
                    result = update_task_memo(task_id, new_memo.strip())
                    if result and result.get("success"):
                        st.success("✅ 메모가 추가되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 메모 추가에 실패했습니다.")
                else:
                    st.warning("메모 내용을 입력해주세요.")
    
    # Zephyr 사이클 연동
    st.subheader("🔗 Zephyr 테스트 사이클 연동")
    
    # 연결된 사이클 표시
    linked_cycles = get_task_linked_cycles(task_id)
    
    if linked_cycles and len(linked_cycles) > 0:
        st.write("**연결된 사이클:**")
        
        for cycle in linked_cycles:
            cycle_name = cycle.get('cycle_name', 'Unknown Cycle')
            cycle_id = cycle.get('id', 'N/A')
            linked_by = cycle.get('linked_by', 'Unknown')
            link_reason = cycle.get('link_reason', '')
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"🔗 **{cycle_name}** (ID: {cycle_id})\n연결자: {linked_by}\n 메모: {link_reason}")
            
            with col2:
                if st.button("연결 해제", key=f"unlink_{task_id}_{cycle_id}"):
                    result = unlink_task_from_cycle(task_id, cycle_id)
                    if result and result.get("success"):
                        st.success("✅ 사이클 연결이 해제되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 사이클 연결 해제에 실패했습니다.")
            
            # 사이클 테스트 결과 표시
            if cycle_id and cycle_id != 'N/A':
                with st.expander(f"📊 {cycle_name} 테스트 실행 현황"):
                    test_summary = get_cycle_test_results_summary(cycle_id)
                    
                    if test_summary and test_summary.get('total_tests', 0) > 0:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("총 테스트", test_summary.get('total_tests', 0))
                        with col2:
                            st.metric("실행률", f"{test_summary.get('executed_tests', 0)}/{test_summary.get('total_tests', 0)} ({test_summary.get('execution_rate', 0)}%)")
                        with col3:
                            st.metric("통과", test_summary.get('passed_tests', 0))
                        with col4:
                            st.metric("실패", test_summary.get('failed_tests', 0))
                        
                        if test_summary.get('executed_tests', 0) > 0:
                            st.success(f"✅ 통과율: {test_summary.get('pass_rate', 0)}%")
                        else:
                            st.info("아직 실행된 테스트가 없습니다.")
                    else:
                        st.info("테스트 결과 정보를 불러올 수 없습니다.")
    
    # 새 사이클 연결
    st.write("**새 사이클 연결:**")
    
    # Zephyr API에서 직접 사이클 조회 (프로젝트 키가 있는 경우)
    if project_key:
        # Zephyr API에서 직접 사이클 목록 가져오기
        zephyr_cycles = get_zephyr_cycles_from_api(project_key)
        
        if zephyr_cycles and len(zephyr_cycles) > 0:
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # 사이클 옵션 생성 (최신순으로 정렬)
                cycle_options = {}
                for cycle in zephyr_cycles:
                    cycle_name = cycle.get('cycle_name', 'Unknown')
                    cycle_id = cycle.get('id', 'N/A')
                    status = cycle.get('status', 'Unknown')
                    created_at = cycle.get('created_at', 'N/A')[:10] if cycle.get('created_at') else 'N/A'
                    
                    display_name = f"{cycle_name} ({status}) - {created_at}"
                    cycle_options[display_name] = cycle
                
                selected_cycle_name = st.selectbox(
                    "연결할 사이클 선택",
                    list(cycle_options.keys()),
                    key=f"zephyr_cycle_select_{task_id}",
                    help=f"총 {len(zephyr_cycles)}개 사이클 중 선택"
                )
                selected_cycle = cycle_options[selected_cycle_name]
            
            with col2:
                link_reason = st.text_input(
                    "메모",
                    placeholder="메모를 입력하세요...",
                    key=f"zephyr_link_reason_{task_id}"
                )
            
            with col3:
                # 입력 폼과 버튼 정렬을 위한 여백 추가
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("사이클 연결", key=f"link_zephyr_cycle_{task_id}"):
                    cycle_id = selected_cycle.get('id')
                    cycle_name = selected_cycle.get('cycle_name', 'Unknown')
                    
                    result = link_task_to_cycle(
                        task_id=task_id,
                        cycle_id=cycle_id,
                        cycle_name=cycle_name,
                        linked_by="QA팀",
                        link_reason=link_reason or "Zephyr API에서 직접 연결"
                    )
                    
                    if result and result.get("success"):
                        st.success(f"✅ '{cycle_name}' 사이클이 연결되었습니다.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 사이클 연결에 실패했습니다.")
            
            # 선택된 사이클 상세 정보 표시
            with st.expander("🔍 선택된 사이클 상세 정보", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("사이클 이름", selected_cycle.get('cycle_name', 'N/A'))
                with col2:
                    st.metric("상태", selected_cycle.get('status', 'N/A'))
                with col3:
                    st.metric("환경", selected_cycle.get('environment', 'N/A'))
                with col4:
                    st.metric("버전", selected_cycle.get('version', 'N/A'))
                
                st.write("**설명:**", selected_cycle.get('description', '설명이 없습니다.'))
                st.write("**생성자:**", selected_cycle.get('created_by', 'N/A'))
                st.write("**담당자:**", selected_cycle.get('assigned_to', 'N/A'))
                
                # 테스트 통계 표시
                total_tests = selected_cycle.get('total_test_cases', 0)
                if total_tests > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("총 테스트", total_tests)
                    with col2:
                        st.metric("실행됨", selected_cycle.get('executed_test_cases', 0))
                    with col3:
                        st.metric("통과", selected_cycle.get('passed_test_cases', 0))
                    with col4:
                        st.metric("실패", selected_cycle.get('failed_test_cases', 0))
                else:
                    st.info("테스트 케이스 정보가 없습니다.")
        
        else:
            st.warning(f"⚠️ {project_key} 프로젝트에서 사이클을 찾을 수 없습니다.")
    else:
        st.warning("⚠️ 프로젝트 키를 찾을 수 없어 사이클을 조회할 수 없습니다.")
        st.info("Jira 키에서 프로젝트 키를 추출할 수 없습니다. 예: RB-6494 → RB")
    
    # 작업 삭제
    st.subheader("🗑️ 작업 삭제")
    st.warning("⚠️ 작업을 삭제하면 복구할 수 없습니다.")
    
    if st.button("작업 삭제", key=f"delete_task_{task_id}", type="secondary"):
        st.session_state[f'show_delete_modal_{task_id}'] = True
        st.rerun()
    
    # 삭제 확인 모달
    if st.session_state.get(f'show_delete_modal_{task_id}', False):
        with st.container():
            st.error(f"정말로 '{jira_key} - {title}' 작업을 삭제하시겠습니까?")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("삭제 확인", key=f"confirm_delete_{task_id}", type="primary"):
                    result = delete_task(task_id)
                    if result and result.get("success"):
                        st.success("✅ 작업이 삭제되었습니다.")
                        st.cache_data.clear()
                        st.session_state.task_page_state = 'list'
                        st.session_state.selected_task_id = None
                        st.rerun()
                    else:
                        st.error("❌ 작업 삭제에 실패했습니다.")
            
            with col2:
                if st.button("취소", key=f"cancel_delete_{task_id}"):
                    st.session_state[f'show_delete_modal_{task_id}'] = False
                    st.rerun()

def show_reset_modal():
    """전체 초기화 확인 모달"""
    with st.container():
        st.error("⚠️ 모든 작업 데이터를 삭제하시겠습니까?")
        st.warning("이 작업은 되돌릴 수 없습니다.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("전체 삭제 확인", key="confirm_reset_all", type="primary"):
                result = reset_all_tasks()
                if result and result.get("success"):
                    st.success("✅ 모든 작업이 삭제되었습니다.")
                    st.cache_data.clear()
                    st.session_state.show_reset_modal = False
                    st.rerun()
                else:
                    st.error("❌ 작업 삭제에 실패했습니다.")
        
        with col2:
            if st.button("취소", key="cancel_reset_all"):
                st.session_state.show_reset_modal = False
                st.rerun()
