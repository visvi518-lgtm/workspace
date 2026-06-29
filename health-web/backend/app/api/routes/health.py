import base64
import calendar
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.health import DietLog, ExerciseLog, WeightRecord
from app.models.user import User, UserProfile

router = APIRouter(prefix="/health", tags=["health"])


# ─── Exercise ───

class ExerciseLogCreate(BaseModel):
    date: date
    content: Optional[str] = None
    duration_minutes: int = 0
    exercises: list[dict] = []


@router.get("/exercise")
def get_exercise_logs(
    month: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ExerciseLog).filter(ExerciseLog.user_id == current_user.id)
    if month:
        year, mon = map(int, month.split("-"))
        start = date(year, mon, 1)
        end = date(year, mon, calendar.monthrange(year, mon)[1])
        query = query.filter(ExerciseLog.date >= start, ExerciseLog.date <= end)
    logs = query.order_by(ExerciseLog.date.desc()).all()
    return [
        {
            "id": l.id,
            "date": str(l.date),
            "content": l.content,
            "duration_minutes": l.duration_minutes,
            "exercises": l.exercises or [],
        }
        for l in logs
    ]


@router.post("/exercise", status_code=201)
def create_exercise_log(
    data: ExerciseLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = ExerciseLog(
        user_id=current_user.id,
        date=data.date,
        content=data.content,
        duration_minutes=data.duration_minutes,
        exercises=data.exercises,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id, "date": str(log.date)}


@router.put("/exercise/{log_id}")
def update_exercise_log(
    log_id: int,
    data: ExerciseLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = db.get(ExerciseLog, log_id)
    if not log or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    log.date = data.date
    log.content = data.content
    log.duration_minutes = data.duration_minutes
    log.exercises = data.exercises
    db.commit()
    return {"message": "업데이트 완료"}


# ─── Diet ───

class DietLogCreate(BaseModel):
    date: date
    meals: list[dict] = []
    note: Optional[str] = None


@router.get("/diet")
def get_diet_logs(
    month: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(DietLog).filter(DietLog.user_id == current_user.id)
    if month:
        year, mon = map(int, month.split("-"))
        start = date(year, mon, 1)
        end = date(year, mon, calendar.monthrange(year, mon)[1])
        query = query.filter(DietLog.date >= start, DietLog.date <= end)
    logs = query.order_by(DietLog.date.desc()).all()
    return [
        {
            "id": l.id,
            "date": str(l.date),
            "meals": l.meals or [],
            "total_calories": l.total_calories,
            "note": l.note,
        }
        for l in logs
    ]


@router.post("/diet", status_code=201)
def create_diet_log(
    data: DietLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = sum(
        food.get("calories", 0)
        for meal in data.meals
        for food in meal.get("foods", [])
    )
    log = DietLog(
        user_id=current_user.id,
        date=data.date,
        meals=data.meals,
        total_calories=total,
        note=data.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id, "date": str(log.date), "total_calories": total}


@router.put("/diet/{log_id}")
def update_diet_log(
    log_id: int,
    data: DietLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = db.get(DietLog, log_id)
    if not log or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="기록을 찾을 수 없습니다.")
    total = sum(food.get("calories", 0) for meal in data.meals for food in meal.get("foods", []))
    log.date = data.date
    log.meals = data.meals
    log.total_calories = total
    log.note = data.note
    db.commit()
    return {"message": "업데이트 완료"}


# ─── Weight ───

class WeightCreate(BaseModel):
    date: date
    weight: float


@router.get("/weight")
def get_weight_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(WeightRecord)
        .filter(WeightRecord.user_id == current_user.id)
        .order_by(WeightRecord.date.asc())
        .all()
    )
    return [{"id": r.id, "date": str(r.date), "weight": r.weight} for r in records]


@router.post("/weight", status_code=201)
def add_weight_record(
    data: WeightCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = WeightRecord(user_id=current_user.id, date=data.date, weight=data.weight)
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "date": str(record.date), "weight": record.weight}


# ─── Calendar ───

@router.get("/calendar")
def get_calendar_data(
    month: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    end = date(year, mon, calendar.monthrange(year, mon)[1])
    ex_logs = (
        db.query(ExerciseLog)
        .filter(ExerciseLog.user_id == current_user.id)
        .filter(ExerciseLog.date >= start, ExerciseLog.date <= end)
        .all()
    )
    diet_logs = (
        db.query(DietLog)
        .filter(DietLog.user_id == current_user.id)
        .filter(DietLog.date >= start, DietLog.date <= end)
        .all()
    )
    return {
        "exercise_dates": [str(l.date) for l in ex_logs],
        "diet_dates": [str(l.date) for l in diet_logs],
    }


# ─── AI Calorie Analysis ───

@router.post("/analyze-calories")
async def analyze_calories(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="AI 서비스가 설정되지 않았습니다. .env에 GEMINI_API_KEY를 입력해 주세요.")

    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기가 너무 큽니다. (최대 10MB)")

    import json
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    img = PILImage.open(io.BytesIO(content))
    prompt = (
        "이 음식 사진을 보고 다음 JSON 형식으로만 답해주세요:\n"
        '{"name": "음식 이름", "calories": 칼로리(숫자), "amount": "양 설명"}\n'
        "칼로리는 1인분 기준으로 추정하세요. JSON만 출력하세요."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, img],
    )

    try:
        text = response.text.strip().strip("```json").strip("```").strip()
        data = json.loads(text)
        return {"name": data.get("name", "알 수 없음"), "calories": int(data.get("calories", 0)), "amount": data.get("amount", "")}
    except Exception:
        raise HTTPException(status_code=500, detail="칼로리 분석에 실패했습니다.")


# ─── Health Profile Update ───

class HealthProfileUpdate(BaseModel):
    exercise_purpose: Optional[str] = None
    diet_purpose: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None


@router.put("/profile")
def update_health_profile(
    data: HealthProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.profile:
        current_user.profile = UserProfile(user_id=current_user.id)
        db.add(current_user.profile)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(current_user.profile, field, value)

    db.commit()
    return {"message": "업데이트 완료"}
