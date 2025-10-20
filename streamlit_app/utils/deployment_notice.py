"""
배포날짜 공지 관리 유틸리티
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEPLOYMENT_NOTICE_FILE = os.path.join(PROJECT_ROOT, "deployment_notice.json")

def load_deployment_notice() -> Dict:
    """배포날짜 공지 정보 로드"""
    try:
        if os.path.exists(DEPLOYMENT_NOTICE_FILE):
            with open(DEPLOYMENT_NOTICE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 기본값 반환
            return {
                "deployment_date": "",
                "notice_message": "",
                "is_active": False,
                "last_updated": ""
            }
    except Exception as e:
        print(f"배포날짜 공지 로드 오류: {e}")
        return {
            "deployment_date": "",
            "notice_message": "",
            "is_active": False,
            "last_updated": ""
        }

def save_deployment_notice(deployment_date: str, notice_message: str, is_active: bool = True) -> bool:
    """배포날짜 공지 정보 저장"""
    try:
        notice_data = {
            "deployment_date": deployment_date,
            "notice_message": notice_message,
            "is_active": is_active,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(DEPLOYMENT_NOTICE_FILE, 'w', encoding='utf-8') as f:
            json.dump(notice_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"배포날짜 공지 저장 오류: {e}")
        return False

def deactivate_deployment_notice() -> bool:
    """배포날짜 공지 비활성화"""
    try:
        notice_data = load_deployment_notice()
        notice_data["is_active"] = False
        notice_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(DEPLOYMENT_NOTICE_FILE, 'w', encoding='utf-8') as f:
            json.dump(notice_data, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        print(f"배포날짜 공지 비활성화 오류: {e}")
        return False

def get_active_deployment_notice() -> Optional[Dict]:
    """활성화된 배포날짜 공지 정보 반환"""
    notice_data = load_deployment_notice()
    if notice_data.get("is_active", False) and notice_data.get("deployment_date"):
        return notice_data
    return None
