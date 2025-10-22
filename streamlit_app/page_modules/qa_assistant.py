"""
QA AI 어시스턴트 페이지 모듈 - 채팅 형식
"""
import streamlit as st
import requests
import json
from datetime import datetime
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

logger = logging.getLogger(__name__)

def show_qa_assistant():
    """QA AI 어시스턴트 페이지 - 채팅 형식"""
    
    st.title("💬 QA AI 어시스턴트")
    
    # API Key 확인
    custom_api_key = os.getenv('CUSTOM_GPT_API_KEY', '')
    if not custom_api_key:
        st.error("❌ API 키가 설정되지 않았습니다.")
        return
    
    # 대화 히스토리 초기화
    if "qa_chat_history" not in st.session_state:
        st.session_state.qa_chat_history = []
    
    # 메시지 전송 후 초기화를 위한 플래그
    if "message_sent" not in st.session_state:
        st.session_state.message_sent = False
    
    # 채팅 영역 - 텍스트 길이에 맞는 말풍선 UI
    if st.session_state.qa_chat_history:
        st.subheader("💬 대화 내용 (테스트 케이스 고안하기, QA 관련 업무 질문 등)")
        
        # 채팅 히스토리 표시
        for i, chat in enumerate(st.session_state.qa_chat_history):
            # 사용자 메시지
            col1, col2, col3 = st.columns([1, 1, 2])
            with col3:
                st.markdown(f"<div style='text-align: right; font-size: 0.8rem; color: #666; margin-bottom: 5px;'>👤 사용자 ({chat['timestamp']})</div>", unsafe_allow_html=True)
                
                # 첨부 파일이 있으면 먼저 표시
                if chat.get('attachments'):
                    for attachment in chat['attachments']:
                        if attachment['type'] == 'image':
                            st.markdown(f"""
                            <div style='text-align: right; margin-bottom: 10px;'>
                                <div style='display: inline-block; max-width: 80%;'>
                                    <img src="data:image/png;base64,{attachment['data']}" 
                                         style="max-width: 200px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" 
                                         alt="{attachment['name']}">
                                    <div style='font-size: 0.7rem; color: #666; text-align: right; margin-top: 2px;'>
                                        {attachment['name']}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                # 사용자 메시지 표시
                import html
                escaped_user_message = html.escape(chat['user_message']).replace('\n', '<br>')
                st.markdown(f"""
                <div style='text-align: right;'>
                    <div style='background: #007bff; color: white; padding: 8px 12px; 
                               border-radius: 15px 15px 5px 15px; 
                               display: inline-block; max-width: 80%; text-align: left; margin-bottom: 10px;'>
                        {escaped_user_message}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # AI 응답
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown("<div style='font-size: 0.8rem; color: #666; margin-bottom: 5px;'>🤖 AI 어시스턴트</div>", unsafe_allow_html=True)
                
                # AI 응답 표시
                import html
                escaped_ai_response = html.escape(chat['ai_response']).replace('\n', '<br>')
                st.markdown(f"""
                <div style='text-align: left;'>
                    <div style='background: #f0f0f0; color: #333; padding: 8px 12px; 
                               border-radius: 15px 15px 15px 5px; 
                               display: inline-block; max-width: 80%; text-align: left; margin-bottom: 15px;'>
                        {escaped_ai_response}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 구분선
            if i < len(st.session_state.qa_chat_history) - 1:
                st.divider()
    else:
        # 빈 채팅 상태
        st.info("💬 QA AI 어시스턴트에게 질문해보세요! 테스트 케이스 작성, 버그 분석 등 QA 관련 도움을 받을 수 있습니다.")
    
    # 입력 영역
    st.markdown("---")
    
    # 파일 업로드 - 전송 후 초기화를 위해 동적 키 사용
    file_key = f"file_upload_{len(st.session_state.qa_chat_history)}"
    uploaded_files = st.file_uploader(
        "📎 이미지 첨부",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=file_key
    )
    
    # 메시지 입력 - 전송 후 초기화를 위해 동적 키 사용
    message_key = f"message_input_{len(st.session_state.qa_chat_history)}"
    
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_question = st.text_area(
            "메시지 입력",
            placeholder="메시지를 입력하세요...",
            height=60,
            label_visibility="collapsed",
            key=message_key
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 정렬을 위한 여백
        send_button = st.button(
            "🚀 전송",
            disabled=not bool(user_question and user_question.strip()),
            key=f"send_btn_{len(st.session_state.qa_chat_history)}",
            type="primary",
            help="메시지를 전송합니다"
        )
    
    # 대화 삭제 버튼 (작게)
    if st.session_state.qa_chat_history:
        if st.button("🗑️ 대화 삭제", key="clear_chat", help="모든 대화 내용을 삭제합니다"):
            st.session_state.qa_chat_history = []
            st.rerun()
    
    # 메시지 전송
    if send_button and user_question.strip():
        send_message(user_question, uploaded_files)

def send_message(message: str, uploaded_files: List = None):
    """메시지 전송"""
    try:
        with st.spinner("💭 AI가 생각하고 있습니다..."):
            # 첨부 파일 처리
            attachments = []
            if uploaded_files:
                import base64
                import io
                from PIL import Image
                for file in uploaded_files:
                    if file.type.startswith('image/'):
                        image = Image.open(file)
                        
                        # 이미지를 base64로 변환하여 저장
                        buffer = io.BytesIO()
                        image.save(buffer, format='PNG')
                        img_base64 = base64.b64encode(buffer.getvalue()).decode()
                        
                        attachments.append({
                            'type': 'image',
                            'name': file.name,
                            'data': img_base64
                        })
            
            # AI 응답 생성 (이미지 포함)
            ai_response = call_ai_api(message, uploaded_files)
            
            # 대화 히스토리에 추가
            chat_entry = {
                'timestamp': datetime.now().strftime("%H:%M"),
                'user_message': message,
                'ai_response': ai_response,
                'attachments': attachments
            }
            
            st.session_state.qa_chat_history.append(chat_entry)
            
            # 페이지 새로고침
            st.rerun()
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {str(e)}")

def call_ai_api(question: str, uploaded_files: List = None) -> str:
    """AI API 호출 - 이미지 포함"""
    try:
        custom_api_key = os.getenv('CUSTOM_GPT_API_KEY')
        
        headers = {
            "Authorization": f"Bearer {custom_api_key}",
            "Content-Type": "application/json"
        }
        
        # 메시지 구성
        user_content = []
        
        # 텍스트 추가
        user_content.append({
            "type": "text",
            "text": question
        })
        
        # 이미지가 있으면 추가
        if uploaded_files:
            import base64
            import io
            from PIL import Image
            
            for file in uploaded_files:
                if file.type.startswith('image/'):
                    # 이미지를 base64로 인코딩
                    image = Image.open(file)
                    
                    # 이미지 크기 조정 (API 제한 고려)
                    if image.width > 1024 or image.height > 1024:
                        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                    
                    # base64 인코딩
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    img_base64 = base64.b64encode(buffer.getvalue()).decode()
                    
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{img_base64}"
                        }
                    })
        
        data = {
            "model": "Product.Anthropic Claude 4 Sonnet",
            "messages": [
                {
                    "role": "system", 
                    "content": "당신은 QA 전문가입니다. 이미지가 포함된 경우 이미지를 분석하여 간결하고 실용적인 답변을 제공해주세요."
                },
                {
                    "role": "user", 
                    "content": user_content
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://rmbrgpt.bizops.rememberapp.co.kr/api/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return "죄송합니다. 일시적인 오류가 발생했습니다."
            
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"
