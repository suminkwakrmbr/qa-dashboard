"""
Zephyr 프로젝트 관리 페이지 - 연동 설정 전용
"""

import streamlit as st
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

def show_zephyr_project_management_page():
    """Zephyr 프로젝트 관리 화면 - 연동 설정 전용"""
    st.header("⚡ 제퍼 연동 관리")
    
    # 연동 설정만 표시
    show_zephyr_connection_settings()


def show_zephyr_connection_settings():
    """Zephyr 연동 설정"""
    st.subheader("🔗 Zephyr 연동 설정")
    
    # .env에서 Zephyr 설정 정보 가져오기
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_server = os.getenv('ZEPHYR_SERVER', 'https://remember-qa.atlassian.net')
    zephyr_username = os.getenv('ZEPHYR_USERNAME', '')
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    # 현재 연동 상태 확인
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"**Zephyr 서버:** {zephyr_server}")
        
        if zephyr_username and zephyr_api_token:
            st.success("✅ 연동 정보가 설정되어 있습니다.")
        else:
            st.warning("⚠️ .env 파일에 Zephyr 연동 정보가 없습니다.")
    
    with col2:
        if st.button("🔄 연결 테스트", use_container_width=True):
            if not zephyr_username or not zephyr_api_token:
                st.error("❌ .env 파일에 ZEPHYR_USERNAME과 ZEPHYR_API_TOKEN을 설정해주세요.")
            else:
                with st.spinner("Zephyr 서버 연결 테스트 중..."):
                    try:
                        # 직접 Zephyr API 호출로 연결 테스트
                        import requests
                        from requests.auth import HTTPBasicAuth
                        import time
                        
                        start_time = time.time()
                        
                        # Zephyr Scale 연결 테스트 - 성공한 엔드포인트를 우선 시도
                        test_urls = [
                            "https://api.zephyrscale.smartbear.com/v2/projects",  # Cloud API (성공 확인됨)
                            f"{zephyr_server}/rest/atm/1.0/project",  # Zephyr Scale Server
                            f"{zephyr_server}/rest/tests/1.0/project"  # 대안 엔드포인트
                        ]
                        
                        connection_success = False
                        last_error = None
                        
                        for i, test_url in enumerate(test_urls):
                            try:
                                # Zephyr Scale API는 Bearer 토큰 방식 사용
                                headers = {
                                    "Authorization": f"Bearer {zephyr_api_token}",
                                    "Accept": "application/json"
                                }
                                
                                response = requests.get(
                                    test_url,
                                    headers=headers,
                                    timeout=15,
                                    verify=False  # SSL 인증서 검증 비활성화
                                )
                                
                                if response.status_code == 200:
                                    connection_success = True
                                    break
                                else:
                                    last_error = f"HTTP {response.status_code}"
                                    
                            except Exception as e:
                                last_error = str(e)
                                continue
                        
                        # 연결 결과 처리를 위해 response 변수 설정
                        if not connection_success:
                            # 마지막 시도로 간단한 연결 테스트
                            response = type('MockResponse', (), {
                                'status_code': 500,
                                'text': f"모든 연결 시도 실패. 마지막 오류: {last_error}"
                            })()
                        
                        connection_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            response_data = response.json()
                            # Zephyr Scale API 응답에서 프로젝트 수 확인
                            if isinstance(response_data, list):
                                project_count = len(response_data)
                                st.success(f"✅ 연결 성공: Zephyr Scale API 접근 가능 (프로젝트 {project_count}개) ({round(connection_time, 2)}초)")
                            else:
                                st.success(f"✅ 연결 성공: Zephyr Scale API 접근 가능 ({round(connection_time, 2)}초)")
                            st.session_state.zephyr_connected = True
                        elif response.status_code == 401:
                            st.error("❌ 인증 실패 (HTTP 401)")
                            st.error("🔐 API 토큰이 올바르지 않거나 만료되었습니다.")
                            st.info("💡 .env 파일의 ZEPHYR_API_TOKEN을 확인해주세요. Zephyr에서 새로운 API 토큰을 발급받아야 할 수 있습니다.")
                            st.session_state.zephyr_connected = False
                        elif response.status_code == 403:
                            st.error("❌ 권한 없음 (HTTP 403)")
                            st.error("🚫 해당 사용자에게 Zephyr 접근 권한이 없습니다.")
                            st.session_state.zephyr_connected = False
                        elif response.status_code == 404:
                            st.error("❌ 서버를 찾을 수 없음 (HTTP 404)")
                            st.error("🔍 서버 URL을 확인해주세요.")
                            st.session_state.zephyr_connected = False
                        else:
                            st.error(f"❌ 연결 실패: HTTP {response.status_code}")
                            try:
                                error_detail = response.json()
                                st.error(f"상세 오류: {error_detail}")
                            except:
                                st.error(f"응답 내용: {response.text[:200]}")
                            st.session_state.zephyr_connected = False
                            
                    except requests.exceptions.Timeout:
                        st.error("❌ 연결 시간 초과")
                        st.session_state.zephyr_connected = False
                    except requests.exceptions.ConnectionError:
                        st.error("❌ 서버에 연결할 수 없습니다.")
                        st.session_state.zephyr_connected = False
                    except Exception as e:
                        st.error(f"❌ 연결 테스트 실패: {str(e)}")
                        st.session_state.zephyr_connected = False
    
    st.markdown("---")
    
    # 연동 정보 표시
    st.markdown("### 📋 현재 연동 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **🌐 서버 URL**  
        `{zephyr_server}`
        
        **👤 사용자명**  
        `{zephyr_username if zephyr_username else '설정되지 않음'}`
        """)
    
    with col2:
        st.markdown(f"""
        **🔑 API 토큰**  
        `{'설정됨' if zephyr_api_token else '설정되지 않음'}`
        
        **🔄 연결 상태**  
        {'✅ 연결됨' if st.session_state.get('zephyr_connected', False) else '❌ 연결 안됨'}
        """)
    
    # 설정 방법 안내
    if not zephyr_username or not zephyr_api_token:
        st.markdown("---")
        st.markdown("### ⚙️ 연동 설정 방법")
        
        st.info("""
        **.env 파일에 다음 정보를 추가하세요:**
        
        ```
        ZEPHYR_SERVER=https://remember-qa.atlassian.net
        ZEPHYR_USERNAME=your-email@company.com
        ZEPHYR_API_TOKEN=your-zephyr-api-token
        ```
        
        설정 후 서버를 재시작하면 자동으로 연동됩니다.
        """)
    else:
        # 상시 자동 연결 확인
        if 'zephyr_connection_checked' not in st.session_state or not st.session_state.get('zephyr_connection_checked', False):
            with st.spinner("Zephyr 연결 상태 확인 중..."):
                try:
                    import requests
                    import time
                    
                    start_time = time.time()
                    
                    # Zephyr Scale 연결 테스트 - 성공한 엔드포인트를 우선 시도
                    test_urls = [
                        "https://api.zephyrscale.smartbear.com/v2/projects",  # Cloud API (성공 확인됨)
                        f"{zephyr_server}/rest/atm/1.0/project",  # Zephyr Scale Server
                        f"{zephyr_server}/rest/tests/1.0/project"  # 대안 엔드포인트
                    ]
                    
                    connection_success = False
                    
                    for test_url in test_urls:
                        try:
                            headers = {
                                "Authorization": f"Bearer {zephyr_api_token}",
                                "Accept": "application/json"
                            }
                            
                            response = requests.get(
                                test_url,
                                headers=headers,
                                timeout=10,
                                verify=False
                            )
                            
                            if response.status_code == 200:
                                connection_success = True
                                connection_time = time.time() - start_time
                                
                                response_data = response.json()
                                if isinstance(response_data, list):
                                    project_count = len(response_data)
                                    st.success(f"🎉 Zephyr Scale에 자동 연결되었습니다! (프로젝트 {project_count}개, {round(connection_time, 2)}초)")
                                else:
                                    st.success(f"🎉 Zephyr Scale에 자동 연결되었습니다! ({round(connection_time, 2)}초)")
                                
                                st.session_state.zephyr_connected = True
                                break
                                
                        except Exception:
                            continue
                    
                    if not connection_success:
                        st.session_state.zephyr_connected = False
                        st.info("ℹ️ Zephyr 자동 연결에 실패했습니다. 필요시 '🔄 연결 테스트' 버튼을 사용해주세요.")
                    
                    st.session_state.zephyr_connection_checked = True
                    
                except Exception:
                    st.session_state.zephyr_connected = False
                    st.session_state.zephyr_connection_checked = True
