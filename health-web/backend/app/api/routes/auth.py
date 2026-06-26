from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import (
    create_access_token, get_password_hash,
    validate_password, verify_password
)
from app.models.user import User, UserProfile

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
