"""
테스트 케이스 관리 페이지
"""

import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

def show_test_case_management():
    """테스트 케이스 관리 화면"""
    st.header("🧪 테스트 케이스 관리")
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📋 테스트 케이스 목록", "➕ 테스트 케이스 생성", "📊 실행 결과"])
    
    with tab1:
        show_test_case_list()
    
    with tab2:
        show_test_case_creation()
    
    with tab3:
        show_test_execution_results()


def show_test_case_list():
    """테스트 케이스 목록 표시"""
    st.subheader("📋 테스트 케이스 목록")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        project_filter = st.selectbox(
            "프로젝트 필터",
            ["전체", "프로젝트 A", "프로젝트 B"],
            key="tc_project_filter"
        )
    
    with col2:
        status_filter = st.selectbox(
            "상태 필터",
            ["전체", "작성중", "검토중", "승인됨", "실행중", "완료"],
            key="tc_status_filter"
        )
    
    with col3:
        priority_filter = st.selectbox(
            "우선순위 필터",
            ["전체", "높음", "보통", "낮음"],
            key="tc_priority_filter"
        )
    
    # 검색
    search_term = st.text_input("🔍 테스트 케이스 검색", placeholder="제목, 설명, 태그로 검색...")
    
    # 새로고침 버튼
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()
    
    # 테스트 케이스 목록 (임시 데이터)
    st.markdown("---")
    
    # 임시 테스트 케이스 데이터
    test_cases = [
        {
            "id": "TC-001",
            "title": "로그인 기능 테스트",
            "description": "사용자 로그인 기능의 정상 동작을 확인",
            "project": "프로젝트 A",
            "status": "승인됨",
            "priority": "높음",
            "created_by": "QA팀",
            "created_at": "2024-01-15",
            "last_executed": "2024-01-20",
            "execution_result": "통과"
        },
        {
            "id": "TC-002",
            "title": "회원가입 유효성 검사",
            "description": "회원가입 시 입력값 유효성 검사 테스트",
            "project": "프로젝트 A",
            "status": "검토중",
            "priority": "보통",
            "created_by": "QA팀",
            "created_at": "2024-01-16",
            "last_executed": "-",
            "execution_result": "-"
        }
    ]
    
    if test_cases:
        st.info(f"📊 총 {len(test_cases)}개의 테스트 케이스")
        
        for i, tc in enumerate(test_cases):
            show_test_case_card(tc, i)
    else:
        st.info("테스트 케이스가 없습니다. 새로운 테스트 케이스를 생성해주세요.")


def show_test_case_card(test_case, index):
    """테스트 케이스 카드 표시"""
    tc_id = test_case.get('id', 'N/A')
    title = test_case.get('title', 'N/A')
    description = test_case.get('description', '설명이 없습니다.')
    project = test_case.get('project', 'N/A')
    status = test_case.get('status', '알 수 없음')
    priority = test_case.get('priority', '보통')
    created_by = test_case.get('created_by', 'N/A')
    created_at = test_case.get('created_at', 'N/A')
    last_executed = test_case.get('last_executed', '-')
    execution_result = test_case.get('execution_result', '-')
    
    # 상태별 색상
    status_colors = {
        '작성중': '#ffa502',
        '검토중': '#3742fa',
        '승인됨': '#2ed573',
        '실행중': '#ff7f50',
        '완료': '#747d8c'
    }
    
    # 우선순위별 색상
    priority_colors = {
        '높음': '#ff4757',
        '보통': '#ffa502',
        '낮음': '#2ed573'
    }
    
    status_color = status_colors.get(status, '#747d8c')
    priority_color = priority_colors.get(priority, '#ffa502')
    
    # 카드 스타일링
    with st.container():
        st.markdown(f"""
        <div style="
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid {priority_color};
            border: 2px solid #555555;
            margin: 20px 0;
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
        ">
        """, unsafe_allow_html=True)
        
        # 첫 번째 행: 기본 정보
        col1, col2, col3 = st.columns([4, 1, 1])
        
        with col1:
            st.markdown(f"## 🧪 {tc_id}: {title}")
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background-color: #404040; color: #ffffff; border-radius: 15px; margin: 5px; border: 1px solid {priority_color};">
                <strong>🔥 {priority}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 8px; background-color: #404040; color: #ffffff; border-radius: 15px; margin: 5px; border: 1px solid {status_color};">
                <strong>📊 {status}</strong>
            </div>
            """, unsafe_allow_html=True)
        
        # 두 번째 행: 메타 정보
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.info(f"📂 **프로젝트:** {project}")
        
        with col2:
            st.info(f"👤 **작성자:** {created_by}")
        
        with col3:
            st.info(f"📅 **생성일:** {created_at}")
        
        with col4:
            st.info(f"🏃 **마지막 실행:** {last_executed}")
        
        # 세 번째 행: 설명
        st.markdown("**📝 테스트 케이스 설명**")
        st.markdown(f"""
        <div style="
            background-color: #404040;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid {priority_color};
            margin: 10px 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        ">
        {description}
        </div>
        """, unsafe_allow_html=True)
        
        # 네 번째 행: 실행 결과 (있는 경우)
        if execution_result != '-':
            result_color = '#2ed573' if execution_result == '통과' else '#ff4757'
            st.markdown(f"""
            <div style="
                background-color: {result_color};
                color: #ffffff;
                padding: 10px;
                border-radius: 8px;
                margin: 10px 0;
                text-align: center;
                font-weight: bold;
            ">
            🎯 마지막 실행 결과: {execution_result}
            </div>
            """, unsafe_allow_html=True)
        
        # 다섯 번째 행: 액션 버튼
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✏️ 편집", key=f"edit_tc_{index}"):
                st.info("테스트 케이스 편집 기능 (구현 예정)")
        
        with col2:
            if st.button("▶️ 실행", key=f"execute_tc_{index}"):
                st.info("테스트 케이스 실행 기능 (구현 예정)")
        
        with col3:
            if st.button("📋 복사", key=f"copy_tc_{index}"):
                st.info("테스트 케이스 복사 기능 (구현 예정)")
        
        with col4:
            if st.button("🗑️ 삭제", key=f"delete_tc_{index}", type="secondary"):
                st.warning("테스트 케이스 삭제 기능 (구현 예정)")
        
        st.markdown("</div>", unsafe_allow_html=True)


def show_test_case_creation():
    """테스트 케이스 생성 폼"""
    st.subheader("➕ 새 테스트 케이스 생성")
    
    with st.form("test_case_form"):
        # 기본 정보
        col1, col2 = st.columns(2)
        
        with col1:
            tc_title = st.text_input("테스트 케이스 제목 *", placeholder="예: 로그인 기능 테스트")
            tc_project = st.selectbox("프로젝트 *", ["프로젝트 A", "프로젝트 B", "프로젝트 C"])
            tc_priority = st.selectbox("우선순위", ["높음", "보통", "낮음"], index=1)
        
        with col2:
            tc_category = st.selectbox("카테고리", ["기능 테스트", "UI 테스트", "API 테스트", "성능 테스트", "보안 테스트"])
            tc_tags = st.text_input("태그", placeholder="쉼표로 구분 (예: 로그인, 인증, 보안)")
            tc_estimated_time = st.number_input("예상 소요시간 (분)", min_value=1, value=30)
        
        # 테스트 케이스 상세
        st.markdown("### 📋 테스트 케이스 상세")
        
        tc_description = st.text_area(
            "테스트 목적 및 설명 *",
            placeholder="이 테스트 케이스의 목적과 검증하고자 하는 내용을 설명해주세요.",
            height=100
        )
        
        tc_preconditions = st.text_area(
            "사전 조건",
            placeholder="테스트 실행 전 필요한 조건들을 나열해주세요.",
            height=80
        )
        
        tc_steps = st.text_area(
            "테스트 단계 *",
            placeholder="1. 로그인 페이지로 이동\n2. 유효한 사용자명과 비밀번호 입력\n3. 로그인 버튼 클릭\n4. 결과 확인",
            height=150
        )
        
        tc_expected_result = st.text_area(
            "예상 결과 *",
            placeholder="테스트 성공 시 예상되는 결과를 설명해주세요.",
            height=100
        )
        
        # 추가 정보
        col1, col2 = st.columns(2)
        
        with col1:
            tc_test_data = st.text_area("테스트 데이터", placeholder="테스트에 필요한 데이터가 있다면 기입해주세요.", height=80)
        
        with col2:
            tc_notes = st.text_area("참고사항", placeholder="추가적인 참고사항이나 주의사항", height=80)
        
        # 제출 버튼
        submitted = st.form_submit_button("🧪 테스트 케이스 생성", use_container_width=True)
        
        if submitted:
            if tc_title and tc_description and tc_steps and tc_expected_result:
                st.success("✅ 테스트 케이스가 생성되었습니다!")
                st.info("실제 구현에서는 데이터베이스에 저장됩니다.")
                
                # 생성된 테스트 케이스 미리보기
                with st.expander("📋 생성된 테스트 케이스 미리보기"):
                    st.markdown(f"**제목:** {tc_title}")
                    st.markdown(f"**프로젝트:** {tc_project}")
                    st.markdown(f"**우선순위:** {tc_priority}")
                    st.markdown(f"**카테고리:** {tc_category}")
                    st.markdown(f"**설명:** {tc_description}")
                    st.markdown(f"**테스트 단계:**\n{tc_steps}")
                    st.markdown(f"**예상 결과:** {tc_expected_result}")
            else:
                st.error("❌ 필수 항목을 모두 입력해주세요.")


def show_test_execution_results():
    """테스트 실행 결과 표시"""
    st.subheader("📊 테스트 실행 결과")
    
    # 실행 결과 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 테스트 케이스", "25", "2")
    
    with col2:
        st.metric("통과", "20", "1")
    
    with col3:
        st.metric("실패", "3", "-1")
    
    with col4:
        st.metric("미실행", "2", "0")
    
    # 실행 결과 차트 (임시)
    st.markdown("---")
    st.markdown("### 📈 실행 결과 추이")
    st.info("차트 기능은 구현 예정입니다.")
    
    # 최근 실행 결과
    st.markdown("### 🕒 최근 실행 결과")
    
    recent_results = [
        {"tc_id": "TC-001", "title": "로그인 기능 테스트", "result": "통과", "executed_at": "2024-01-20 14:30", "duration": "2분 30초"},
        {"tc_id": "TC-003", "title": "비밀번호 변경 테스트", "result": "실패", "executed_at": "2024-01-20 14:25", "duration": "1분 45초"},
        {"tc_id": "TC-005", "title": "프로필 업데이트 테스트", "result": "통과", "executed_at": "2024-01-20 14:20", "duration": "3분 10초"}
    ]
    
    for result in recent_results:
        result_color = "#2ed573" if result["result"] == "통과" else "#ff4757"
        result_icon = "✅" if result["result"] == "통과" else "❌"
        
        st.markdown(f"""
        <div style="
            background-color: #2d2d2d;
            color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid {result_color};
            margin: 10px 0;
        ">
            <strong>{result_icon} {result['tc_id']}: {result['title']}</strong><br>
            <small>실행 시간: {result['executed_at']} | 소요 시간: {result['duration']}</small>
        </div>
        """, unsafe_allow_html=True)
