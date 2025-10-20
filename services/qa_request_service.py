"""
QA 요청서 서비스
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from datetime import datetime

from models.database_models import QARequest, QARequestDocument
from models.pydantic_models import (
    QARequestCreate, QARequestUpdate, QARequestResponse, 
    QARequestDocumentResponse, QARequestListResponse,
    QARequestStatusUpdate
)


class QARequestService:
    """QA 요청서 서비스 클래스"""
    
    def create_qa_request(self, db: Session, qa_request_data: QARequestCreate) -> QARequestResponse:
        """QA 요청서 생성"""
        # QA 요청서 생성
        qa_request = QARequest(
            requester=qa_request_data.requester,
            project_name=qa_request_data.project_name,
            test_content=qa_request_data.test_content,
            platform=qa_request_data.platform,
            build_link=qa_request_data.build_link,
            desired_deploy_date=qa_request_data.desired_deploy_date,
            assignee=qa_request_data.assignee
        )
        
        db.add(qa_request)
        db.commit()
        db.refresh(qa_request)
        
        # 문서들 생성
        documents = []
        if qa_request_data.documents:
            for doc_data in qa_request_data.documents:
                document = QARequestDocument(
                    qa_request_id=qa_request.id,
                    document_type=doc_data.document_type,
                    document_name=doc_data.document_name,
                    document_link=doc_data.document_link
                )
                db.add(document)
                documents.append(document)
            
            db.commit()
            for doc in documents:
                db.refresh(doc)
        
        # 응답 데이터 구성
        return self._build_qa_request_response(qa_request, documents)
    
    def get_qa_requests(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> QARequestListResponse:
        """QA 요청서 목록 조회"""
        query = db.query(QARequest)
        
        # 필터링
        if status:
            query = query.filter(QARequest.status == status)
        if platform:
            query = query.filter(QARequest.platform == platform)
        if assignee:
            query = query.filter(QARequest.assignee == assignee)
        
        # 전체 개수
        total = query.count()
        
        # 페이징 및 정렬
        offset = (page - 1) * size
        qa_requests = query.order_by(desc(QARequest.created_at)).offset(offset).limit(size).all()
        
        # 응답 데이터 구성
        requests = []
        for qa_request in qa_requests:
            documents = db.query(QARequestDocument).filter(
                QARequestDocument.qa_request_id == qa_request.id
            ).all()
            requests.append(self._build_qa_request_response(qa_request, documents))
        
        return {
            "success": True,
            "message": "QA 요청서 목록 조회 성공",
            "requests": requests,
            "total": total,
            "page": page,
            "size": size
        }
    
    def get_qa_request(self, db: Session, qa_request_id: int) -> Optional[QARequestResponse]:
        """QA 요청서 상세 조회"""
        qa_request = db.query(QARequest).filter(QARequest.id == qa_request_id).first()
        if not qa_request:
            return None
        
        documents = db.query(QARequestDocument).filter(
            QARequestDocument.qa_request_id == qa_request_id
        ).all()
        
        return self._build_qa_request_response(qa_request, documents)
    
    def update_qa_request(
        self, 
        db: Session, 
        qa_request_id: int, 
        update_data: QARequestUpdate
    ) -> Optional[QARequestResponse]:
        """QA 요청서 업데이트"""
        qa_request = db.query(QARequest).filter(QARequest.id == qa_request_id).first()
        if not qa_request:
            return None
        
        # 업데이트할 필드들
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(qa_request, field, value)
        
        qa_request.updated_at = datetime.now()
        db.commit()
        db.refresh(qa_request)
        
        documents = db.query(QARequestDocument).filter(
            QARequestDocument.qa_request_id == qa_request_id
        ).all()
        
        return self._build_qa_request_response(qa_request, documents)
    
    def update_qa_request_status(
        self, 
        db: Session, 
        qa_request_id: int, 
        status_data: QARequestStatusUpdate
    ) -> Optional[QARequestResponse]:
        """QA 요청서 상태 업데이트"""
        qa_request = db.query(QARequest).filter(QARequest.id == qa_request_id).first()
        if not qa_request:
            return None
        
        qa_request.status = status_data.status
        if status_data.assignee is not None:
            qa_request.assignee = status_data.assignee
        qa_request.updated_at = datetime.now()
        
        db.commit()
        db.refresh(qa_request)
        
        documents = db.query(QARequestDocument).filter(
            QARequestDocument.qa_request_id == qa_request_id
        ).all()
        
        return self._build_qa_request_response(qa_request, documents)
    
    def delete_qa_request(self, db: Session, qa_request_id: int) -> bool:
        """QA 요청서 삭제"""
        qa_request = db.query(QARequest).filter(QARequest.id == qa_request_id).first()
        if not qa_request:
            return False
        
        # 관련 문서들도 함께 삭제 (cascade로 자동 삭제됨)
        db.delete(qa_request)
        db.commit()
        return True
    
    def get_qa_request_stats(self, db: Session) -> dict:
        """QA 요청서 통계"""
        total = db.query(QARequest).count()
        pending = db.query(QARequest).filter(QARequest.status == "요청").count()
        in_progress = db.query(QARequest).filter(QARequest.status == "진행중").count()
        completed = db.query(QARequest).filter(QARequest.status == "완료").count()
        on_hold = db.query(QARequest).filter(QARequest.status == "보류").count()
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "on_hold": on_hold,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
    
    def _build_qa_request_response(
        self, 
        qa_request: QARequest, 
        documents: List[QARequestDocument]
    ) -> dict:
        """QA 요청서 응답 데이터 구성"""
        document_responses = [
            {
                "id": doc.id,
                "qa_request_id": doc.qa_request_id,
                "document_type": doc.document_type,
                "document_name": doc.document_name,
                "document_link": doc.document_link,
                "created_at": doc.created_at
            }
            for doc in documents
        ]
        
        return {
            "id": qa_request.id,
            "requester": qa_request.requester,
            "project_name": qa_request.project_name,
            "test_content": qa_request.test_content,
            "platform": qa_request.platform,
            "build_link": qa_request.build_link,
            "desired_deploy_date": qa_request.desired_deploy_date,
            "assignee": qa_request.assignee,
            "status": qa_request.status,
            "created_at": qa_request.created_at,
            "updated_at": qa_request.updated_at,
            "documents": document_responses
        }


# 서비스 인스턴스
qa_request_service = QARequestService()
