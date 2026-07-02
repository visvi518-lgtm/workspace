from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.core.database import Base


class ExerciseRoutine(Base):
    __tablename__ = "exercise_routines"

    id = Column(Integer, primary_key=True, index=True)
    purpose = Column(String(50), nullable=False)   # posture / strength / weight_management
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(50), nullable=True)  # beginner / intermediate / advanced
    sessions_per_week = Column(Integer, default=3)
    exercises = Column(JSON, default=list)          # [{name, sets, reps, rest, notes}]
    order_idx = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class DietRecommendation(Base):
    __tablename__ = "diet_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    purpose = Column(String(50), nullable=False)   # loss / gain / maintain / medical
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    carb_ratio = Column(Integer, default=50)        # %
    protein_ratio = Column(Integer, default=25)     # %
    fat_ratio = Column(Integer, default=25)         # %
    calorie_note = Column(String(500), nullable=True)
    nutrients = Column(JSON, default=list)          # [{name, target, unit, notes}]
    order_idx = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
