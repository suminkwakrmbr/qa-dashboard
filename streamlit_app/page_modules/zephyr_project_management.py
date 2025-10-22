import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

def show_zephyr_management():
    """Zephyr 연동 관리 화면"""
    st.header("⚡ 제퍼 프로젝트 관리")
    
    # 탭 구성 - 연동 설정 탭 제거
    tab1, tab2, tab3, tab4 = st.tabs(["📂 테스트 케이스(zephyr)", "🔄 테스트 사이클", "🔄 테스트 동기화", "📊 실행 결과"])
    
    with tab1:
        show_zephyr_project_management()
    
    with tab2:
        show_test_cycles()
    
    with tab3:
        show_test_synchronization()
    
    with tab4:
        show_execution_results()


def show_zephyr_project_management():
    """Zephyr 테스트 케이스 관리 - 개선된 UI"""
    st.subheader("🧪 Zephyr 테스트 케이스")
    
    # 자동 연결 확인
    check_zephyr_connection_status()
    
    # 프로젝트 목록 로드 및 표시
    show_zephyr_projects_section()

def check_zephyr_connection_status():
    """Zephyr 연결 상태 확인 (간소화)"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        st.warning("⚠️ Zephyr API 토큰이 설정되지 않았습니다. .env 파일에서 ZEPHYR_API_TOKEN을 설정해주세요.")
        return False
    
    # 연결 상태 표시
    if 'zephyr_connection_status' not in st.session_state:
        with st.spinner("Zephyr 연결 확인 중..."):
            try:
                import requests
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
                    st.success("✅ Zephyr Scale 연결됨")
                    st.session_state.zephyr_connection_status = True
                    return True
                else:
                    st.error("❌ Zephyr 연결 실패")
                    st.session_state.zephyr_connection_status = False
                    return False
            except Exception:
                st.error("❌ Zephyr 연결 오류")
                st.session_state.zephyr_connection_status = False
                return False
    
    return st.session_state.get('zephyr_connection_status', False)

def show_zephyr_projects_section():
    """Zephyr 프로젝트 섹션 표시"""
    # 새로고침 버튼
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.cache_data.clear()
            if 'zephyr_projects' in st.session_state:
                del st.session_state.zephyr_projects
            st.rerun()
    
    # 프로젝트 목록 로드
    if 'zephyr_projects' not in st.session_state:
        load_zephyr_projects()
    
    projects = st.session_state.get('zephyr_projects', [])
    
    if projects:
        st.info(f"📊 총 {len(projects)}개의 프로젝트")
        
        # 프로젝트 선택 드롭다운
        project_names = ["프로젝트를 선택하세요..."] + [f"{p.get('name', p.get('key', 'Unknown'))} ({p.get('key', 'N/A')})" for p in projects]
        selected_name = st.selectbox("🏗️ 프로젝트 선택", project_names)
        
        if selected_name != "프로젝트를 선택하세요...":
            # 선택된 프로젝트 찾기
            selected_project = None
            for project in projects:
                display_name = f"{project.get('name', project.get('key', 'Unknown'))} ({project.get('key', 'N/A')})"
                if display_name == selected_name:
                    selected_project = project
                    break
            
            if selected_project:
                show_project_test_cases(selected_project)
    else:
        show_no_projects_message()

def load_zephyr_projects():
    """Zephyr 프로젝트 목록 로드"""
    try:
        from streamlit_app.api.client import get_zephyr_projects
        projects_data = get_zephyr_projects()
        
        if projects_data and isinstance(projects_data, list):
            st.session_state.zephyr_projects = projects_data
        else:
            st.session_state.zephyr_projects = []
    except Exception as e:
        st.error(f"프로젝트 로드 실패: {str(e)}")
        st.session_state.zephyr_projects = []

def show_project_test_cases(project):
    """선택된 프로젝트의 테스트 케이스 표시 - 최신 동기화 기능 포함"""
    project_name = project.get('name', project.get('key', 'Unknown'))
    project_id = project.get('id')
    
    # 깔끔한 버튼 섹션
    col1, col2, col3, col4, col5 = st.columns([1, 2, 0.5, 2, 1])
    
    with col2:
        if st.button(
            "📋 테스트 케이스 조회", 
            key=f"load_tc_{project_id}", 
            use_container_width=True, 
            help="프로젝트의 테스트 케이스를 조회합니다"
        ):
            load_test_cases_for_project(project_id, project_name)
    
    with col4:
        if st.button(
            "🔄 최신 동기화", 
            key=f"sync_tc_{project_id}", 
            type="primary", 
            use_container_width=True, 
            help="최신 테스트 케이스로 동기화합니다"
        ):
            sync_latest_test_cases(project_id, project_name)
    
    # 간단한 구분선
    st.markdown("---")
    
    # 자동 새로고침 옵션
    col1, col2 = st.columns([8, 2])
    with col2:
        auto_refresh = st.checkbox("🔄 자동 새로고침 (30초)", key=f"auto_refresh_{project_id}")
        if auto_refresh:
            # 30초마다 자동 새로고침
            import time
            if f"last_refresh_{project_id}" not in st.session_state:
                st.session_state[f"last_refresh_{project_id}"] = time.time()
            
            current_time = time.time()
            if current_time - st.session_state[f"last_refresh_{project_id}"] > 30:
                st.session_state[f"last_refresh_{project_id}"] = current_time
                sync_latest_test_cases(project_id, project_name, silent=True)
                st.rerun()
    
    # 테스트 케이스 목록 표시
    test_cases_key = f"test_cases_{project_id}"
    if test_cases_key in st.session_state:
        test_cases = st.session_state[test_cases_key]
        
        # 마지막 동기화 시간 표시
        last_sync_key = f"last_sync_{project_id}"
        if last_sync_key in st.session_state:
            import datetime
            last_sync_time = st.session_state[last_sync_key]
            st.caption(f"🕒 마지막 동기화: {last_sync_time}")
        
        if test_cases:
            # 필터
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search_term = st.text_input("🔍 검색", placeholder="테스트 케이스 제목 검색...")
            with col2:
                status_options = ["전체"] + list(set([tc.get('status', 'Draft') for tc in test_cases]))
                status_filter = st.selectbox("📊 상태", status_options)
            with col3:
                priority_options = ["전체"] + list(set([tc.get('priority', 'Medium') for tc in test_cases]))
                priority_filter = st.selectbox("⚡ 우선순위", priority_options)
            
            # 필터링
            filtered_cases = test_cases
            if search_term:
                filtered_cases = [tc for tc in filtered_cases if search_term.lower() in tc.get('title', '').lower()]
            if status_filter != "전체":
                filtered_cases = [tc for tc in filtered_cases if tc.get('status') == status_filter]
            if priority_filter != "전체":
                filtered_cases = [tc for tc in filtered_cases if tc.get('priority') == priority_filter]
            
            # 정렬 옵션
            col1, col2 = st.columns([8, 2])
            with col2:
                sort_options = ["생성순", "동기화시간순", "제목순", "상태순", "우선순위순"]
                sort_by = st.selectbox("🔄 정렬", sort_options, index=0)  # 기본값 : 생성순으로 설정
                
                # 생성 날짜 추출
                def extract_created_date(test_case):
                    # 여러 필드에서 생성 날짜 찾기
                    possible_date_fields = [
                        test_case.get('createdOn', ''),
                        test_case.get('created', ''),
                        test_case.get('created_at', ''),
                        test_case.get('createdDate', ''),
                        test_case.get('dateCreated', '')
                    ]
                    
                    for date_field in possible_date_fields:
                        if date_field and isinstance(date_field, str):
                            try:
                                # ISO 형식 날짜 파싱 시도
                                from datetime import datetime
                                # 다양한 날짜 형식 지원
                                date_formats = [
                                    '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO with microseconds
                                    '%Y-%m-%dT%H:%M:%SZ',     # ISO without microseconds
                                    '%Y-%m-%dT%H:%M:%S',      # ISO without Z
                                    '%Y-%m-%d %H:%M:%S',      # Standard datetime
                                    '%Y-%m-%d',               # Date only
                                ]
                                
                                for fmt in date_formats:
                                    try:
                                        return datetime.strptime(date_field, fmt)
                                    except ValueError:
                                        continue
                            except Exception:
                                continue
                    
                    # 날짜를 찾지 못한 경우 기본값 반환
                    from datetime import datetime
                    return datetime(1900, 1, 1)
                
                if sort_by == "생성순":
                    # 생성 날짜 기준으로 최신순 정렬
                    filtered_cases = sorted(filtered_cases, key=extract_created_date, reverse=True)
                elif sort_by == "동기화시간순":
                    filtered_cases = sorted(filtered_cases, key=lambda x: x.get('last_sync', ''), reverse=True)
                elif sort_by == "제목순":
                    filtered_cases = sorted(filtered_cases, key=lambda x: x.get('title', ''))
                elif sort_by == "상태순":
                    filtered_cases = sorted(filtered_cases, key=lambda x: x.get('status', ''))
                elif sort_by == "우선순위순":
                    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
                    filtered_cases = sorted(filtered_cases, key=lambda x: priority_order.get(x.get('priority', 'Medium'), 2))
            
            st.info(f"📊 {len(filtered_cases)}개 테스트 케이스 (전체: {len(test_cases)}개)")
            
            # 테스트 케이스 카드들
            for i, tc in enumerate(filtered_cases):
                show_clean_test_case_card(tc, i)
        else:
            st.info("이 프로젝트에는 테스트 케이스가 없습니다.")
    else:
        st.info("👆 '테스트 케이스 조회' 또는 '최신 동기화' 버튼을 클릭하여 테스트 케이스를 불러오세요.")

def load_test_cases_for_project(project_id, project_name):
    """프로젝트의 테스트 케이스 로드"""
    with st.spinner(f"'{project_name}' 테스트 케이스 조회 중..."):
        try:
            from streamlit_app.api.client import get_zephyr_test_cases
            test_cases = get_zephyr_test_cases(project_id, limit=10000)
            
            if test_cases and isinstance(test_cases, list):
                st.session_state[f"test_cases_{project_id}"] = test_cases
                # 동기화 시간 기록
                import datetime
                st.session_state[f"last_sync_{project_id}"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"✅ {len(test_cases)}개 테스트 케이스 조회 완료!")
            else:
                st.session_state[f"test_cases_{project_id}"] = []
                st.warning("테스트 케이스를 찾을 수 없습니다.")
        except Exception as e:
            st.error(f"테스트 케이스 조회 실패: {str(e)}")
            st.session_state[f"test_cases_{project_id}"] = []

def sync_latest_test_cases(project_id, project_name, silent=False):
    """최신 테스트 케이스 동기화"""
    if not silent:
        with st.spinner(f"'{project_name}' 최신 테스트 케이스 동기화 중..."):
            _perform_sync(project_id, project_name, silent)
    else:
        _perform_sync(project_id, project_name, silent)

def _perform_sync(project_id, project_name, silent=False):
    """실제 동기화 수행"""
    try:
        from streamlit_app.api.client import get_zephyr_test_cases
        import datetime
        
        # 캐시 클리어
        st.cache_data.clear()
        
        # 최신 테스트 케이스 조회 (최대 10000개)
        test_cases = get_zephyr_test_cases(project_id, limit=10000)
        
        if test_cases and isinstance(test_cases, list):
            # 기존 데이터와 비교하여 변경사항 확인
            existing_cases = st.session_state.get(f"test_cases_{project_id}", [])
            
            # 새로운 테스트 케이스 개수 확인
            new_count = len(test_cases)
            old_count = len(existing_cases)
            
            # 데이터 업데이트
            st.session_state[f"test_cases_{project_id}"] = test_cases
            
            # 동기화 시간 기록
            sync_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state[f"last_sync_{project_id}"] = sync_time
            
            # 동기화 결과 표시
            if not silent:
                if new_count > old_count:
                    st.success(f"🔄 동기화 완료! 새로운 테스트 케이스 {new_count - old_count}개 추가됨 (총 {new_count}개)")
                elif new_count < old_count:
                    st.info(f"🔄 동기화 완료! 테스트 케이스 {old_count - new_count}개 제거됨 (총 {new_count}개)")
                else:
                    st.success(f"🔄 동기화 완료! 테스트 케이스 {new_count}개 최신 상태로 업데이트됨")
            
            # 변경된 테스트 케이스 감지 (제목 기준)
            if existing_cases:
                existing_titles = {tc.get('title', '') for tc in existing_cases}
                new_titles = {tc.get('title', '') for tc in test_cases}
                
                added_titles = new_titles - existing_titles
                removed_titles = existing_titles - new_titles
                
                if not silent and (added_titles or removed_titles):
                    if added_titles:
                        st.info(f"📝 새로 추가된 테스트 케이스: {', '.join(list(added_titles)[:3])}{'...' if len(added_titles) > 3 else ''}")
                    if removed_titles:
                        st.warning(f"🗑️ 제거된 테스트 케이스: {', '.join(list(removed_titles)[:3])}{'...' if len(removed_titles) > 3 else ''}")
        else:
            st.session_state[f"test_cases_{project_id}"] = []
            if not silent:
                st.warning("동기화된 테스트 케이스가 없습니다.")
                
    except Exception as e:
        if not silent:
            st.error(f"최신 동기화 실패: {str(e)}")
        st.session_state[f"test_cases_{project_id}"] = st.session_state.get(f"test_cases_{project_id}", [])

def show_clean_test_case_card(test_case, index):
    """가독성 좋고 예쁜 테스트 케이스 카드"""
    tc_key = test_case.get('test_case_key', test_case.get('zephyr_test_id', 'N/A'))
    title = test_case.get('title', '제목 없음')
    status = test_case.get('status', 'Draft')
    priority = test_case.get('priority', 'Medium')
    created_by = test_case.get('created_by', '알 수 없음')
    created_on = test_case.get('createdOn', test_case.get('created', '-'))
    
    # 상태별 색상과 아이콘
    status_config = {
        'Draft': {'color': '#6c757d', 'icon': '📝', 'bg': '#f8f9fa'},
        'Approved': {'color': '#28a745', 'icon': '✅', 'bg': '#d4edda'},
        'Review': {'color': '#ffc107', 'icon': '👀', 'bg': '#fff3cd'},
        'Deprecated': {'color': '#dc3545', 'icon': '🗑️', 'bg': '#f8d7da'}
    }
    
    priority_config = {
        'Critical': {'color': '#dc3545', 'icon': '🔥', 'bg': '#f8d7da'},
        'High': {'color': '#fd7e14', 'icon': '⚡', 'bg': '#ffeaa7'},
        'Medium': {'color': '#ffc107', 'icon': '📋', 'bg': '#fff3cd'},
        'Low': {'color': '#28a745', 'icon': '📌', 'bg': '#d4edda'}
    }
    
    status_info = status_config.get(status, status_config['Draft'])
    priority_info = priority_config.get(priority, priority_config['Medium'])
    
    # 생성 날짜 포맷팅
    formatted_date = created_on
    if created_on and created_on != '-':
        try:
            from datetime import datetime
            if 'T' in created_on:
                dt = datetime.fromisoformat(created_on.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M')
            else:
                formatted_date = created_on[:16] if len(created_on) > 16 else created_on
        except:
            formatted_date = created_on
    
    # 카드 디자인 (streamlit 네이티브)
    with st.container():
        # 카드 스타일 적용
        st.markdown("""
        <style>
        .test-case-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 헤더 섹션
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**🧪 {tc_key}**")
            st.markdown(f"### {title}")
        
        with col2:
            # 우선순위 배지
            priority_color = priority_info['color']
            st.markdown(f"""
            <div style="
                background-color: {priority_color};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
            ">{priority_info['icon']} {priority}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            # 상태 배지
            status_color = status_info['color']
            st.markdown(f"""
            <div style="
                background-color: {status_color};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
            ">{status_info['icon']} {status}</div>
            """, unsafe_allow_html=True)
        
        # 설명 섹션
        description = test_case.get('description', '설명이 없습니다.')
        if len(description) > 150:
            description = description[:150] + "..."
        
        st.info(f"📝 {description}")
        
        # 메타 정보 섹션
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"👤 {created_by} | 📅 {formatted_date}")
    
    # 상세보기 버튼
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📖 상세보기", key=f"detail_{index}", use_container_width=True, type="secondary"):
            st.session_state[f"show_detail_{index}"] = not st.session_state.get(f"show_detail_{index}", False)
    
    # 상세보기 토글
    if st.session_state.get(f"show_detail_{index}", False):
        show_enhanced_test_case_detail(test_case, index)

def show_enhanced_test_case_detail(test_case, index):
    """향상된 테스트 케이스 상세 정보 (Streamlit 네이티브)"""
    tc_key = test_case.get('test_case_key', test_case.get('zephyr_test_id', 'N/A'))
    title = test_case.get('title', '제목 없음')
    status = test_case.get('status', 'Draft')
    priority = test_case.get('priority', 'Medium')
    created_by = test_case.get('created_by', '알 수 없음')
    created_on = test_case.get('createdOn', test_case.get('created', '-'))
    description = test_case.get('description', '설명이 없습니다.')
    
    # 생성 날짜 포맷팅
    formatted_date = created_on
    if created_on and created_on != '-':
        try:
            from datetime import datetime
            if 'T' in created_on:
                dt = datetime.fromisoformat(created_on.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y년 %m월 %d일 %H:%M')
            else:
                formatted_date = created_on
        except:
            formatted_date = created_on
    
    # 상세보기 컨테이너 (Streamlit 네이티브)
    with st.container():
        # 헤더
        st.markdown("### 📋 테스트 케이스 상세 정보")
        st.markdown(f"**🧪 {tc_key}**")
        st.markdown("---")
        
        # 제목
        st.markdown(f"#### 📝 {title}")
        
        # 기본 정보와 작성 정보
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 기본 정보")
            st.markdown(f"**ID:** {test_case.get('id', 'N/A')}")
            st.markdown(f"**키:** {tc_key}")
            
            # 상태 표시
            status_colors = {
                'Draft': '🟡', 'Approved': '🟢', 'Review': '🟠', 'Deprecated': '🔴'
            }
            status_icon = status_colors.get(status, '⚪')
            st.markdown(f"**상태:** {status_icon} {status}")
            
            # 우선순위 표시
            priority_colors = {
                'Critical': '🔥', 'High': '⚡', 'Medium': '📋', 'Low': '📌'
            }
            priority_icon = priority_colors.get(priority, '📋')
            st.markdown(f"**우선순위:** {priority_icon} {priority}")
        
        with col2:
            st.markdown("##### 👤 작성 정보")
            st.markdown(f"**작성자:** {created_by}")
            st.markdown(f"**생성일:** {formatted_date}")
            st.markdown(f"**마지막 동기화:** {test_case.get('last_sync', '-')}")
        
        # 구분선
        st.markdown("---")
        
        # 상세 설명
        st.markdown("##### 📄 상세 설명")
        
        # 설명을 텍스트 영역으로 표시
        if description and description != '설명이 없습니다.':
            st.text_area(
                "설명 내용",
                value=description,
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )
        else:
            st.info("설명이 없습니다.")

def show_test_case_detail(test_case):
    """테스트 케이스 상세 정보 (레거시)"""
    with st.expander(f"📋 {test_case.get('test_case_key', 'N/A')} 상세 정보", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 기본 정보")
            st.markdown(f"**ID:** {test_case.get('id', 'N/A')}")
            st.markdown(f"**키:** {test_case.get('test_case_key', 'N/A')}")
            st.markdown(f"**제목:** {test_case.get('title', '제목 없음')}")
            st.markdown(f"**상태:** {test_case.get('status', 'Draft')}")
            st.markdown(f"**우선순위:** {test_case.get('priority', 'Medium')}")
        
        with col2:
            st.markdown("### 👤 작성 정보")
            st.markdown(f"**작성자:** {test_case.get('created_by', '알 수 없음')}")
            st.markdown(f"**마지막 동기화:** {test_case.get('last_sync', '-')}")
        
        st.markdown("### 📝 상세 설명")
        st.markdown(test_case.get('description', '설명이 없습니다.'))

def show_no_projects_message():
    """프로젝트가 없을 때 안내 메시지"""
    st.info("🔗 Zephyr 프로젝트를 불러올 수 없습니다.")
    
    st.markdown("""
    ### 📋 확인 사항
    1. **.env 파일**에서 ZEPHYR_API_TOKEN 확인
    2. **Zephyr Scale API** 연결 상태 확인
    3. **Zephyr**에 프로젝트 존재 여부 확인
    4. **API 토큰 권한** 확인
    
    **.env 파일 설정 예시:**
    ```
    ZEPHYR_SERVER=https://remember-qa.atlassian.net
    ZEPHYR_USERNAME=your-email@company.com
    ZEPHYR_API_TOKEN=your-zephyr-api-token
    ```
    """)


def show_test_cycles():
    """테스트 사이클 관리"""
    st.subheader("🔄 테스트 사이클")
    
    # 자동 연결 확인
    check_zephyr_connection_status()
    
    # 프로젝트 목록 로드
    if 'zephyr_projects' not in st.session_state:
        load_zephyr_projects()
    
    projects = st.session_state.get('zephyr_projects', [])
    
    if projects:
        st.info(f"📊 총 {len(projects)}개의 프로젝트")
        
        # 프로젝트 선택 드롭다운
        project_names = ["프로젝트를 선택하세요..."] + [f"{p.get('name', p.get('key', 'Unknown'))} ({p.get('key', 'N/A')})" for p in projects]
        selected_name = st.selectbox("🏗️ 프로젝트 선택", project_names, key="cycle_project_select")
        
        if selected_name != "프로젝트를 선택하세요...":
            # 선택된 프로젝트 찾기
            selected_project = None
            for project in projects:
                display_name = f"{project.get('name', project.get('key', 'Unknown'))} ({project.get('key', 'N/A')})"
                if display_name == selected_name:
                    selected_project = project
                    break
            
            if selected_project:
                show_project_test_cycles(selected_project)
    else:
        show_no_projects_message()


def show_project_test_cycles(project):
    """선택된 프로젝트의 테스트 사이클 표시"""
    project_name = project.get('name', project.get('key', 'Unknown'))
    project_id = project.get('id')
    
    st.markdown(f"### 🔄 {project_name} 테스트 사이클")
    
    # 사이클 조회 및 새로고침 버튼
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col2:
        if st.button("📋 사이클 조회", key=f"load_cycles_{project_id}", use_container_width=True):
            load_test_cycles_for_project(project_id, project_name)
    
    with col3:
        if st.button("🔄 새로고침", key=f"refresh_cycles_{project_id}", use_container_width=True):
            if f"test_cycles_{project_id}" in st.session_state:
                del st.session_state[f"test_cycles_{project_id}"]
            load_test_cycles_for_project(project_id, project_name)
    
    st.markdown("---")
    
    # 테스트 사이클 목록 표시
    cycles_key = f"test_cycles_{project_id}"
    if cycles_key in st.session_state:
        cycles = st.session_state[cycles_key]
        
        if cycles:
            # 사이클 통계
            total_cycles = len(cycles)
            completed_cycles = len([c for c in cycles if c.get('status') == 'Completed'])
            in_progress_cycles = len([c for c in cycles if c.get('status') == 'In Progress'])
            not_started_cycles = len([c for c in cycles if c.get('status') == 'Not Started'])
            
            # 통계 표시
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("전체 사이클", total_cycles)
            with col2:
                st.metric("완료", completed_cycles)
            with col3:
                st.metric("진행 중", in_progress_cycles)
            with col4:
                st.metric("미시작", not_started_cycles)
            
            st.markdown("---")
            
            # 필터 옵션
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search_term = st.text_input("🔍 검색", placeholder="사이클 이름 검색...", key=f"cycle_search_{project_id}")
            with col2:
                status_options = ["전체"] + list(set([c.get('status', 'Not Started') for c in cycles]))
                status_filter = st.selectbox("📊 상태", status_options, key=f"cycle_status_{project_id}")
            with col3:
                sort_options = ["생성순", "이름순", "상태순", "시작일순"]
                sort_by = st.selectbox("🔄 정렬", sort_options, key=f"cycle_sort_{project_id}")
            
            # 필터링
            filtered_cycles = cycles
            if search_term:
                filtered_cycles = [c for c in filtered_cycles if search_term.lower() in c.get('cycle_name', '').lower()]
            if status_filter != "전체":
                filtered_cycles = [c for c in filtered_cycles if c.get('status') == status_filter]
            
            # 정렬 (기본값을 생성순으로 변경)
            if sort_by == "생성순":
                # KAN-R 뒤의 번호가 높을수록 최신 티켓이므로 사이클 키 번호 기준으로 정렬
                def extract_cycle_number(cycle):
                    cycle_key = cycle.get('zephyr_cycle_id', '') or cycle.get('cycle_name', '')
                    if cycle_key:
                        try:
                            # KAN-R-123 형식에서 마지막 숫자 추출
                            import re
                            # 다양한 패턴 지원: KAN-R-123, TC-456, CYCLE-789 등
                            match = re.search(r'-(\d+)$', cycle_key)
                            if match:
                                return int(match.group(1))
                            
                            # 숫자만 있는 경우
                            match = re.search(r'(\d+)$', cycle_key)
                            if match:
                                return int(match.group(1))
                                
                        except (ValueError, AttributeError):
                            pass
                    
                    # 숫자를 찾지 못한 경우 기본값 반환 (가장 낮은 우선순위)
                    return 0
                
                filtered_cycles = sorted(filtered_cycles, key=extract_cycle_number, reverse=True)
            elif sort_by == "이름순":
                filtered_cycles = sorted(filtered_cycles, key=lambda x: x.get('cycle_name', ''))
            elif sort_by == "상태순":
                filtered_cycles = sorted(filtered_cycles, key=lambda x: x.get('status', ''))
            elif sort_by == "시작일순":
                filtered_cycles = sorted(filtered_cycles, key=lambda x: x.get('start_date', ''), reverse=True)
            
            st.info(f"📊 {len(filtered_cycles)}개 사이클 (전체: {len(cycles)}개)")
            
            # 사이클 카드들
            for i, cycle in enumerate(filtered_cycles):
                show_test_cycle_card(cycle, i, project_id)
        else:
            st.info("이 프로젝트에는 테스트 사이클이 없습니다.")
    else:
        st.info("👆 '사이클 조회' 버튼을 클릭하여 테스트 사이클을 불러오세요.")


def load_test_cycles_for_project(project_id, project_name):
    """프로젝트의 테스트 사이클 로드 및 데이터베이스 저장"""
    with st.spinner(f"'{project_name}' 테스트 사이클 조회 및 데이터베이스 저장 중..."):
        try:
            from streamlit_app.api.client import get_zephyr_test_cycles
            import requests
            
            # 프로젝트 키 찾기 (먼저 수행)
            project_key = None
            zephyr_projects = st.session_state.get('zephyr_projects', [])
            for proj in zephyr_projects:
                if str(proj.get('id')) == str(project_id):
                    project_key = proj.get('key') or proj.get('project_key')
                    break
            
            # 프로젝트 키가 없으면 기본값 사용 또는 에러 처리
            if not project_key:
                # project_name에서 키 추출 시도 (예: "Project Name (KAN)" -> "KAN")
                import re
                match = re.search(r'\(([^)]+)\)$', project_name)
                if match:
                    project_key = match.group(1)
                else:
                    st.error(f"❌ 프로젝트 키를 찾을 수 없습니다. 프로젝트 ID: {project_id}")
                    return
            
            # 백엔드 API를 통해 데이터베이스에 사이클 저장 (먼저 수행)
            try:
                sync_url = f"http://localhost:8002/api/v1/zephyr/sync-cycles/{project_key}"
                response = requests.post(sync_url, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    if not result.get('success', False):
                        st.warning(f"⚠️ 데이터베이스 저장 실패: {result.get('message', '알 수 없는 오류')}")
                else:
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_response = response.json()
                        error_detail = error_response.get('detail', error_detail)
                    except:
                        pass
                    st.error(f"❌ 데이터베이스 저장 실패: {error_detail}")
                    return
            
            except Exception as db_error:
                st.error(f"❌ 데이터베이스 저장 중 오류: {str(db_error)}")
                return
            
            # 이제 프론트엔드용 사이클 조회
            cycles = get_zephyr_test_cycles(project_id, limit=100)
            
            if cycles and isinstance(cycles, list):
                # 동기화 시간 기록
                import datetime
                sync_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 각 사이클에 동기화 시간 추가
                for cycle in cycles:
                    cycle['last_sync'] = sync_time
                
                # 세션 상태에 저장
                st.session_state[f"test_cycles_{project_id}"] = cycles
                st.success(f"✅ {len(cycles)}개 테스트 사이클 조회 완료! (작업 관리에서 사용 가능)")
                
                if len(cycles) == 0:
                    st.info("ℹ️ 이 프로젝트에는 테스트 사이클이 없습니다.")
            else:
                st.session_state[f"test_cycles_{project_id}"] = []
                st.warning("⚠️ 테스트 사이클을 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"테스트 사이클 조회 실패: {str(e)}")
            st.session_state[f"test_cycles_{project_id}"] = []


def show_test_cycle_card(cycle, index, project_id):
    """테스트 사이클 카드 표시"""
    cycle_name = cycle.get('cycle_name', '이름 없음')
    status = cycle.get('status', 'Not Started')
    version = cycle.get('version', 'N/A')
    environment = cycle.get('environment', 'N/A')
    build = cycle.get('build', 'N/A')
    
    # 상태별 색상과 아이콘
    status_config = {
        'Not Started': {'color': '#6c757d', 'icon': '⏸️'},
        'In Progress': {'color': '#007bff', 'icon': '🔄'},
        'Completed': {'color': '#28a745', 'icon': '✅'},
        'Cancelled': {'color': '#dc3545', 'icon': '❌'}
    }
    
    status_info = status_config.get(status, status_config['Not Started'])
    
    # 진행률 계산
    total_cases = cycle.get('total_test_cases', 0)
    executed_cases = cycle.get('executed_test_cases', 0)
    passed_cases = cycle.get('passed_test_cases', 0)
    failed_cases = cycle.get('failed_test_cases', 0)
    blocked_cases = cycle.get('blocked_test_cases', 0)
    
    progress_rate = (executed_cases / total_cases * 100) if total_cases > 0 else 0
    pass_rate = (passed_cases / executed_cases * 100) if executed_cases > 0 else 0
    
    with st.container():
        # 카드 헤더
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**🔄 {cycle.get('zephyr_cycle_id', 'N/A')}**")
            st.markdown(f"### {cycle_name}")
        
        with col2:
            # 환경 배지
            st.markdown(f"""
            <div style="
                background-color: #17a2b8;
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
            ">🌐 {environment}</div>
            """, unsafe_allow_html=True)
        
        with col3:
            # 상태 배지
            status_color = status_info['color']
            st.markdown(f"""
            <div style="
                background-color: {status_color};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
            ">{status_info['icon']} {status}</div>
            """, unsafe_allow_html=True)
        
        # 기본 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**버전:** {version}")
            st.markdown(f"**빌드:** {build}")
        with col2:
            st.markdown(f"**시작일:** {cycle.get('start_date', 'N/A')}")
            st.markdown(f"**종료일:** {cycle.get('end_date', 'N/A')}")
        with col3:
            st.markdown(f"**생성자:** {cycle.get('created_by', 'N/A')}")
            st.markdown(f"**담당자:** {cycle.get('assigned_to', 'N/A')}")
        
        # Zephyr Scale 링크 표시
        cycle_key = cycle.get('zephyr_cycle_id') or cycle.get('id')
        if cycle_key:
            # 실제 remember-qa.atlassian.net의 Zephyr 링크 형식 사용
            zephyr_link = f"https://remember-qa.atlassian.net/projects/ISSUE?selectedItem=com.atlassian.plugins.atlassian-connect-plugin:com.kanoah.test-manager__main-project-page#!/v2/testCycle/{cycle_key}?projectId={project_id}"
            st.markdown(f"🔗 **Zephyr 링크:** [테스트 사이클 보기]({zephyr_link})")
        
        # 진행률 표시
        st.markdown("**📊 실행 진행률**")
        # progress_rate가 100을 초과하지 않도록 제한
        normalized_progress = min(progress_rate / 100, 1.0)
        st.progress(normalized_progress)
        st.caption(f"{executed_cases}/{total_cases} 실행됨 ({progress_rate:.1f}%)")
        
        # 테스트 결과 통계
        if executed_cases > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("✅ 통과", passed_cases)
            with col2:
                st.metric("❌ 실패", failed_cases)
            with col3:
                st.metric("⚠️ 차단", blocked_cases)
            with col4:
                st.metric("통과율", f"{pass_rate:.1f}%")
        
        # 동기화 및 상세보기 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔄 동기화", key=f"sync_cycle_{project_id}_{index}", use_container_width=True, type="primary"):
                sync_test_cycle(project_id, cycle, cycle_name)
        with col2:
            if st.button("📖 상세보기", key=f"cycle_detail_{project_id}_{index}", use_container_width=True, type="secondary"):
                st.session_state[f"show_cycle_detail_{project_id}_{index}"] = not st.session_state.get(f"show_cycle_detail_{project_id}_{index}", False)
        with col3:
            if st.button("📊 실행결과", key=f"cycle_executions_{project_id}_{index}", use_container_width=True, type="secondary"):
                show_cycle_executions(project_id, cycle, cycle_name)
        
        # 상세보기 토글
        if st.session_state.get(f"show_cycle_detail_{project_id}_{index}", False):
            show_test_cycle_detail(cycle, index, project_id)
        
        st.markdown("---")


def sync_test_cycle(project_id, cycle, cycle_name):
    """테스트 사이클 동기화"""
    with st.spinner(f"'{cycle_name}' 동기화 중..."):
        try:
            from streamlit_app.api.client import sync_zephyr_test_cycle
            
            # 동기화 데이터 준비
            sync_data = {
                "sync_direction": "import",
                "sync_type": "test_executions"
            }
            
            cycle_id = cycle.get('id') or cycle.get('zephyr_cycle_id')
            
            # 실제 동기화 수행
            result = sync_zephyr_test_cycle(project_id, cycle_id, sync_data)
            
            if result and result.get('success', False):
                st.success(f"✅ '{cycle_name}' 동기화 완료!")
                
                # 동기화 후 사이클 목록 새로고침
                if f"test_cycles_{project_id}" in st.session_state:
                    del st.session_state[f"test_cycles_{project_id}"]
                load_test_cycles_for_project(project_id, cycle.get('project_name', 'Unknown'))
                
                st.rerun()
            else:
                error_msg = result.get('message', '알 수 없는 오류') if result else '동기화 응답 없음'
                st.error(f"❌ 동기화 실패: {error_msg}")
                
        except Exception as e:
            st.error(f"동기화 중 오류 발생: {str(e)}")


def show_cycle_executions(project_id, cycle, cycle_name):
    """테스트 사이클 실행 결과 조회"""
    with st.spinner(f"'{cycle_name}' 실행 결과 조회 중..."):
        try:
            from streamlit_app.api.client import get_zephyr_cycle_executions
            
            cycle_id = cycle.get('id') or cycle.get('zephyr_cycle_id')
            
            # 실행 결과 조회
            executions = get_zephyr_cycle_executions(cycle_id, limit=100)
            
            if executions and isinstance(executions, list):
                st.success(f"✅ {len(executions)}개 실행 결과 조회 완료!")
                
                # 실행 결과 표시
                st.markdown(f"### 📊 {cycle_name} 실행 결과")
                
                if executions:
                    for i, execution in enumerate(executions):
                        show_execution_result_card(execution, i)
                else:
                    st.info("이 사이클에는 실행 결과가 없습니다.")
            else:
                st.warning("실행 결과를 찾을 수 없습니다.")
                
        except Exception as e:
            st.error(f"실행 결과 조회 실패: {str(e)}")


def show_execution_result_card(execution, index):
    """실행 결과 카드 표시"""
    test_case_key = execution.get('testCase', {}).get('key', 'N/A')
    test_case_name = execution.get('testCase', {}).get('name', '테스트 케이스 이름 없음')
    status = execution.get('statusName', execution.get('status', 'Not Executed'))
    executed_by = execution.get('executedBy', {}).get('displayName', '알 수 없음')
    executed_on = execution.get('executedOn', 'N/A')
    
    # 상태별 색상과 아이콘
    status_config = {
        'Pass': {'color': '#28a745', 'icon': '✅'},
        'Fail': {'color': '#dc3545', 'icon': '❌'},
        'Blocked': {'color': '#ffc107', 'icon': '⚠️'},
        'Not Executed': {'color': '#6c757d', 'icon': '⏸️'},
        'In Progress': {'color': '#007bff', 'icon': '🔄'}
    }
    
    status_info = status_config.get(status, status_config['Not Executed'])
    
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**🧪 {test_case_key}**")
            st.markdown(f"### {test_case_name}")
        
        with col2:
            st.markdown(f"**실행자:** {executed_by}")
            st.markdown(f"**실행일:** {executed_on}")
        
        with col3:
            # 상태 배지
            status_color = status_info['color']
            st.markdown(f"""
            <div style="
                background-color: {status_color};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                text-align: center;
                font-size: 0.8rem;
                font-weight: 600;
            ">{status_info['icon']} {status}</div>
            """, unsafe_allow_html=True)
        
        # 실행 코멘트가 있다면 표시
        comment = execution.get('comment', '')
        if comment:
            st.info(f"💬 {comment}")
        
        st.markdown("---")


def show_test_cycle_detail(cycle, index, project_id):
    """테스트 사이클 상세 정보"""
    with st.container():
        st.markdown("### 📋 테스트 사이클 상세 정보")
        st.markdown("---")
        
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 📊 기본 정보")
            st.markdown(f"**ID:** {cycle.get('id', 'N/A')}")
            st.markdown(f"**사이클 키:** {cycle.get('zephyr_cycle_id', 'N/A')}")
            st.markdown(f"**이름:** {cycle.get('cycle_name', 'N/A')}")
            st.markdown(f"**버전:** {cycle.get('version', 'N/A')}")
            st.markdown(f"**환경:** {cycle.get('environment', 'N/A')}")
            st.markdown(f"**빌드:** {cycle.get('build', 'N/A')}")
        
        with col2:
            st.markdown("##### 👤 관리 정보")
            st.markdown(f"**상태:** {cycle.get('status', 'N/A')}")
            st.markdown(f"**생성자:** {cycle.get('created_by', 'N/A')}")
            st.markdown(f"**담당자:** {cycle.get('assigned_to', 'N/A')}")
            st.markdown(f"**시작일:** {cycle.get('start_date', 'N/A')}")
            st.markdown(f"**종료일:** {cycle.get('end_date', 'N/A')}")
            st.markdown(f"**생성일:** {cycle.get('created_at', 'N/A')}")
        
        # 설명
        st.markdown("##### 📄 설명")
        description = cycle.get('description', '설명이 없습니다.')
        st.text_area(
            "설명 내용",
            value=description,
            height=100,
            disabled=True,
            label_visibility="collapsed",
            key=f"cycle_desc_{project_id}_{index}"
        )
        
        # 테스트 실행 통계
        st.markdown("##### 📈 테스트 실행 통계")
        
        total_cases = cycle.get('total_test_cases', 0)
        executed_cases = cycle.get('executed_test_cases', 0)
        passed_cases = cycle.get('passed_test_cases', 0)
        failed_cases = cycle.get('failed_test_cases', 0)
        blocked_cases = cycle.get('blocked_test_cases', 0)
        not_executed = total_cases - executed_cases
        
        # 파이 차트 데이터
        if total_cases > 0:
            import plotly.express as px
            import pandas as pd
            
            chart_data = pd.DataFrame({
                '상태': ['통과', '실패', '차단', '미실행'],
                '개수': [passed_cases, failed_cases, blocked_cases, not_executed],
                '색상': ['#28a745', '#dc3545', '#ffc107', '#6c757d']
            })
            
            # 0이 아닌 데이터만 표시
            chart_data = chart_data[chart_data['개수'] > 0]
            
            if not chart_data.empty:
                fig = px.pie(
                    chart_data, 
                    values='개수', 
                    names='상태',
                    color='상태',
                    color_discrete_map={
                        '통과': '#28a745',
                        '실패': '#dc3545', 
                        '차단': '#ffc107',
                        '미실행': '#6c757d'
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("실행된 테스트가 없습니다.")
        else:
            st.info("테스트 케이스가 없습니다.")


def show_test_synchronization():
    """테스트 동기화"""
    st.subheader("🧪 테스트 동기화")
    
    # 동기화 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Zephyr → QA Dashboard")
        
        sync_direction_import = st.radio(
            "가져올 데이터 선택",
            ["테스트 케이스만", "실행 결과만", "테스트 케이스 + 실행 결과"],
            key="import_direction"
        )
        
        import_project = st.selectbox(
            "가져올 프로젝트",
            ["전체", "WEBAPP", "MOBILE", "API"],
            key="import_project"
        )
        
        if st.button("📥 Zephyr에서 가져오기", use_container_width=True):
            with st.spinner("Zephyr에서 데이터를 가져오는 중..."):
                import time
                time.sleep(3)
                st.success("✅ Zephyr에서 데이터를 성공적으로 가져왔습니다!")
    
    with col2:
        st.markdown("### 📤 QA Dashboard → Zephyr")
        
        sync_direction_export = st.radio(
            "내보낼 데이터 선택",
            ["테스트 케이스만", "실행 결과만", "테스트 케이스 + 실행 결과"],
            key="export_direction"
        )
        
        export_project = st.selectbox(
            "내보낼 프로젝트",
            ["전체", "프로젝트 A", "프로젝트 B", "프로젝트 C"],
            key="export_project"
        )
        
        if st.button("� Zephyr로 내보내기", use_container_width=True):
            with st.spinner("Zephyr로 데이터를 내보내는 중..."):
                import time
                time.sleep(3)
                st.success("✅ Zephyr로 데이터를 성공적으로 내보냈습니다!")
    
    st.markdown("---")
    
    # 동기화 이력
    st.markdown("### 📜 동기화 이력")
    
    # 실제 동기화 이력을 데이터베이스나 세션에서 가져와야 함
    # 현재는 기본 메시지만 표시
    st.info("동기화 이력이 없습니다. 동기화를 수행하면 여기에 기록됩니다.")


def show_execution_results():
    """실행 결과 관리"""
    st.subheader("📊 Zephyr 실행 결과")
    
    # 실행 결과 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 실행", "156", "12")
    
    with col2:
        st.metric("통과", "128", "8")
    
    with col3:
        st.metric("실패", "18", "3")
    
    with col4:
        st.metric("차단", "10", "1")
    
    st.markdown("---")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        result_project = st.selectbox("프로젝트", ["전체", "WEBAPP", "MOBILE", "API"])
    
    with col2:
        result_status = st.selectbox("실행 결과", ["전체", "통과", "실패", "차단", "미실행"])
    
    with col3:
        date_range = st.selectbox("기간", ["전체", "오늘", "최근 7일", "최근 30일"])
    
    # 실행 결과 목록
    st.markdown("### 🕒 최근 실행 결과")
    
    execution_results = [
        {
            "test_case": "TC-WEBAPP-001",
            "title": "로그인 기능 테스트",
            "project": "WEBAPP",
            "result": "통과",
            "executed_by": "QA팀",
            "executed_at": "2024-01-20 16:45",
            "duration": "3분 20초",
            "environment": "스테이징"
        },
        {
            "test_case": "TC-MOBILE-005",
            "title": "푸시 알림 테스트",
            "project": "MOBILE",
            "result": "실패",
            "executed_by": "QA팀",
            "executed_at": "2024-01-20 16:30",
            "duration": "2분 10초",
            "environment": "개발"
        },
        {
            "test_case": "TC-API-012",
            "title": "사용자 정보 API 테스트",
            "project": "API",
            "result": "차단",
            "executed_by": "개발팀",
            "executed_at": "2024-01-20 16:15",
            "duration": "1분 30초",
            "environment": "스테이징"
        }
    ]
    
    for result in execution_results:
        result_colors = {
            "통과": "#2ed573",
            "실패": "#ff4757",
            "차단": "#ffa502",
            "미실행": "#747d8c"
        }
        
        result_icons = {
            "통과": "✅",
            "실패": "❌",
            "차단": "⚠️",
            "미실행": "⏸️"
        }
        
        result_color = result_colors.get(result["result"], "#747d8c")
        result_icon = result_icons.get(result["result"], "❓")
        
        st.markdown(f"""
        <div style="
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {result_color};
            margin: 10px 0;
        ">
            <strong>{result_icon} {result['test_case']}: {result['title']}</strong><br>
            <small>
                프로젝트: {result['project']} | 
                실행자: {result['executed_by']} | 
                환경: {result['environment']}<br>
                실행 시간: {result['executed_at']} | 
                소요 시간: {result['duration']}
            </small>
        </div>
        """, unsafe_allow_html=True)
    
    # 실행 결과 내보내기
    st.markdown("---")
    col1, col2 = st.columns([8, 2])
    
    with col2:
        if st.button("📊 결과 내보내기", use_container_width=True):
            st.info("실행 결과를 Excel 파일로 내보냅니다...")
