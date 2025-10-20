"""
Pydantic 모델 정의 (API 요청/응답)
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# 기본 응답 모델
class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = True
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


# 프로젝트 관련 모델
class ProjectBase(BaseModel):
    """프로젝트 기본 모델"""
    name: str = Field(..., max_length=255)
    jira_project_key: str = Field(..., max_length=50)
    description: Optional[str] = None
    is_active: bool = True


class ProjectCreate(ProjectBase):
    """프로젝트 생성 모델"""
    pass


class ProjectUpdate(BaseModel):
    """프로젝트 업데이트 모델"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectResponse(ProjectBase):
    """프로젝트 응답 모델"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 작업 관련 모델
class TaskBase(BaseModel):
    """작업 기본 모델"""
    jira_key: str
    jira_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "To Do"  # 지라 상태
    qa_status: str = "미시작"  # QA 검수 상태
    assignee: Optional[str] = None
    priority: str = "Medium"
    project_id: int
    memo: Optional[str] = None


class TaskCreate(TaskBase):
    """작업 생성 모델"""
    pass


class TaskUpdate(BaseModel):
    """작업 업데이트 모델"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # 지라 상태
    qa_status: Optional[str] = None  # QA 검수 상태
    assignee: Optional[str] = None
    priority: Optional[str] = None
    memo: Optional[str] = None


class TaskResponse(TaskBase):
    """작업 응답 모델"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 테스트 케이스 관련 모델
class TestCaseBase(BaseModel):
    """테스트 케이스 기본 모델"""
    zephyr_key: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: str = Field(default="Not Executed", max_length=20)
    executed_by: Optional[str] = Field(None, max_length=100)


class TestCaseCreate(TestCaseBase):
    """테스트 케이스 생성 모델"""
    task_id: int


class TestCaseUpdate(BaseModel):
    """테스트 케이스 업데이트 모델"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, max_length=20)
    executed_by: Optional[str] = Field(None, max_length=100)


class TestCaseResponse(TestCaseBase):
    """테스트 케이스 응답 모델"""
    id: int
    task_id: int
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Jira 관련 모델
class JiraConnectionTest(BaseResponse):
    """Jira 연결 테스트 응답"""
    server: Optional[str] = None
    username: Optional[str] = None


class JiraProject(BaseModel):
    """Jira 프로젝트 모델 (API v3)"""
    key: str
    name: str
    description: Optional[str] = None
    projectTypeKey: Optional[str] = None
    lead: Optional[dict] = None
    url: Optional[str] = None
    avatarUrls: Optional[dict] = None
    projectCategory: Optional[dict] = None
    simplified: Optional[bool] = None
    style: Optional[str] = None
    isPrivate: Optional[bool] = None
    issueTypes: Optional[List[dict]] = None
    # 추가된 필드들
    issue_count: Optional[int] = None
    is_active: Optional[bool] = None


class JiraProjectsResponse(BaseResponse):
    """Jira 프로젝트 목록 응답"""
    projects: List[JiraProject] = []
    count: int = 0


class JiraIssueFields(BaseModel):
    """Jira 이슈 필드 모델 (API v3)"""
    summary: Optional[str] = None
    description: Optional[dict] = None  # v3에서는 Atlassian Document Format
    status: Optional[dict] = None
    assignee: Optional[dict] = None
    reporter: Optional[dict] = None
    priority: Optional[dict] = None
    issuetype: Optional[dict] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    resolutiondate: Optional[str] = None
    labels: Optional[List[str]] = None
    components: Optional[List[dict]] = None
    fixVersions: Optional[List[dict]] = None
    versions: Optional[List[dict]] = None


class JiraIssue(BaseModel):
    """Jira 이슈 모델 (API v3)"""
    key: str
    id: str
    self: Optional[str] = None
    fields: Optional[JiraIssueFields] = None
    expand: Optional[str] = None
    
    # 정규화된 필드들 (jira_service에서 추가)
    summary: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    status_id: Optional[str] = None
    issue_type: Optional[str] = None
    issue_type_id: Optional[str] = None
    priority: Optional[str] = None
    priority_id: Optional[str] = None
    assignee: Optional[str] = None
    assignee_email: Optional[str] = None
    reporter: Optional[str] = None
    reporter_email: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class JiraIssuesResponse(BaseResponse):
    """Jira 이슈 목록 응답"""
    project_key: str
    issues: List[JiraIssue] = []
    count: int = 0
    total: Optional[int] = None
    startAt: Optional[int] = None
    maxResults: Optional[int] = None


# 동기화 관련 모델
class SyncRequest(BaseModel):
    """동기화 요청 모델"""
    selected_issues: Optional[List[str]] = None


class SyncStatus(BaseModel):
    """동기화 상태 모델"""
    status: str  # starting, connecting, fetching_issues, processing, completed, error
    progress: int = 0
    message: str = ""
    total_issues: int = 0
    processed_issues: int = 0
    selected_issues: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SyncResponse(BaseResponse):
    """동기화 응답 모델"""
    project_key: str
    selected_issues_count: Optional[int] = None


# 대시보드 통계 모델
class DashboardStats(BaseModel):
    """대시보드 통계 모델"""
    total_tasks: int = 0
    completed_tasks: int = 0
    qa_ready_tasks: int = 0
    in_progress_tasks: int = 0
    completion_rate: float = 0.0


# 메모 관련 모델
class MemoRequest(BaseModel):
    """메모 요청 모델"""
    memo: str = Field(..., max_length=2000)


class MemoResponse(BaseResponse):
    """메모 응답 모델"""
    task_id: int
    jira_key: str
    memo: str
    updated_at: Optional[datetime] = None


# 삭제 관련 모델
class DeleteResponse(BaseResponse):
    """삭제 응답 모델"""
    deleted_count: int = 0
    deleted_items: Optional[List[dict]] = None


# QA 상태 업데이트 모델
class QAStatusUpdate(BaseModel):
    """QA 상태 업데이트 모델"""
    qa_status: str = Field(..., pattern="^(미시작|QA 시작|QA 진행중|QA 완료)$")


class QAStatusResponse(BaseResponse):
    """QA 상태 응답 모델"""
    task_id: int
    jira_key: str
    old_status: str
    new_status: str


# QA 요청서 관련 모델
class QARequestDocumentBase(BaseModel):
    """QA 요청서 문서 기본 모델"""
    document_type: str = Field(..., max_length=50)  # 기획서, 디자인문서
    document_name: str = Field(..., max_length=255)
    document_link: str = Field(..., max_length=500)


class QARequestDocumentCreate(QARequestDocumentBase):
    """QA 요청서 문서 생성 모델"""
    pass


class QARequestDocumentResponse(QARequestDocumentBase):
    """QA 요청서 문서 응답 모델"""
    id: int
    qa_request_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class QARequestBase(BaseModel):
    """QA 요청서 기본 모델"""
    requester: str = Field(..., max_length=100)  # 요청자
    project_name: str = Field(..., max_length=255)  # 프로젝트명
    test_content: str = Field(..., min_length=1)  # 검수 희망 내용
    platform: str = Field(..., max_length=50)  # android, ios, web, api
    build_link: Optional[str] = Field(None, max_length=500)  # 빌드 링크
    desired_deploy_date: Optional[datetime] = None  # 희망 배포 날짜
    assignee: Optional[str] = Field(None, max_length=100)  # 담당자


class QARequestCreate(QARequestBase):
    """QA 요청서 생성 모델"""
    documents: Optional[List[QARequestDocumentCreate]] = []


class QARequestUpdate(BaseModel):
    """QA 요청서 업데이트 모델"""
    requester: Optional[str] = Field(None, max_length=100)
    project_name: Optional[str] = Field(None, max_length=255)
    test_content: Optional[str] = None
    platform: Optional[str] = Field(None, max_length=50)
    build_link: Optional[str] = Field(None, max_length=500)
    desired_deploy_date: Optional[datetime] = None
    assignee: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=20)


class QARequestResponse(QARequestBase):
    """QA 요청서 응답 모델"""
    id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    documents: List[QARequestDocumentResponse] = []
    
    class Config:
        from_attributes = True


class QARequestListResponse(BaseResponse):
    """QA 요청서 목록 응답 모델"""
    requests: List[QARequestResponse] = []
    total: int = 0
    page: int = 1
    size: int = 20


class QARequestStatusUpdate(BaseModel):
    """QA 요청서 상태 업데이트 모델"""
    status: str = Field(..., pattern="^(요청|진행중|완료|보류)$")
    assignee: Optional[str] = Field(None, max_length=100)


# Zephyr 연동 관련 모델
class ZephyrConnectionBase(BaseModel):
    """Zephyr 연동 설정 기본 모델"""
    server_url: str = Field(default="https://remember-qa.atlassian.net", max_length=500)
    username: str = Field(..., max_length=255)
    auto_sync: bool = False
    sync_interval: str = Field(default="manual", max_length=20)
    max_results: int = Field(default=100, ge=10, le=1000)
    include_archived: bool = False


class ZephyrConnectionCreate(ZephyrConnectionBase):
    """Zephyr 연동 설정 생성 모델"""
    api_token: str = Field(..., min_length=1)


class ZephyrConnectionUpdate(BaseModel):
    """Zephyr 연동 설정 업데이트 모델"""
    username: Optional[str] = Field(None, max_length=255)
    api_token: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_interval: Optional[str] = Field(None, max_length=20)
    max_results: Optional[int] = Field(None, ge=10, le=1000)
    include_archived: Optional[bool] = None


class ZephyrConnectionResponse(ZephyrConnectionBase):
    """Zephyr 연동 설정 응답 모델"""
    id: int
    is_active: bool
    last_connection_test: Optional[datetime] = None
    connection_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ZephyrConnectionTest(BaseResponse):
    """Zephyr 연결 테스트 응답"""
    server_url: Optional[str] = None
    username: Optional[str] = None
    connection_time: Optional[float] = None


# Zephyr 프로젝트 관련 모델
class ZephyrProjectBase(BaseModel):
    """Zephyr 프로젝트 기본 모델"""
    zephyr_project_id: str = Field(..., max_length=50)
    project_key: str = Field(..., max_length=50)
    project_name: str = Field(..., max_length=255)
    description: Optional[str] = None


class ZephyrProjectCreate(ZephyrProjectBase):
    """Zephyr 프로젝트 생성 모델"""
    pass


class ZephyrProjectUpdate(BaseModel):
    """Zephyr 프로젝트 업데이트 모델"""
    project_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_synced: Optional[bool] = None
    sync_status: Optional[str] = Field(None, max_length=20)


class ZephyrProjectResponse(ZephyrProjectBase):
    """Zephyr 프로젝트 응답 모델"""
    id: int
    is_synced: bool
    sync_status: str
    test_case_count: int
    last_sync: Optional[datetime] = None
    sync_error: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Zephyr 테스트 케이스 관련 모델
class ZephyrTestCaseBase(BaseModel):
    """Zephyr 테스트 케이스 기본 모델"""
    zephyr_test_id: str = Field(..., max_length=50)
    test_case_key: Optional[str] = Field(None, max_length=50)
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None
    test_data: Optional[str] = None
    priority: str = Field(default="Medium", max_length=20)
    status: str = Field(default="Draft", max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)
    estimated_time: Optional[int] = None
    created_by: Optional[str] = Field(None, max_length=100)
    assigned_to: Optional[str] = Field(None, max_length=100)


class ZephyrTestCaseCreate(ZephyrTestCaseBase):
    """Zephyr 테스트 케이스 생성 모델"""
    zephyr_project_id: int


class ZephyrTestCaseUpdate(BaseModel):
    """Zephyr 테스트 케이스 업데이트 모델"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    preconditions: Optional[str] = None
    test_data: Optional[str] = None
    priority: Optional[str] = Field(None, max_length=20)
    status: Optional[str] = Field(None, max_length=20)
    category: Optional[str] = Field(None, max_length=50)
    tags: Optional[str] = Field(None, max_length=500)
    estimated_time: Optional[int] = None
    assigned_to: Optional[str] = Field(None, max_length=100)


class ZephyrTestCaseResponse(ZephyrTestCaseBase):
    """Zephyr 테스트 케이스 응답 모델"""
    id: int
    zephyr_project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Zephyr 테스트 실행 관련 모델
class ZephyrTestExecutionBase(BaseModel):
    """Zephyr 테스트 실행 기본 모델"""
    zephyr_execution_id: str = Field(..., max_length=50)
    execution_status: str = Field(..., max_length=20)
    executed_by: Optional[str] = Field(None, max_length=100)
    executed_at: Optional[datetime] = None
    execution_time: Optional[int] = None
    environment: Optional[str] = Field(None, max_length=50)
    browser: Optional[str] = Field(None, max_length=50)
    os: Optional[str] = Field(None, max_length=50)
    comments: Optional[str] = None
    defects: Optional[str] = None


class ZephyrTestExecutionCreate(ZephyrTestExecutionBase):
    """Zephyr 테스트 실행 생성 모델"""
    test_case_id: int


class ZephyrTestExecutionUpdate(BaseModel):
    """Zephyr 테스트 실행 업데이트 모델"""
    execution_status: Optional[str] = Field(None, max_length=20)
    executed_by: Optional[str] = Field(None, max_length=100)
    executed_at: Optional[datetime] = None
    execution_time: Optional[int] = None
    environment: Optional[str] = Field(None, max_length=50)
    browser: Optional[str] = Field(None, max_length=50)
    os: Optional[str] = Field(None, max_length=50)
    comments: Optional[str] = None
    defects: Optional[str] = None


class ZephyrTestExecutionResponse(ZephyrTestExecutionBase):
    """Zephyr 테스트 실행 응답 모델"""
    id: int
    test_case_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Zephyr 동기화 관련 모델
class ZephyrSyncRequest(BaseModel):
    """Zephyr 동기화 요청 모델"""
    project_ids: Optional[List[int]] = None
    sync_direction: str = Field(..., pattern="^(import|export)$")
    sync_type: str = Field(..., pattern="^(test_cases|executions|both)$")
    force_sync: bool = False


class ZephyrSyncHistoryResponse(BaseModel):
    """Zephyr 동기화 이력 응답 모델"""
    id: int
    zephyr_project_id: int
    sync_direction: str
    sync_type: str
    sync_status: str
    total_items: int
    processed_items: int
    success_items: int
    failed_items: int
    error_message: Optional[str] = None
    sync_details: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[int] = None
    
    class Config:
        from_attributes = True


class ZephyrSyncResponse(BaseResponse):
    """Zephyr 동기화 응답 모델"""
    sync_id: int
    project_count: int
    estimated_time: Optional[int] = None


class ZephyrSyncStatus(BaseModel):
    """Zephyr 동기화 상태 모델"""
    sync_id: int
    status: str  # started, in_progress, completed, failed
    progress: int = 0
    message: str = ""
    total_items: int = 0
    processed_items: int = 0
    success_items: int = 0
    failed_items: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


# Zephyr 통계 관련 모델
class ZephyrProjectStats(BaseModel):
    """Zephyr 프로젝트 통계 모델"""
    project_id: int
    project_key: str
    project_name: str
    total_test_cases: int = 0
    draft_test_cases: int = 0
    approved_test_cases: int = 0
    total_executions: int = 0
    passed_executions: int = 0
    failed_executions: int = 0
    blocked_executions: int = 0
    not_executed: int = 0
    last_execution: Optional[datetime] = None


class ZephyrDashboardStats(BaseModel):
    """Zephyr 대시보드 통계 모델"""
    total_projects: int = 0
    synced_projects: int = 0
    total_test_cases: int = 0
    total_executions: int = 0
    passed_executions: int = 0
    failed_executions: int = 0
    blocked_executions: int = 0
    pass_rate: float = 0.0
    projects: List[ZephyrProjectStats] = []


# Zephyr API 응답 모델 (외부 API)
class ZephyrApiProject(BaseModel):
    """Zephyr API 프로젝트 모델"""
    id: str
    key: str
    name: str
    description: Optional[str] = None
    projectTypeKey: Optional[str] = None
    lead: Optional[dict] = None


class ZephyrApiTestCase(BaseModel):
    """Zephyr API 테스트 케이스 모델"""
    id: str
    key: Optional[str] = None
    name: str
    description: Optional[str] = None
    testScript: Optional[str] = None
    expectedResult: Optional[str] = None
    precondition: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    labels: Optional[List[str]] = None
    estimatedTime: Optional[int] = None
    owner: Optional[dict] = None


class ZephyrApiExecution(BaseModel):
    """Zephyr API 실행 결과 모델"""
    id: str
    testCaseId: str
    status: str
    executedBy: Optional[dict] = None
    executedOn: Optional[str] = None
    executionTime: Optional[int] = None
    environment: Optional[str] = None
    comment: Optional[str] = None
    defects: Optional[List[str]] = None
