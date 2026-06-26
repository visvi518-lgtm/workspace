from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    nickname = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=True)

    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_dormant = Column(Boolean, default=False, nullable=False)

    banned_until = Column(DateTime(timezone=True), nullable=True)
    ban_reason = Column(Text, nullable=True)

    google_id = Column(String(255), nullable=True, unique=True)
    naver_id = Column(String(255), nullable=True, unique=True)

    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    exercise_logs = relationship("ExerciseLog", back_populates="user", cascade="all, delete-orphan")
    diet_logs = relationship("DietLog", back_populates="user", cascade="all, delete-orphan")
    weight_records = relationship("WeightRecord", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    height = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    medical_history = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    exercise_habits = Column(Text, nullable=True)
    nationality = Column(String(20), default="korean", nullable=False)
    exercise_purpose = Column(String(30), nullable=True)
    diet_purpose = Column(String(30), nullable=True)

    user = relationship("User", back_populates="profile")
