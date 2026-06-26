from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models.board import Post
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

BAN_DURATIONS = {
    "3d": timedelta(days=3),
    "3w": timedelta(weeks=3),
    "3m": timedelta(days=90),
    "3y": timedelta(days=1095),
    "permanent": timedelta(days=365 * 100),
}


class BanRequest(BaseModel):
    user_id: int
    duration: str
    reason: str


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "is_dormant": user.is_dormant,
        "banned_until": user.banned_until.isoformat() if user.banned_until else None,
        "ban_reason": user.ban_reason,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        query = query.filter(
            or_(User.email.ilike(f"%{search}%"), User.nickname.ilike(f"%{search}%"))
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": [serialize_user(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.post("/users/ban")
def ban_user(
    data: BanRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if data.duration not in BAN_DURATIONS:
        raise HTTPException(status_code=400, detail="유효하지 않은 정지 기간입니다.")

    user = db.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if user.is_admin:
        raise HTTPException(status_code=403, detail="관리자 계정은 정지할 수 없습니다.")

    user.banned_until = datetime.now(timezone.utc) + BAN_DURATIONS[data.duration]
    user.ban_reason = data.reason
    db.commit()
    return {"message": f"{user.nickname} 계정이 정지되었습니다."}


@router.post("/users/{user_id}/unban")
def unban_user(
    user_id: int,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    user.banned_until = None
    user.ban_reason = None
    db.commit()
    return {"message": "계정 정지가 해제되었습니다."}


@router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(
    post_id: int,
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    post.is_deleted = True
    db.commit()


@router.get("/stats")
def get_stats(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    total_users = db.query(func.count(User.id)).scalar()
    new_today = db.query(func.count(User.id)).filter(func.date(User.created_at) == today).scalar()
    total_posts = db.query(func.count(Post.id)).filter(Post.is_deleted.is_(False)).scalar()
    banned = (
        db.query(func.count(User.id))
        .filter(User.banned_until > datetime.now(timezone.utc))
        .scalar()
    )
    return {
        "total_users": total_users,
        "new_users_today": new_today,
        "total_posts": total_posts,
        "banned_users": banned,
    }
