"""
QA 요청서 페이지
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import sys
import os
import json

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from streamlit_app.api.client import get_tasks, get_projects
from streamlit_app.utils.helpers import format_datetime

# QA 요청서 데이터 파일 경로
QA_REQUESTS_FILE = os.path.join(project_root, "qa_requests.json")

def load_qa_requests():
    """QA 요청서 데이터를 파일에서 로드"""
    try:
        if os.path.exists(QA_REQUESTS_FILE):
            with open(QA_REQUESTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        st.error(f"QA 요청서 데이터 로드 중 오류: {str(e)}")
        return []

def save_qa_requests(qa_requests):
    """QA 요청서 데이터를 파일에 저장"""
    try:
        with open(QA_REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(qa_requests, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"QA 요청서 데이터 저장 중 오류: {str(e)}")
        return False

def get_next_qa_id():
    """다음 QA 요청서 ID 생성"""
    qa_requests = load_qa_requests()
    if not qa_requests:
        return 1
    return max([req.get('id', 0) for req in qa_requests]) + 1

def show_qa_request():
    """QA 요청서 페이지 표시"""
    st.title("📋 QA 요청서 상세")
    
    # 세션 상태 초기화
    if 'qa_current_view' not in st.session_state:
        st.session_state.qa_current_view = 'list'  # 기본값을 목록으로 설정
    if 'qa_selected_request_id' not in st.session_state:
        st.session_state.qa_selected_request_id = None
    
    # 상세 페이지가 아닌 경우에만 상단 네비게이션 버튼 표시
    if st.session_state.qa_current_view != 'detail':
        # 상단 네비게이션 버튼
        col1, col2, col3, col4 = st.columns([2, 2, 2, 6])
        
        with col1:
            if st.button("📋 요청서 목록", use_container_width=True, 
                        type="primary" if st.session_state.qa_current_view == 'list' else "secondary"):
                st.session_state.qa_current_view = 'list'
                st.session_state.qa_selected_request_id = None
                st.rerun()
        
        with col2:
            if st.button("📝 새 요청서", use_container_width=True,
                        type="primary" if st.session_state.qa_current_view == 'create' else "secondary"):
                st.session_state.qa_current_view = 'create'
                st.session_state.qa_selected_request_id = None
                st.rerun()
        
        with col3:
            if st.button("📊 통계", use_container_width=True,
                        type="primary" if st.session_state.qa_current_view == 'stats' else "secondary"):
                st.session_state.qa_current_view = 'stats'
                st.session_state.qa_selected_request_id = None
                st.rerun()
        
        st.markdown("---")
    
    # 현재 뷰에 따라 페이지 표시
    if st.session_state.qa_current_view == 'list':
        show_qa_request_list()
    elif st.session_state.qa_current_view == 'create':
        show_create_qa_request()
    elif st.session_state.qa_current_view == 'detail':
        show_qa_request_detail()
    elif st.session_state.qa_current_view == 'stats':
        show_qa_request_stats()

def show_create_qa_request():
    """새 QA 요청서 작성"""
    st.subheader("📝 새 QA 요청서 작성")
    
    with st.form("qa_request_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # 기본 정보
            st.markdown("### 기본 정보")
            
            # 요청자 정보
            requester_info = st.text_input(
                "요청자/소속 *",
                placeholder="홍길동 / QA팀",
                key="qa_requester_info"
            )
            
            # 요청 제목
            request_title = st.text_input(
                "요청 제목 *",
                placeholder="예: 로그인 기능 QA 요청",
                key="qa_request_title"
            )
            
            # 우선순위
            priority = st.selectbox(
                "우선순위 *",
                options=["낮음", "보통", "높음", "긴급"],
                index=1,
                key="qa_priority"
            )
        
        with col2:
            # 일정 정보
            st.markdown("### 일정 정보")
            
            # 요청 날짜 (자동)
            request_date = st.date_input(
                "요청 날짜",
                value=date.today(),
                disabled=True,
                key="qa_request_date"
            )
            
            # 희망 완료 날짜
            desired_completion_date = st.date_input(
                "희망 완료 날짜 *",
                min_value=date.today(),
                key="qa_desired_completion"
            )
            
            # QA 유형
            qa_type = st.multiselect(
                "QA 유형 *",
                options=[
                    "기능 테스트",
                    "UI/UX 테스트",
                    "성능 테스트",
                    "보안 테스트",
                    "호환성 테스트",
                    "회귀 테스트",
                    "사용성 테스트",
                    "기타"
                ],
                default=["기능 테스트"],
                key="qa_type"
            )
            
            # QA 담당자
            qa_assignee = st.selectbox(
                "QA 담당자",
                options=["없음", "곽수민", "양희찬", "박한샘", "고강호", "조병찬"],
                index=0,
                key="qa_assignee",
                help="QA를 담당할 팀원을 선택해주세요"
            )
        
        # 상세 정보
        st.markdown("### 상세 정보")
        
        # 요청 내용
        request_description = st.text_area(
            "요청 내용 *",
            placeholder="QA를 요청하는 기능이나 변경사항에 대해 자세히 설명해주세요.",
            height=150,
            key="qa_description"
        )
        
        # 테스트 범위
        test_scope = st.text_area(
            "테스트 범위",
            placeholder="테스트해야 할 구체적인 범위나 기능을 명시해주세요.",
            height=100,
            key="qa_test_scope"
        )
        
        # 예상 이슈
        expected_issues = st.text_area(
            "예상 이슈 또는 주의사항",
            placeholder="테스트 중 발생할 수 있는 이슈나 특별히 주의해야 할 사항이 있다면 기재해주세요.",
            height=100,
            key="qa_expected_issues"
        )
        
        # 관련 작업
        st.markdown("### 관련 작업")
        
        # 기획/디자인 문서 링크 (고정 3개 필드)
        st.markdown("**기획/디자인 문서**")
        
        # 문서 링크 필드들 (고정 3개)
        document_links = []
        
        for i in range(3):
            # 문서 링크
            doc_link = st.text_input(
                f"문서 링크 {i+1}",
                placeholder="예: https://www.figma.com/design/..., https://docs.google.com/...",
                key=f"doc_link_{i}",
                help="Figma, Google Docs, Notion 등의 문서 링크를 입력해주세요."
            )
            document_links.append(doc_link)
        
        # 관련 작업 선택 (에러 처리 개선)
        try:
            tasks_response = get_tasks()
            
            # API 응답 처리
            tasks = []
            if tasks_response:
                if isinstance(tasks_response, dict) and 'tasks' in tasks_response:
                    tasks = tasks_response['tasks']
                elif isinstance(tasks_response, list):
                    tasks = tasks_response
                else:
                    st.warning(f"예상하지 못한 작업 응답 형식: {type(tasks_response)}")
                    tasks = []
            
            if tasks and isinstance(tasks, list):
                try:
                    task_options = [
                        f"{task.get('jira_key', task.get('id', 'Unknown'))} - {task.get('title', task.get('summary', 'Unknown'))[:50]}" 
                        for task in tasks 
                        if isinstance(task, dict)
                    ]
                    related_tasks = st.multiselect(
                        "관련 작업",
                        options=task_options,
                        key="qa_related_tasks"
                    )
                except Exception as e:
                    st.warning(f"작업 옵션 생성 중 오류: {str(e)}")
                    related_tasks = []
            else:
                related_tasks = []
                
        except Exception as e:
            st.warning(f"작업 목록을 불러오는 중 오류: {str(e)}")
            related_tasks = []
        
        # 첨부 파일
        st.markdown("### 첨부 파일")
        uploaded_files = st.file_uploader(
            "관련 문서나 스크린샷을 첨부해주세요",
            accept_multiple_files=True,
            type=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx', 'txt'],
            key="qa_attachments"
        )
        
        # 제출 버튼
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button(
                "📋 QA 요청서 제출",
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            # 필수 필드 검증
            errors = []
            if not requester_info.strip():
                errors.append("요청자/소속을 입력해주세요.")
            if not request_title.strip():
                errors.append("요청 제목을 입력해주세요.")
            if not qa_type:
                errors.append("QA 유형을 선택해주세요.")
            if not request_description.strip():
                errors.append("요청 내용을 입력해주세요.")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # 문서 링크 정보 수집 (고정 3개)
                document_links_data = []
                for i in range(3):
                    doc_link = st.session_state.get(f"doc_link_{i}", "")
                    if doc_link.strip():
                        document_links_data.append(doc_link.strip())
                
                # QA 요청서 데이터 생성
                qa_request_data = {
                    "id": get_next_qa_id(),
                    "requester_info": requester_info,
                    "title": request_title,
                    "priority": priority,
                    "request_date": request_date.isoformat(),
                    "desired_completion_date": desired_completion_date.isoformat(),
                    "qa_type": qa_type,
                    "qa_assignee": qa_assignee if qa_assignee != "없음" else None,
                    "description": request_description,
                    "test_scope": test_scope,
                    "expected_issues": expected_issues,
                    "document_links": document_links_data,
                    "related_tasks": related_tasks,
                    "status": "대기",
                    "created_at": datetime.now().isoformat()
                }
                
                # 파일에 저장
                qa_requests = load_qa_requests()
                qa_requests.append(qa_request_data)
                
                if save_qa_requests(qa_requests):
                    st.success("✅ QA 요청서가 성공적으로 제출되었습니다!")
                    st.info(f"요청서 ID: QA-{qa_request_data['id']:04d}")
                    
                    # 2초 후 목록으로 이동
                    import time
                    time.sleep(2)
                    
                    # 목록 페이지로 이동
                    st.session_state.qa_current_view = 'list'
                    st.rerun()
                else:
                    st.error("❌ QA 요청서 저장 중 오류가 발생했습니다.")
    

def show_qa_request_list():
    """QA 요청서 목록"""
    st.subheader("📋 QA 요청서 목록")
    
    # 파일에서 요청서 목록 가져오기
    qa_requests = load_qa_requests()
    
    if not qa_requests:
        st.info("등록된 QA 요청서가 없습니다.")
        return
    
    # 필터 옵션
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 상태 필터
        status_options = ["전체"] + list(set([req.get('status', '대기') for req in qa_requests]))
        selected_status = st.selectbox(
            "상태",
            options=status_options,
            key="qa_list_status_filter"
        )
    
    with col2:
        # 우선순위 필터
        priority_options = ["전체"] + list(set([req.get('priority', '보통') for req in qa_requests]))
        selected_priority = st.selectbox(
            "우선순위",
            options=priority_options,
            key="qa_list_priority_filter"
        )
    
    with col3:
        # QA 유형 필터
        qa_type_options = ["전체"]
        for req in qa_requests:
            for qa_type in req.get('qa_type', []):
                if qa_type not in qa_type_options:
                    qa_type_options.append(qa_type)
        selected_qa_type = st.selectbox(
            "QA 유형",
            options=qa_type_options,
            key="qa_list_qa_type_filter"
        )
    
    with col4:
        # 요청자 필터
        requester_options = ["전체"] + list(set([req.get('requester_info', '') for req in qa_requests]))
        selected_requester = st.selectbox(
            "요청자",
            options=requester_options,
            key="qa_list_requester_filter"
        )
    
    # 필터 적용
    filtered_requests = qa_requests
    if selected_status != "전체":
        filtered_requests = [req for req in filtered_requests if req.get('status') == selected_status]
    if selected_priority != "전체":
        filtered_requests = [req for req in filtered_requests if req.get('priority') == selected_priority]
    if selected_qa_type != "전체":
        filtered_requests = [req for req in filtered_requests if selected_qa_type in req.get('qa_type', [])]
    if selected_requester != "전체":
        filtered_requests = [req for req in filtered_requests if req.get('requester_info') == selected_requester]
    
    # 최신순 정렬 (ID 기준 내림차순)
    filtered_requests = sorted(filtered_requests, key=lambda x: x.get('id', 0), reverse=True)
    
    if filtered_requests:
        st.subheader(f"📋 요청서 목록 ({len(filtered_requests)}개)")
        
        # 테이블 헤더 (통합된 디자인)
        st.markdown("""
        <style>
        .qa-table-header {
            background: linear-gradient(90deg, #4a5568, #2d3748);
            padding: 16px;
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
            border: 1px solid #4a5568;
            display: flex;
            align-items: center;
        }
        .qa-table-row {
            background: linear-gradient(90deg, #2d3748, #1a202c);
            padding: 14px 16px;
            border-left: 1px solid #4a5568;
            border-right: 1px solid #4a5568;
            border-bottom: 1px solid #4a5568;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
        }
        .qa-table-row:hover {
            background: linear-gradient(90deg, #374151, #1f2937);
            border-color: #6b7280;
        }
        .qa-table-row:last-child {
            border-radius: 0 0 8px 8px;
        }
        .qa-id-link {
            color: #667eea;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
        }
        .qa-id-link:hover {
            color: #5a67d8;
            text-decoration: underline;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 헤더 행 (QA담당자 컬럼 추가) - 컬럼 비율 정확히 맞춤
        header_html = """
        <div class="qa-table-header">
            <div style="flex: 0.8; color: #e2e8f0; font-weight: 600; text-align: center;">ID</div>
            <div style="flex: 2.5; color: #e2e8f0; font-weight: 600; text-align: left; padding-left: 8px;">제목</div>
            <div style="flex: 1; color: #e2e8f0; font-weight: 600; text-align: center;">상태</div>
            <div style="flex: 1; color: #e2e8f0; font-weight: 600; text-align: center;">우선순위</div>
            <div style="flex: 1; color: #e2e8f0; font-weight: 600; text-align: center;">요청자</div>
            <div style="flex: 1; color: #e2e8f0; font-weight: 600; text-align: center;">QA담당자</div>
            <div style="flex: 1.2; color: #e2e8f0; font-weight: 600; text-align: center;">요청일</div>
            <div style="flex: 0.8; color: #e2e8f0; font-weight: 600; text-align: center;">상세보기</div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
        
        # 요청서 목록을 헤더 정렬에 맞춰 카드로 표시
        for i, req in enumerate(filtered_requests):
            # 요청자 이름만 추출 (소속 제거)
            requester_name = req.get('requester_info', 'N/A')
            if ' / ' in requester_name:
                requester_name = requester_name.split(' / ')[0]
            
            # QA 유형 요약
            qa_types = req.get('qa_type', [])
            qa_type_display = qa_types[0] if qa_types else 'N/A'
            if len(qa_types) > 1:
                qa_type_display += f" +{len(qa_types)-1}"
            
            # 상태 및 우선순위
            status = req.get('status', '대기')
            priority = req.get('priority', '보통')
            
            # 제목 길이 제한
            title_display = req['title'][:40] + '...' if len(req['title']) > 40 else req['title']
            
            # 요청자 이름 길이 제한
            requester_display = requester_name[:10] + '...' if len(requester_name) > 10 else requester_name
            
            # QA 유형 길이 제한
            qa_type_short = qa_type_display[:12] + '...' if len(qa_type_display) > 12 else qa_type_display
            
            # 상태별 색상 및 이모지
            status_display = ""
            if status == "완료":
                status_display = '<span style="color: #28a745; font-size: 0.9rem;">✅ 완료</span>'
            elif status == "진행중":
                status_display = '<span style="color: #007bff; font-size: 0.9rem;">🔄 진행중</span>'
            elif status == "보류":
                status_display = '<span style="color: #ffc107; font-size: 0.9rem;">⏸️ 보류</span>'
            elif status == "취소":
                status_display = '<span style="color: #dc3545; font-size: 0.9rem;">❌ 취소</span>'
            else:
                status_display = '<span style="color: #6c757d; font-size: 0.9rem;">⏳ 대기</span>'
            
            # 우선순위별 색상 및 이모지
            priority_display = ""
            if priority == "긴급":
                priority_display = '<span style="color: #dc3545; font-size: 1.1rem;">🔴</span> <span style="color: #e2e8f0; font-size: 0.9rem;">긴급</span>'
            elif priority == "높음":
                priority_display = '<span style="color: #ffc107; font-size: 1.1rem;">🟡</span> <span style="color: #e2e8f0; font-size: 0.9rem;">높음</span>'
            elif priority == "보통":
                priority_display = '<span style="color: #007bff; font-size: 1.1rem;">🔵</span> <span style="color: #e2e8f0; font-size: 0.9rem;">보통</span>'
            else:
                priority_display = '<span style="color: #28a745; font-size: 1.1rem;">🟢</span> <span style="color: #e2e8f0; font-size: 0.9rem;">낮음</span>'
            
            # 마지막 행인지 확인
            is_last_row = (i == len(filtered_requests) - 1)
            
            # QA담당자 정보 처리
            qa_assignee = req.get('qa_assignee', None)
            qa_assignee_display = qa_assignee if qa_assignee else '미지정'
            
            # 헤더에 맞춘 카드 (QA담당자 컬럼 추가)
            row_cols = st.columns([0.8, 2.5, 1, 1, 1, 1, 1.2, 0.8])
            
            with row_cols[0]:
                # ID 표시 (중앙 정렬)
                st.markdown(f'<div style="padding: 12px 8px; color: #667eea; font-weight: bold; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">QA-{req["id"]:04d}</div>', unsafe_allow_html=True)
            
            with row_cols[1]:
                # 제목 표시 (왼쪽 정렬, 헤더와 일치 - 패딩 추가)
                st.markdown(f'<div style="padding: 12px 8px; padding-left: 15px; color: #e2e8f0; font-size: 0.95rem; display: flex; align-items: center; height: 100%;">{title_display}</div>', unsafe_allow_html=True)
            
            with row_cols[2]:
                # 상태 표시 (중앙 정렬)
                st.markdown(f'<div style="padding: 12px 8px; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">{status_display}</div>', unsafe_allow_html=True)
            
            with row_cols[3]:
                # 우선순위 표시 (중앙 정렬)
                st.markdown(f'<div style="padding: 12px 8px; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">{priority_display}</div>', unsafe_allow_html=True)
            
            with row_cols[4]:
                # 요청자 정보 표시 (중앙 정렬)
                st.markdown(f'<div style="padding: 12px 8px; color: #cbd5e0; font-size: 0.9rem; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">{requester_display}</div>', unsafe_allow_html=True)
            
            with row_cols[5]:
                # QA담당자 표시 (중앙 정렬)
                qa_color = '#10b981' if qa_assignee else '#6c757d'
                st.markdown(f'<div style="padding: 12px 8px; color: {qa_color}; font-size: 0.9rem; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">{qa_assignee_display}</div>', unsafe_allow_html=True)
            
            with row_cols[6]:
                # 요청일 표시 (중앙 정렬)
                st.markdown(f'<div style="padding: 12px 8px; color: #a0aec0; font-size: 0.9rem; text-align: center; display: flex; align-items: center; justify-content: center; height: 100%;">{req["request_date"]}</div>', unsafe_allow_html=True)
            
            with row_cols[7]:
                # 상세보기 버튼 (Streamlit 네이티브 버튼만 사용)
                if st.button("👁️ 보기", key=f"detail_btn_{req['id']}", 
                           type="primary", use_container_width=True,
                           help=f"QA-{req['id']:04d} 상세보기"):
                    st.session_state.qa_selected_request_id = req['id']
                    st.session_state.qa_current_view = 'detail'
                    st.rerun()
            
            # 행 구분선
            st.markdown('<div style="border-bottom: 1px solid #4a5568; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)
    
    else:
        st.info("필터 조건에 맞는 요청서가 없습니다.")

def show_qa_request_stats():
    """QA 요청서 통계"""
    st.subheader("📊 QA 요청서 통계")
    
    qa_requests = load_qa_requests()
    
    if not qa_requests:
        st.info("통계를 표시할 데이터가 없습니다.")
        return
    
    # 전체 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_requests = len(qa_requests)
        st.metric("전체 요청서", total_requests)
    
    with col2:
        completed_requests = len([req for req in qa_requests if req.get('status') == '완료'])
        st.metric("완료된 요청서", completed_requests)
    
    with col3:
        in_progress_requests = len([req for req in qa_requests if req.get('status') == '진행중'])
        st.metric("진행중인 요청서", in_progress_requests)
    
    with col4:
        pending_requests = len([req for req in qa_requests if req.get('status') == '대기'])
        st.metric("대기중인 요청서", pending_requests)
    
    # 상태별 분포
    st.markdown("### 상태별 분포")
    status_counts = {}
    for req in qa_requests:
        status = req.get('status', '대기')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    if status_counts:
        status_df = pd.DataFrame(list(status_counts.items()), columns=['상태', '개수'])
        st.bar_chart(status_df.set_index('상태'))
    
    # 우선순위별 분포
    st.markdown("### 우선순위별 분포")
    priority_counts = {}
    for req in qa_requests:
        priority = req.get('priority', '보통')
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
    
    if priority_counts:
        priority_df = pd.DataFrame(list(priority_counts.items()), columns=['우선순위', '개수'])
        st.bar_chart(priority_df.set_index('우선순위'))
    
    # QA 유형별 분포
    st.markdown("### QA 유형별 분포")
    qa_type_counts = {}
    for req in qa_requests:
        for qa_type in req.get('qa_type', []):
            qa_type_counts[qa_type] = qa_type_counts.get(qa_type, 0) + 1
    
    if qa_type_counts:
        qa_type_df = pd.DataFrame(list(qa_type_counts.items()), columns=['QA 유형', '개수'])
        st.bar_chart(qa_type_df.set_index('QA 유형'))

def get_qa_request_status_color(status):
    """QA 요청서 상태에 따른 색상 반환"""
    colors = {
        "대기": "#6c757d",      # 회색
        "진행중": "#007bff",    # 파란색
        "완료": "#28a745",      # 초록색
        "보류": "#ffc107",      # 노란색
        "취소": "#dc3545"       # 빨간색
    }
    return colors.get(status, "#6c757d")

def show_qa_request_detail():
    """QA 요청서 상세 페이지"""
    if not st.session_state.qa_selected_request_id:
        st.error("선택된 요청서가 없습니다.")
        return
    
    # 요청서 상세 페이지에서 사이드바 완전 제거
    st.markdown("""
    <style>
    /* 사이드바 완전 숨김 */
    .css-1d391kg, .css-1lcbmhc, .css-1y4p8pa, [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* 메인 콘텐츠 전체 너비 사용 */
    .main .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    qa_requests = load_qa_requests()
    selected_request = None
    
    for req in qa_requests:
        if req['id'] == st.session_state.qa_selected_request_id:
            selected_request = req
            break
    
    if not selected_request:
        st.error("요청서를 찾을 수 없습니다.")
        return
    
    # 상단 네비게이션 - 축소된 버튼
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    
    with nav_col1:
        if st.button("← 뒤로가기", type="secondary"):
            st.session_state.qa_current_view = 'list'
            st.session_state.qa_selected_request_id = None
            st.rerun()
    
    st.markdown("---")
    
    # 상태별 색상 정의
    status_colors = {
        "대기": "#6c757d",      # 회색
        "진행중": "#007bff",    # 파란색
        "완료": "#28a745",      # 초록색
        "보류": "#ffc107",      # 노란색
        "취소": "#dc3545"       # 빨간색
    }
    
    # 우선순위별 색상 정의
    priority_colors = {
        "낮음": "#28a745",      # 초록색
        "보통": "#007bff",      # 파란색
        "높음": "#ffc107",      # 노란색
        "긴급": "#dc3545"       # 빨간색
    }
    
    status = selected_request.get('status', '대기')
    priority = selected_request.get('priority', '보통')
    status_color = status_colors.get(status, "#6c757d")
    priority_color = priority_colors.get(priority, "#007bff")
    
    # 헤더 섹션 - 축소된 크기
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%); 
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; 
                box-shadow: 0 4px 16px rgba(0,0,0,0.2); border: 1px solid #4a5568;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 1rem;">
                <span style="color: #667eea; font-size: 1.8rem; font-weight: 700;">QA-{selected_request['id']:04d}</span>
                <span style="color: #e2e8f0; font-size: 1.2rem; font-weight: 500;">{selected_request['title']}</span>
            </div>
            <div style="display: flex; gap: 0.8rem;">
                <span style="background: {status_color}; color: white; padding: 0.4rem 0.8rem; border-radius: 16px; font-size: 0.85rem; font-weight: 500;">
                    {status}
                </span>
                <span style="background: {priority_color}; color: white; padding: 0.4rem 0.8rem; border-radius: 16px; font-size: 0.85rem; font-weight: 500;">
                    {priority}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 기본 정보 섹션과 관리 기능을 나란히 배치
    info_col, mgmt_col = st.columns([3, 1])
    
    with info_col:
        st.markdown("### 📋 기본 정보")
        
        # QA담당자 정보 처리
        qa_assignee = selected_request.get('qa_assignee', None)
        qa_assignee_display = qa_assignee if qa_assignee else '미지정'
        qa_assignee_color = '#10b981' if qa_assignee else '#6c757d'
        
        # 기본 정보를 보더가 있는 컨테이너로 감싸기 (QA담당자 추가)
        st.markdown(f"""
        <div style="background: #374151; padding: 1.5rem; border-radius: 8px; border: 1px solid #4a5568; margin-bottom: 1rem;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                <div style="padding: 1rem; background: #2d3748; border-radius: 6px; border-left: 3px solid #667eea;">
                    <p style="color: #9ca3af; margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">요청자/소속</p>
                    <p style="color: #e2e8f0; margin: 0; font-size: 1rem; font-weight: 500;">{selected_request.get('requester_info', 'N/A')}</p>
                </div>
                <div style="padding: 1rem; background: #2d3748; border-radius: 6px; border-left: 3px solid #10b981;">
                    <p style="color: #9ca3af; margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">QA 담당자</p>
                    <p style="color: {qa_assignee_color}; margin: 0; font-size: 1rem; font-weight: 500;">{qa_assignee_display}</p>
                </div>
                <div style="padding: 1rem; background: #2d3748; border-radius: 6px; border-left: 3px solid #f59e0b;">
                    <p style="color: #9ca3af; margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">요청일</p>
                    <p style="color: #e2e8f0; margin: 0; font-size: 1rem; font-weight: 500;">{selected_request['request_date']}</p>
                </div>
                <div style="padding: 1rem; background: #2d3748; border-radius: 6px; border-left: 3px solid #8b5cf6;">
                    <p style="color: #9ca3af; margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">희망 완료일</p>
                    <p style="color: #e2e8f0; margin: 0; font-size: 1rem; font-weight: 500;">{selected_request['desired_completion_date']}</p>
                </div>
            </div>
            <div style="margin-top: 1.5rem;">
                <div style="padding: 1rem; background: #2d3748; border-radius: 6px; border-left: 3px solid #ef4444;">
                    <p style="color: #9ca3af; margin: 0 0 0.5rem 0; font-size: 0.9rem; font-weight: 600;">QA 유형</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        {''.join([f'<span style="background: #667eea; color: white; padding: 0.3rem 0.6rem; border-radius: 12px; font-size: 0.8rem;">{qa_type}</span>' for qa_type in selected_request.get('qa_type', [])])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with mgmt_col:
        st.markdown("### ⚙️ 관리")
        
        # 상태 변경
        status = selected_request.get('status', '대기')
        new_status = st.selectbox(
            "상태 변경",
            options=["대기", "진행중", "완료", "보류", "취소"],
            index=["대기", "진행중", "완료", "보류", "취소"].index(status),
            key=f"detail_status_change_{selected_request['id']}"
        )
        
        if new_status != status:
            if st.button("✅ 상태 변경", type="primary", use_container_width=True):
                # 파일에서 데이터 로드하여 상태 업데이트
                qa_requests = load_qa_requests()
                for i, r in enumerate(qa_requests):
                    if r['id'] == selected_request['id']:
                        qa_requests[i]['status'] = new_status
                        break
                
                # 파일에 저장
                if save_qa_requests(qa_requests):
                    st.success(f"✅ 상태가 '{new_status}'로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 상태 변경 중 오류가 발생했습니다.")
        
        # QA담당자 변경
        st.markdown("---")
        current_assignee = selected_request.get('qa_assignee', None)
        assignee_options = ["없음", "곽수민", "양희찬", "박한샘", "고강호", "조병찬"]
        current_index = 0
        if current_assignee and current_assignee in assignee_options:
            current_index = assignee_options.index(current_assignee)
        
        new_assignee = st.selectbox(
            "QA담당자 변경",
            options=assignee_options,
            index=current_index,
            key=f"detail_assignee_change_{selected_request['id']}"
        )
        
        # 담당자가 변경된 경우
        new_assignee_value = new_assignee if new_assignee != "없음" else None
        if new_assignee_value != current_assignee:
            if st.button("👤 담당자 변경", type="secondary", use_container_width=True):
                # 파일에서 데이터 로드하여 담당자 업데이트
                qa_requests = load_qa_requests()
                for i, r in enumerate(qa_requests):
                    if r['id'] == selected_request['id']:
                        qa_requests[i]['qa_assignee'] = new_assignee_value
                        break
                
                # 파일에 저장
                if save_qa_requests(qa_requests):
                    assignee_display = new_assignee if new_assignee != "없음" else "미지정"
                    st.success(f"✅ QA담당자가 '{assignee_display}'로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ QA담당자 변경 중 오류가 발생했습니다.")
        
        # 우선순위 변경
        st.markdown("---")
        current_priority = selected_request.get('priority', '보통')
        new_priority = st.selectbox(
            "우선순위 변경",
            options=["낮음", "보통", "높음", "긴급"],
            index=["낮음", "보통", "높음", "긴급"].index(current_priority),
            key=f"detail_priority_change_{selected_request['id']}"
        )
        
        if new_priority != current_priority:
            if st.button("🔄 우선순위 변경", type="secondary", use_container_width=True):
                # 파일에서 데이터 로드하여 우선순위 업데이트
                qa_requests = load_qa_requests()
                for i, r in enumerate(qa_requests):
                    if r['id'] == selected_request['id']:
                        qa_requests[i]['priority'] = new_priority
                        break
                
                # 파일에 저장
                if save_qa_requests(qa_requests):
                    st.success(f"✅ 우선순위가 '{new_priority}'로 변경되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 우선순위 변경 중 오류가 발생했습니다.")
        
    
    # 요청 내용 섹션
    st.markdown("### 📝 요청 내용")
    st.markdown(f"""
    <div style="background: #374151; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #667eea;">
        <p style="color: #e2e8f0; margin: 0; line-height: 1.7; font-size: 1rem;">{selected_request['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 테스트 범위 (있는 경우)
    if selected_request.get('test_scope'):
        st.markdown("### 🎯 테스트 범위")
        st.markdown(f"""
        <div style="background: #374151; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #10b981;">
            <p style="color: #e2e8f0; margin: 0; line-height: 1.7; font-size: 1rem;">{selected_request['test_scope']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 예상 이슈 (있는 경우)
    if selected_request.get('expected_issues'):
        st.markdown("### ⚠️ 예상 이슈 및 주의사항")
        st.markdown(f"""
        <div style="background: #374151; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ef4444;">
            <p style="color: #e2e8f0; margin: 0; line-height: 1.7; font-size: 1rem;">{selected_request['expected_issues']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 관련 자료 (있는 경우)
    if selected_request.get('document_links') or selected_request.get('related_tasks'):
        st.markdown("### 🔗 관련 자료")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if selected_request.get('document_links'):
                st.write("**📎 문서 링크**")
                for i, link in enumerate(selected_request.get('document_links', [])):
                    st.markdown(f"[🔗 문서 링크 {i+1}]({link})")
        
        with col2:
            if selected_request.get('related_tasks'):
                st.write("**🔗 관련 작업**")
                for task in selected_request.get('related_tasks', []):
                    # 티켓 키 추출 (예: "RB-6357 - [메시지] ..." -> "RB-6357")
                    if ' - ' in task:
                        ticket_key = task.split(' - ')[0].strip()
                        task_description = task.split(' - ', 1)[1].strip()
                        
                        # JIRA 링크 생성 (기본 JIRA URL 사용)
                        jira_url = f"https://dramancompany.atlassian.net/browse/{ticket_key}"
                        st.markdown(f"• [{ticket_key}]({jira_url}) - {task_description}")
                    else:
                        # 티켓 키가 명확하지 않은 경우 그대로 표시
                        st.write(f"• {task}")
    
    # 화면 하단 삭제 기능
    st.markdown("---")
    st.markdown("### 🗑️ 요청서 삭제")
    
    delete_col1, delete_col2 = st.columns([1, 5])
    
    with delete_col1:
        if st.button("🗑️ 삭제", type="secondary", use_container_width=True):
            st.session_state.show_delete_modal = True
    
    # Streamlit 네이티브 다이얼로그 모달 사용
    if st.session_state.get('show_delete_modal', False):
        show_delete_confirmation_dialog(selected_request)

@st.dialog("요청서 삭제")
def show_delete_confirmation_dialog(selected_request):
    """삭제 확인 다이얼로그"""
    
    # 모달 내용
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem;">
        <div style="color: #e2e8f0; margin-bottom: 1.5rem; line-height: 1.8; font-size: 1.1rem;">
            <strong>QA-{selected_request['id']:04d}</strong> 요청서를 삭제하시겠습니까?
        </div>
        <div style="color: #fbbf24; font-size: 1rem; line-height: 1.7; margin-bottom: 2rem;">
            이 작업은 되돌릴 수 없습니다.<br>
            삭제하려면 비밀번호 <strong style="color: #667eea; font-size: 1.1rem;">qa2025</strong>를 입력하세요.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 비밀번호 입력
    password = st.text_input(
        "비밀번호",
        type="password",
        placeholder="qa2025",
        key="dialog_password_input",
        label_visibility="collapsed",
        help="삭제하려면 qa2025를 입력하세요"
    )
    
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    
    # 버튼들
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ 삭제", type="primary", use_container_width=True, key="dialog_confirm_delete"):
            if password == "qa2025":
                # 요청서 삭제
                qa_requests = load_qa_requests()
                qa_requests = [req for req in qa_requests if req['id'] != selected_request['id']]
                
                if save_qa_requests(qa_requests):
                    # 한줄 성공 메시지
                    st.markdown('<div style="text-align: center; color: #28a745; font-weight: 600; margin-top: 1rem;">✅ 요청서가 삭제되었습니다!</div>', unsafe_allow_html=True)
                    # 상태 초기화 및 목록으로 이동
                    st.session_state.qa_current_view = 'list'
                    st.session_state.qa_selected_request_id = None
                    st.session_state.show_delete_modal = False
                    st.rerun()
                else:
                    # 한줄 오류 메시지
                    st.markdown('<div style="text-align: center; color: #dc3545; font-weight: 600; margin-top: 1rem;">❌ 삭제 중 오류가 발생했습니다.</div>', unsafe_allow_html=True)
            else:
                # 한줄 오류 메시지
                st.markdown('<div style="text-align: center; color: #dc3545; font-weight: 600; margin-top: 1rem;">❌ 비밀번호가 올바르지 않습니다.</div>', unsafe_allow_html=True)
    
    with col2:
        if st.button("❌ 취소", use_container_width=True, key="dialog_cancel_delete"):
            st.session_state.show_delete_modal = False
            st.rerun()

def get_qa_request_status_color(status):
    """QA 요청서 상태에 따른 색상 반환"""
    colors = {
        "대기": "#6c757d",      # 회색
        "진행중": "#007bff",    # 파란색
        "완료": "#28a745",      # 초록색
        "보류": "#ffc107",      # 노란색
        "취소": "#dc3545"       # 빨간색
    }
    return colors.get(status, "#6c757d")

def get_qa_request_priority_color(priority):
    """QA 요청서 우선순위에 따른 색상 반환"""
    colors = {
        "낮음": "#28a745",      # 초록색
        "보통": "#007bff",      # 파란색
        "높음": "#ffc107",      # 노란색
        "긴급": "#dc3545"       # 빨간색
    }
    return colors.get(priority, "#007bff")
