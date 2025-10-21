"""
지라 프로젝트 관리 페이지 모듈
"""
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

from streamlit_app.api.client import get_api_base_url, get_sync_status, get_jira_project_issues, sync_jira_project

# 로거 설정
logger = logging.getLogger(__name__)

def get_current_selection_count(project_key: str, issues: List[Dict[str, Any]]) -> int:
    """현재 선택된 이슈 수 반환"""
    if not issues:
        return 0
    
    # 세션 상태에서 선택된 키들만 직접 카운트 (더 정확함)
    selected_count = 0
    for key in st.session_state.keys():
        if key.startswith(f"issue_select_{project_key}_") and st.session_state[key]:
            selected_count += 1
    
    return selected_count

def should_select_all_be_checked(project_key: str, issues: List[Dict[str, Any]]) -> bool:
    """전체 선택 체크박스가 체크되어야 하는지 판단"""
    if not issues:
        return False
    
    selected_count = get_current_selection_count(project_key, issues)
    return selected_count == len(issues)

def show_jira_project_management():
    """지라 프로젝트 관리 페이지"""
    # 동기화 상세 페이지 표시 여부 확인
    if 'sync_detail_project' in st.session_state and st.session_state.sync_detail_project:
        show_sync_detail_page(st.session_state.sync_detail_project)
    else:
        st.title("📂 지라 프로젝트 관리")
        st.markdown("---")
        
        # 탭 생성
        tab1, tab2 = st.tabs(["🔍 프로젝트 조회", "📊 프로젝트 통계"])
        
        with tab1:
            show_project_list()
        
        with tab2:
            show_project_statistics()

def show_project_list():
    """프로젝트 목록 조회"""
    st.subheader("🔍 지라 프로젝트 목록")
    
    # 프로젝트 조회 옵션
    col1, col2 = st.columns([2, 1])
    
    with col1:
        include_issue_count = st.checkbox(
            "이슈 수 포함 (처음 20개 프로젝트만)", 
            value=False,
            help="이슈 수를 포함하면 조회 시간이 오래 걸릴 수 있습니다."
        )
    
    with col2:
        if st.button("🔄 프로젝트 조회", type="primary", use_container_width=True):
            fetch_projects(include_issue_count)
    
    # 프로젝트 목록 표시
    if 'jira_projects' in st.session_state:
        display_projects(st.session_state.jira_projects)

def fetch_projects(include_issue_count: bool = False):
    """지라 프로젝트 목록 가져오기"""
    try:
        with st.spinner("지라 프로젝트를 조회하는 중..."):
            api_base_url = get_api_base_url()
            params = {"include_issue_count": include_issue_count}
            
            response = requests.get(
                f"{api_base_url}/jira/projects",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    st.session_state.jira_projects = data.get("projects", [])
                    st.success(f"✅ {len(st.session_state.jira_projects)}개 프로젝트를 조회했습니다.")
                else:
                    st.error(f"❌ 프로젝트 조회 실패: {data.get('message', '알 수 없는 오류')}")
            else:
                st.error(f"❌ API 호출 실패: {response.status_code}")
                
    except requests.exceptions.Timeout:
        st.error("❌ 요청 시간 초과. 네트워크 연결을 확인해주세요.")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 네트워크 오류: {str(e)}")
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류: {str(e)}")

def display_projects(projects: List[Dict[str, Any]]):
    """프로젝트 목록 표시"""
    if not projects:
        st.info("📋 조회된 프로젝트가 없습니다.")
        return
    
    st.markdown(f"**총 {len(projects)}개 프로젝트**")
    
    # 검색 필터
    search_term = st.text_input("🔍 프로젝트 검색", placeholder="프로젝트 키 또는 이름으로 검색...")
    
    # 필터링
    if search_term:
        filtered_projects = [
            p for p in projects 
            if search_term.lower() in p.get('key', '').lower() 
            or search_term.lower() in p.get('name', '').lower()
        ]
    else:
        filtered_projects = projects
    
    if not filtered_projects:
        st.warning("🔍 검색 조건에 맞는 프로젝트가 없습니다.")
        return
    
    # 자주 사용하는 프로젝트를 상단에 정렬
    frequent_projects = ['RB', 'ANDROID', 'IOS', 'PCWEB', 'API']
    
    # 자주 사용하는 프로젝트와 나머지 프로젝트 분리
    priority_projects = []
    other_projects = []
    
    for project in filtered_projects:
        project_key = project.get('key', '')
        if project_key in frequent_projects:
            priority_projects.append(project)
        else:
            other_projects.append(project)
    
    # 자주 사용하는 프로젝트를 지정된 순서대로 정렬
    priority_projects.sort(key=lambda x: frequent_projects.index(x.get('key', '')) if x.get('key', '') in frequent_projects else len(frequent_projects))
    
    # 최종 정렬된 프로젝트 목록
    sorted_projects = priority_projects + other_projects
    
    # 자주 사용하는 프로젝트 섹션 표시
    if priority_projects:
        st.markdown("### ⭐ 자주 사용하는 프로젝트")
        for i in range(0, len(priority_projects), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(priority_projects):
                    project = priority_projects[i + j]
                    display_project_card(col, project)
        
        st.markdown("---")
    
    # 나머지 프로젝트 섹션 표시
    if other_projects:
        st.markdown("### 📂 기타 프로젝트")
        for i in range(0, len(other_projects), 2):
            cols = st.columns(2)
            
            for j, col in enumerate(cols):
                if i + j < len(other_projects):
                    project = other_projects[i + j]
                    display_project_card(col, project)

def display_project_card(col, project: Dict[str, Any]):
    """프로젝트 카드 표시"""
    with col:
        project_key = project.get('key', 'N/A')
        
        # 프로젝트 상태 표시
        is_active = project.get('is_active')
        issue_count = project.get('issue_count')
        
        if is_active is True:
            status_color = "🟢"
            status_text = "활성"
        elif is_active is False:
            status_color = "🔴"
            status_text = "비활성"
        else:
            status_color = "⚪"
            status_text = "알 수 없음"
        
        # 동기화 상태 확인
        sync_status_info = ""
        sync_button_disabled = False
        
        try:
            sync_status = get_sync_status(project_key)
            if sync_status:
                sync_state = sync_status.get('status', 'unknown')
                sync_progress = sync_status.get('progress', 0)
                processed_issues = sync_status.get('processed_issues', 0)
                total_issues = sync_status.get('total_issues', 0)
                
                if sync_state in ["starting", "connecting", "fetching_issues", "processing"]:
                    if total_issues > 0:
                        sync_status_info = f"🔄 동기화 진행 중... ({processed_issues}/{total_issues}, {sync_progress}%)"
                    else:
                        sync_status_info = f"🔄 동기화 진행 중... ({sync_progress}%)"
                    sync_button_disabled = True
                elif sync_state == "completed":
                    if total_issues > 0:
                        sync_status_info = f"✅ 동기화 완료 ({processed_issues}/{total_issues})"
                    else:
                        sync_status_info = f"✅ 동기화 완료"
                elif sync_state == "error":
                    error_message = sync_status.get('message', '동기화 실패')
                    # 에러 메시지가 너무 길면 축약
                    if len(error_message) > 50:
                        error_message = error_message[:47] + "..."
                    sync_status_info = f"❌ {error_message}"
        except Exception as e:
            # 동기화 상태 조회 실패 시 로그만 남기고 무시
            logger.warning(f"동기화 상태 조회 실패 ({project_key}): {str(e)}")
        
        # 카드 내용 (다크 테마)
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1rem;
                background-color: #2b2b2b;
                color: #e5e7eb;
            ">
                <h4 style="margin: 0 0 0.5rem 0; color: #f3f4f6;">
                    {status_color} {project_key}
                </h4>
                <p style="margin: 0 0 0.5rem 0; color: #d1d5db; font-size: 0.9rem;">
                    <strong>{project.get('name', project.get('key', 'N/A')) if project.get('name', '').strip() else project.get('key', 'N/A')}</strong>
                </p>
                <p style="margin: 0 0 0.5rem 0; color: #9ca3af; font-size: 0.8rem;">
                    상태: {status_text}
                </p>
                {f'<p style="margin: 0 0 0.5rem 0; color: #60a5fa; font-size: 0.8rem;">이슈 수: {issue_count}개</p>' if issue_count is not None else ''}
                {sync_status_info}
            </div>
            """, unsafe_allow_html=True)
            
            # 동기화 버튼
            button_text = "🔄 동기화 진행 중..." if sync_button_disabled else f"🔄 {project_key} 동기화"
            
            if st.button(
                button_text,
                key=f"sync_{project_key}",
                use_container_width=True,
                disabled=sync_button_disabled
            ):
                # 동기화 상세 페이지로 이동
                st.session_state.sync_detail_project = project_key
                st.rerun()

def sync_project(project_key: str):
    """프로젝트 동기화 - 실시간 상태 업데이트"""
    if not project_key:
        st.error("❌ 프로젝트 키가 없습니다.")
        return
    
    try:
        # 동기화 시작
        api_base_url = get_api_base_url()
        
        # 동기화 요청 전송
        response = requests.post(
            f"{api_base_url}/jira/sync/{project_key}",
            timeout=20  # 시작 요청은 빠르게
        )
        
        if response.status_code != 200:
            st.error(f"❌ 동기화 시작 실패: {response.status_code}")
            return
        
        data = response.json()
        if not data.get("success"):
            st.error(f"❌ 동기화 시작 실패: {data.get('message', '알 수 없는 오류')}")
            return
        
        # 동기화 시작 성공 메시지
        st.info(f"🚀 {data.get('message', '동기화를 시작했습니다.')}")
        
        # 실시간 상태 모니터링
        monitor_sync_progress(project_key)
        
    except requests.exceptions.Timeout:
        st.error("❌ 동기화 시작 시간 초과. 잠시 후 다시 시도해주세요.")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 네트워크 오류: {str(e)}")
    except Exception as e:
        st.error(f"❌ 예상치 못한 오류: {str(e)}")

@st.dialog("동기화 진행 상황")
def sync_progress_modal(project_key: str):
    """동기화 진행 상황"""
    # 동기화 상태 조회
    sync_status = get_sync_status(project_key)
    
    if not sync_status:
        st.markdown("⚠️ **동기화 상태를 확인할 수 없습니다.**")
        st.markdown("상태 확인을 재시도하는 중...")
        time.sleep(2)
        st.rerun()
        return
    
    status = sync_status.get('status', 'unknown')
    progress = sync_status.get('progress', 0)
    message = sync_status.get('message', '진행 중...')
    total_issues = sync_status.get('total_issues', 0)
    processed_issues = sync_status.get('processed_issues', 0)
    
    # 메시지에서 불필요한 문구 제거
    if message:
        message = message.replace('(고성능 배치 처리)', '').strip()
        # 연속된 공백 제거
        import re
        message = re.sub(r'\s+', ' ', message)
    
    # 상태별 아이콘 설정
    if status == "starting":
        status_icon = "●"
        status_text = "시작 중"
    elif status == "connecting":
        status_icon = "●"
        status_text = "연결 중"
    elif status == "fetching_issues":
        status_icon = "●"
        status_text = "이슈 조회 중"
    elif status == "processing":
        status_icon = "●"
        status_text = "처리 중"
    elif status == "completed":
        status_icon = "✓"
        status_text = "완료"
    elif status == "error":
        status_icon = "✗"
        status_text = "오류"
    elif status == "not_found":
        status_icon = "!"
        status_text = "찾을 수 없음"
    else:
        status_icon = "●"
        status_text = "진행 중"
    
    # 상태 표시
    if status == "completed":
        st.markdown(f"**{status_icon} {status_text}**")
        if total_issues > 0:
            st.markdown(f"**완료:** {processed_issues}/{total_issues} 이슈 처리됨")
        else:
            st.markdown(f"{message}")
    elif status == "error":
        st.markdown(f"**{status_icon} {status_text}**")
        st.markdown(f"{message}")
    elif status == "not_found":
        st.markdown(f"**{status_icon} {status_text}**")
        st.markdown(f"{message}")
    else:
        st.markdown(f"**{status_icon} {status_text}**")
        st.markdown(f"{message}")
    
    # 진행률 표시
    st.progress(progress / 100.0)
    st.markdown(f"**진행률:** {progress}%")
    
    # 상세 정보 표시
    if total_issues > 0 and status == "processing":
        st.markdown(f"**처리 중:** {processed_issues}/{total_issues} 이슈")
    
    # 완료 상태가 아니면 자동 새로고침
    if status not in ["completed", "error", "not_found"]:
        st.markdown("---")
        st.markdown("동기화가 진행 중입니다. 잠시만 기다려주세요...")
        time.sleep(2)
        st.rerun()
    else:
        # 완료 상태면 확인 버튼 표시
        st.markdown("---")
        st.markdown("**동기화가 완료되었습니다. 아래 확인 버튼을 클릭해주세요.**")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("확인", key=f"sync_complete_{project_key}", use_container_width=True, type="primary"):
                st.rerun()

def monitor_sync_progress(project_key: str):
    """동기화 진행 상황 실시간 모니터링 (실제 모달)"""
    sync_progress_modal(project_key)

def show_project_statistics():
    """프로젝트 통계"""
    st.subheader("📊 프로젝트 통계")
    
    if 'jira_projects' not in st.session_state:
        st.info("📋 먼저 프로젝트를 조회해주세요.")
        return
    
    projects = st.session_state.jira_projects
    
    if not projects:
        st.info("� 통계를 표시할 프로젝트가 없습니다.")
        return
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    total_projects = len(projects)
    active_projects = len([p for p in projects if p.get('is_active') is True])
    inactive_projects = len([p for p in projects if p.get('is_active') is False])
    unknown_projects = total_projects - active_projects - inactive_projects
    
    with col1:
        st.metric("전체 프로젝트", total_projects)
    
    with col2:
        st.metric("활성 프로젝트", active_projects)
    
    with col3:
        st.metric("비활성 프로젝트", inactive_projects)
    
    with col4:
        st.metric("상태 불명", unknown_projects)
    
    # 이슈 수 통계 (이슈 수가 있는 경우)
    projects_with_issues = [p for p in projects if p.get('issue_count') is not None]
    
    if projects_with_issues:
        st.markdown("### 📈 이슈 수 통계")
        
        # 이슈 수 데이터프레임 생성
        df = pd.DataFrame([
            {
                'project_key': p.get('key', 'N/A'),
                'project_name': p.get('name', 'N/A'),
                'issue_count': p.get('issue_count', 0),
                'is_active': p.get('is_active', None)
            }
            for p in projects_with_issues
        ])
        
        # 이슈 수 상위 10개 프로젝트
        top_projects = df.nlargest(10, 'issue_count')
        
        if not top_projects.empty:
            st.markdown("#### 🔝 이슈 수 상위 10개 프로젝트")
            
            # 차트 표시
            st.bar_chart(
                top_projects.set_index('project_key')['issue_count'],
                height=400
            )
            
            # 테이블 표시
            st.dataframe(
                top_projects[['project_key', 'project_name', 'issue_count']],
                use_container_width=True,
                hide_index=True
            )
        
        # 전체 이슈 수
        total_issues = df['issue_count'].sum()
        avg_issues = df['issue_count'].mean()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("전체 이슈 수", f"{total_issues:,}")
        with col2:
            st.metric("평균 이슈 수", f"{avg_issues:.1f}")

def show_sync_detail_page(project_key: str):
    """동기화 상세 페이지"""
    st.title(f"🔄 {project_key} 프로젝트 동기화")
    
    # 페이지 첫 진입 시 모든 선택 상태 초기화
    if f"sync_detail_initialized_{project_key}" not in st.session_state:
        # 해당 프로젝트의 모든 선택 상태 초기화
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith(f"issue_select_{project_key}_")]
        for key in keys_to_remove:
            del st.session_state[key]
        # 초기화 완료 플래그 설정
        st.session_state[f"sync_detail_initialized_{project_key}"] = True
    
    # 뒤로 가기 버튼 (왼쪽 정렬)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("← 뒤로 가기"):
            st.session_state.sync_detail_project = None
            # 캐시된 이슈 목록도 삭제
            if f"cached_issues_{project_key}" in st.session_state:
                del st.session_state[f"cached_issues_{project_key}"]
            # 초기화 플래그도 삭제
            if f"sync_detail_initialized_{project_key}" in st.session_state:
                del st.session_state[f"sync_detail_initialized_{project_key}"]
            st.rerun()
    
    with col2:
        if st.button("🗑️ 선택 초기화"):
            # 해당 프로젝트의 모든 선택 상태 초기화
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith(f"issue_select_{project_key}_")]
            for key in keys_to_remove:
                del st.session_state[key]
            st.success("✅ 모든 선택이 초기화되었습니다.")
            st.rerun()
    
    st.markdown("---")
    
    # 동기화 상태 확인
    sync_status = get_sync_status(project_key)
    if sync_status:
        status = sync_status.get('status', 'unknown')
        if status in ["starting", "connecting", "fetching_issues", "processing"]:
            st.warning("🔄 현재 동기화가 진행 중입니다. 완료 후 다시 시도해주세요.")
            monitor_sync_progress(project_key)
            return
    
    # 이슈 목록 캐시 확인 (성능 최적화)
    cache_key = f"cached_issues_{project_key}"
    if cache_key not in st.session_state:
        # 이슈 목록 가져오기
        with st.spinner("이슈 목록을 가져오는 중... (최근 1년)"):
            issues_data = get_jira_project_issues(project_key, quick=True)
            
        if not issues_data or not issues_data.get("success"):
            st.error(f"❌ 이슈 목록을 가져올 수 없습니다: {issues_data.get('message', '알 수 없는 오류') if issues_data else '연결 실패'}")
            return
        
        # 이슈 목록 캐시에 저장
        st.session_state[cache_key] = issues_data.get("issues", [])
        st.success(f"✅ {len(st.session_state[cache_key])}개의 이슈를 찾았습니다.")
    else:
        # 캐시된 이슈 목록 사용
        st.info(f"📋 캐시된 이슈 목록 사용 중: {len(st.session_state[cache_key])}개")
    
    issues = st.session_state[cache_key]
    
    if not issues:
        st.info("📋 동기화할 이슈가 없습니다.")
        return
    
    # 이슈 선택 섹션
    st.subheader("📋 동기화할 이슈 선택")
    
    # 현재 선택된 이슈 수 확인
    currently_selected_count = get_current_selection_count(project_key, issues)
    
    # 전체 선택/해제 체크박스
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # 전체 선택 체크박스의 기본값을 현재 상태에 따라 설정
        default_select_all = should_select_all_be_checked(project_key, issues)
        select_all = st.checkbox("전체 선택", value=default_select_all, key=f"select_all_issues_{project_key}")
    
    with col2:
        if st.button("전체 선택", use_container_width=True, key=f"select_all_btn_{project_key}"):
            # 모든 이슈 선택 (한 번에 처리)
            for issue in issues:
                issue_key = issue.get('key', '')
                if issue_key:
                    st.session_state[f"issue_select_{project_key}_{issue_key}"] = True
            st.rerun()
    
    with col3:
        if st.button("선택 해제", use_container_width=True, key=f"deselect_all_btn_{project_key}"):
            # 모든 이슈 선택 해제 (한 번에 처리)
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith(f"issue_select_{project_key}_")]
            for key in keys_to_remove:
                del st.session_state[key]
            st.rerun()
    
    # 전체 선택 체크박스 클릭 시 처리 (최적화)
    previous_select_all = st.session_state.get(f"previous_select_all_{project_key}", False)
    
    if select_all != previous_select_all:
        if select_all:
            # 전체 선택
            for issue in issues:
                issue_key = issue.get('key', '')
                if issue_key:
                    st.session_state[f"issue_select_{project_key}_{issue_key}"] = True
        else:
            # 전체 해제
            keys_to_remove = [key for key in st.session_state.keys() if key.startswith(f"issue_select_{project_key}_")]
            for key in keys_to_remove:
                del st.session_state[key]
        
        # 이전 상태 저장
        st.session_state[f"previous_select_all_{project_key}"] = select_all
        st.rerun()
    
    # 선택 상태 정보 표시
    if currently_selected_count > 0:
        st.info(f"📌 현재 {currently_selected_count}개 이슈가 선택되었습니다.")
    
    # 검색 및 필터링
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 이슈 검색", placeholder="이슈 키, 제목, 상태로 검색...")
    
    with col2:
        issue_types = list(set([issue.get('issue_type', 'Unknown') for issue in issues]))
        selected_type = st.selectbox("이슈 타입 필터", ["전체"] + issue_types)
    
    # 이슈 필터링
    filtered_issues = issues
    if search_term:
        filtered_issues = [
            issue for issue in filtered_issues
            if (search_term.lower() in issue.get('key', '').lower() or
                search_term.lower() in issue.get('summary', '').lower() or
                search_term.lower() in issue.get('status', '').lower())
        ]
    
    if selected_type != "전체":
        filtered_issues = [
            issue for issue in filtered_issues
            if issue.get('issue_type', 'Unknown') == selected_type
        ]
    
    if not filtered_issues:
        st.warning("🔍 검색 조건에 맞는 이슈가 없습니다.")
        return
    
    st.markdown(f"**필터링된 이슈: {len(filtered_issues)}개**")
    
    # 이슈 목록 표시
    display_issue_list(project_key, filtered_issues)
    
    # 동기화 실행 버튼
    st.markdown("---")
    
    # 현재 선택된 이슈 개수를 정확히 계산
    currently_selected_count = get_current_selection_count(project_key, issues)
    
    # 실제 선택된 이슈 키들만 수집
    selected_issues = []
    for issue in issues:
        issue_key = issue.get('key', '')
        if issue_key and st.session_state.get(f"issue_select_{project_key}_{issue_key}", False):
            selected_issues.append(issue_key)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if currently_selected_count > 0 and selected_issues:
            if st.button(
                f"🚀 선택된 {currently_selected_count}개 이슈 동기화",
                type="primary",
                use_container_width=True
            ):
                execute_selective_sync(project_key, selected_issues)
        else:
            st.button(
                "이슈를 선택해주세요",
                disabled=True,
                use_container_width=True
            )

def display_issue_list(project_key: str, issues: List[Dict[str, Any]]):
    """이슈 목록 표시"""
    # 페이지네이션 설정
    items_per_page = 20
    total_pages = (len(issues) + items_per_page - 1) // items_per_page
    
    if total_pages > 1:
        page = st.selectbox("페이지", range(1, total_pages + 1), key="issue_page") - 1
    else:
        page = 0
    
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(issues))
    page_issues = issues[start_idx:end_idx]
    
    # 이슈 카드 표시
    for issue in page_issues:
        issue_key = issue.get('key', '')
        issue_summary = issue.get('summary', 'No Summary')
        issue_status = issue.get('status', 'Unknown')
        issue_type = issue.get('issue_type', 'Unknown')
        issue_priority = issue.get('priority', 'Unknown')
        issue_assignee = issue.get('assignee', 'Unassigned')
        created_date = issue.get('created', '')
        updated_date = issue.get('updated', '')
        
        # 상태별 색상
        status_colors = {
            'To Do': '#6b7280',
            'In Progress': '#f59e0b',
            'Done': '#10b981',
            'Closed': '#6b7280'
        }
        status_color = status_colors.get(issue_status, '#6b7280')
        
        # 우선순위별 아이콘
        priority_icons = {
            'Highest': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Lowest': '🔵'
        }
        priority_icon = priority_icons.get(issue_priority, '⚪')
        
        # 이슈 카드
        with st.container():
            col1, col2 = st.columns([0.5, 9.5])
            
            with col1:
                # 체크박스 - 개별 선택/해제
                checkbox_key = f"issue_select_{project_key}_{issue_key}"
                is_selected = st.checkbox(
                    f"선택: {issue_key}" if issue_key else "선택",
                    key=checkbox_key,
                    label_visibility="collapsed"
                )
            
            with col2:
                # 이슈 정보 (다크 테마)
                st.markdown(f"""
                <div style="
                    border: 1px solid #404040;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 0.5rem;
                    background-color: {'#1e3a5f' if is_selected else '#2b2b2b'};
                    border-left: 4px solid {status_color};
                    color: #e5e7eb;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
                        <h5 style="margin: 0; color: #f3f4f6;">
                            {priority_icon} {issue_key if issue_key else 'NO-KEY'}
                        </h5>
                        <span style="
                            background-color: {status_color};
                            color: white;
                            padding: 0.2rem 0.5rem;
                            border-radius: 4px;
                            font-size: 0.75rem;
                            font-weight: bold;
                        ">{issue_status if issue_status else 'Unknown'}</span>
                    </div>
                    <p style="margin: 0 0 0.5rem 0; color: #d1d5db; font-weight: 500;">
                        {issue_summary if issue_summary and issue_summary != 'No Summary' else '제목 없음'}
                    </p>
                    <div style="display: flex; gap: 1rem; font-size: 0.8rem; color: #9ca3af;">
                        <span>📋 {issue_type if issue_type and issue_type != 'Unknown' else '타입 없음'}</span>
                        <span>� {issue_assignee if issue_assignee and issue_assignee != 'Unassigned' else '미할당'}</span>
                        {f'<span>📅 생성: {created_date[:10] if created_date else "N/A"}</span>' if created_date else ''}
                        {f'<span>🔄 수정: {updated_date[:10] if updated_date else "N/A"}</span>' if updated_date else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # 페이지 정보
    if total_pages > 1:
        st.markdown(f"**페이지 {page + 1} / {total_pages}** (총 {len(issues)}개 이슈)")

def execute_selective_sync(project_key: str, selected_issues: List[str]):
    """선택된 이슈들만 동기화 실행"""
    if not selected_issues:
        st.error("❌ 선택된 이슈가 없습니다.")
        return
    
    # 실제 선택된 이슈 개수 확인 (중복 제거)
    unique_selected_issues = list(set(selected_issues))
    actual_count = len(unique_selected_issues)
    
    try:
        with st.spinner(f"선택된 {actual_count}개 이슈를 동기화하는 중..."):
            # 선택된 이슈만 동기화
            result = sync_jira_project(project_key, unique_selected_issues)
            
            if result and result.get("success"):
                st.success(f"✅ {result.get('message', '동기화를 시작했습니다.')}")
                
                # 실시간 상태 모니터링 (자동 이동 제거)
                monitor_sync_progress(project_key)
                
            else:
                st.error(f"❌ 동기화 시작 실패: {result.get('message', '알 수 없는 오류') if result else '연결 실패'}")
                
    except Exception as e:
        st.error(f"❌ 동기화 중 오류 발생: {str(e)}")
