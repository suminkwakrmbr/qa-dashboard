"""
커스텀 스타일 모듈
Streamlit 앱의 CSS 스타일을 정의합니다.
"""

import streamlit as st

def apply_custom_styles():
    """커스텀 CSS 스타일 적용"""
    st.markdown("""
    <style>
        /* Google Fonts 임포트 */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Pretendard:wght@300;400;500;600;700&display=swap');
        
        /* 전체 앱 스타일링 */
        .stApp {
            background: linear-gradient(135deg, #0f1419 0%, #1a1f2e 50%, #0f1419 100%);
            font-family: 'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #e2e8f0;
        }
        
        /* 메인 컨테이너 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 1400px;
            background-color: transparent;
        }
        
        /* 사이드바 스타일링 */
        .css-1d391kg {
            background: linear-gradient(180deg, #1e2329 0%, #2d3748 100%);
            border-right: 1px solid #4a5568;
        }
        
        /* 헤더 스타일 */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Pretendard', 'Inter', sans-serif;
            font-weight: 600;
            letter-spacing: -0.025em;
            color: #f7fafc !important;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1.5rem;
        }
        
        h2 {
            font-size: 1.875rem;
            color: #e2e8f0 !important;
            border-bottom: 2px solid #4a5568;
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        
        h3 {
            font-size: 1.5rem;
            color: #cbd5e0 !important;
            margin-bottom: 1rem;
        }
        
        /* 텍스트 스타일 */
        .stMarkdown, .stText, p, div, span {
            font-family: 'Pretendard', 'Inter', sans-serif;
            color: #e2e8f0;
            line-height: 1.6;
        }
        
        /* 버튼 스타일링 */
        .stButton > button {
            font-family: 'Pretendard', 'Inter', sans-serif;
            font-weight: 500;
            border-radius: 8px;
            border: none;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            letter-spacing: 0.025em;
        }
        
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }
        
        .stButton > button[kind="primary"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .stButton > button[kind="secondary"] {
            background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
            color: #e2e8f0;
            border: 1px solid #4a5568;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border-color: #667eea;
            transform: translateY(-1px);
        }
        
        /* 입력 필드 스타일링 */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            background-color: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 8px;
            color: #e2e8f0;
            font-family: 'Pretendard', 'Inter', sans-serif;
            padding: 0.75rem;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            outline: none;
        }
        
        /* 메트릭 카드 스타일링 */
        .css-1r6slb0 {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border: 1px solid #4a5568;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* 탭 스타일링 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #1a202c;
            border-radius: 8px;
            padding: 4px;
        }
        
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            border-radius: 6px;
            color: #a0aec0;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: all 0.2s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
        }
        
        /* 사이드바 버튼 스타일링 */
        .css-1d391kg .stButton > button {
            width: 100%;
            text-align: left;
            background: transparent;
            border: 1px solid transparent;
            color: #cbd5e0;
            font-weight: 500;
            padding: 0.875rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        
        .css-1d391kg .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: transparent;
            font-weight: 600;
        }
        
        .css-1d391kg .stButton > button:hover {
            background-color: #2d3748;
            border-color: #4a5568;
            transform: translateX(4px);
        }
        
        /* Streamlit 기본 알림 스타일 오버라이드 */
        .stAlert {
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
        }
        
        .stSuccess {
            background: linear-gradient(135deg, #065f46 0%, #047857 100%) !important;
            border-color: #10b981 !important;
            color: #d1fae5 !important;
        }
        
        .stError {
            background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%) !important;
            border-color: #ef4444 !important;
            color: #fecaca !important;
        }
        
        .stWarning {
            background: linear-gradient(135deg, #92400e 0%, #b45309 100%) !important;
            border-color: #f59e0b !important;
            color: #fef3c7 !important;
        }
        
        .stInfo {
            background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%) !important;
            border-color: #3b82f6 !important;
            color: #dbeafe !important;
        }
        
        /* 알림 박스 스타일링 */
        .success-box { 
            background: linear-gradient(135deg, #065f46 0%, #047857 100%);
            border: 1px solid #10b981;
            color: #d1fae5;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.1);
            font-weight: 500;
        }
        
        .error-box { 
            background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
            border: 1px solid #ef4444;
            color: #fecaca;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(239, 68, 68, 0.1);
            font-weight: 500;
        }
        
        .info-box { 
            background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);
            border: 1px solid #3b82f6;
            color: #dbeafe;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1);
            font-weight: 500;
        }
        
        .warning-box {
            background: linear-gradient(135deg, #92400e 0%, #b45309 100%);
            border: 1px solid #f59e0b;
            color: #fef3c7;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(245, 158, 11, 0.1);
            font-weight: 500;
        }
        
        /* 코드 스타일링 */
        code {
            font-family: 'JetBrains Mono', monospace;
            background-color: #1a202c;
            color: #e2e8f0;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
        }
        
        /* 체크박스 스타일링 */
        .stCheckbox > label {
            color: #e2e8f0 !important;
            font-weight: 500;
        }
        
        /* 라벨 스타일링 */
        .stSelectbox > label,
        .stTextInput > label,
        .stTextArea > label {
            color: #cbd5e0 !important;
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        
        /* 데이터프레임 스타일링 */
        .dataframe {
            background-color: #1a202c;
            border: 1px solid #4a5568;
            border-radius: 8px;
        }
        
        /* 확장 가능한 섹션 스타일링 */
        .streamlit-expanderHeader {
            background-color: #2d3748;
            border: 1px solid #4a5568;
            border-radius: 8px;
            color: #e2e8f0;
            font-weight: 600;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
        }
        
        .streamlit-expanderContent {
            background-color: #1a202c;
            border: 1px solid #4a5568;
            border-top: none;
            border-radius: 0 0 8px 8px;
            padding: 1rem;
            margin-top: -0.5rem;
        }
        
        /* 메트릭 카드 간격 개선 */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border: 1px solid #4a5568;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* 커스텀 카드 스타일 */
        .premium-card {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border: 1px solid #4a5568;
            border-radius: 16px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        .premium-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            border-color: #667eea;
        }
        
        /* 그라데이션 텍스트 */
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }
        
        /* 추가 Streamlit 요소 스타일링 */
        .stMultiSelect > div > div {
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 8px !important;
            color: #e2e8f0 !important;
        }
        
        .stDateInput > div > div > input {
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            color: #e2e8f0 !important;
        }
        
        .stFileUploader > div {
            background-color: #2d3748 !important;
            border: 1px solid #4a5568 !important;
            border-radius: 8px !important;
        }
        
        .stSlider > div > div > div {
            background-color: #1a202c !important;
        }
        
        .stProgress > div > div {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        }
        
        /* 사이드바 추가 스타일링 */
        .css-1d391kg .stMarkdown {
            color: #e2e8f0 !important;
        }
        
        .css-1d391kg h2 {
            color: #f7fafc !important;
        }
        
        /* 폼 스타일링 */
        .stForm {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%) !important;
            border: 1px solid #4a5568 !important;
            border-radius: 12px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        }
        
        /* 상태 배지 */
        .status-badge {
            display: inline-block;
            padding: 0.375rem 0.875rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .status-success { 
            background: linear-gradient(135deg, #065f46, #047857); 
            color: #d1fae5; 
        }
        .status-warning { 
            background: linear-gradient(135deg, #92400e, #b45309); 
            color: #fef3c7; 
        }
        .status-error { 
            background: linear-gradient(135deg, #7f1d1d, #991b1b); 
            color: #fecaca; 
        }
        .status-info { 
            background: linear-gradient(135deg, #1e3a8a, #1d4ed8); 
            color: #dbeafe; 
        }
        
        /* 애니메이션 */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        
        /* 반응형 디자인 */
        @media (max-width: 768px) {
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            
            h1 {
                font-size: 2rem;
            }
            
            .premium-card {
                padding: 1.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
