"""
데이터베이스 모델 정의
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base


class Project(Base):
    """프로젝트 모델"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    jira_project_key = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, key={self.jira_project_key}, name={self.name})>"


class Task(Base):
    """작업 모델"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_key = Column(String(50), unique=True, index=True, nullable=False)
    jira_id = Column(String(50))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="To Do")  # 지라 상태 (변경되면 안됨)
    qa_status = Column(String(50), default="미시작")  # QA 검수 상태
    assignee = Column(String(100))
    priority = Column(String(20), default="Medium")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    memo = Column(Text)  # QA 메모
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    project = relationship("Project", back_populates="tasks")
    test_cases = relationship("TestCase", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, jira_key={self.jira_key}, title={self.title[:50]})>"


class TestCase(Base):
    """테스트 케이스 모델"""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_key = Column(String(50), unique=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="Not Executed")  # Pass, Fail, Blocked, Not Executed
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    executed_by = Column(String(100))
    executed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    task = relationship("Task", back_populates="test_cases")
    
    def __repr__(self):
        return f"<TestCase(id={self.id}, title={self.title[:50]}, status={self.status})>"


class SyncHistory(Base):
    """동기화 이력 모델"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    project_key = Column(String(50), nullable=False)
    sync_type = Column(String(20), default="full")  # full, partial, selected
    status = Column(String(20), default="started")  # started, completed, failed
    total_issues = Column(Integer, default=0)
    processed_issues = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<SyncHistory(id={self.id}, project_key={self.project_key}, status={self.status})>"


class QARequest(Base):
    """QA 요청서 모델"""
    __tablename__ = "qa_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    requester = Column(String(100), nullable=False)  # 요청자
    project_name = Column(String(255), nullable=False)  # 프로젝트명
    test_content = Column(Text, nullable=False)  # 검수 희망 내용
    platform = Column(String(50), nullable=False)  # android, ios, web, api
    build_link = Column(String(500))  # 빌드 링크
    desired_deploy_date = Column(DateTime(timezone=True))  # 희망 배포 날짜
    assignee = Column(String(100))  # 담당자
    status = Column(String(20), default="요청")  # 요청, 진행중, 완료, 보류
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    documents = relationship("QARequestDocument", back_populates="qa_request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QARequest(id={self.id}, project_name={self.project_name}, status={self.status})>"


class QARequestDocument(Base):
    """QA 요청서 문서 모델"""
    __tablename__ = "qa_request_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    qa_request_id = Column(Integer, ForeignKey("qa_requests.id"), nullable=False)
    document_type = Column(String(50), nullable=False)  # 기획서, 디자인문서
    document_name = Column(String(255), nullable=False)
    document_link = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 설정
    qa_request = relationship("QARequest", back_populates="documents")
    
    def __repr__(self):
        return f"<QARequestDocument(id={self.id}, type={self.document_type}, name={self.document_name})>"


class ZephyrConnection(Base):
    """Zephyr 연동 설정 모델"""
    __tablename__ = "zephyr_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    server_url = Column(String(500), nullable=False, default="https://remember-qa.atlassian.net")
    username = Column(String(255), nullable=False)
    api_token = Column(Text, nullable=False)  # 암호화된 API 토큰
    is_active = Column(Boolean, default=True)
    auto_sync = Column(Boolean, default=False)
    sync_interval = Column(String(20), default="manual")  # manual, 5min, 15min, 30min, 1hour, 6hour, 24hour
    max_results = Column(Integer, default=100)
    include_archived = Column(Boolean, default=False)
    last_connection_test = Column(DateTime(timezone=True))
    connection_status = Column(String(20), default="not_tested")  # not_tested, connected, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ZephyrConnection(id={self.id}, username={self.username}, status={self.connection_status})>"


class ZephyrProject(Base):
    """Zephyr 프로젝트 모델"""
    __tablename__ = "zephyr_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_project_id = Column(String(50), nullable=False)
    project_key = Column(String(50), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text)
    is_synced = Column(Boolean, default=False)
    sync_status = Column(String(20), default="not_synced")  # not_synced, syncing, completed, failed
    test_case_count = Column(Integer, default=0)
    last_sync = Column(DateTime(timezone=True))
    sync_error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    test_cases = relationship("ZephyrTestCase", back_populates="zephyr_project", cascade="all, delete-orphan")
    test_cycles = relationship("ZephyrTestCycle", back_populates="zephyr_project", cascade="all, delete-orphan")
    sync_histories = relationship("ZephyrSyncHistory", back_populates="zephyr_project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ZephyrProject(id={self.id}, key={self.project_key}, name={self.project_name})>"


class ZephyrTestCase(Base):
    """Zephyr 테스트 케이스 모델"""
    __tablename__ = "zephyr_test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_test_id = Column(String(50), nullable=False)
    zephyr_project_id = Column(Integer, ForeignKey("zephyr_projects.id"), nullable=False)
    test_case_key = Column(String(50))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    test_steps = Column(Text)
    expected_result = Column(Text)
    preconditions = Column(Text)
    test_data = Column(Text)
    priority = Column(String(20), default="Medium")  # High, Medium, Low
    status = Column(String(20), default="Draft")  # Draft, Review, Approved, Deprecated
    category = Column(String(50))
    tags = Column(String(500))
    estimated_time = Column(Integer)  # 분 단위
    created_by = Column(String(100))
    assigned_to = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    zephyr_project = relationship("ZephyrProject", back_populates="test_cases")
    executions = relationship("ZephyrTestExecution", back_populates="test_case", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ZephyrTestCase(id={self.id}, key={self.test_case_key}, title={self.title[:50]})>"


class ZephyrTestExecution(Base):
    """Zephyr 테스트 실행 결과 모델"""
    __tablename__ = "zephyr_test_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_execution_id = Column(String(50), nullable=False)
    test_case_id = Column(Integer, ForeignKey("zephyr_test_cases.id"), nullable=False)
    execution_status = Column(String(20), nullable=False)  # Pass, Fail, Blocked, Not Executed
    executed_by = Column(String(100))
    executed_at = Column(DateTime(timezone=True))
    execution_time = Column(Integer)  # 실행 소요 시간 (초)
    environment = Column(String(50))  # Development, Staging, Production
    browser = Column(String(50))
    os = Column(String(50))
    comments = Column(Text)
    defects = Column(Text)  # 연결된 결함 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    test_case = relationship("ZephyrTestCase", back_populates="executions")
    
    def __repr__(self):
        return f"<ZephyrTestExecution(id={self.id}, status={self.execution_status}, executed_by={self.executed_by})>"


class ZephyrTestCycle(Base):
    """Zephyr 테스트 사이클 모델"""
    __tablename__ = "zephyr_test_cycles"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_cycle_id = Column(String(50), nullable=False)
    zephyr_project_id = Column(Integer, ForeignKey("zephyr_projects.id"), nullable=False)
    cycle_name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50))
    environment = Column(String(50))
    build = Column(String(100))
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    status = Column(String(20), default="Not Started")  # Not Started, In Progress, Completed, Cancelled
    created_by = Column(String(100))
    assigned_to = Column(String(100))
    total_test_cases = Column(Integer, default=0)
    executed_test_cases = Column(Integer, default=0)
    passed_test_cases = Column(Integer, default=0)
    failed_test_cases = Column(Integer, default=0)
    blocked_test_cases = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    zephyr_project = relationship("ZephyrProject", back_populates="test_cycles")
    cycle_executions = relationship("ZephyrCycleExecution", back_populates="test_cycle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ZephyrTestCycle(id={self.id}, name={self.cycle_name}, status={self.status})>"


class ZephyrCycleExecution(Base):
    """Zephyr 사이클 실행 결과 모델"""
    __tablename__ = "zephyr_cycle_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_execution_id = Column(String(50), nullable=False)
    test_cycle_id = Column(Integer, ForeignKey("zephyr_test_cycles.id"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("zephyr_test_cases.id"), nullable=False)
    execution_status = Column(String(20), nullable=False)  # Pass, Fail, Blocked, Not Executed, In Progress
    executed_by = Column(String(100))
    executed_at = Column(DateTime(timezone=True))
    execution_time = Column(Integer)  # 실행 소요 시간 (초)
    comments = Column(Text)
    defects = Column(Text)  # 연결된 결함 정보
    attachments = Column(Text)  # 첨부파일 정보 (JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True))
    
    # 관계 설정
    test_cycle = relationship("ZephyrTestCycle", back_populates="cycle_executions")
    test_case = relationship("ZephyrTestCase")
    
    def __repr__(self):
        return f"<ZephyrCycleExecution(id={self.id}, status={self.execution_status}, executed_by={self.executed_by})>"


class ZephyrSyncHistory(Base):
    """Zephyr 동기화 이력 모델"""
    __tablename__ = "zephyr_sync_history"
    
    id = Column(Integer, primary_key=True, index=True)
    zephyr_project_id = Column(Integer, ForeignKey("zephyr_projects.id"), nullable=False)
    sync_direction = Column(String(20), nullable=False)  # import, export
    sync_type = Column(String(50), nullable=False)  # test_cases, executions, cycles, both
    sync_status = Column(String(20), default="started")  # started, completed, failed
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    success_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    error_message = Column(Text)
    sync_details = Column(Text)  # JSON 형태의 상세 정보
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration = Column(Integer)  # 동기화 소요 시간 (초)
    
    # 관계 설정
    zephyr_project = relationship("ZephyrProject", back_populates="sync_histories")
    
    def __repr__(self):
        return f"<ZephyrSyncHistory(id={self.id}, direction={self.sync_direction}, status={self.sync_status})>"
