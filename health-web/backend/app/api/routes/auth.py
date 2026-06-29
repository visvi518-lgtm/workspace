from datetime import datetime, timezone
from urllib.parse import urlencode
import secrets

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token, get_password_hash,
    validate_password, verify_password
)
from app.models.user import User, UserProfile

GOOGLE_REDIRECT_URI = f"{settings.BACKEND_URL}/api/v1/auth/google/callback"
NAVER_REDIRECT_URI = f"{settings.BACKEND_URL}/api/v1/auth/naver/callback"


def _unique_nickname(db: Session, base: str) -> str:
    base = (base or "user").strip()[:20]
    nickname = base
    i = 1
    while db.query(User).filter(User.nickname == nickname).first():
        nickname = f"{base[:18]}{i}"
        i += 1
    return nickname

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nickname: str
    name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = None
    name: str | None = None
    profile: dict | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "name": user.name,
        "is_admin": user.is_admin,
        "is_active": user.is_active,
        "is_dormant": user.is_dormant,
        "banned_until": user.banned_until.isoformat() if user.banned_until else None,
        "ban_reason": user.ban_reason,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "profile": {
            "height": user.profile.height,
            "weight": user.profile.weight,
            "medical_history": user.profile.medical_history,
            "medications": user.profile.medications,
            "exercise_habits": user.profile.exercise_habits,
            "nationality": user.profile.nationality,
            "exercise_purpose": user.profile.exercise_purpose,
            "diet_purpose": user.profile.diet_purpose,
        } if user.profile else None,
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if not validate_password(data.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="비밀번호는 영문, 숫자, 특수문자를 포함한 8~20자여야 합니다."
        )
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 이메일입니다.")
    if db.query(User).filter(User.nickname == data.nickname).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 닉네임입니다.")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        nickname=data.nickname,
        name=data.name,
    )
    user.profile = UserProfile()
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "회원가입이 완료되었습니다."}


@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="비활성화된 계정입니다.")
    if user.is_dormant:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="dormant")
    if user.banned_until and user.banned_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="banned")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": serialize_user(user)}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)


@router.put("/profile")
def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.nickname and data.nickname != current_user.nickname:
        if db.query(User).filter(User.nickname == data.nickname, User.id != current_user.id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 닉네임입니다.")
        current_user.nickname = data.nickname

    if data.name is not None:
        current_user.name = data.name

    if data.profile:
        if not current_user.profile:
            current_user.profile = UserProfile(user_id=current_user.id)
        for key, value in data.profile.items():
            if hasattr(current_user.profile, key):
                setattr(current_user.profile, key, value)

    db.commit()
    db.refresh(current_user)
    return serialize_user(current_user)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    # 유저가 없어도 동일한 응답 (이메일 노출 방지)
    if user:
        from datetime import timedelta
        from app.core.email import send_password_reset_email
        reset_token = create_access_token(
            {"sub": str(user.id), "type": "password_reset"},
            expires_delta=timedelta(hours=1),
        )
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        try:
            send_password_reset_email(user.email, reset_url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이메일 전송에 실패했습니다: {str(e)}")
    return {"message": "입력하신 이메일로 재설정 링크를 발송했습니다."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    from app.core.security import decode_token
    payload = decode_token(data.token)
    if not payload or payload.get("type") != "password_reset":
        raise HTTPException(status_code=400, detail="유효하지 않거나 만료된 링크입니다.")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    if not validate_password(data.new_password):
        raise HTTPException(status_code=422, detail="비밀번호는 영문, 숫자, 특수문자를 포함한 8~20자여야 합니다.")

    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}


@router.put("/password")
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.password_hash or not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다.")
    if not validate_password(data.new_password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="비밀번호 형식이 올바르지 않습니다.")

    current_user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


# ─── Google OAuth ───

@router.get("/google")
def google_login():
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Google OAuth가 설정되지 않았습니다. .env에 GOOGLE_CLIENT_ID를 입력해 주세요.")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
    }
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None, db: Session = Depends(get_db)):
    if error or not code:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=google_cancelled")

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=google_failed")

        info_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info = info_res.json()

    google_id = info.get("id")
    email = info.get("email")
    name = info.get("name", "")

    if not google_id or not email:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=google_info")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            nickname = _unique_nickname(db, name or email.split("@")[0])
            user = User(email=email, nickname=nickname, name=name, google_id=google_id)
            user.profile = UserProfile()
            db.add(user)

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={token}")


# ─── Naver OAuth ───

@router.get("/naver")
def naver_login():
    if not settings.NAVER_CLIENT_ID:
        raise HTTPException(status_code=400, detail="Naver OAuth가 설정되지 않았습니다.")
    state = secrets.token_urlsafe(16)
    params = {
        "response_type": "code",
        "client_id": settings.NAVER_CLIENT_ID,
        "redirect_uri": NAVER_REDIRECT_URI,
        "state": state,
    }
    return RedirectResponse(f"https://nid.naver.com/oauth2.0/authorize?{urlencode(params)}")


@router.get("/naver/callback")
async def naver_callback(code: str = None, state: str = None, error: str = None, db: Session = Depends(get_db)):
    if error or not code:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=naver_cancelled")

    async with httpx.AsyncClient() as client:
        token_res = await client.get(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "code": code,
                "state": state,
            },
        )
        token_data = token_res.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=naver_failed")

        info_res = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        info = info_res.json()

    resp = info.get("response", {})
    naver_id = resp.get("id")
    email = resp.get("email", "")
    name = resp.get("name", "")
    nickname_base = resp.get("nickname") or name or (email.split("@")[0] if email else "")

    if not naver_id:
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=naver_info")

    user = db.query(User).filter(User.naver_id == naver_id).first()
    if not user:
        if email:
            user = db.query(User).filter(User.email == email).first()
        if user:
            user.naver_id = naver_id
        else:
            unique_nick = _unique_nickname(db, nickname_base or "user")
            fallback_email = email or f"naver_{naver_id}@naver.com"
            user = User(email=fallback_email, nickname=unique_nick, name=name, naver_id=naver_id)
            user.profile = UserProfile()
            db.add(user)

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/callback?token={token}")
