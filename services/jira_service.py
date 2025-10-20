"""
Jira API 서비스
"""
import logging
import base64
from typing import List, Dict, Optional, Tuple
import requests
import urllib3
from config.settings import settings

# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class JiraService:
    """Jira API 서비스 클래스"""
    
    def __init__(self):
        self.server_url = settings.JIRA_SERVER.rstrip('/')
        self.username = settings.JIRA_USERNAME
        self.api_token = settings.JIRA_API_TOKEN
        self.configured = settings.is_jira_configured
        
        if self.configured:
            credentials = f"{self.username}:{self.api_token}"
            self.auth = base64.b64encode(credentials.encode()).decode()
            logger.info(f"Jira 서비스 초기화 완료: {self.server_url}")
        else:
            logger.warning("Jira 설정이 불완전합니다.")
    
    def get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        return {
            "Authorization": f"Basic {self.auth}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def test_connection(self) -> Tuple[bool, str]:
        """Jira 연결 테스트"""
        if not self.configured:
            return False, "Jira 설정이 불완전합니다."
        
        try:
            logger.info(f"Jira 연결 테스트 시작: {self.server_url}")
            
            # API 토큰 길이 확인
            if len(self.api_token) < 50:
                return False, "API 토큰이 올바르지 않습니다. 새로운 토큰을 생성해주세요."
            
            response = requests.get(
                f"{self.server_url}/rest/api/3/myself",
                headers=self.get_headers(),
                timeout=settings.JIRA_CONNECTION_TIMEOUT,
                verify=False
            )
            
            logger.info(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                display_name = user_info.get('displayName', 'Unknown')
                logger.info(f"✅ Jira 연결 성공! 사용자: {display_name}")
                return True, f"연결 성공: {display_name}"
            elif response.status_code == 401:
                logger.error("❌ Jira 인증 실패")
                return False, "인증 실패: API 토큰이 만료되었거나 올바르지 않습니다."
            elif response.status_code == 403:
                logger.error("❌ Jira 권한 없음")
                return False, "권한 없음: Jira 프로젝트에 대한 접근 권한이 없습니다."
            else:
                logger.error(f"❌ Jira 연결 실패: HTTP {response.status_code}")
                return False, f"연결 실패: HTTP {response.status_code}"
                
        except requests.exceptions.SSLError as e:
            logger.error(f"❌ SSL 인증서 오류: {str(e)}")
            return False, "SSL 인증서 오류: 회사 네트워크 설정을 확인해주세요"
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ 네트워크 연결 오류: {str(e)}")
            return False, f"네트워크 연결 오류: 서버 URL '{self.server_url}'을 확인해주세요"
        except requests.exceptions.Timeout as e:
            logger.error(f"❌ 연결 시간 초과: {str(e)}")
            return False, "연결 시간 초과: 네트워크 상태를 확인해주세요"
        except Exception as e:
            logger.error(f"❌ 연결 오류: {str(e)}")
            return False, f"연결 오류: {str(e)}"
    
    def get_projects(self) -> List[Dict]:
        """Jira 프로젝트 목록 가져오기 - 모든 프로젝트 조회 (페이지네이션 지원)"""
        if not self.configured:
            return []
        
        try:
            logger.info("Jira 프로젝트 조회 시작 (모든 프로젝트)")
            
            all_projects = []
            start_at = 0
            max_results = 100  # 한 번에 가져올 최대 개수
            
            while True:
                # API v3에서는 페이지네이션 지원
                params = {
                    "expand": "description,lead,issueTypes,url,projectKeys",
                    "maxResults": max_results,
                    "startAt": start_at
                }
                
                response = requests.get(
                    f"{self.server_url}/rest/api/3/project/search",
                    headers=self.get_headers(),
                    params=params,
                    timeout=settings.JIRA_QUICK_TIMEOUT,
                    verify=False
                )
                
                if response.status_code == 200:
                    result = response.json()
                    projects = result.get("values", [])
                    total = result.get("total", 0)
                    
                    all_projects.extend(projects)
                    logger.info(f"📄 페이지 {start_at//max_results + 1}: {len(projects)}개 프로젝트 조회 (전체 {total}개 중 {len(all_projects)}개 완료)")
                    
                    # 더 이상 가져올 프로젝트가 없으면 종료
                    if len(projects) < max_results or len(all_projects) >= total:
                        break
                    
                    start_at += max_results
                    
                else:
                    # v3 search API 실패 시 기본 API로 폴백 (페이지네이션 없음)
                    logger.warning(f"v3 search API 실패 (HTTP {response.status_code}), 기본 API로 재시도")
                    response = requests.get(
                        f"{self.server_url}/rest/api/3/project",
                        headers=self.get_headers(),
                        timeout=settings.JIRA_QUICK_TIMEOUT,
                        verify=False
                    )
                    
                    if response.status_code == 200:
                        projects = response.json()
                        logger.info(f"✅ Jira 프로젝트 {len(projects)}개 조회 성공 (기본 API - 페이지네이션 없음)")
                        return projects
                    else:
                        error_msg = self._parse_error_response(response)
                        logger.error(f"❌ 프로젝트 조회 실패: HTTP {response.status_code} - {error_msg}")
                        return all_projects if all_projects else []
            
            logger.info(f"✅ Jira 프로젝트 총 {len(all_projects)}개 조회 완료")
            return all_projects
                
        except Exception as e:
            logger.error(f"❌ 프로젝트 조회 오류: {str(e)}")
            return []
    
    def get_project_issue_count(self, project_key: str) -> int:
        """프로젝트의 이슈 수 조회 - 동기화 전에는 간단한 조회만 수행"""
        if not self.configured:
            return 0
        
        try:
            logger.info(f"프로젝트 {project_key} 이슈 수 조회 (간단 모드)")
            
            # 동기화 전에는 이슈 데이터 없이 총 개수만 조회
            params = {
                "jql": f'project = "{project_key}"',
                "maxResults": 0,  # 이슈 데이터는 필요없고 total만 필요
                "fields": "key"
            }
            
            response = requests.get(
                f"{self.server_url}/rest/api/3/search/jql",
                headers=self.get_headers(),
                params=params,
                timeout=settings.JIRA_QUICK_TIMEOUT,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                total = result.get("total", 0)
                logger.info(f"프로젝트 {project_key}: {total}개 이슈 확인")
                return total
            elif response.status_code == 400:
                # JQL 구문 오류 시 다른 방식으로 시도
                logger.warning(f"프로젝트 {project_key}: JQL 오류, 기본 방식으로 재시도")
                params = {
                    "jql": f'project = {project_key}',
                    "maxResults": 0,
                    "fields": "key"
                }
                
                response = requests.get(
                    f"{self.server_url}/rest/api/3/search/jql",
                    headers=self.get_headers(),
                    params=params,
                    timeout=settings.JIRA_QUICK_TIMEOUT,
                    verify=False
                )
                
                if response.status_code == 200:
                    result = response.json()
                    total = result.get("total", 0)
                    logger.info(f"프로젝트 {project_key}: {total}개 이슈 확인 (재시도)")
                    return total
                else:
                    logger.warning(f"프로젝트 {project_key}: 이슈 수 조회 실패 (HTTP {response.status_code})")
                    return 0
            else:
                logger.warning(f"프로젝트 {project_key}: 이슈 수 조회 실패 (HTTP {response.status_code})")
                return 0
                
        except requests.exceptions.Timeout as e:
            logger.warning(f"프로젝트 {project_key} 이슈 수 조회 시간 초과: {str(e)}")
            return 0
        except Exception as e:
            logger.warning(f"프로젝트 {project_key} 이슈 수 조회 실패: {str(e)}")
            return 0
    
    def get_issues(self, project_key: str, limit: int = None, max_results: int = None, quick_mode: bool = False) -> List[Dict]:
        """Jira 이슈 목록 가져오기 - 성능 최적화된 조회"""
        if not self.configured:
            return []
        
        # quick_mode일 때는 최초 1000개만 빠르게 가져오기
        if quick_mode:
            target_limit = 1000
            logger.info(f"Jira 이슈 조회: 프로젝트 {project_key} (빠른 모드 - 최초 1000개)")
        elif limit is not None:
            target_limit = limit
        elif max_results is not None:
            target_limit = max_results
        else:
            target_limit = None  # 무제한으로 설정
        
        try:
            if not quick_mode:
                logger.info(f"Jira 이슈 조회: 프로젝트 {project_key} (전체 모드)")
            
            # 프로젝트 존재 여부 먼저 확인
            project_exists = self._check_project_exists(project_key)
            if not project_exists:
                logger.error(f"❌ 프로젝트 {project_key}가 존재하지 않거나 접근할 수 없습니다.")
                return []
            
            # 최근 1년치 이슈 조회 (성능 최적화) - 우선순위 순
            jql_queries = [
                # 최근 1년 + 최신순 정렬 (가장 효율적)
                f'project = {project_key} AND updated >= -365d ORDER BY updated DESC',
                f'project = "{project_key}" AND updated >= -365d ORDER BY updated DESC',
                f'project = {project_key} AND created >= -365d ORDER BY created DESC',
                f'project = "{project_key}" AND created >= -365d ORDER BY created DESC',
                
                # 폴백: 6개월 기간 제한
                f'project = {project_key} AND updated >= -180d ORDER BY updated DESC',
                f'project = "{project_key}" AND updated >= -180d ORDER BY updated DESC',
                
                # 폴백: 3개월 기간 제한
                f'project = {project_key} AND updated >= -90d ORDER BY updated DESC',
                f'project = "{project_key}" AND updated >= -90d ORDER BY updated DESC',
                
                # 최종 폴백: 기간 제한 없음 (기존 방식)
                f'project = {project_key} ORDER BY updated DESC',
                f'project = "{project_key}" ORDER BY updated DESC',
            ]
            
            last_error_details = None
            
            for i, jql in enumerate(jql_queries):
                try:
                    logger.info(f"JQL 시도 {i+1}: {jql}")
                    
                    # 페이지네이션으로 모든 이슈 가져오기
                    all_issues = []
                    start_at = 0
                    page_size = 100  # 한 번에 가져올 페이지 크기
                    
                    while True:
                        params = {
                            "jql": jql,
                            "maxResults": page_size,
                            "startAt": start_at,
                            "fields": "key,summary,description,status,assignee,priority,created,updated,issuetype,reporter"
                        }
                        
                        # GET 방식으로 시도 (API v3 사용 - 새로운 엔드포인트)
                        response = requests.get(
                            f"{self.server_url}/rest/api/3/search/jql",
                            headers=self.get_headers(),
                            params=params,
                            timeout=settings.JIRA_SYNC_TIMEOUT,
                            verify=False
                        )
                        
                        # GET 실패 시 POST 방식으로 재시도
                        if response.status_code == 405:
                            logger.info(f"GET 방식 실패, POST 방식으로 재시도: {jql}")
                            post_data = {
                                "jql": jql,
                                "maxResults": page_size,
                                "startAt": start_at,
                                "fields": ["key", "summary", "description", "status", "assignee", "priority", "created", "updated", "issuetype", "reporter"]
                            }
                            
                            response = requests.post(
                                f"{self.server_url}/rest/api/3/search/jql",
                                headers=self.get_headers(),
                                json=post_data,
                                timeout=settings.JIRA_SYNC_TIMEOUT,
                                verify=False
                            )
                        
                        logger.info(f"응답 상태: HTTP {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            page_issues = result.get("issues", [])
                            total = result.get("total", 0)
                            
                            all_issues.extend(page_issues)
                            logger.info(f"📄 페이지 {start_at//page_size + 1}: {len(page_issues)}개 이슈 조회 (전체 {total}개 중 {len(all_issues)}개 완료)")
                            
                            # 더 이상 가져올 이슈가 없으면 종료
                            if len(page_issues) < page_size:
                                break
                            
                            # total이 정확하고 도달했으면 종료
                            if total > 0 and len(all_issues) >= total:
                                break
                            
                            # 사용자 제한이 있고 도달했으면 종료
                            if target_limit and len(all_issues) >= target_limit:
                                all_issues = all_issues[:target_limit]
                                logger.info(f"사용자 제한 {target_limit}개에 도달하여 조회 종료")
                                break
                            
                            # 안전장치: 무제한 조회 시 최대 10,000개로 제한
                            if target_limit is None and len(all_issues) >= 10000:
                                logger.warning(f"안전장치 발동: 무제한 조회에서 10,000개 도달하여 조회 종료")
                                break
                            
                            start_at += page_size
                        else:
                            # 첫 페이지 실패 시 다른 JQL로 시도
                            if start_at == 0:
                                break
                            else:
                                # 중간 페이지 실패 시 현재까지 수집한 이슈 반환
                                logger.warning(f"페이지 {start_at//page_size + 1} 조회 실패, 현재까지 {len(all_issues)}개 이슈 반환")
                                break
                    
                    if all_issues:
                        logger.info(f"✅ Jira 이슈 총 {len(all_issues)}개 조회 성공")
                        
                        # 이슈 데이터 정규화
                        normalized_issues = []
                        for issue in all_issues:
                            normalized_issue = self._normalize_issue_data(issue)
                            normalized_issues.append(normalized_issue)
                        
                        logger.info(f"이슈 데이터 정규화 완료: {len(normalized_issues)}개")
                        return normalized_issues
                    elif response.status_code == 400:
                        error_msg = self._parse_error_response(response)
                        logger.warning(f"JQL 쿼리 오류 (400): {error_msg}")
                        last_error_details = f"JQL 구문 오류: {error_msg}"
                        continue
                    elif response.status_code == 410:
                        logger.warning(f"프로젝트 {project_key}가 비활성화되었거나 삭제됨 (410)")
                        last_error_details = f"프로젝트 {project_key}가 비활성화되었거나 삭제되었습니다."
                        # 410 에러의 경우 다른 쿼리도 실패할 가능성이 높으므로 조기 종료
                        if i >= 2:  # 몇 개 시도 후 종료
                            break
                        continue
                    elif response.status_code == 403:
                        logger.warning(f"프로젝트 {project_key}에 대한 권한 없음 (403)")
                        last_error_details = f"프로젝트 {project_key}에 대한 접근 권한이 없습니다."
                        continue
                    elif response.status_code == 404:
                        logger.warning(f"프로젝트 {project_key}를 찾을 수 없음 (404)")
                        last_error_details = f"프로젝트 {project_key}를 찾을 수 없습니다."
                        continue
                    else:
                        error_msg = self._parse_error_response(response)
                        logger.warning(f"이슈 조회 실패: HTTP {response.status_code} - {error_msg}")
                        last_error_details = f"HTTP {response.status_code}: {error_msg}"
                        continue
                        
                except Exception as query_error:
                    logger.warning(f"JQL 쿼리 {i+1} 실행 오류: {str(query_error)}")
                    last_error_details = f"쿼리 실행 오류: {str(query_error)}"
                    continue
            
            # 모든 쿼리 실패
            logger.error(f"❌ 프로젝트 {project_key}: 모든 JQL 쿼리 실패")
            if last_error_details:
                logger.error(f"마지막 오류 상세: {last_error_details}")
            return []
                
        except Exception as e:
            logger.error(f"❌ 이슈 조회 전체 오류: {str(e)}")
            return []
    
    def get_issue(self, issue_key: str) -> Optional[Dict]:
        """개별 이슈 조회"""
        if not self.configured:
            return None
        
        try:
            logger.info(f"개별 이슈 조회: {issue_key}")
            
            response = requests.get(
                f"{self.server_url}/rest/api/3/issue/{issue_key}",
                headers=self.get_headers(),
                params={
                    "fields": "key,summary,description,status,assignee,priority,created,updated,issuetype,reporter"
                },
                timeout=settings.JIRA_QUICK_TIMEOUT,
                verify=False
            )
            
            if response.status_code == 200:
                issue = response.json()
                normalized_issue = self._normalize_issue_data(issue)
                logger.info(f"✅ 이슈 {issue_key} 조회 성공")
                return normalized_issue
            else:
                logger.warning(f"이슈 {issue_key} 조회 실패: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"이슈 {issue_key} 조회 오류: {str(e)}")
            return None
    
    def _check_project_exists(self, project_key: str) -> bool:
        """프로젝트 존재 여부 확인"""
        try:
            response = requests.get(
                f"{self.server_url}/rest/api/3/project/{project_key}",
                headers=self.get_headers(),
                timeout=settings.JIRA_QUICK_TIMEOUT,
                verify=False
            )
            
            if response.status_code == 200:
                project_info = response.json()
                logger.info(f"프로젝트 {project_key} 확인됨: {project_info.get('name', 'Unknown')}")
                return True
            elif response.status_code == 404:
                logger.warning(f"프로젝트 {project_key}가 존재하지 않음")
                return False
            elif response.status_code == 403:
                logger.warning(f"프로젝트 {project_key}에 대한 접근 권한 없음")
                return False
            elif response.status_code == 410:
                logger.warning(f"프로젝트 {project_key}가 비활성화됨")
                return False
            else:
                logger.warning(f"프로젝트 {project_key} 확인 실패: HTTP {response.status_code}")
                return True  # 다른 오류의 경우 이슈 조회를 시도해볼 수 있도록 True 반환
                
        except Exception as e:
            logger.warning(f"프로젝트 {project_key} 존재 확인 오류: {str(e)}")
            return True  # 오류 시에도 이슈 조회를 시도해볼 수 있도록 True 반환
    
    def _parse_error_response(self, response) -> str:
        """에러 응답에서 상세 메시지 추출"""
        try:
            error_data = response.json()
            if 'errorMessages' in error_data and error_data['errorMessages']:
                return '; '.join(error_data['errorMessages'])
            elif 'errors' in error_data:
                errors = error_data['errors']
                if isinstance(errors, dict):
                    return '; '.join([f"{k}: {v}" for k, v in errors.items()])
                else:
                    return str(errors)
            else:
                return response.text[:200]
        except:
            return response.text[:200] if response.text else f"HTTP {response.status_code}"
    
    def get_alternative_projects(self, failed_project_key: str) -> List[Dict]:
        """실패한 프로젝트와 유사한 대안 프로젝트 찾기"""
        try:
            all_projects = self.get_projects()
            if not all_projects:
                return []
            
            alternatives = []
            failed_key_lower = failed_project_key.lower()
            
            for project in all_projects:
                project_key = project.get('key', '').lower()
                project_name = project.get('name', '').lower()
                
                # 키나 이름이 유사한 프로젝트 찾기
                if (failed_key_lower in project_key or 
                    project_key in failed_key_lower or
                    failed_key_lower in project_name or
                    any(word in project_name for word in failed_key_lower.split('-') if len(word) > 2)):
                    
                    # 이슈 수 확인
                    issue_count = self.get_project_issue_count(project.get('key', ''))
                    if issue_count > 0:
                        project['issue_count'] = issue_count
                        alternatives.append(project)
            
            # 이슈 수 기준으로 정렬
            alternatives.sort(key=lambda x: x.get('issue_count', 0), reverse=True)
            return alternatives[:5]  # 최대 5개만 반환
            
        except Exception as e:
            logger.warning(f"대안 프로젝트 검색 오류: {str(e)}")
            return []
    
    def diagnose_project_issue(self, project_key: str) -> Dict[str, any]:
        """프로젝트 문제 진단"""
        diagnosis = {
            "project_key": project_key,
            "exists": False,
            "accessible": False,
            "has_issues": False,
            "issue_count": 0,
            "error_details": [],
            "recommendations": [],
            "alternatives": []
        }
        
        try:
            # 1. 프로젝트 존재 확인
            project_exists = self._check_project_exists(project_key)
            diagnosis["exists"] = project_exists
            
            if not project_exists:
                diagnosis["error_details"].append("프로젝트가 존재하지 않거나 접근할 수 없음")
                diagnosis["recommendations"].extend([
                    "Jira 관리자에게 프로젝트 상태 확인",
                    "올바른 프로젝트 키 확인",
                    "프로젝트 접근 권한 요청"
                ])
                
                # 대안 프로젝트 찾기
                diagnosis["alternatives"] = self.get_alternative_projects(project_key)
                return diagnosis
            
            # 2. 이슈 수 확인
            issue_count = self.get_project_issue_count(project_key)
            diagnosis["issue_count"] = issue_count
            diagnosis["has_issues"] = issue_count > 0
            diagnosis["accessible"] = True
            
            if issue_count == 0:
                diagnosis["error_details"].append("프로젝트에 이슈가 없거나 조회 권한이 없음")
                diagnosis["recommendations"].extend([
                    "Jira 웹에서 직접 프로젝트 확인",
                    "이슈 조회 권한 확인",
                    "프로젝트에 실제 이슈가 있는지 확인"
                ])
            else:
                diagnosis["recommendations"].append(f"프로젝트에 {issue_count}개의 이슈가 있음을 확인")
            
            return diagnosis
            
        except Exception as e:
            diagnosis["error_details"].append(f"진단 중 오류 발생: {str(e)}")
            diagnosis["recommendations"].append("네트워크 연결 및 Jira 서버 상태 확인")
            return diagnosis
    
    def _normalize_issue_data(self, issue: Dict) -> Dict:
        """Jira 이슈 데이터를 정규화하여 프론트엔드에서 사용하기 쉽게 변환"""
        try:
            fields = issue.get('fields', {})
            
            # 기본 정보
            normalized = {
                'key': issue.get('key', ''),
                'id': issue.get('id', ''),
                'summary': fields.get('summary', 'No Summary'),
                'description': self.safe_description(fields.get('description')),
            }
            
            # 상태 정보
            status = fields.get('status', {})
            if isinstance(status, dict):
                normalized['status'] = status.get('name', 'Unknown')
                normalized['status_id'] = status.get('id', '')
            else:
                normalized['status'] = str(status) if status else 'Unknown'
                normalized['status_id'] = ''
            
            # 이슈 타입
            issuetype = fields.get('issuetype', {})
            if isinstance(issuetype, dict):
                normalized['issue_type'] = issuetype.get('name', 'Unknown')
                normalized['issue_type_id'] = issuetype.get('id', '')
            else:
                normalized['issue_type'] = str(issuetype) if issuetype else 'Unknown'
                normalized['issue_type_id'] = ''
            
            # 우선순위
            priority = fields.get('priority', {})
            if isinstance(priority, dict):
                normalized['priority'] = priority.get('name', 'Unknown')
                normalized['priority_id'] = priority.get('id', '')
            else:
                normalized['priority'] = str(priority) if priority else 'Unknown'
                normalized['priority_id'] = ''
            
            # 담당자
            assignee = fields.get('assignee', {})
            if isinstance(assignee, dict) and assignee:
                normalized['assignee'] = assignee.get('displayName', assignee.get('name', 'Unknown'))
                normalized['assignee_email'] = assignee.get('emailAddress', '')
            else:
                normalized['assignee'] = 'Unassigned'
                normalized['assignee_email'] = ''
            
            # 보고자
            reporter = fields.get('reporter', {})
            if isinstance(reporter, dict) and reporter:
                normalized['reporter'] = reporter.get('displayName', reporter.get('name', 'Unknown'))
                normalized['reporter_email'] = reporter.get('emailAddress', '')
            else:
                normalized['reporter'] = 'Unknown'
                normalized['reporter_email'] = ''
            
            # 날짜 정보
            normalized['created'] = fields.get('created', '')
            normalized['updated'] = fields.get('updated', '')
            
            # 날짜 포맷 정리 (ISO 형식을 간단한 형식으로 변환)
            for date_field in ['created', 'updated']:
                if normalized[date_field]:
                    try:
                        # ISO 형식에서 날짜 부분만 추출 (예: 2023-12-01T10:30:00.000+0900 -> 2023-12-01)
                        if 'T' in normalized[date_field]:
                            normalized[date_field] = normalized[date_field].split('T')[0]
                    except:
                        pass  # 변환 실패 시 원본 유지
            
            logger.debug(f"이슈 {normalized['key']} 정규화 완료")
            return normalized
            
        except Exception as e:
            logger.error(f"이슈 데이터 정규화 오류: {str(e)}")
            # 오류 발생 시 최소한의 정보라도 반환
            return {
                'key': issue.get('key', 'UNKNOWN'),
                'id': issue.get('id', ''),
                'summary': 'Error parsing issue data',
                'description': '',
                'status': 'Unknown',
                'status_id': '',
                'issue_type': 'Unknown',
                'issue_type_id': '',
                'priority': 'Unknown',
                'priority_id': '',
                'assignee': 'Unknown',
                'assignee_email': '',
                'reporter': 'Unknown',
                'reporter_email': '',
                'created': '',
                'updated': ''
            }
    
    def safe_description(self, desc_field) -> str:
        """description 필드를 안전하게 문자열로 변환"""
        if not desc_field:
            return ""
        
        # 문자열인 경우
        if isinstance(desc_field, str):
            return desc_field[:1000]
        
        # 딕셔너리인 경우 (Atlassian Document Format)
        if isinstance(desc_field, dict):
            if 'content' in desc_field:
                try:
                    text_parts = []
                    
                    def extract_text(content):
                        if isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    if item.get('type') == 'text':
                                        text_parts.append(item.get('text', ''))
                                    elif 'content' in item:
                                        extract_text(item['content'])
                    
                    extract_text(desc_field['content'])
                    return ' '.join(text_parts)[:1000]
                except:
                    return str(desc_field)[:1000]
            else:
                return str(desc_field)[:1000]
        
        # 기타 타입인 경우 문자열로 변환
        return str(desc_field)[:1000]


# 전역 Jira 서비스 인스턴스
jira_service = JiraService()
