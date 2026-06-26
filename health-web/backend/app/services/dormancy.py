"""
2년 이상 미접속 사용자를 휴면 처리하는 스케줄 서비스
"""
import logging
from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

TWO_YEARS = timedelta(days=730)


def mark_dormant_accounts():
    """2년간 미접속 사용자를 휴면으로 전환합니다."""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - TWO_YEARS
        users = (
            db.query(User)
            .filter(
                User.is_active.is_(True),
                User.is_dormant.is_(False),
                User.is_admin.is_(False),
            )
            .all()
        )
        count = 0
        for user in users:
            last = user.last_login or user.created_at
            if last and last < cutoff:
                user.is_dormant = True
                count += 1
                logger.info(f"휴면 처리: {user.email}")

        db.commit()
        if count:
            logger.info(f"총 {count}명 휴면 처리 완료")
    except Exception as e:
        logger.error(f"휴면 처리 실패: {e}")
        db.rollback()
    finally:
        db.close()
