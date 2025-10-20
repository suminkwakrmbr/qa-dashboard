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
        
        # 우선순위별 정렬 옵션
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox("정렬 기준", ["전체", "우선순위", "상태", "업데이트 시간"])
        with col2:
            # '전체' 선택 시 정렬 순서 옵션 비활성화
            if sort_by != "전체":
                sort_order = st.selectbox("정렬 순서", ["높은 순", "낮은 순"])
            else:
                sort_order = st.selectbox("정렬 순서", ["미지정"], disabled=True)
        
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
            tasks.sort(key=lambda x: qa_status_order.get(x.get('status', '미시작'), 1), 
                      reverse=(sort_order == "높은 순"))
        elif sort_by == "업데이트 시간":
            tasks.sort(key=lambda x: x.get('updated_at', ''), 
                      reverse=(sort_order == "높은 순"))
        
        # 페이지네이션 설정
        items_per_page = 20
        total_pages = (len(tasks) + items_per_page - 1) // items_per_page
        
        # 페이지 선택
        if total_pages > 1:
            current_page = st.selectbox(
                "페이지 선택",
                range(1, total_pages + 1),
                key="task_page_selector"
            ) - 1
        else:
            current_page = 0
        
        # 현재 페이지의 작업들만 표시
        start_idx = current_page * items_per_page
        end_idx = min(start_idx + items_per_page, len(tasks))
        page_tasks = tasks[start_idx:end_idx]
        
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
    """순수 Streamlit 컴포넌트로 구성된 안정적인 작업 카드"""
    
    # 기본 정보 추출
    jira_key = task.get('jira_key', 'N/A')
    title = task.get('title', 'N/A')
    description = task.get('description', '설명이 없습니다.')
    priority = task.get('priority', 'Medium')
    qa_status = task.get('qa_status', '미시작')  # qa_status 필드 사용
    assignee = task.get('assignee', 'N/A')  # 실제 데이터베이스 필드 사용
    updated_at = task.get('updated_at', 'N/A')[:10] if task.get('updated_at') else 'N/A'
    created_at = task.get('created_at', 'N/A')[:10] if task.get('created_at') else 'N/A'
    task_id = task.get('id')
    project_id = task.get('project_id', 'N/A')
    
    # 지라 URL
    jira_url = get_jira_issue_url(jira_key) if jira_key and jira_key != 'N/A' else None
    
    # 메모 불러오기
    current_memo = ""
    memo_data = get_task_memo(task_id)
    if memo_data and memo_data.get('memo'):
        current_memo = memo_data['memo']
    
    # 우선순위별 이모지
    priority_emojis = {
        'Highest': '🔴',
        'High': '🟠', 
        'Medium': '🟡',
        'Low': '🟢',
        'Lowest': '🔵'
    }
    priority_emoji = priority_emojis.get(priority, '🟡')
    
    # QA 상태별 이모지
    status_emojis = {
        'QA 완료': '✅',
        'QA 진행중': '🔄',
        'QA 시작': '🚀',
        '미시작': '⏸️'
    }
    status_emoji = status_emojis.get(qa_status, '⏸️')
    
    # 삭제 모달 표시
    if st.session_state.get(f'show_delete_modal_{task_id}', False):
        delete_task_modal(task_id, jira_key, title)
    
    # 카드 컨테이너 - 다크테마 디자인
    with st.container():
        # 상태별 배경색 설정 (다크테마)
        status_colors = {
            'QA 완료': '#1e3a2e',  # 다크 초록
            'QA 진행중': '#3d3a1e',  # 다크 노랑
            'QA 시작': '#1e2a3d',   # 다크 파랑
            '미시작': '#2d2d2d'     # 다크 회색
        }
        
        card_color = status_colors.get(qa_status, '#2d2d2d')
        
        # 우선순위별 테두리 색상 (다크테마용)
        priority_border_colors = {
            'Highest': '#ff4757',  # 밝은 빨강
            'High': '#ff7f50',     # 밝은 주황
            'Medium': '#ffa502',   # 밝은 노랑
            'Low': '#2ed573',      # 밝은 초록
            'Lowest': '#3742fa'    # 밝은 파랑
        }
        
        border_color = priority_border_colors.get(priority, '#ffa502')
        
        # 스크롤 위치 유지를 위한 앵커 추가
        scroll_anchor = f"task_card_{task_id}"
        
        # 카드 스타일링 (다크테마 + 보더)
        st.markdown(f"""
        <div id="{scroll_anchor}" style="
            background-color: {card_color};
            color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid {border_color};
            border: 2px solid #555555;
            margin: 20px 0;
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        ">
        """, unsafe_allow_html=True)
        
        # 상태 변경 후 스크롤 위치 복원
        if st.session_state.get(f'scroll_to_task_{task_id}', False):
            st.markdown(f"""
            <script>
                setTimeout(function() {{
                    document.getElementById('{scroll_anchor}').scrollIntoView({{
                        behavior: 'smooth',
                        block: 'center'
                    }});
                }}, 100);
            </script>
            """, unsafe_allow_html=True)
            # 스크롤 완료 후 플래그 제거
            del st.session_state[f'scroll_to_task_{task_id}']
        
        # 첫 번째 행: 기본 정보
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            # 제목과 지라 키 - 더 큰 폰트
            if jira_url:
                st.markdown(f"## 🎫 [{jira_key}]({jira_url}) {title}")
            else:
                st.markdown(f"## 🎫 {jira_key} {title}")
        
        with col2:
            # 우선순위 - 배지 스타일 (다크테마)
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background-color: #404040; color: #ffffff; border-radius: 15px; margin: 5px; border: 1px solid {border_color};">
                <strong>{priority_emoji} {priority}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # QA 상태 - 배지 스타일 (다크테마)
            status_badge_colors = {
                'QA 완료': '#2ed573',
                'QA 진행중': '#ffa502',
                'QA 시작': '#3742fa',
                '미시작': '#747d8c'
            }
            status_badge_color = status_badge_colors.get(qa_status, '#747d8c')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background-color: #404040; color: #ffffff; border-radius: 15px; margin: 5px; border: 1px solid {status_badge_color};">
                <strong>{status_emoji} {qa_status}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # 두 번째 행: 메타 정보
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"👤 **담당자:** {assignee}")
        
        with col2:
            st.info(f"📅 **생성일:** {created_at}")
        
        with col3:
            if jira_url:
                st.link_button("🔗 지라에서 보기", jira_url)
        
        # 세 번째 행: 작업 설명
        st.markdown("**📝 작업 설명**")
        with st.container():
            # 설명 텍스트 정리 - 앞뒤 공백 제거 및 연속된 줄바꿈 정리
            if description and description.strip():
                # 앞뒤 공백 제거
                clean_description = description.strip()
                # 연속된 줄바꿈을 하나로 정리
                import re
                clean_description = re.sub(r'\n\s*\n', '\n\n', clean_description)
                # HTML 이스케이프 처리
                clean_description = clean_description.replace('&', '&').replace('<', '<').replace('>', '>')
                # 줄바꿈을 <br>로 변환
                description_formatted = clean_description.replace('\n', '<br>')
            else:
                description_formatted = '설명이 없습니다.'
            
            st.markdown(f"""
            <div style="
                background-color: #404040;
                color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                border-left: 3px solid {border_color};
                margin: 10px 0;
                word-wrap: break-word;
                max-height: 200px;
                overflow-y: auto;
                line-height: 1.5;
            ">
            {description_formatted}
            </div>
            """, unsafe_allow_html=True)
        
        # 네 번째 행: 기존 메모 (있는 경우)
        if current_memo:
            st.markdown("**📝 기존 메모**")
            with st.container():
                st.text_area(
                    "기존 메모 내용",
                    value=current_memo,
                    height=60,
                    disabled=True,
                    key=f"existing_memo_{task_type}_{task_id}_{index}"
                )
        
        # 다섯 번째 행: 컨트롤 영역 (3컬럼으로 변경)
        col1, col2, col3 = st.columns([4, 2, 1])
        
        with col1:
            # 새 메모 입력
            memo_text = st.text_area(
                "새 메모 작성",
                value="",
                height=80,
                key=f"new_memo_{task_type}_{task_id}_{index}",
                placeholder="QA 진행 상황, 발견된 이슈, 특이사항 등을 기록하세요..."
            )
            
            if st.button("💾 메모 저장", key=f"save_memo_{task_type}_{task_id}_{index}"):
                if memo_text.strip():
                    # 기존 메모와 새 메모를 합치기
                    combined_memo = current_memo
                    if combined_memo:
                        combined_memo += f"\n\n--- {updated_at} 추가 ---\n{memo_text}"
                    else:
                        combined_memo = memo_text
                    
                    result = update_task_memo(task_id, combined_memo)
                    if result and result.get("success"):
                        st.success("✅ 메모가 저장되었습니다.")
                        st.rerun()
                    else:
                        st.error("❌ 메모 저장에 실패했습니다.")
                else:
                    st.warning("메모 내용을 입력해주세요.")
        
        with col2:
            # QA 상태 변경
            st.markdown("**검수 상태 변경**")
            current_status = task.get('qa_status', '미시작')  # qa_status 필드 사용
            qa_statuses = ["미시작", "QA 시작", "QA 진행중", "QA 완료"]
            
            new_status = st.selectbox(
                "검수 상태",
                qa_statuses,
                index=qa_statuses.index(current_status) if current_status in qa_statuses else 0,
                key=f"qa_status_{task_type}_{task_id}_{index}",
                label_visibility="collapsed"
            )
            
            if st.button("🔄 상태 변경", key=f"update_status_{task_type}_{task_id}_{index}"):
                if new_status != current_status:
                    result = update_qa_status(task_id, new_status)
                    if result and result.get("success"):
                        st.success(f"✅ 상태가 '{new_status}'로 변경되었습니다.")
                        # 현재 위치 저장 (스크롤 위치 유지를 위해)
                        st.session_state[f'scroll_to_task_{task_id}'] = True
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("❌ 상태 변경에 실패했습니다.")
                else:
                    st.info("현재 상태와 동일합니다.")
        
        with col3:
            # 삭제 버튼 - 모달 트리거
            st.markdown("**작업 삭제**")
            if st.button("🗑️ 삭제", key=f"delete_{task_type}_{task_id}_{index}", type="secondary"):
                st.session_state[f'show_delete_modal_{task_id}'] = True
                st.rerun()
        
        # 카드 스타일링 종료
        st.markdown("</div>", unsafe_allow_html=True)
