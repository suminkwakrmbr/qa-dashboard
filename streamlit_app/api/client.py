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

def get_zephyr_cycle_test_cases(cycle_id, skip=0, limit=100):
    """Zephyr 테스트 사이클에 할당된 테스트 케이스 목록 조회 - 여러 API 엔드포인트 시도"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return []
    
    try:
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        params = {
            "maxResults": limit,
            "startAt": skip
        }
        
        # 여러 API 엔드포인트 시도
        api_endpoints = [
            f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}/testcases",
            f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}/tests",
            f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}",  # 사이클 상세 정보에서 테스트 케이스 정보 추출
        ]
        
        for i, url in enumerate(api_endpoints):
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                test_cases_data = response.json()
                
                if isinstance(test_cases_data, dict):
                    # 1. values 키가 있는 경우
                    if "values" in test_cases_data:
                        test_cases = test_cases_data.get("values", [])
                        if len(test_cases) > 0:
                            return format_test_cases(test_cases)
                    
                    # 2. testCases 키가 있는 경우
                    elif "testCases" in test_cases_data:
                        test_cases = test_cases_data.get("testCases", [])
                        if len(test_cases) > 0:
                            return format_test_cases(test_cases)
                    
                    # 3. tests 키가 있는 경우
                    elif "tests" in test_cases_data:
                        test_cases = test_cases_data.get("tests", [])
                        if len(test_cases) > 0:
                            return format_test_cases(test_cases)
                    
                    # 4. 사이클 상세 정보인 경우 (세 번째 API)
                    elif i == 2:  # 사이클 상세 API
                        # 사이클 정보에서 테스트 관련 정보 추출
                        cycle_info = test_cases_data
                        
                        # 통계 정보 확인
                        if "testExecutions" in cycle_info:
                            executions = cycle_info.get("testExecutions", {})
                            total_tests = executions.get("total", 0)
                            if total_tests > 0:
                                # 실제 테스트 케이스 목록은 없지만 통계는 있는 상태
                                # 다른 방법으로 테스트 케이스 조회 필요
                                continue
                
                elif isinstance(test_cases_data, list):
                    if len(test_cases_data) > 0:
                        return format_test_cases(test_cases_data)
        
        return []
            
    except Exception:
        return []


def format_test_cases(test_cases):
    """테스트 케이스 목록을 표준 형식으로 변환"""
    formatted_test_cases = []
    
    for test_case in test_cases:
        try:
            formatted_test_case = {
                "id": test_case.get("id"),
                "key": test_case.get("key", "N/A"),
                "name": test_case.get("name", "Unknown Test"),
                "status": test_case.get("status", {}).get("name", "Draft") if isinstance(test_case.get("status"), dict) else str(test_case.get("status", "Draft")),
                "priority": test_case.get("priority", {}).get("name", "Medium") if isinstance(test_case.get("priority"), dict) else str(test_case.get("priority", "Medium"))
            }
            formatted_test_cases.append(formatted_test_case)
        except Exception:
            continue
    
    return formatted_test_cases


def get_zephyr_cycle_executions(cycle_id, skip=0, limit=100):
    """Zephyr 테스트 사이클의 테스트 실행 결과 조회"""
    import os
    from dotenv import load_dotenv
    
    # .env 파일 로드
    load_dotenv()
    
    zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
    
    if not zephyr_api_token:
        return []
    
    try:
        # 1. 먼저 테스트 플레이어(Test Player) API 시도
        player_url = f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}/testexecutions"
        headers = {
            "Authorization": f"Bearer {zephyr_api_token}",
            "Accept": "application/json"
        }
        
        params = {
            "maxResults": limit,
            "startAt": skip
        }
        
        response = requests.get(player_url, headers=headers, params=params, timeout=30, verify=False)
        
        if response.status_code == 200:
            executions_data = response.json()
            
            if isinstance(executions_data, dict):
                if "values" in executions_data:
                    values = executions_data.get("values", [])
                    return values
            elif isinstance(executions_data, list):
                return executions_data
        
        # 2. 테스트 플레이어 API가 실패하면 기존 testexecutions API 시도
        url = "https://api.zephyrscale.smartbear.com/v2/testexecutions"
        
        # 여러 파라미터 조합 시도 (가장 일반적인 것부터)
        param_combinations = [
            {"testCycle": cycle_id, "maxResults": limit, "startAt": skip},
            {"testCycleId": cycle_id, "maxResults": limit, "startAt": skip},
            {"cycleId": cycle_id, "maxResults": limit, "startAt": skip},
            {"cycle": cycle_id, "maxResults": limit, "startAt": skip}
        ]
        
        for params in param_combinations:
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                executions_data = response.json()
                
                # API 응답을 내부 형식으로 변환
                if isinstance(executions_data, dict):
                    if "values" in executions_data:
                        values = executions_data.get("values", [])
                        return values
                elif isinstance(executions_data, list):
                    return executions_data
        
        return []
            
    except Exception:
        return []


def get_cycle_test_results_summary(cycle_id):
    """사이클의 테스트 결과 요약 정보 조회"""
    try:
        # 1. 먼저 테스트 실행 결과를 여러 방법으로 조회
        executions = []
        
        # 방법 1: 기존 함수 사용
        executions = get_zephyr_cycle_executions(cycle_id, limit=1000)
        if not isinstance(executions, list):
            executions = []
        
        # 방법 2: 실행 결과가 없으면 직접 API 호출로 다시 시도
        if len(executions) == 0:
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
            
            if zephyr_api_token:
                try:
                    headers = {
                        "Authorization": f"Bearer {zephyr_api_token}",
                        "Accept": "application/json"
                    }
                    
                    # 다양한 실행 결과 조회 API 시도 (작동하는 API를 우선순위로)
                    execution_apis = [
                        f"https://api.zephyrscale.smartbear.com/v2/testexecutions?cycleId={cycle_id}&maxResults=1000",  # 이 API가 올바른 결과 반환
                        f"https://api.zephyrscale.smartbear.com/v2/testexecutions?testCycle={cycle_id}&maxResults=1000",
                        f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}/testexecutions?maxResults=1000",
                        f"https://api.zephyrscale.smartbear.com/v2/testexecutions?cycle={cycle_id}&maxResults=1000"
                    ]
                    
                    for i, api_url in enumerate(execution_apis):
                        try:
                            response = requests.get(api_url, headers=headers, timeout=30, verify=False)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                if isinstance(data, dict):
                                    if "values" in data:
                                        potential_executions = data.get("values", [])
                                        if len(potential_executions) > 0:
                                            executions = potential_executions
                                            break
                                elif isinstance(data, list):
                                    if len(data) > 0:
                                        executions = data
                                        break
                        except Exception:
                            continue
                            
                except Exception:
                    pass
        
        # 3. 실행 결과가 있는 경우 통계 계산
        if len(executions) > 0:
            # 통계 계산
            total_tests = len(executions)
            passed_tests = 0
            failed_tests = 0
            blocked_tests = 0
            not_executed_tests = 0
            
            test_results = []
            
            for i, execution in enumerate(executions):
                try:
                    # 첫 번째 실행 결과의 전체 구조를 디버깅으로 출력
                    if i == 0:
                        st.info(f"🔍 [디버깅] 첫 번째 실행 결과 전체 구조:")
                        st.json(execution)
                    
                    # 실행 상태 추출 (다양한 필드명 지원)
                    status_name = "Not Executed"
                    found_status_field = None
                    
                    # 여러 가능한 상태 필드 확인
                    status_fields = [
                        "testExecutionStatus",
                        "executionStatus", 
                        "status",
                        "result",
                        "testResult",
                        "statusName",
                        "resultStatus"
                    ]
                    
                    for field in status_fields:
                        if execution.get(field):
                            status_obj = execution.get(field)
                            if isinstance(status_obj, dict):
                                if status_obj.get("name"):
                                    status_name = status_obj.get("name")
                                    found_status_field = f"{field}.name"
                                    break
                                elif status_obj.get("status"):
                                    status_name = status_obj.get("status")
                                    found_status_field = f"{field}.status"
                                    break
                            elif isinstance(status_obj, str):
                                status_name = status_obj
                                found_status_field = field
                                break
                    
                    # 첫 번째 실행 결과의 상태 정보 디버깅
                    if i == 0:
                        st.info(f"🔍 [디버깅] 상태 추출 결과: '{status_name}' (필드: {found_status_field})")
                        
                        # 모든 가능한 상태 필드 값 출력
                        for field in status_fields:
                            if execution.get(field):
                                st.info(f"🔍 [디버깅] {field}: {execution.get(field)}")
                    
                    # 상태별 카운트 (대소문자 무시하고 다양한 표현 지원)
                    status_lower = status_name.lower()
                    if status_lower in ["pass", "passed", "success", "successful"]:
                        passed_tests += 1
                    elif status_lower in ["fail", "failed", "failure", "error"]:
                        failed_tests += 1
                    elif status_lower in ["blocked", "block", "skip", "skipped"]:
                        blocked_tests += 1
                    else:
                        not_executed_tests += 1
                    
                    # 처음 5개 실행 결과의 상태 분류 디버깅
                    if i < 5:
                        st.info(f"🔍 [디버깅] 실행 결과 {i+1}: '{status_name}' → 분류: {'Pass' if status_lower in ['pass', 'passed', 'success', 'successful'] else 'Fail' if status_lower in ['fail', 'failed', 'failure', 'error'] else 'Blocked' if status_lower in ['blocked', 'block', 'skip', 'skipped'] else 'Not Executed'}")
                    
                    # 테스트 케이스 정보 추출
                    test_case = execution.get("testCase", {})
                    test_case_name = "Unknown Test"
                    test_case_key = "N/A"
                    
                    if isinstance(test_case, dict):
                        test_case_name = test_case.get("name", "Unknown Test")
                        test_case_key = test_case.get("key", "N/A")
                    
                    # 실행자 정보 추출
                    executed_by = "Unknown"
                    executor_fields = ["executedBy", "executor", "assignee", "user"]
                    
                    for field in executor_fields:
                        if execution.get(field):
                            executed_by_info = execution.get(field)
                            if isinstance(executed_by_info, dict):
                                executed_by = executed_by_info.get("displayName", executed_by_info.get("name", "Unknown"))
                                break
                            elif isinstance(executed_by_info, str):
                                executed_by = executed_by_info
                                break
                    
                    # 실행 날짜 추출
                    executed_on = "N/A"
                    date_fields = ["executedOn", "executionDate", "completedDate", "updatedOn"]
                    
                    for field in date_fields:
                        if execution.get(field):
                            executed_on = str(execution.get(field))
                            break
                    
                    test_result = {
                        "test_case_key": test_case_key,
                        "test_case_name": test_case_name,
                        "status": status_name,
                        "executed_by": executed_by,
                        "executed_on": executed_on,
                        "comment": execution.get("comment", execution.get("notes", ""))
                    }
                    test_results.append(test_result)
                    
                except Exception:
                    # 개별 실행 결과 처리 실패 시 건너뛰기
                    continue
            
            executed_tests = passed_tests + failed_tests + blocked_tests
            
            # 비율 계산
            pass_rate = (passed_tests / executed_tests * 100) if executed_tests > 0 else 0.0
            execution_rate = (executed_tests / total_tests * 100) if total_tests > 0 else 0.0
            
            return {
                "total_tests": total_tests,
                "executed_tests": executed_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "blocked_tests": blocked_tests,
                "not_executed_tests": not_executed_tests,
                "pass_rate": round(pass_rate, 1),
                "execution_rate": round(execution_rate, 1),
                "test_results": test_results
            }
        
        # 4. 실행 결과가 없는 경우, 사이클에 할당된 테스트 케이스 직접 조회
        if len(executions) == 0:
            # 직접 API 호출로 테스트 케이스 조회
            import os
            from dotenv import load_dotenv
            
            try:
                load_dotenv()
                zephyr_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
                
                if not zephyr_api_token:
                    return {
                        "total_tests": 0,
                        "executed_tests": 0,
                        "passed_tests": 0,
                        "failed_tests": 0,
                        "blocked_tests": 0,
                        "not_executed_tests": 0,
                        "pass_rate": 0.0,
                        "execution_rate": 0.0,
                        "test_results": []
                    }
                
                headers = {
                    "Authorization": f"Bearer {zephyr_api_token}",
                    "Accept": "application/json"
                }
                
                # Zephyr Scale Cloud API 공식 문서에 따른 올바른 엔드포인트들
                api_endpoints = [
                    # 1. 테스트 사이클에 연결된 테스트 실행 결과 조회 (공식 방법)
                    f"https://api.zephyrscale.smartbear.com/v2/testexecutions?testCycle={cycle_id}",
                    # 2. 테스트 사이클 상세 정보 조회 (통계 포함)
                    f"https://api.zephyrscale.smartbear.com/v2/testcycles/{cycle_id}",
                    # 3. 테스트 케이스를 사이클 ID로 필터링하여 조회
                    f"https://api.zephyrscale.smartbear.com/v2/testcases?testCycle={cycle_id}",
                ]
                
                for i, url in enumerate(api_endpoints):
                    try:
                        response = requests.get(url, headers=headers, params={"maxResults": 100}, timeout=30, verify=False)
                        
                        if response.status_code == 200:
                            test_cases_data = response.json()
                            
                            if isinstance(test_cases_data, dict):
                                # values 키 확인
                                if "values" in test_cases_data:
                                    test_cases = test_cases_data.get("values", [])
                                    if len(test_cases) > 0:
                                        return {
                                            "total_tests": len(test_cases),
                                            "executed_tests": 0,
                                            "passed_tests": 0,
                                            "failed_tests": 0,
                                            "blocked_tests": 0,
                                            "not_executed_tests": len(test_cases),
                                            "pass_rate": 0.0,
                                            "execution_rate": 0.0,
                                            "test_results": [],
                                            "assigned_test_cases": test_cases[:10]
                                        }
                                
                                # testCases 키 확인
                                elif "testCases" in test_cases_data:
                                    test_cases = test_cases_data.get("testCases", [])
                                    if len(test_cases) > 0:
                                        return {
                                            "total_tests": len(test_cases),
                                            "executed_tests": 0,
                                            "passed_tests": 0,
                                            "failed_tests": 0,
                                            "blocked_tests": 0,
                                            "not_executed_tests": len(test_cases),
                                            "pass_rate": 0.0,
                                            "execution_rate": 0.0,
                                            "test_results": [],
                                            "assigned_test_cases": test_cases[:10]
                                        }
                                
                                # 사이클 상세 정보인 경우 (두 번째 API)
                                elif i == 1:  # 사이클 상세 API
                                    # 통계 정보 확인
                                    if "testExecutions" in test_cases_data:
                                        executions_info = test_cases_data.get("testExecutions", {})
                                        total_tests = executions_info.get("total", 0)
                                        if total_tests > 0:
                                            return {
                                                "total_tests": total_tests,
                                                "executed_tests": 0,
                                                "passed_tests": 0,
                                                "failed_tests": 0,
                                                "blocked_tests": 0,
                                                "not_executed_tests": total_tests,
                                                "pass_rate": 0.0,
                                                "execution_rate": 0.0,
                                                "test_results": []
                                            }
                            
                            elif isinstance(test_cases_data, list):
                                if len(test_cases_data) > 0:
                                    return {
                                        "total_tests": len(test_cases_data),
                                        "executed_tests": 0,
                                        "passed_tests": 0,
                                        "failed_tests": 0,
                                        "blocked_tests": 0,
                                        "not_executed_tests": len(test_cases_data),
                                        "pass_rate": 0.0,
                                        "execution_rate": 0.0,
                                        "test_results": [],
                                        "assigned_test_cases": test_cases_data[:10]
                                    }
                    
                    except Exception:
                        continue
                
            except Exception:
                pass
            
            # 할당된 테스트 케이스도 없는 경우
            return {
                "total_tests": 0,
                "executed_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "blocked_tests": 0,
                "not_executed_tests": 0,
                "pass_rate": 0.0,
                "execution_rate": 0.0,
                "test_results": []
            }
        
        # 통계 계산
        total_tests = len(executions)
        passed_tests = 0
        failed_tests = 0
        blocked_tests = 0
        not_executed_tests = 0
        
        test_results = []
        
        for execution in executions:
            try:
                # 실행 상태 추출
                status = execution.get("testExecutionStatus", {})
                status_name = "Not Executed"
                
                if isinstance(status, dict):
                    status_name = status.get("name", "Not Executed")
                elif isinstance(status, str):
                    status_name = status
                
                # 상태별 카운트
                if status_name in ["Pass", "Passed", "PASS"]:
                    passed_tests += 1
                elif status_name in ["Fail", "Failed", "FAIL"]:
                    failed_tests += 1
                elif status_name in ["Blocked", "BLOCKED"]:
                    blocked_tests += 1
                else:
                    not_executed_tests += 1
                
                # 테스트 케이스 정보 추출
                test_case = execution.get("testCase", {})
                test_case_name = "Unknown Test"
                test_case_key = "N/A"
                
                if isinstance(test_case, dict):
                    test_case_name = test_case.get("name", "Unknown Test")
                    test_case_key = test_case.get("key", "N/A")
                
                # 실행자 정보 추출
                executed_by = "Unknown"
                if execution.get("executedBy"):
                    executed_by_info = execution.get("executedBy")
                    if isinstance(executed_by_info, dict):
                        executed_by = executed_by_info.get("displayName", "Unknown")
                    elif isinstance(executed_by_info, str):
                        executed_by = executed_by_info
                
                # 실행 날짜 추출
                executed_on = execution.get("executedOn", "N/A")
                
                test_result = {
                    "test_case_key": test_case_key,
                    "test_case_name": test_case_name,
                    "status": status_name,
                    "executed_by": executed_by,
                    "executed_on": executed_on,
                    "comment": execution.get("comment", "")
                }
                test_results.append(test_result)
                
            except Exception as e:
                # 개별 실행 결과 처리 실패 시 건너뛰기
                continue
        
        executed_tests = passed_tests + failed_tests + blocked_tests
        
        # 비율 계산
        pass_rate = (passed_tests / executed_tests * 100) if executed_tests > 0 else 0.0
        execution_rate = (executed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        return {
            "total_tests": total_tests,
            "executed_tests": executed_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "blocked_tests": blocked_tests,
            "not_executed_tests": not_executed_tests,
            "pass_rate": round(pass_rate, 1),
            "execution_rate": round(execution_rate, 1),
            "test_results": test_results
        }
        
    except Exception as e:
        st.error(f"사이클 테스트 결과 요약 조회 실패: {str(e)}")
        return {
            "total_tests": 0,
            "executed_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "blocked_tests": 0,
            "not_executed_tests": 0,
            "pass_rate": 0.0,
            "execution_rate": 0.0,
            "test_results": []
        }


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


# Task와 Cycle 연동 관련 API 함수들
@st.cache_data(ttl=1)  # 1초 캐시로 단축 (실시간성 극대화)
def get_task_linked_cycles(task_id):
    """Task에 연결된 Zephyr 테스트 사이클 목록 조회 - 백엔드 서버 없이 임시 구현"""
    try:
        # 백엔드 서버가 없는 경우를 위한 임시 구현
        # 실제로는 데이터베이스나 파일에서 연결 정보를 조회해야 함
        # 현재는 빈 배열을 반환하여 모든 사이클이 연결 가능한 것으로 표시
        
        # 백엔드 API 호출 시도
        endpoint = f"/tasks/{task_id}/linked-cycles"
        result = api_call(endpoint)
        
        # API 응답 타입 검증
        if result is None:
            return []
        elif isinstance(result, list):
            return result
        elif isinstance(result, dict):
            # 딕셔너리 응답인 경우 success 필드 확인
            if result.get("success", True):
                # 데이터가 있는 경우 반환, 없으면 빈 배열
                return result.get("data", result.get("cycles", []))
            else:
                # API 에러인 경우 빈 배열 반환
                return []
        elif isinstance(result, str):
            # 문자열 응답인 경우 (에러 메시지 등) 빈 배열 반환
            return []
        else:
            # 예상하지 못한 타입인 경우 빈 배열 반환
            return []
            
    except Exception as e:
        # 백엔드 서버 연결 실패 시 빈 배열 반환 (에러 메시지 없이)
        # 이렇게 하면 모든 사이클이 연결 가능한 것으로 표시됨
        return []

@st.cache_data(ttl=60)  # 1분 캐시
def get_cycles_for_project(project_key):
    """프로젝트의 모든 Zephyr 테스트 사이클 조회 (간소화된 정보) - 사용하지 않음, get_available_cycles_for_task 사용"""
    # 이 함수는 더 이상 사용하지 않음
    # get_available_cycles_for_task 함수가 모든 프로젝트에서 사이클을 조회하므로 이 함수는 빈 배열 반환
    return []

def link_task_to_cycle(task_id, cycle_id, cycle_name="", linked_by="QA팀", link_reason=""):
    """Task와 Zephyr 테스트 사이클 연결"""
    try:
        # URL 파라미터로 전달하도록 수정 (사이클 이름 추가)
        import urllib.parse
        encoded_cycle_name = urllib.parse.quote(cycle_name) if cycle_name else ""
        encoded_link_reason = urllib.parse.quote(link_reason) if link_reason else ""
        
        params = f"?task_id={task_id}&cycle_id={cycle_id}&cycle_name={encoded_cycle_name}&linked_by={linked_by}&link_reason={encoded_link_reason}"
        result = api_call(f"/tasks/link-cycle{params}", method="POST")
        
        # API 응답 타입 검증
        if result is None:
            return {"success": False, "message": "API 응답이 없습니다."}
        elif isinstance(result, dict):
            if result.get("success", True):
                # 연결 후 캐시 클리어
                st.cache_data.clear()
            return result
        elif isinstance(result, str):
            # 문자열 응답인 경우 에러로 처리
            return {"success": False, "message": result}
        else:
            # 예상하지 못한 타입인 경우
            return {"success": False, "message": f"예상하지 못한 응답 타입: {type(result)}"}
            
    except Exception as e:
        st.error(f"Task-Cycle 연결 실패: {str(e)}")
        return {"success": False, "message": str(e)}

def unlink_task_from_cycle(task_id, cycle_id):
    """Task와 Zephyr 테스트 사이클 연결 해제"""
    try:
        result = api_call(f"/tasks/{task_id}/unlink-cycle/{cycle_id}", method="DELETE")
        
        # API 응답 타입 검증
        if result is None:
            return {"success": False, "message": "API 응답이 없습니다."}
        elif isinstance(result, dict):
            if result.get("success", True):
                # 연결 해제 후 캐시 클리어
                st.cache_data.clear()
            return result
        elif isinstance(result, str):
            # 문자열 응답인 경우 에러로 처리
            return {"success": False, "message": result}
        else:
            # 예상하지 못한 타입인 경우
            return {"success": False, "message": f"예상하지 못한 응답 타입: {type(result)}"}
            
    except Exception as e:
        st.error(f"Task-Cycle 연결 해제 실패: {str(e)}")
        return {"success": False, "message": str(e)}

def get_available_cycles_for_task(task_id, project_key=None):
    """Task에 연결 가능한 사이클 목록 조회 (이미 연결된 사이클 제외) - Zephyr 관리와 동일한 로직 사용"""
    try:
        # 프로젝트 키가 없으면 빈 배열 반환
        if not project_key:
            return []
        
        # 1. 먼저 Zephyr 프로젝트 목록에서 해당 프로젝트 ID 찾기
        zephyr_projects = get_zephyr_projects()
        project_id = None
        
        if isinstance(zephyr_projects, list):
            for project in zephyr_projects:
                if project.get('key') == project_key:
                    project_id = project.get('id')
                    break
        
        if not project_id:
            st.warning(f"⚠️ Zephyr에서 프로젝트 '{project_key}'를 찾을 수 없습니다.")
            return []
        
        # 2. Zephyr 관리와 동일한 방식으로 테스트 사이클 조회 (캐시 클리어 후 최신 데이터)
        st.cache_data.clear()  # 최신 데이터를 위해 캐시 클리어
        all_cycles = get_zephyr_test_cycles(project_id, limit=100)  # Zephyr 관리와 동일한 limit
        
        if not isinstance(all_cycles, list):
            st.info(f"ℹ️ '{project_key}' 프로젝트에서 사이클을 조회할 수 없습니다.")
            return []
        
        if len(all_cycles) == 0:
            st.info(f"ℹ️ '{project_key}' 프로젝트에는 테스트 사이클이 없습니다.")
            return []
        
        # 동기화 시간 기록 (Zephyr 관리와 동일)
        import datetime
        sync_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 각 사이클에 동기화 시간 추가
        for cycle in all_cycles:
            cycle['last_sync'] = sync_time
        
        # 3. 이미 연결된 사이클 목록 조회
        linked_cycles = get_task_linked_cycles(task_id)
        linked_cycle_ids = []
        
        if isinstance(linked_cycles, list):
            for linked_cycle in linked_cycles:
                if isinstance(linked_cycle, dict) and linked_cycle.get('id'):
                    linked_cycle_ids.append(str(linked_cycle.get('id')))
        
        # 4. 연결되지 않은 사이클만 필터링
        available_cycles = []
        for cycle in all_cycles:
            if isinstance(cycle, dict) and cycle.get('id'):
                cycle_id = str(cycle.get('id'))
                if cycle_id not in linked_cycle_ids:
                    available_cycles.append(cycle)
        
        # 5. Zephyr 관리와 동일한 정렬 (생성순 - 최신순)
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
        
        available_cycles = sorted(available_cycles, key=extract_cycle_number, reverse=True)
        
        # 디버깅 정보 표시
        st.info(f"🔍 '{project_key}' 프로젝트: 전체 {len(all_cycles)}개 사이클 중 {len(available_cycles)}개 연결 가능")
        
        return available_cycles
            
    except Exception as e:
        st.error(f"연결 가능한 사이클 조회 실패: {str(e)}")
        return []

def sync_zephyr_cycles_from_api(project_key):
    """Zephyr Scale API에서 실제 테스트 사이클 데이터를 동기화"""
    try:
        result = api_call(f"/zephyr/sync-cycles/{project_key}", method="POST")
        
        if result and result.get("success", True):
            # 동기화 후 캐시 클리어
            st.cache_data.clear()
        
        return result
        
    except Exception as e:
        st.error(f"Zephyr 사이클 동기화 실패: {str(e)}")
        return {"success": False, "message": str(e)}
