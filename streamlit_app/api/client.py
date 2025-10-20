"""
API 클라이언트 모듈 - 백엔드 서버와의 통신을 담당
"""

import requests
import streamlit as st

# API 기본 URL
API_BASE_URL = "http://localhost:8002/api/v1"

def get_api_base_url():
    """API 기본 URL 반환"""
    return API_BASE_URL

def get_safe_author_name(test_case):
    """테스트 케이스에서 안전하게 작성자 이름 추출"""
    try:
        # owner 필드 확인
        owner = test_case.get("owner")
        if owner and isinstance(owner, dict):
            display_name = owner.get("displayName")
            if display_name:
                return display_name
        elif owner and isinstance(owner, str):
            return owner
        
        # createdBy 필드 확인
        created_by = test_case.get("createdBy")
        if created_by and isinstance(created_by, dict):
            display_name = created_by.get("displayName")
            if display_name:
                return display_name
        elif created_by and isinstance(created_by, str):
            return created_by
        
        # author 필드 확인
        author = test_case.get("author")
        if author and isinstance(author, dict):
            display_name = author.get("displayName")
            if display_name:
                return display_name
        elif author and isinstance(author, str):
            return author
        
        # 모든 필드가 없거나 유효하지 않은 경우
        return "알 수 없음"
        
    except Exception:
        return "알 수 없음"

def api_call(endpoint, method="GET", data=None):
    """API 호출 공통 함수"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=15)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=15)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=15)
        elif method == "PATCH":
            response = requests.patch(url, json=data, timeout=15)
        elif method == "DELETE":
            response = requests.delete(url, timeout=15)
        
        # 성공 상태 코드 범위 확장 (200-299)
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except ValueError:
                # JSON 응답이 없는 경우 (예: 204 No Content)
                return {"success": True, "message": "요청이 성공적으로 처리되었습니다."}
        else:
            # 에러 응답 처리
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'API 오류: {response.status_code}')
            except ValueError:
                error_message = f'API 오류: {response.status_code}'
            
            st.error(f"❌ {error_message}")
            return {"success": False, "message": error_message, "status_code": response.status_code}
    except requests.exceptions.RequestException as e:
        error_message = f"연결 오류: {str(e)}"
        st.error(f"❌ {error_message}")
        return {"success": False, "message": error_message}

def check_api_connection():
    """API 서버 연결 확인"""
    try:
        url = "http://localhost:8002/health"
        response = requests.get(url, timeout=15)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=30)
def get_dashboard_stats():
    """대시보드 통계 데이터 가져오기"""
    try:
        # 새로운 API 엔드포인트 먼저 시도
        url = "http://localhost:8002/api/v1/tasks/stats/dashboard"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            # 레거시 엔드포인트 시도
            url = "http://localhost:8002/stats/dashboard"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                # 기본 통계 데이터 반환
                return {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "in_progress_tasks": 0,
                    "qa_ready_tasks": 0,
                    "completion_rate": 0
                }
    except:
        return {
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "qa_ready_tasks": 0,
            "completion_rate": 0
        }

@st.cache_data(ttl=60)
def get_projects():
    """프로젝트 목록 가져오기"""
    try:
        # 새로운 API 엔드포인트 먼저 시도
        url = "http://localhost:8002/api/v1/jira/projects"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            # 레거시 엔드포인트 시도
            url = "http://localhost:8002/projects"
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                # 기본 프로젝트 목록 반환
                return []
    except:
        return []

@st.cache_data(ttl=30)
def get_tasks(project_id=None, status=None):
    """작업 목록 가져오기"""
    try:
        params = []
        if project_id:
            params.append(f"project_id={project_id}")
        if status:
            params.append(f"status={status}")
        
        # 새로운 API 엔드포인트 먼저 시도
        url = "http://localhost:8002/api/v1/tasks/"
        if params:
            url += "?" + "&".join(params)
        
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            # 레거시 엔드포인트 시도
            url = "http://localhost:8002/tasks"
            if params:
                url += "?" + "&".join(params)
            response = requests.get(url, timeout=15)
            return response.json() if response.status_code == 200 else None
    except:
        return None

def test_jira_connection():
    """지라 연결 테스트"""
    return api_call("/jira/test-connection", method="POST")

@st.cache_data(ttl=300)  # 5분 캐시
def get_jira_projects():
    """지라 프로젝트 목록 가져오기"""
    return api_call("/jira/projects")

def sync_jira_project(project_key, selected_issues=None):
    """지라 프로젝트 동기화 - 타임아웃 연장"""
    try:
        url = f"{API_BASE_URL}/jira/sync/{project_key}"
        
        if selected_issues:
            # 선택된 이슈만 동기화
            data = {"selected_issues": selected_issues}
            response = requests.post(url, json=data, timeout=60)  # 60초로 연장
        else:
            # 전체 동기화
            response = requests.post(url, timeout=60)  # 60초로 연장
        
        if 200 <= response.status_code < 300:
            result = response.json()
            # 동기화 시작 후 캐시 클리어
            st.cache_data.clear()
            return result
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'API 오류: {response.status_code}')
            except ValueError:
                error_message = f'API 오류: {response.status_code}'
            
            st.error(f"❌ {error_message}")
            return {"success": False, "message": error_message, "status_code": response.status_code}
            
    except requests.exceptions.Timeout:
        error_message = "동기화 요청 시간 초과 (60초). 백그라운드에서 계속 진행될 수 있습니다."
        st.warning(f"⚠️ {error_message}")
        return {"success": False, "message": error_message, "timeout": True}
    except requests.exceptions.RequestException as e:
        error_message = f"연결 오류: {str(e)}"
        st.error(f"❌ {error_message}")
        return {"success": False, "message": error_message}

def get_jira_project_issues(project_key, limit=None, quick=False):
    """지라 프로젝트의 이슈 목록 가져오기 (빠른 모드 지원) - 타임아웃 연장"""
    try:
        params = []
        if limit is not None:
            params.append(f"limit={limit}")
        if quick:
            params.append("quick=true")
        
        url = f"{API_BASE_URL}/jira/projects/{project_key}/issues"
        if params:
            url += "?" + "&".join(params)
        
        response = requests.get(url, timeout=60)  # 60초로 연장
        
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'API 오류: {response.status_code}')
            except ValueError:
                error_message = f'API 오류: {response.status_code}'
            
            st.error(f"❌ {error_message}")
            return {"success": False, "message": error_message, "status_code": response.status_code}
            
    except requests.exceptions.Timeout:
        error_message = "이슈 조회 요청 시간 초과 (60초). 네트워크 상태를 확인해주세요."
        st.error(f"❌ {error_message}")
        return {"success": False, "message": error_message, "timeout": True}
    except requests.exceptions.RequestException as e:
        error_message = f"연결 오류: {str(e)}"
        st.error(f"❌ {error_message}")
        return {"success": False, "message": error_message}

def get_sync_status(project_key):
    """동기화 상태 조회 - 타임아웃 연장"""
    try:
        url = f"{API_BASE_URL}/jira/sync-status/{project_key}"
        response = requests.get(url, timeout=60)  # 60초로 연장
        
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except ValueError:
                # JSON 응답이 없는 경우
                return {"success": True, "message": "상태 조회 완료"}
        else:
            # 에러 응답 처리
            try:
                error_data = response.json()
                error_message = error_data.get('detail', f'API 오류: {response.status_code}')
            except ValueError:
                error_message = f'API 오류: {response.status_code}'
            
            return {"success": False, "message": error_message, "status_code": response.status_code}
            
    except requests.exceptions.Timeout:
        # 타임아웃 시 None 반환 (모달에서 재시도)
        return None
    except requests.exceptions.RequestException as e:
        # 연결 오류 시 None 반환 (모달에서 재시도)
        return None

def reset_all_tasks():
    """모든 작업 데이터 초기화"""
    try:
        result = api_call("/tasks/reset", method="DELETE")
        if result:
            # 캐시 클리어
            st.cache_data.clear()
        return result
    except Exception as e:
        st.error(f"초기화 요청 중 오류 발생: {str(e)}")
        return None

def delete_task(task_id):
    """개별 작업 삭제"""
    return api_call(f"/tasks/{task_id}", method="DELETE")

def update_qa_status(task_id, qa_status):
    """작업의 QA 상태 업데이트"""
    return api_call(f"/tasks/{task_id}/qa-status?qa_status={qa_status}", method="PUT")

def update_task_memo(task_id, memo):
    """작업의 메모 업데이트"""
    data = {"memo": memo}
    return api_call(f"/tasks/{task_id}/memo", method="PUT", data=data)

def get_task_memo(task_id):
    """작업의 메모 조회"""
    return api_call(f"/tasks/{task_id}/memo")


# Zephyr 관련 API 함수들
def create_zephyr_connection(connection_data):
    """Zephyr 연결 설정 생성"""
    result = api_call("/zephyr/connection", method="POST", data=connection_data)
    if result and result.get("success", True):
        # 연결 설정 생성 후 캐시 클리어
        st.cache_data.clear()
    return result

def get_zephyr_connection():
    """현재 Zephyr 연결 설정 조회"""
    return api_call("/zephyr/connection")

def update_zephyr_connection(connection_id, connection_data):
    """Zephyr 연결 설정 업데이트"""
    result = api_call(f"/zephyr/connection/{connection_id}", method="PUT", data=connection_data)
    if result and result.get("success", True):
        # 연결 설정 업데이트 후 캐시 클리어
        st.cache_data.clear()
    return result

def test_zephyr_connection():
    """Zephyr 연결 테스트"""
    return api_call("/zephyr/connection/test", method="POST")

@st.cache_data(ttl=60)  # 1분 캐시로 단축하여 최신 데이터 반영
def get_zephyr_projects():
    """Zephyr 프로젝트 목록 조회 - 직접 Zephyr Scale API 호출"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return {"success": False, "message": "ZEPHYR_API_TOKEN이 설정되지 않았습니다."}
    
    try:
        # Zephyr Scale Cloud API 직접 호출
        url = "https://api.zephyrscale.smartbear.com/v2/projects"
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        
        if response.status_code == 200:
            projects_data = response.json()
            
            # API 응답을 내부 형식으로 변환
            if isinstance(projects_data, list):
                if len(projects_data) == 0:
                    st.warning("⚠️ Zephyr Scale에서 빈 프로젝트 목록을 반환했습니다. API 토큰의 프로젝트 접근 권한을 확인해주세요.")
                    return []
                
                formatted_projects = []
                for project in projects_data:
                    formatted_project = {
                        "id": project.get("id"),
                        "key": project.get("key"),
                        "name": project.get("name"),
                        "description": project.get("description", ""),
                        "project_key": project.get("key"),
                        "project_name": project.get("name"),
                        "test_cases": 0,  # 별도 API 호출로 조회 필요
                        "last_sync": "-",
                        "sync_status": "미동기화",
                        "is_synced": False
                    }
                    formatted_projects.append(formatted_project)
                return formatted_projects
            elif isinstance(projects_data, dict):
                # 딕셔너리 응답인 경우 values 키 확인
                if "values" in projects_data:
                    projects_list = projects_data["values"]
                    if len(projects_list) == 0:
                        st.warning("⚠️ Zephyr Scale에서 빈 프로젝트 목록을 반환했습니다.")
                        return []
                    
                    formatted_projects = []
                    for project in projects_list:
                        formatted_project = {
                            "id": project.get("id"),
                            "key": project.get("key"),
                            "name": project.get("name"),
                            "description": project.get("description", ""),
                            "project_key": project.get("key"),
                            "project_name": project.get("name"),
                            "test_cases": 0,
                            "last_sync": "-",
                            "sync_status": "미동기화",
                            "is_synced": False
                        }
                        formatted_projects.append(formatted_project)
                    return formatted_projects
                else:
                    st.warning(f"⚠️ 예상하지 못한 API 응답 구조: {list(projects_data.keys())}")
                    return []
            else:
                st.warning(f"⚠️ 예상하지 못한 응답 타입: {type(projects_data)}")
                return []
        else:
            try:
                error_detail = response.json()
                st.error(f"Zephyr API 오류: HTTP {response.status_code} - {error_detail}")
            except:
                st.error(f"Zephyr API 오류: HTTP {response.status_code} - {response.text[:200]}")
            return []
            
    except Exception as e:
        st.error(f"Zephyr 프로젝트 조회 실패: {str(e)}")
        return []

def sync_zephyr_project(project_id, sync_data):
    """Zephyr 프로젝트 동기화 - 시뮬레이션"""
    import time
    
    try:
        # 동기화 시뮬레이션 (실제로는 복잡한 동기화 로직 필요)
        sync_direction = sync_data.get("sync_direction", "import")
        sync_type = sync_data.get("sync_type", "test_cases")
        
        # 간단한 지연 시뮬레이션
        time.sleep(1)
        
        # 캐시 클리어
        st.cache_data.clear()
        
        return {
            "success": True,
            "message": f"{sync_direction} 동기화가 시작되었습니다.",
            "sync_id": f"sync_{project_id}_{int(time.time())}",
            "project_id": project_id,
            "sync_direction": sync_direction,
            "sync_type": sync_type,
            "status": "started"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"동기화 시작 실패: {str(e)}"
        }

def get_zephyr_project(project_id):
    """Zephyr 프로젝트 상세 조회"""
    return api_call(f"/zephyr/projects/{project_id}")

def get_zephyr_test_cases(project_id, skip=0, limit=10000, status=None, priority=None):
    """Zephyr 테스트 케이스 목록 조회 - 직접 Zephyr Scale API 호출"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return {"success": False, "message": "ZEPHYR_API_TOKEN이 설정되지 않았습니다."}
    
    try:
        # Zephyr Scale Cloud API 공식 엔드포인트 사용
        url = "https://api.zephyrscale.smartbear.com/v2/testcases"
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        # 쿼리 파라미터 설정
        params = {
            "projectId": project_id,
            "maxResults": limit,
            "startAt": skip
        }
        
        if status:
            params["status"] = status
        if priority:
            params["priority"] = priority
        
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
        
        if response.status_code == 200:
            test_cases_data = response.json()
            
            # API 응답을 내부 형식으로 변환
            if isinstance(test_cases_data, dict) and "values" in test_cases_data:
                formatted_test_cases = []
                for test_case in test_cases_data.get("values", []):
                    try:
                        # 안전한 필드 추출
                        test_case_id = test_case.get("id") if test_case.get("id") else None
                        test_case_key = test_case.get("key") if test_case.get("key") else None
                        title = test_case.get("name") if test_case.get("name") else "제목 없음"
                        
                        # description 안전 추출
                        description = "설명이 없습니다."
                        if test_case.get("objective"):
                            description = str(test_case.get("objective"))
                        elif test_case.get("precondition"):
                            description = str(test_case.get("precondition"))
                        
                        # status 안전 추출
                        status = "Draft"
                        if test_case.get("statusName"):
                            status = str(test_case.get("statusName"))
                        elif test_case.get("status"):
                            status_val = test_case.get("status")
                            if isinstance(status_val, str):
                                status = status_val
                            elif isinstance(status_val, dict) and status_val.get("name"):
                                status = str(status_val.get("name"))
                        
                        # priority 안전 추출
                        priority = "Medium"
                        if test_case.get("priorityName"):
                            priority = str(test_case.get("priorityName"))
                        elif test_case.get("priority"):
                            priority_val = test_case.get("priority")
                            if isinstance(priority_val, str):
                                priority = priority_val
                            elif isinstance(priority_val, dict) and priority_val.get("name"):
                                priority = str(priority_val.get("name"))
                        
                        # 작성자 안전 추출
                        created_by = get_safe_author_name(test_case)
                        
                        # 날짜 안전 추출
                        last_sync = "-"
                        if test_case.get("updatedOn"):
                            last_sync = str(test_case.get("updatedOn"))
                        elif test_case.get("modifiedOn"):
                            last_sync = str(test_case.get("modifiedOn"))
                        
                        # 생성 날짜 안전 추출
                        created_on = "-"
                        if test_case.get("createdOn"):
                            created_on = str(test_case.get("createdOn"))
                        elif test_case.get("created"):
                            created_on = str(test_case.get("created"))
                        elif test_case.get("createdDate"):
                            created_on = str(test_case.get("createdDate"))
                        
                        # 프로젝트 ID 안전 추출
                        project_id = None
                        if test_case.get("projectId"):
                            project_id = str(test_case.get("projectId"))
                        elif test_case.get("projectKey"):
                            project_id = str(test_case.get("projectKey"))
                        
                        formatted_test_case = {
                            "id": test_case_id,
                            "test_case_key": test_case_key,
                            "title": title,
                            "description": description,
                            "status": status,
                            "priority": priority,
                            "created_by": created_by,
                            "zephyr_test_id": test_case_key,
                            "last_sync": last_sync,
                            "project_id": project_id,
                            "createdOn": created_on,
                            "created": created_on,
                            "created_at": created_on
                        }
                        formatted_test_cases.append(formatted_test_case)
                        
                    except Exception as e:
                        st.warning(f"테스트 케이스 처리 중 오류: {str(e)}")
                        continue
                        
                return formatted_test_cases
            else:
                return []
        else:
            st.error(f"Zephyr 테스트 케이스 조회 API 오류: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Zephyr 테스트 케이스 조회 실패: {str(e)}")
        return []

def get_zephyr_test_case(test_case_id):
    """Zephyr 테스트 케이스 상세 조회"""
    return api_call(f"/zephyr/test-cases/{test_case_id}")

def get_zephyr_test_executions(test_case_id, skip=0, limit=50, status=None):
    """Zephyr 테스트 실행 결과 목록 조회"""
    params = [f"skip={skip}", f"limit={limit}"]
    if status:
        params.append(f"status={status}")
    
    endpoint = f"/zephyr/test-cases/{test_case_id}/executions"
    if params:
        endpoint += "?" + "&".join(params)
    
    return api_call(endpoint)

def get_zephyr_test_execution(execution_id):
    """Zephyr 테스트 실행 결과 상세 조회"""
    return api_call(f"/zephyr/executions/{execution_id}")

def get_zephyr_sync_history(project_id=None, sync_direction=None, sync_status=None, skip=0, limit=50):
    """Zephyr 동기화 이력 조회"""
    params = [f"skip={skip}", f"limit={limit}"]
    if project_id:
        params.append(f"project_id={project_id}")
    if sync_direction:
        params.append(f"sync_direction={sync_direction}")
    if sync_status:
        params.append(f"sync_status={sync_status}")
    
    endpoint = "/zephyr/sync-history"
    if params:
        endpoint += "?" + "&".join(params)
    
    return api_call(endpoint)

def get_zephyr_sync_history_detail(sync_id):
    """Zephyr 동기화 이력 상세 조회"""
    return api_call(f"/zephyr/sync-history/{sync_id}")

def get_zephyr_sync_status(sync_id):
    """Zephyr 동기화 상태 조회"""
    return api_call(f"/zephyr/sync-status/{sync_id}")

@st.cache_data(ttl=60)  # 1분 캐시
def get_zephyr_dashboard_stats():
    """Zephyr 대시보드 통계 조회"""
    return api_call("/zephyr/stats/dashboard")

def reset_zephyr_project(project_id):
    """Zephyr 프로젝트 데이터 초기화"""
    result = api_call(f"/zephyr/projects/{project_id}/reset", method="DELETE")
    if result and result.get("success", True):
        # 초기화 후 캐시 클리어
        st.cache_data.clear()
    return result

def reset_all_zephyr_data():
    """모든 Zephyr 데이터 초기화"""
    result = api_call("/zephyr/reset-all", method="DELETE")
    if result and result.get("success", True):
        # 초기화 후 캐시 클리어
        st.cache_data.clear()
    return result


# Zephyr 테스트 사이클 관련 API 함수들
@st.cache_data(ttl=60)  # 1분 캐시
def get_zephyr_test_cycles(project_id, skip=0, limit=1000):
    """Zephyr 테스트 사이클 목록 조회 - 직접 Zephyr Scale API 호출 (전체 조회)"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return {"success": False, "message": "ZEPHYR_API_TOKEN이 설정되지 않았습니다."}
    
    try:
        all_cycles = []
        current_skip = 0
        max_results_per_request = 100  # API 제한에 맞춰 한 번에 100개씩 요청
        
        while True:
            # Zephyr Scale Cloud API 공식 엔드포인트 사용
            url = "https://api.zephyrscale.smartbear.com/v2/testcycles"
            headers = {
                "Authorization": f"Bearer {zephyr_api_token}",
                "Accept": "application/json"
            }
            
            # 쿼리 파라미터 설정
            params = {
                "projectId": project_id,
                "maxResults": max_results_per_request,
                "startAt": current_skip
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                cycles_data = response.json()
                
                # API 응답을 내부 형식으로 변환
                if isinstance(cycles_data, dict) and "values" in cycles_data:
                    batch_cycles = cycles_data.get("values", [])
                    
                    # 배치가 비어있으면 더 이상 데이터가 없음
                    if not batch_cycles:
                        break
                    
                    # 각 사이클 처리
                    for cycle in batch_cycles:
                        try:
                            # 안전한 필드 추출
                            cycle_id = cycle.get("id") if cycle.get("id") else None
                            cycle_key = cycle.get("key") if cycle.get("key") else None
                            cycle_name = cycle.get("name") if cycle.get("name") else "이름 없음"
                            
                            # description 안전 추출
                            description = cycle.get("description", "설명이 없습니다.")
                            
                            # status 안전 추출
                            status = "Not Started"
                            if cycle.get("statusName"):
                                status = str(cycle.get("statusName"))
                            elif cycle.get("status"):
                                status_val = cycle.get("status")
                                if isinstance(status_val, str):
                                    status = status_val
                                elif isinstance(status_val, dict) and status_val.get("name"):
                                    status = str(status_val.get("name"))
                            
                            # 환경 정보 추출
                            environment = cycle.get("environment", "Unknown")
                            if isinstance(environment, dict):
                                environment = environment.get("name", "Unknown")
                            
                            # 버전 정보 추출
                            version = cycle.get("version", "N/A")
                            if isinstance(version, dict):
                                version = version.get("name", "N/A")
                            
                            # 빌드 정보 추출
                            build = cycle.get("build", "N/A")
                            
                            # 작성자 안전 추출
                            created_by = get_safe_author_name(cycle)
                            
                            # 담당자 추출
                            assigned_to = "미할당"
                            if cycle.get("owner"):
                                owner = cycle.get("owner")
                                if isinstance(owner, dict):
                                    assigned_to = owner.get("displayName", "미할당")
                                elif isinstance(owner, str):
                                    assigned_to = owner
                            
                            # 날짜 안전 추출
                            start_date = cycle.get("plannedStartDate", "N/A")
                            end_date = cycle.get("plannedEndDate", "N/A")
                            created_at = cycle.get("createdOn", "N/A")
                            
                            # 테스트 케이스 통계 (기본값)
                            total_test_cases = 0
                            executed_test_cases = 0
                            passed_test_cases = 0
                            failed_test_cases = 0
                            blocked_test_cases = 0
                            
                            # 통계 정보가 있다면 추출
                            if cycle.get("testExecutions"):
                                executions = cycle.get("testExecutions", {})
                                total_test_cases = executions.get("total", 0)
                                passed_test_cases = executions.get("passed", 0)
                                failed_test_cases = executions.get("failed", 0)
                                blocked_test_cases = executions.get("blocked", 0)
                                executed_test_cases = passed_test_cases + failed_test_cases + blocked_test_cases
                            
                            formatted_cycle = {
                                "id": cycle_id,
                                "zephyr_cycle_id": cycle_key,
                                "cycle_name": cycle_name,
                                "description": description,
                                "version": version,
                                "environment": environment,
                                "build": build,
                                "status": status,
                                "created_by": created_by,
                                "assigned_to": assigned_to,
                                "start_date": start_date,
                                "end_date": end_date,
                                "total_test_cases": total_test_cases,
                                "executed_test_cases": executed_test_cases,
                                "passed_test_cases": passed_test_cases,
                                "failed_test_cases": failed_test_cases,
                                "blocked_test_cases": blocked_test_cases,
                                "created_at": created_at,
                                "last_sync": created_at,
                                "project_id": project_id
                            }
                            all_cycles.append(formatted_cycle)
                            
                        except Exception as e:
                            st.warning(f"테스트 사이클 처리 중 오류: {str(e)}")
                            continue
                    
                    # 다음 배치로 이동
                    current_skip += max_results_per_request
                    
                    # 배치 크기가 요청한 크기보다 작으면 마지막 배치
                    if len(batch_cycles) < max_results_per_request:
                        break
                else:
                    # API 응답 구조가 예상과 다름
                    break
            else:
                st.error(f"Zephyr 테스트 사이클 조회 API 오류: HTTP {response.status_code}")
                break
        
        # 생성일 기준으로 최신순 정렬
        all_cycles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return all_cycles
            
    except Exception as e:
        st.error(f"Zephyr 테스트 사이클 조회 실패: {str(e)}")
        return []

def get_zephyr_test_cycle(cycle_id):
    """Zephyr 테스트 사이클 상세 조회"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return {"success": False, "message": "ZEPHYR_API_TOKEN이 설정되지 않았습니다."}
    
    try:
        # Zephyr Scale Cloud API 공식 엔드포인트 사용
        url = f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}"
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Zephyr 테스트 사이클 상세 조회 API 오류: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        st.error(f"Zephyr 테스트 사이클 상세 조회 실패: {str(e)}")
        return None

def sync_zephyr_test_cycle(project_id, cycle_id, sync_data):
    """Zephyr 테스트 사이클 동기화"""
    import time
    
    try:
        # 동기화 시뮬레이션 (실제로는 복잡한 동기화 로직 필요)
        sync_direction = sync_data.get("sync_direction", "import")
        sync_type = sync_data.get("sync_type", "test_executions")
        
        # 간단한 지연 시뮬레이션
        time.sleep(2)
        
        # 캐시 클리어
        st.cache_data.clear()
        
        return {
            "success": True,
            "message": f"테스트 사이클 {sync_direction} 동기화가 시작되었습니다.",
            "sync_id": f"cycle_sync_{cycle_id}_{int(time.time())}",
            "project_id": project_id,
            "cycle_id": cycle_id,
            "sync_direction": sync_direction,
            "sync_type": sync_type,
            "status": "started"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"테스트 사이클 동기화 시작 실패: {str(e)}"
        }

def get_zephyr_cycle_executions(cycle_id, skip=0, limit=100):
    """Zephyr 테스트 사이클의 실행 결과 조회"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return {"success": False, "message": "ZEPHYR_API_TOKEN이 설정되지 않았습니다."}
    
    try:
        # Zephyr Scale Cloud API 공식 엔드포인트 사용
        url = "https://api.zephyrscale.smartbear.com/v2/testexecutions"
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        # 쿼리 파라미터 설정
        params = {
            "testCycle": cycle_id,
            "maxResults": limit,
            "startAt": skip
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
        
        if response.status_code == 200:
            executions_data = response.json()
            
            # API 응답을 내부 형식으로 변환
            if isinstance(executions_data, dict) and "values" in executions_data:
                return executions_data.get("values", [])
            else:
                return []
        else:
            st.error(f"Zephyr 테스트 실행 결과 조회 API 오류: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Zephyr 테스트 실행 결과 조회 실패: {str(e)}")
        return []


# QA 요청서 관련 API 함수들
def create_qa_request(qa_request_data):
    """QA 요청서 생성"""
    result = api_call("/qa-requests/", method="POST", data=qa_request_data)
    if result and result.get("success", True):
        # QA 요청서 생성 후 캐시 클리어
        st.cache_data.clear()
    return result

@st.cache_data(ttl=60)  # 1분 캐시
def get_qa_requests(page=1, size=20, status=None, platform=None):
    """QA 요청서 목록 조회"""
    params = [f"page={page}", f"size={size}"]
    if status:
        params.append(f"status={status}")
    if platform:
        params.append(f"platform={platform}")
    
    endpoint = "/qa-requests/"
    if params:
        endpoint += "?" + "&".join(params)
    
    return api_call(endpoint)

def get_qa_request(request_id):
    """QA 요청서 상세 조회"""
    return api_call(f"/qa-requests/{request_id}")

def update_qa_request(request_id, qa_request_data):
    """QA 요청서 업데이트"""
    result = api_call(f"/qa-requests/{request_id}", method="PUT", data=qa_request_data)
    if result and result.get("success", True):
        # QA 요청서 업데이트 후 캐시 클리어
        st.cache_data.clear()
    return result

def update_qa_request_status(request_id, status_data):
    """QA 요청서 상태 업데이트"""
    result = api_call(f"/qa-requests/{request_id}/status", method="PUT", data=status_data)
    if result and result.get("success", True):
        # 상태 업데이트 후 캐시 클리어
        st.cache_data.clear()
    return result

def delete_qa_request(request_id):
    """QA 요청서 삭제"""
    result = api_call(f"/qa-requests/{request_id}", method="DELETE")
    if result and result.get("success", True):
        # QA 요청서 삭제 후 캐시 클리어
        st.cache_data.clear()
    return result
