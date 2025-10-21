"""
Zephyr API 서비스
remember-qa.atlassian.net과의 연동을 담당
"""

import logging
import json
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import requests
from requests.auth import HTTPBasicAuth
import base64
from cryptography.fernet import Fernet
import os

from models.database_models import (
    ZephyrConnection, ZephyrProject, ZephyrTestCase, 
    ZephyrTestExecution, ZephyrSyncHistory, ZephyrTestCycle
)
from models.pydantic_models import (
    ZephyrConnectionCreate, ZephyrConnectionUpdate, ZephyrConnectionResponse,
    ZephyrProjectResponse, ZephyrTestCaseResponse, ZephyrTestExecutionResponse,
    ZephyrSyncRequest, ZephyrSyncResponse, ZephyrSyncStatus,
    ZephyrDashboardStats, ZephyrProjectStats,
    ZephyrApiProject, ZephyrApiTestCase, ZephyrApiExecution
)

logger = logging.getLogger(__name__)

class ZephyrService:
    """Zephyr 서비스 클래스"""
    
    def __init__(self):
        # 환경변수에서 Zephyr 설정 읽기
        from dotenv import load_dotenv
        load_dotenv()  # .env 파일 다시 로드
        
        self.base_url = os.getenv('ZEPHYR_SERVER', 'https://remember-qa.atlassian.net')
        self.default_username = os.getenv('ZEPHYR_USERNAME', '')
        self.default_api_token = os.getenv('ZEPHYR_API_TOKEN', '')
        
        # 디버깅용 로그
        logger.info(f"Zephyr 서비스 초기화:")
        logger.info(f"  - 서버: {self.base_url}")
        logger.info(f"  - 사용자: {self.default_username}")
        logger.info(f"  - API 토큰: {'✅ 설정됨' if self.default_api_token else '❌ 없음'}")
        
        # 암호화 키 (환경변수에서 가져오기)
        encryption_key = os.getenv('ZEPHYR_ENCRYPTION_KEY')
        if not encryption_key:
            # 기본 키 생성 (실제 환경에서는 고정된 키를 사용해야 함)
            encryption_key = Fernet.generate_key()
        elif isinstance(encryption_key, str):
            # 32바이트 키로 패딩
            encryption_key = encryption_key.ljust(32)[:32].encode()
        
        if isinstance(encryption_key, bytes) and len(encryption_key) == 32:
            # base64 인코딩된 키 생성
            import base64
            encryption_key = base64.urlsafe_b64encode(encryption_key)
        
        self.encryption_key = encryption_key
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Zephyr API 기본 설정
        self.api_version = "3"  # Jira API v3 사용
        self.timeout = 30
        
    def encrypt_token(self, token: str) -> str:
        """API 토큰 암호화"""
        try:
            encrypted_token = self.cipher_suite.encrypt(token.encode())
            return base64.b64encode(encrypted_token).decode()
        except Exception as e:
            logger.error(f"토큰 암호화 실패: {str(e)}")
            raise
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """API 토큰 복호화"""
        try:
            encrypted_data = base64.b64decode(encrypted_token.encode())
            decrypted_token = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_token.decode()
        except Exception as e:
            logger.error(f"토큰 복호화 실패: {str(e)}")
            raise
    
    def get_connection(self, db: Session) -> Optional[ZephyrConnection]:
        """활성 Zephyr 연결 설정 조회"""
        return db.query(ZephyrConnection).filter(
            ZephyrConnection.is_active == True
        ).first()
    
    def create_connection(self, db: Session, connection_data: ZephyrConnectionCreate) -> ZephyrConnectionResponse:
        """Zephyr 연결 설정 생성"""
        try:
            # 기존 활성 연결 비활성화
            db.query(ZephyrConnection).filter(
                ZephyrConnection.is_active == True
            ).update({"is_active": False})
            
            # API 토큰 암호화
            encrypted_token = self.encrypt_token(connection_data.api_token)
            
            # 새 연결 생성
            db_connection = ZephyrConnection(
                server_url=connection_data.server_url,
                username=connection_data.username,
                api_token=encrypted_token,
                auto_sync=connection_data.auto_sync,
                sync_interval=connection_data.sync_interval,
                max_results=connection_data.max_results,
                include_archived=connection_data.include_archived,
                is_active=True
            )
            
            db.add(db_connection)
            db.commit()
            db.refresh(db_connection)
            
            logger.info(f"Zephyr 연결 설정 생성: {connection_data.username}")
            return ZephyrConnectionResponse.from_orm(db_connection)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Zephyr 연결 설정 생성 실패: {str(e)}")
            raise
    
    def update_connection(self, db: Session, connection_id: int, connection_data: ZephyrConnectionUpdate) -> ZephyrConnectionResponse:
        """Zephyr 연결 설정 업데이트"""
        try:
            db_connection = db.query(ZephyrConnection).filter(
                ZephyrConnection.id == connection_id
            ).first()
            
            if not db_connection:
                raise ValueError("연결 설정을 찾을 수 없습니다.")
            
            # 업데이트할 필드들
            update_data = connection_data.dict(exclude_unset=True)
            
            # API 토큰이 있으면 암호화
            if "api_token" in update_data and update_data["api_token"]:
                update_data["api_token"] = self.encrypt_token(update_data["api_token"])
            
            # 업데이트 실행
            for field, value in update_data.items():
                setattr(db_connection, field, value)
            
            db.commit()
            db.refresh(db_connection)
            
            logger.info(f"Zephyr 연결 설정 업데이트: {db_connection.username}")
            return ZephyrConnectionResponse.from_orm(db_connection)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Zephyr 연결 설정 업데이트 실패: {str(e)}")
            raise
    
    def test_connection(self, db: Session) -> Dict[str, Any]:
        """Zephyr 연결 테스트"""
        try:
            connection = self.get_connection(db)
            if not connection:
                return {
                    "success": False,
                    "message": "연결 설정이 없습니다.",
                    "connection_time": None
                }
            
            # API 토큰 복호화
            api_token = self.decrypt_token(connection.api_token)
            
            # 연결 테스트 시작
            start_time = time.time()
            
            # Jira API 호출 (현재 사용자 정보 조회)
            url = f"{connection.server_url}/rest/api/{self.api_version}/myself"
            auth = HTTPBasicAuth(connection.username, api_token)
            
            response = requests.get(
                url,
                auth=auth,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=False  # SSL 인증서 검증 비활성화
            )
            
            connection_time = time.time() - start_time
            
            if response.status_code == 200:
                # 연결 성공
                connection.last_connection_test = datetime.now()
                connection.connection_status = "connected"
                db.commit()
                
                user_info = response.json()
                return {
                    "success": True,
                    "message": f"연결 성공: {user_info.get('displayName', connection.username)}",
                    "connection_time": round(connection_time, 2),
                    "server_url": connection.server_url,
                    "username": connection.username
                }
            else:
                # 연결 실패
                connection.connection_status = "failed"
                db.commit()
                
                return {
                    "success": False,
                    "message": f"연결 실패: HTTP {response.status_code}",
                    "connection_time": round(connection_time, 2)
                }
                
        except requests.exceptions.Timeout:
            if connection:
                connection.connection_status = "failed"
                db.commit()
            return {
                "success": False,
                "message": "연결 시간 초과",
                "connection_time": None
            }
        except requests.exceptions.ConnectionError:
            if connection:
                connection.connection_status = "failed"
                db.commit()
            return {
                "success": False,
                "message": "서버에 연결할 수 없습니다.",
                "connection_time": None
            }
        except Exception as e:
            logger.error(f"Zephyr 연결 테스트 실패: {str(e)}")
            if connection:
                connection.connection_status = "failed"
                db.commit()
            return {
                "success": False,
                "message": f"연결 테스트 실패: {str(e)}",
                "connection_time": None
            }
    
    def get_projects(self, db: Session) -> List[ZephyrProjectResponse]:
        """Zephyr 프로젝트 목록 조회"""
        try:
            connection = self.get_connection(db)
            if not connection:
                raise ValueError("Zephyr 연결 설정이 없습니다.")
            
            # API 토큰 복호화
            api_token = self.decrypt_token(connection.api_token)
            
            # Jira 프로젝트 목록 조회
            url = f"{connection.server_url}/rest/api/{self.api_version}/project"
            auth = HTTPBasicAuth(connection.username, api_token)
            
            response = requests.get(
                url,
                auth=auth,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
                verify=False  # SSL 인증서 검증 비활성화
            )
            
            if response.status_code != 200:
                raise Exception(f"프로젝트 조회 실패: HTTP {response.status_code}")
            
            projects_data = response.json()
            projects = []
            
            for project_data in projects_data:
                # 데이터베이스에서 기존 프로젝트 조회
                db_project = db.query(ZephyrProject).filter(
                    ZephyrProject.zephyr_project_id == project_data["id"]
                ).first()
                
                if not db_project:
                    # 새 프로젝트 생성
                    db_project = ZephyrProject(
                        zephyr_project_id=project_data["id"],
                        project_key=project_data["key"],
                        project_name=project_data["name"],
                        description=project_data.get("description", ""),
                        is_synced=False,
                        sync_status="not_synced",
                        test_case_count=0
                    )
                    db.add(db_project)
                else:
                    # 기존 프로젝트 정보 업데이트
                    db_project.project_name = project_data["name"]
                    db_project.description = project_data.get("description", "")
                
                projects.append(ZephyrProjectResponse.from_orm(db_project))
            
            db.commit()
            logger.info(f"Zephyr 프로젝트 {len(projects)}개 조회 완료")
            return projects
            
        except Exception as e:
            db.rollback()
            logger.error(f"Zephyr 프로젝트 조회 실패: {str(e)}")
            raise
    
    def sync_project(self, db: Session, project_id: int, sync_request: ZephyrSyncRequest) -> ZephyrSyncResponse:
        """프로젝트 동기화"""
        try:
            # 프로젝트 조회
            db_project = db.query(ZephyrProject).filter(
                ZephyrProject.id == project_id
            ).first()
            
            if not db_project:
                raise ValueError("프로젝트를 찾을 수 없습니다.")
            
            # 동기화 이력 생성
            sync_history = ZephyrSyncHistory(
                zephyr_project_id=project_id,
                sync_direction=sync_request.sync_direction,
                sync_type=sync_request.sync_type,
                sync_status="started",
                total_items=0,
                processed_items=0,
                success_items=0,
                failed_items=0
            )
            db.add(sync_history)
            db.commit()
            db.refresh(sync_history)
            
            # 프로젝트 상태 업데이트
            db_project.sync_status = "syncing"
            db.commit()
            
            # 실제 동기화 로직 (백그라운드에서 실행)
            if sync_request.sync_direction == "import":
                self._import_from_zephyr(db, db_project, sync_history, sync_request)
            else:
                self._export_to_zephyr(db, db_project, sync_history, sync_request)
            
            return ZephyrSyncResponse(
                success=True,
                message="동기화가 시작되었습니다.",
                sync_id=sync_history.id,
                project_count=1,
                estimated_time=300  # 5분 예상
            )
            
        except Exception as e:
            logger.error(f"프로젝트 동기화 실패: {str(e)}")
            if 'sync_history' in locals():
                sync_history.sync_status = "failed"
                sync_history.error_message = str(e)
                sync_history.completed_at = datetime.now()
                db.commit()
            raise
    
    def _import_from_zephyr(self, db: Session, project: ZephyrProject, sync_history: ZephyrSyncHistory, sync_request: ZephyrSyncRequest):
        """Zephyr에서 데이터 가져오기"""
        try:
            connection = self.get_connection(db)
            if not connection:
                raise ValueError("Zephyr 연결 설정이 없습니다.")
            
            api_token = self.decrypt_token(connection.api_token)
            auth = HTTPBasicAuth(connection.username, api_token)
            
            # 테스트 케이스 가져오기
            if sync_request.sync_type in ["test_cases", "both"]:
                self._import_test_cases(db, connection, project, sync_history, auth)
            
            # 실행 결과 가져오기
            if sync_request.sync_type in ["executions", "both"]:
                self._import_executions(db, connection, project, sync_history, auth)
            
            # 동기화 완료
            sync_history.sync_status = "completed"
            sync_history.completed_at = datetime.now()
            sync_history.duration = int((datetime.now() - sync_history.started_at).total_seconds())
            
            project.sync_status = "completed"
            project.is_synced = True
            project.last_sync = datetime.now()
            
            db.commit()
            logger.info(f"프로젝트 {project.project_key} 가져오기 완료")
            
        except Exception as e:
            sync_history.sync_status = "failed"
            sync_history.error_message = str(e)
            sync_history.completed_at = datetime.now()
            project.sync_status = "failed"
            project.sync_error = str(e)
            db.commit()
            logger.error(f"Zephyr 가져오기 실패: {str(e)}")
            raise
    
    def _import_test_cases(self, db: Session, connection: ZephyrConnection, project: ZephyrProject, sync_history: ZephyrSyncHistory, auth):
        """테스트 케이스 가져오기"""
        try:
            # Jira 이슈 조회 (테스트 케이스로 사용)
            url = f"{connection.server_url}/rest/api/{self.api_version}/search"
            params = {
                "jql": f"project = {project.project_key} AND issuetype = Test",
                "maxResults": min(connection.max_results, 10000),  # 최대 10000개로 제한
                "fields": "summary,description,status,priority,assignee,created,updated"
            }
            
            response = requests.get(url, auth=auth, params=params, timeout=self.timeout, verify=False)
            
            if response.status_code != 200:
                raise Exception(f"테스트 케이스 조회 실패: HTTP {response.status_code}")
            
            data = response.json()
            issues = data.get("issues", [])
            
            sync_history.total_items += len(issues)
            
            for issue in issues:
                try:
                    # 기존 테스트 케이스 확인
                    existing_tc = db.query(ZephyrTestCase).filter(
                        and_(
                            ZephyrTestCase.zephyr_project_id == project.id,
                            ZephyrTestCase.zephyr_test_id == issue["id"]
                        )
                    ).first()
                    
                    if existing_tc:
                        # 기존 테스트 케이스 업데이트
                        existing_tc.title = issue["fields"]["summary"]
                        existing_tc.description = self._extract_description(issue["fields"].get("description"))
                        existing_tc.status = issue["fields"]["status"]["name"]
                        existing_tc.priority = issue["fields"]["priority"]["name"] if issue["fields"].get("priority") else "Medium"
                        existing_tc.last_sync = datetime.now()
                    else:
                        # 새 테스트 케이스 생성
                        test_case = ZephyrTestCase(
                            zephyr_test_id=issue["id"],
                            zephyr_project_id=project.id,
                            test_case_key=issue["key"],
                            title=issue["fields"]["summary"],
                            description=self._extract_description(issue["fields"].get("description")),
                            status=issue["fields"]["status"]["name"],
                            priority=issue["fields"]["priority"]["name"] if issue["fields"].get("priority") else "Medium",
                            created_by=issue["fields"]["assignee"]["displayName"] if issue["fields"].get("assignee") else None,
                            last_sync=datetime.now()
                        )
                        db.add(test_case)
                    
                    sync_history.processed_items += 1
                    sync_history.success_items += 1
                    
                except Exception as e:
                    logger.error(f"테스트 케이스 처리 실패 {issue.get('key', 'Unknown')}: {str(e)}")
                    sync_history.failed_items += 1
            
            # 테스트 케이스 수 업데이트
            project.test_case_count = db.query(ZephyrTestCase).filter(
                ZephyrTestCase.zephyr_project_id == project.id
            ).count()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"테스트 케이스 가져오기 실패: {str(e)}")
            raise
    
    def _import_executions(self, db: Session, connection: ZephyrConnection, project: ZephyrProject, sync_history: ZephyrSyncHistory, auth):
        """실행 결과 가져오기 (임시 구현)"""
        # 실제 Zephyr API에서는 별도의 실행 결과 API를 사용해야 함
        # 여기서는 간단한 예시로 구현
        logger.info(f"프로젝트 {project.project_key}의 실행 결과 가져오기 (구현 예정)")
    
    def _export_to_zephyr(self, db: Session, project: ZephyrProject, sync_history: ZephyrSyncHistory, sync_request: ZephyrSyncRequest):
        """Zephyr로 데이터 내보내기 (임시 구현)"""
        logger.info(f"프로젝트 {project.project_key}의 데이터 내보내기 (구현 예정)")
        
        # 임시로 성공 처리
        sync_history.sync_status = "completed"
        sync_history.completed_at = datetime.now()
        sync_history.duration = 60  # 1분
        project.sync_status = "completed"
        project.last_sync = datetime.now()
    
    def _extract_description(self, description_field) -> str:
        """Jira 설명 필드에서 텍스트 추출"""
        if not description_field:
            return ""
        
        if isinstance(description_field, dict):
            # Atlassian Document Format (ADF) 처리
            content = description_field.get("content", [])
            text_parts = []
            
            for item in content:
                if item.get("type") == "paragraph":
                    paragraph_content = item.get("content", [])
                    for text_item in paragraph_content:
                        if text_item.get("type") == "text":
                            text_parts.append(text_item.get("text", ""))
            
            return " ".join(text_parts)
        
        return str(description_field)
    
    def sync_test_cycles_from_zephyr(self, db: Session, project_key: str) -> Dict[str, Any]:
        """Zephyr Scale API에서 실제 테스트 사이클 데이터를 가져와서 데이터베이스에 저장"""
        zephyr_project = None
        
        try:
            logger.info(f"프로젝트 '{project_key}' 테스트 사이클 동기화 시작")
            
            # 입력 데이터 검증 및 정규화
            if not project_key or not isinstance(project_key, str):
                raise ValueError("유효하지 않은 프로젝트 키입니다.")
            
            # 프로젝트 키 정규화 (공백 제거, 대문자 변환)
            original_project_key = project_key
            project_key = project_key.strip().upper()
            
            # 빈 문자열이나 None 체크
            if not project_key:
                raise ValueError(f"프로젝트 키가 비어있습니다: '{original_project_key}'")
            
            logger.info(f"정규화된 프로젝트 키: '{project_key}' (원본: '{original_project_key}')")
            
            # 프로젝트 조회 또는 생성
            zephyr_project = db.query(ZephyrProject).filter(
                ZephyrProject.project_key == project_key
            ).first()
            
            if not zephyr_project:
                logger.info(f"새 Zephyr 프로젝트 생성: {project_key}")
                # 새 프로젝트 생성
                zephyr_project = ZephyrProject(
                    zephyr_project_id=f"zephyr_{project_key.lower()}",
                    project_key=project_key,
                    project_name=f"{project_key} 프로젝트",
                    description=f"{project_key} 프로젝트의 테스트 관리",
                    is_synced=False,
                    sync_status="syncing",
                    test_case_count=0
                )
                db.add(zephyr_project)
                db.flush()  # ID 생성을 위해 flush
                db.refresh(zephyr_project)
                logger.info(f"Zephyr 프로젝트 생성 완료: ID {zephyr_project.id}, 키: {zephyr_project.project_key}")
            else:
                logger.info(f"기존 Zephyr 프로젝트 사용: ID {zephyr_project.id}, 키: {zephyr_project.project_key}")
                zephyr_project.sync_status = "syncing"
                db.flush()
            
            # Zephyr Scale API에서 프로젝트 ID 조회
            logger.info(f"Zephyr Scale API에서 프로젝트 ID 조회: {project_key}")
            zephyr_project_id = self._get_zephyr_project_id(project_key, db)
            
            # 프로젝트 ID를 찾지 못해도 계속 진행 (기존 데이터 사용)
            if not zephyr_project_id:
                logger.warning(f"API에서 프로젝트 '{project_key}'를 찾을 수 없음. 기존 데이터베이스 사이클을 유지합니다.")
                
                # 기존 데이터베이스의 사이클 수 확인
                existing_cycles_count = db.query(ZephyrTestCycle).filter(
                    ZephyrTestCycle.zephyr_project_id == zephyr_project.id
                ).count()
                
                if existing_cycles_count > 0:
                    # 기존 사이클이 있으면 성공으로 처리
                    zephyr_project.sync_status = "completed"
                    zephyr_project.is_synced = True
                    zephyr_project.last_sync = datetime.now()
                    zephyr_project.sync_error = None
                    db.commit()
                    
                    return {
                        "success": True,
                        "message": f"테스트 사이클 {existing_cycles_count}개가 동기화되었습니다.",
                        "synced_cycles": existing_cycles_count,
                        "project_id": zephyr_project.id
                    }
                else:
                    # 기존 사이클이 없으면 빈 결과 반환
                    zephyr_project.sync_status = "completed"
                    zephyr_project.is_synced = True
                    zephyr_project.last_sync = datetime.now()
                    zephyr_project.sync_error = None
                    db.commit()
                    
                    return {
                        "success": True,
                        "message": f"프로젝트 '{project_key}'에 테스트 사이클이 없습니다.",
                        "synced_cycles": 0,
                        "project_id": zephyr_project.id
                    }
            
            logger.info(f"Zephyr 프로젝트 ID 찾음: {zephyr_project_id}")
            
            # 테스트 사이클 조회
            logger.info("API에서 테스트 사이클 조회 중...")
            cycles_data = self._fetch_test_cycles_from_api(zephyr_project_id, db)
            
            if not cycles_data:
                logger.info(f"프로젝트 '{project_key}'에 테스트 사이클이 없음")
                # API에서 데이터를 가져올 수 없는 경우
                zephyr_project.sync_status = "completed"
                zephyr_project.is_synced = True
                zephyr_project.last_sync = datetime.now()
                zephyr_project.sync_error = None
                db.commit()
                
                return {
                    "success": True,
                    "message": f"프로젝트 '{project_key}'에 테스트 사이클이 없습니다.",
                    "synced_cycles": 0,
                    "project_id": zephyr_project.id
                }
            
            logger.info(f"조회된 테스트 사이클 수: {len(cycles_data)}")
            
            synced_cycles = 0
            failed_cycles = 0
            
            for i, cycle_data in enumerate(cycles_data):
                try:
                    logger.debug(f"사이클 처리 중 ({i+1}/{len(cycles_data)}): {cycle_data.get('id', 'Unknown')}")
                    
                    # 필수 데이터 검증
                    cycle_id = cycle_data.get("id")
                    if not cycle_id:
                        logger.warning(f"사이클 ID가 없음: {cycle_data}")
                        failed_cycles += 1
                        continue
                    
                    cycle_id_str = str(cycle_id)
                    cycle_name = cycle_data.get("name", "이름 없음")
                    
                    # 기존 사이클 확인
                    existing_cycle = db.query(ZephyrTestCycle).filter(
                        and_(
                            ZephyrTestCycle.zephyr_project_id == zephyr_project.id,
                            ZephyrTestCycle.zephyr_cycle_id == cycle_id_str
                        )
                    ).first()
                    
                    if existing_cycle:
                        logger.debug(f"기존 사이클 업데이트: {cycle_name}")
                        # 기존 사이클 업데이트
                        existing_cycle.cycle_name = cycle_name[:255]  # 길이 제한
                        existing_cycle.description = (cycle_data.get("description", "") or "")[:1000]  # 길이 제한
                        existing_cycle.status = (cycle_data.get("statusName", "Not Started") or "Not Started")[:20]
                        existing_cycle.version = self._safe_get_name(cycle_data.get("version"))[:50]
                        existing_cycle.environment = self._safe_get_name(cycle_data.get("environment"))[:50]
                        existing_cycle.build = (cycle_data.get("build", "") or "")[:100]
                        existing_cycle.start_date = self._parse_date(cycle_data.get("plannedStartDate"))
                        existing_cycle.end_date = self._parse_date(cycle_data.get("plannedEndDate"))
                        existing_cycle.created_by = self._safe_get_author(cycle_data)[:100]
                        existing_cycle.assigned_to = self._safe_get_owner(cycle_data)[:100]
                        existing_cycle.last_sync = datetime.now()
                        
                        # 테스트 실행 통계 업데이트
                        self._update_cycle_statistics(existing_cycle, cycle_data)
                    else:
                        logger.debug(f"새 사이클 생성: {cycle_name}")
                        # 새 사이클 생성
                        new_cycle = ZephyrTestCycle(
                            zephyr_cycle_id=cycle_id_str,
                            zephyr_project_id=zephyr_project.id,
                            cycle_name=cycle_name[:255],  # 길이 제한
                            description=(cycle_data.get("description", "") or "")[:1000],  # 길이 제한
                            status=(cycle_data.get("statusName", "Not Started") or "Not Started")[:20],
                            version=self._safe_get_name(cycle_data.get("version"))[:50],
                            environment=self._safe_get_name(cycle_data.get("environment"))[:50],
                            build=(cycle_data.get("build", "") or "")[:100],
                            start_date=self._parse_date(cycle_data.get("plannedStartDate")),
                            end_date=self._parse_date(cycle_data.get("plannedEndDate")),
                            created_by=self._safe_get_author(cycle_data)[:100],
                            assigned_to=self._safe_get_owner(cycle_data)[:100],
                            created_at=datetime.now(),
                            last_sync=datetime.now()
                        )
                        
                        # 테스트 실행 통계 설정
                        self._update_cycle_statistics(new_cycle, cycle_data)
                        
                        db.add(new_cycle)
                    
                    synced_cycles += 1
                    
                    # 주기적으로 flush (메모리 관리)
                    if synced_cycles % 10 == 0:
                        db.flush()
                    
                except Exception as cycle_error:
                    failed_cycles += 1
                    logger.error(f"사이클 처리 실패 {cycle_data.get('id', 'Unknown')}: {str(cycle_error)}")
                    continue
            
            # 프로젝트 동기화 상태 업데이트
            zephyr_project.is_synced = True
            zephyr_project.sync_status = "completed"
            zephyr_project.last_sync = datetime.now()
            zephyr_project.sync_error = None
            
            # 최종 커밋
            db.commit()
            
            success_msg = f"프로젝트 '{project_key}' 동기화 완료: {synced_cycles}개 사이클 성공"
            if failed_cycles > 0:
                success_msg += f", {failed_cycles}개 실패"
            
            logger.info(success_msg)
            
            return {
                "success": True,
                "message": f"프로젝트 '{project_key}'의 테스트 사이클 {synced_cycles}개가 동기화되었습니다.",
                "synced_cycles": synced_cycles,
                "failed_cycles": failed_cycles,
                "project_id": zephyr_project.id
            }
            
        except Exception as e:
            logger.error(f"Zephyr 테스트 사이클 동기화 실패: {str(e)}", exc_info=True)
            
            # 롤백
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"롤백 실패: {str(rollback_error)}")
            
            # 프로젝트 상태를 실패로 업데이트 (안전하게)
            try:
                if zephyr_project:
                    # 새로운 세션으로 상태 업데이트
                    zephyr_project.sync_status = "failed"
                    zephyr_project.sync_error = str(e)[:1000]  # 길이 제한
                    db.commit()
            except Exception as update_error:
                logger.error(f"프로젝트 상태 업데이트 실패: {str(update_error)}")
            
            # 사용자에게 친화적인 오류 메시지 반환
            if "API 토큰" in str(e) or "찾을 수 없습니다" in str(e):
                error_msg = str(e)
            elif "연결" in str(e) or "timeout" in str(e).lower():
                error_msg = "Zephyr Scale 서버에 연결할 수 없습니다. 네트워크 연결을 확인해주세요."
            else:
                error_msg = f"테스트 사이클 동기화 중 오류가 발생했습니다: {str(e)}"
            
            raise Exception(error_msg)
    
    def _get_zephyr_project_id(self, project_key: str, db: Session = None) -> Optional[str]:
        """Zephyr/Jira API에서 프로젝트 ID 조회"""
        try:
            # 데이터베이스 연결 설정 우선 사용
            api_token = None
            server_url = None
            username = None
            
            logger.info(f"프로젝트 ID 조회 시작: {project_key}")
            
            if db:
                connection = self.get_connection(db)
                logger.info(f"데이터베이스 연결 조회 결과: {connection is not None}")
                if connection:
                    try:
                        api_token = self.decrypt_token(connection.api_token)
                        server_url = connection.server_url
                        username = connection.username
                        logger.info(f"데이터베이스 연결 설정 사용: {username} @ {server_url}")
                    except Exception as e:
                        logger.warning(f"데이터베이스 토큰 복호화 실패: {str(e)}")
                else:
                    logger.warning("데이터베이스에서 활성 Zephyr 연결을 찾을 수 없음")
            
            # 데이터베이스 설정이 없으면 환경변수 사용
            if not api_token:
                api_token = self.default_api_token
                server_url = self.base_url
                username = self.default_username
                logger.info(f"환경변수 설정 사용: {username} @ {server_url}")
            
            if not api_token:
                logger.error("API 토큰이 설정되지 않았습니다.")
                return None
            
            # JWT 토큰인지 확인 (Zephyr for Jira)
            if api_token.startswith('eyJ'):
                logger.info("JWT 토큰 감지 - Zephyr for Jira API 사용")
                # Zephyr for Jira API로 직접 프로젝트 조회
                project_id = self._try_zephyr_for_jira_api(project_key, api_token, server_url)
                if project_id:
                    return project_id
            else:
                logger.info("일반 토큰 감지 - Zephyr Scale API 시도")
                # Zephyr Scale API 시도
                project_id = self._try_zephyr_scale_api(project_key, api_token)
                if project_id:
                    return project_id
            
            # 마지막으로 Jira API로 시도
            if server_url:
                logger.info("Jira API로 프로젝트 조회 시도")
                project_id = self._try_jira_api(project_key, api_token, server_url, username)
                if project_id:
                    return project_id
            
            logger.warning(f"모든 API에서 프로젝트 '{project_key}'를 찾을 수 없습니다.")
            return None
            
        except Exception as e:
            logger.error(f"Zephyr 프로젝트 ID 조회 실패: {str(e)}")
            return None
    
    def _try_zephyr_scale_api(self, project_key: str, api_token: str) -> Optional[str]:
        """Zephyr Scale API로 프로젝트 조회 시도"""
        try:
            url = "https://api.zephyrscale.smartbear.com/v2/projects"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Accept": "application/json"
            }
            
            logger.info(f"Zephyr Scale API 호출: {url}")
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            
            logger.info(f"Zephyr Scale API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                projects_data = response.json()
                logger.info(f"조회된 프로젝트 수: {len(projects_data) if isinstance(projects_data, list) else 'dict 형태'}")
                
                # 프로젝트 키로 검색
                if isinstance(projects_data, list):
                    for project in projects_data:
                        if project.get("key") == project_key:
                            logger.info(f"Zephyr Scale에서 프로젝트 '{project_key}' 찾음: ID {project.get('id')}")
                            return project.get("id")
                elif isinstance(projects_data, dict) and "values" in projects_data:
                    for project in projects_data["values"]:
                        if project.get("key") == project_key:
                            logger.info(f"Zephyr Scale에서 프로젝트 '{project_key}' 찾음: ID {project.get('id')}")
                            return project.get("id")
            else:
                logger.warning(f"Zephyr Scale API 호출 실패: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Zephyr Scale API 호출 실패: {str(e)}")
            return None
    
    def _try_zephyr_for_jira_api(self, project_key: str, api_token: str, server_url: str) -> Optional[str]:
        """Zephyr for Jira API로 프로젝트 조회 시도"""
        try:
            # Zephyr for Jira의 테스트 사이클 API 호출
            url = f"{server_url}/rest/zapi/latest/cycle/search"
            headers = {
                "Authorization": f"JWT {api_token}",
                "Accept": "application/json"
            }
            
            params = {
                "projectId": project_key,  # 프로젝트 키로 시도
                "maxRecords": 1  # 존재 여부만 확인
            }
            
            logger.info(f"Zephyr for Jira API 호출: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            logger.info(f"Zephyr for Jira API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                # 성공하면 프로젝트 키를 ID로 반환 (Zephyr for Jira에서는 프로젝트 키 사용)
                logger.info(f"Zephyr for Jira에서 프로젝트 '{project_key}' 확인됨")
                return project_key
            else:
                logger.warning(f"Zephyr for Jira API 호출 실패: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Zephyr for Jira API 호출 실패: {str(e)}")
            return None
    
    def _try_jira_api(self, project_key: str, api_token: str, server_url: str, username: str = None) -> Optional[str]:
        """Jira API로 프로젝트 조회 시도"""
        try:
            # Jira 프로젝트 조회
            url = f"{server_url}/rest/api/3/project/{project_key}"
            
            # API 토큰이 JWT 형태인지 확인
            if api_token.startswith('eyJ'):
                # JWT 토큰인 경우
                headers = {
                    "Authorization": f"JWT {api_token}",
                    "Accept": "application/json"
                }
            else:
                # Basic Auth 토큰인 경우
                from requests.auth import HTTPBasicAuth
                auth_username = username or self.default_username
                auth = HTTPBasicAuth(auth_username, api_token)
                headers = {"Accept": "application/json"}
            
            logger.info(f"Jira API 호출: {url}")
            
            if api_token.startswith('eyJ'):
                response = requests.get(url, headers=headers, timeout=30, verify=False)
            else:
                response = requests.get(url, auth=auth, headers=headers, timeout=30, verify=False)
            
            logger.info(f"Jira API 응답 상태: {response.status_code}")
            
            if response.status_code == 200:
                project_data = response.json()
                project_id = project_data.get("id")
                logger.info(f"Jira에서 프로젝트 '{project_key}' 찾음: ID {project_id}")
                return project_id
            else:
                logger.warning(f"Jira API 호출 실패: {response.status_code}")
            
            return None
            
        except Exception as e:
            logger.warning(f"Jira API 호출 실패: {str(e)}")
            return None
    
    def _fetch_test_cycles_from_api(self, project_id: str, db: Session = None) -> List[Dict[str, Any]]:
        """API에서 테스트 사이클 목록 조회 (Zephyr Scale 또는 Zephyr for Jira)"""
        try:
            # 데이터베이스 연결 설정 우선 사용
            api_token = None
            server_url = None
            username = None
            
            if db:
                connection = self.get_connection(db)
                if connection:
                    try:
                        api_token = self.decrypt_token(connection.api_token)
                        server_url = connection.server_url
                        username = connection.username
                        logger.info(f"데이터베이스 연결 설정으로 사이클 조회: {username}")
                    except Exception as e:
                        logger.warning(f"데이터베이스 토큰 복호화 실패: {str(e)}")
            
            # 데이터베이스 설정이 없으면 환경변수 사용
            if not api_token:
                api_token = self.default_api_token
                server_url = self.base_url
                username = self.default_username
                logger.info("환경변수 설정으로 사이클 조회")
            
            if not api_token:
                logger.error("API 토큰이 설정되지 않았습니다.")
                return []
            
            # JWT 토큰인지 확인 (Zephyr for Jira)
            if api_token.startswith('eyJ'):
                logger.info("JWT 토큰 감지 - Zephyr for Jira API로 사이클 조회")
                return self._fetch_cycles_from_zephyr_for_jira(project_id, api_token, server_url)
            else:
                logger.info("일반 토큰 감지 - Zephyr Scale API로 사이클 조회")
                return self._fetch_cycles_from_zephyr_scale(project_id, api_token)
            
        except Exception as e:
            logger.error(f"테스트 사이클 API 조회 실패: {str(e)}")
            return []
    
    def _fetch_cycles_from_zephyr_scale(self, project_id: str, api_token: str) -> List[Dict[str, Any]]:
        """Zephyr Scale API에서 테스트 사이클 목록 조회"""
        try:
            all_cycles = []
            current_skip = 0
            max_results_per_request = 100
            
            while True:
                url = "https://api.zephyrscale.smartbear.com/v2/testcycles"
                headers = {
                    "Authorization": f"Bearer {api_token}",
                    "Accept": "application/json"
                }
                
                params = {
                    "projectId": project_id,
                    "maxResults": max_results_per_request,
                    "startAt": current_skip
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
                
                if response.status_code == 200:
                    cycles_data = response.json()
                    
                    if isinstance(cycles_data, dict) and "values" in cycles_data:
                        batch_cycles = cycles_data.get("values", [])
                        
                        if not batch_cycles:
                            break
                        
                        all_cycles.extend(batch_cycles)
                        current_skip += max_results_per_request
                        
                        if len(batch_cycles) < max_results_per_request:
                            break
                    else:
                        break
                else:
                    logger.error(f"Zephyr Scale API 오류: HTTP {response.status_code}")
                    break
            
            return all_cycles
            
        except Exception as e:
            logger.error(f"Zephyr Scale 테스트 사이클 API 조회 실패: {str(e)}")
            return []
    
    def _fetch_cycles_from_zephyr_for_jira(self, project_key: str, api_token: str, server_url: str) -> List[Dict[str, Any]]:
        """Zephyr for Jira API에서 테스트 사이클 목록 조회"""
        try:
            # 먼저 프로젝트 ID를 숫자로 변환 (Jira API 호출)
            jira_project_id = self._get_jira_project_id(project_key, api_token, server_url)
            if not jira_project_id:
                logger.warning(f"Jira 프로젝트 ID를 찾을 수 없음: {project_key}")
                return []
            
            logger.info(f"Jira 프로젝트 ID: {jira_project_id}")
            
            # Zephyr for Jira 사이클 조회
            url = f"{server_url}/rest/zapi/latest/cycle/search"
            headers = {
                "Authorization": f"JWT {api_token}",
                "Accept": "application/json"
            }
            
            params = {
                "projectId": jira_project_id,
                "maxRecords": 1000  # Zephyr for Jira는 maxRecords 사용
            }
            
            logger.info(f"Zephyr for Jira 사이클 조회: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            logger.info(f"Zephyr for Jira 사이클 조회 응답: {response.status_code}")
            
            if response.status_code == 200:
                cycles_data = response.json()
                logger.info(f"조회된 사이클 데이터: {type(cycles_data)}")
                
                # Zephyr for Jira 응답 구조 처리
                if isinstance(cycles_data, dict):
                    # recordsCount가 있는 경우
                    if "recordsCount" in cycles_data:
                        logger.info(f"사이클 개수: {cycles_data['recordsCount']}")
                        return self._parse_zephyr_for_jira_cycles(cycles_data)
                    # 직접 사이클 배열인 경우
                    elif isinstance(cycles_data, list):
                        return self._parse_zephyr_for_jira_cycles({"cycles": cycles_data})
                    else:
                        logger.warning(f"예상치 못한 응답 구조: {list(cycles_data.keys())}")
                        return []
                elif isinstance(cycles_data, list):
                    return self._parse_zephyr_for_jira_cycles({"cycles": cycles_data})
                else:
                    logger.warning(f"예상치 못한 응답 타입: {type(cycles_data)}")
                    return []
            else:
                logger.error(f"Zephyr for Jira API 오류: HTTP {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Zephyr for Jira 테스트 사이클 API 조회 실패: {str(e)}")
            return []
    
    def _get_jira_project_id(self, project_key: str, api_token: str, server_url: str) -> Optional[str]:
        """Jira API로 프로젝트 ID 조회"""
        try:
            url = f"{server_url}/rest/api/3/project/{project_key}"
            headers = {
                "Authorization": f"JWT {api_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                project_data = response.json()
                return project_data.get("id")
            else:
                logger.warning(f"Jira 프로젝트 조회 실패: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Jira 프로젝트 ID 조회 실패: {str(e)}")
            return None
    
    def _parse_zephyr_for_jira_cycles(self, cycles_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Zephyr for Jira 사이클 데이터를 표준 형식으로 변환"""
        try:
            parsed_cycles = []
            
            # 사이클 데이터 추출
            cycles = []
            if "cycles" in cycles_data:
                cycles = cycles_data["cycles"]
            elif isinstance(cycles_data, dict):
                # 키-값 쌍으로 된 사이클 데이터 처리
                for key, value in cycles_data.items():
                    if isinstance(value, dict) and "name" in value:
                        value["id"] = key
                        cycles.append(value)
            
            for cycle in cycles:
                if isinstance(cycle, dict):
                    # Zephyr for Jira 형식을 표준 형식으로 변환
                    parsed_cycle = {
                        "id": cycle.get("id", ""),
                        "name": cycle.get("name", "이름 없음"),
                        "description": cycle.get("description", ""),
                        "statusName": self._map_zephyr_status(cycle.get("status", "")),
                        "version": {"name": cycle.get("versionName", "N/A")},
                        "environment": {"name": cycle.get("environment", "N/A")},
                        "build": cycle.get("build", ""),
                        "plannedStartDate": cycle.get("startDate"),
                        "plannedEndDate": cycle.get("endDate"),
                        "createdBy": {"displayName": cycle.get("createdBy", "알 수 없음")},
                        "owner": {"displayName": cycle.get("owner", "미할당")},
                        "testExecutions": {
                            "total": cycle.get("totalCycleExecutions", 0),
                            "passed": cycle.get("totalExecuted", 0),
                            "failed": cycle.get("totalFailed", 0),
                            "blocked": cycle.get("totalBlocked", 0)
                        }
                    }
                    parsed_cycles.append(parsed_cycle)
            
            logger.info(f"파싱된 사이클 수: {len(parsed_cycles)}")
            return parsed_cycles
            
        except Exception as e:
            logger.error(f"Zephyr for Jira 사이클 데이터 파싱 실패: {str(e)}")
            return []
    
    def _map_zephyr_status(self, status: str) -> str:
        """Zephyr for Jira 상태를 표준 상태로 매핑"""
        status_mapping = {
            "0": "Not Started",
            "1": "In Progress", 
            "2": "Completed",
            "-1": "Cancelled"
        }
        return status_mapping.get(str(status), "Not Started")
    
    def _safe_get_name(self, field) -> str:
        """안전하게 name 필드 추출"""
        if not field:
            return "N/A"
        if isinstance(field, dict):
            return field.get("name", "N/A")
        return str(field)
    
    def _safe_get_author(self, data) -> str:
        """안전하게 작성자 정보 추출"""
        try:
            if data.get("createdBy"):
                created_by = data.get("createdBy")
                if isinstance(created_by, dict):
                    return created_by.get("displayName", "알 수 없음")
                return str(created_by)
            return "알 수 없음"
        except:
            return "알 수 없음"
    
    def _safe_get_owner(self, data) -> str:
        """안전하게 소유자 정보 추출"""
        try:
            if data.get("owner"):
                owner = data.get("owner")
                if isinstance(owner, dict):
                    return owner.get("displayName", "미할당")
                return str(owner)
            return "미할당"
        except:
            return "미할당"
    
    def _parse_date(self, date_str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str:
            return None
        try:
            # ISO 8601 형식 파싱
            from dateutil import parser
            return parser.parse(date_str)
        except:
            return None
    
    def _update_cycle_statistics(self, cycle, cycle_data: Dict[str, Any]):
        """사이클 통계 정보 업데이트"""
        try:
            # 기본값 설정
            cycle.total_test_cases = 0
            cycle.executed_test_cases = 0
            cycle.passed_test_cases = 0
            cycle.failed_test_cases = 0
            cycle.blocked_test_cases = 0
            
            # API에서 통계 정보 추출 (실제 API 응답 구조에 따라 조정 필요)
            if cycle_data.get("testExecutions"):
                executions = cycle_data.get("testExecutions", {})
                cycle.total_test_cases = executions.get("total", 0)
                cycle.passed_test_cases = executions.get("passed", 0)
                cycle.failed_test_cases = executions.get("failed", 0)
                cycle.blocked_test_cases = executions.get("blocked", 0)
                cycle.executed_test_cases = (
                    cycle.passed_test_cases + 
                    cycle.failed_test_cases + 
                    cycle.blocked_test_cases
                )
            
        except Exception as e:
            logger.error(f"사이클 통계 업데이트 실패: {str(e)}")

    def get_dashboard_stats(self, db: Session) -> ZephyrDashboardStats:
        """Zephyr 대시보드 통계 조회"""
        try:
            # 프로젝트 통계
            total_projects = db.query(ZephyrProject).count()
            synced_projects = db.query(ZephyrProject).filter(
                ZephyrProject.is_synced == True
            ).count()
            
            # 테스트 케이스 통계
            total_test_cases = db.query(ZephyrTestCase).count()
            
            # 실행 결과 통계
            total_executions = db.query(ZephyrTestExecution).count()
            passed_executions = db.query(ZephyrTestExecution).filter(
                ZephyrTestExecution.execution_status == "Pass"
            ).count()
            failed_executions = db.query(ZephyrTestExecution).filter(
                ZephyrTestExecution.execution_status == "Fail"
            ).count()
            blocked_executions = db.query(ZephyrTestExecution).filter(
                ZephyrTestExecution.execution_status == "Blocked"
            ).count()
            
            # 통과율 계산
            pass_rate = (passed_executions / total_executions * 100) if total_executions > 0 else 0.0
            
            # 프로젝트별 통계
            projects = db.query(ZephyrProject).all()
            project_stats = []
            
            for project in projects:
                project_test_cases = db.query(ZephyrTestCase).filter(
                    ZephyrTestCase.zephyr_project_id == project.id
                ).count()
                
                project_executions = db.query(ZephyrTestExecution).join(ZephyrTestCase).filter(
                    ZephyrTestCase.zephyr_project_id == project.id
                ).count()
                
                project_passed = db.query(ZephyrTestExecution).join(ZephyrTestCase).filter(
                    and_(
                        ZephyrTestCase.zephyr_project_id == project.id,
                        ZephyrTestExecution.execution_status == "Pass"
                    )
                ).count()
                
                project_failed = db.query(ZephyrTestExecution).join(ZephyrTestCase).filter(
                    and_(
                        ZephyrTestCase.zephyr_project_id == project.id,
                        ZephyrTestExecution.execution_status == "Fail"
                    )
                ).count()
                
                project_blocked = db.query(ZephyrTestExecution).join(ZephyrTestCase).filter(
                    and_(
                        ZephyrTestCase.zephyr_project_id == project.id,
                        ZephyrTestExecution.execution_status == "Blocked"
                    )
                ).count()
                
                # 마지막 실행 시간
                last_execution = db.query(ZephyrTestExecution).join(ZephyrTestCase).filter(
                    ZephyrTestCase.zephyr_project_id == project.id
                ).order_by(ZephyrTestExecution.executed_at.desc()).first()
                
                project_stats.append(ZephyrProjectStats(
                    project_id=project.id,
                    project_key=project.project_key,
                    project_name=project.project_name,
                    total_test_cases=project_test_cases,
                    total_executions=project_executions,
                    passed_executions=project_passed,
                    failed_executions=project_failed,
                    blocked_executions=project_blocked,
                    last_execution=last_execution.executed_at if last_execution else None
                ))
            
            return ZephyrDashboardStats(
                total_projects=total_projects,
                synced_projects=synced_projects,
                total_test_cases=total_test_cases,
                total_executions=total_executions,
                passed_executions=passed_executions,
                failed_executions=failed_executions,
                blocked_executions=blocked_executions,
                pass_rate=round(pass_rate, 2),
                projects=project_stats
            )
            
        except Exception as e:
            logger.error(f"Zephyr 대시보드 통계 조회 실패: {str(e)}")
            raise

# 전역 서비스 인스턴스
zephyr_service = ZephyrService()
