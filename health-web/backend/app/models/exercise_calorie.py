from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.core.database import Base


class ExerciseCalorie(Base):
    __tablename__ = "exercise_calories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)   # 유산소 / 근력 / 스포츠 / 기타
    met = Column(Float, nullable=False)              # Metabolic Equivalent of Task
    description = Column(String(300), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
