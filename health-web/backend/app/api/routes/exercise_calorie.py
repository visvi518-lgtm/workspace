from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user, get_db
from app.models.exercise_calorie import ExerciseCalorie
from app.models.user import User

router = APIRouter()

# ── Pydantic ──────────────────────────────────────────────────────────────────

class ExerciseCalorieCreate(BaseModel):
    name: str
    category: str
    met: float
    description: Optional[str] = None

class ExerciseCalorieUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    met: Optional[float] = None
    description: Optional[str] = None

class ToggleActive(BaseModel):
    is_active: bool


# ── Public ────────────────────────────────────────────────────────────────────

@router.get("/exercise-calories")
def get_exercise_calories(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ExerciseCalorie).filter(ExerciseCalorie.is_active.is_(True))
    if category:
        q = q.filter(ExerciseCalorie.category == category)
    return [_to_dict(r) for r in q.order_by(ExerciseCalorie.category, ExerciseCalorie.name).all()]


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/exercise-calories")
def admin_list(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    rows = db.query(ExerciseCalorie).order_by(ExerciseCalorie.category, ExerciseCalorie.name).all()
    return [_to_dict_admin(r) for r in rows]


@router.post("/admin/exercise-calories", status_code=201)
def admin_create(
    data: ExerciseCalorieCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = ExerciseCalorie(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_dict_admin(row)


@router.put("/admin/exercise-calories/{rid}")
def admin_update(
    rid: int,
    data: ExerciseCalorieUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseCalorie).filter(ExerciseCalorie.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(row, key, val)
    db.commit()
    db.refresh(row)
    return _to_dict_admin(row)


@router.patch("/admin/exercise-calories/{rid}")
def admin_toggle(
    rid: int,
    data: ToggleActive,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseCalorie).filter(ExerciseCalorie.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    row.is_active = data.is_active
    db.commit()
    return {"message": "업데이트되었습니다."}


@router.delete("/admin/exercise-calories/{rid}")
def admin_delete(
    rid: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseCalorie).filter(ExerciseCalorie.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"message": "삭제되었습니다."}


@router.post("/admin/exercise-calories/seed")
def admin_seed(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    existing_names = {r.name for r in db.query(ExerciseCalorie.name).all()}

    defaults = [
        # ── 유산소 ──────────────────────────────────────────────
        ("걷기 (느린 속도, 3km/h)", "유산소", 2.5, "가벼운 산책 수준"),
        ("걷기 (보통 속도, 5km/h)", "유산소", 3.5, "일반적인 걷기 속도"),
        ("빠르게 걷기 (6km/h)", "유산소", 4.5, "다소 빠른 보행"),
        ("조깅 (7km/h)", "유산소", 7.0, "가벼운 달리기"),
        ("달리기 (9km/h)", "유산소", 9.0, "중간 강도 달리기"),
        ("달리기 (12km/h)", "유산소", 11.5, "빠른 달리기"),
        ("달리기 (16km/h)", "유산소", 14.5, "매우 빠른 달리기"),
        ("사이클 (보통, 16km/h)", "유산소", 6.0, "일반 자전거 타기"),
        ("사이클 (빠른, 22km/h)", "유산소", 10.0, "빠른 자전거 타기"),
        ("실내 사이클 (중강도)", "유산소", 8.0, "스피닝, 실내 자전거"),
        ("수영 (자유형, 보통)", "유산소", 6.0, "일반적인 자유형"),
        ("수영 (자유형, 빠름)", "유산소", 9.5, "빠른 자유형"),
        ("수영 (평영)", "유산소", 5.3, "일반적인 평영"),
        ("줄넘기 (보통)", "유산소", 10.0, "일반적인 줄넘기"),
        ("줄넘기 (빠름)", "유산소", 12.0, "빠른 줄넘기"),
        ("등산 (오르막)", "유산소", 6.0, "산 오르기"),
        ("계단 오르기", "유산소", 8.0, "계단 오르내리기"),
        ("HIIT (고강도 인터벌)", "유산소", 9.0, "버피, 점프 스쿼트 등 포함"),
        ("에어로빅", "유산소", 6.5, "일반 에어로빅 수업"),
        ("킥복싱/복싱 (유산소)", "유산소", 7.0, "유산소 복싱 운동"),
        ("인라인 스케이팅", "유산소", 7.5, "일반 속도"),
        ("노래방 (춤추며)", "유산소", 4.0, "경쾌하게 움직이는 경우"),
        # ── 근력 ──────────────────────────────────────────────
        ("웨이트 트레이닝 (일반)", "근력", 3.5, "기구·바벨 이용 근력 운동"),
        ("웨이트 트레이닝 (고강도)", "근력", 6.0, "무거운 중량, 짧은 휴식"),
        ("스쿼트", "근력", 5.0, "바벨/덤벨 스쿼트"),
        ("데드리프트", "근력", 6.0, "고중량 데드리프트"),
        ("벤치프레스", "근력", 4.0, "바벨 벤치프레스"),
        ("풀업/친업", "근력", 5.0, "매달려 당기는 운동"),
        ("딥스", "근력", 4.5, "삼두·가슴 딥스"),
        ("케틀벨 스윙", "근력", 8.0, "전신 근력+유산소"),
        ("TRX 서스펜션 트레이닝", "근력", 5.0, "자체 중량 서스펜션"),
        ("크로스핏 WOD", "근력", 9.0, "고강도 기능성 훈련"),
        ("플라이오메트릭 (점프 훈련)", "근력", 7.0, "파워 향상 점프 운동"),
        ("버피", "근력", 8.0, "전신 복합 운동"),
        # ── 스포츠 ──────────────────────────────────────────────
        ("축구", "스포츠", 7.0, "11인제 경기"),
        ("풋살", "스포츠", 7.5, "실내 소형 축구"),
        ("농구", "스포츠", 6.5, "경기 기준"),
        ("배드민턴", "스포츠", 5.5, "복식·단식 혼합"),
        ("테니스 (단식)", "스포츠", 7.0, "단식 경기"),
        ("테니스 (복식)", "스포츠", 5.0, "복식 경기"),
        ("탁구", "스포츠", 4.0, "일반 경기"),
        ("볼링", "스포츠", 3.0, "일반 볼링"),
        ("골프 (걸으며)", "스포츠", 4.5, "카트 없이 걸으며 플레이"),
        ("클라이밍 (실내)", "스포츠", 7.5, "볼더링·리드 클라이밍"),
        ("수상스키/웨이크보드", "스포츠", 6.0, "수상 스포츠"),
        ("야구/소프트볼", "스포츠", 5.0, "경기 기준"),
        ("배구", "스포츠", 4.0, "일반 배구 경기"),
        # ── 기타 ──────────────────────────────────────────────
        ("요가 (하타/일반)", "기타", 2.5, "스트레칭 중심 요가"),
        ("요가 (빈야사/파워)", "기타", 4.0, "동적 흐름 요가"),
        ("요가 (핫/비크람)", "기타", 5.0, "고온 환경 요가"),
        ("필라테스 (매트)", "기타", 3.0, "매트 필라테스"),
        ("필라테스 (기구)", "기타", 3.5, "리포머 등 기구 사용"),
        ("스트레칭", "기타", 2.3, "정적 스트레칭"),
        ("태극권", "기타", 3.0, "기공·태극권"),
        ("댄스 (일반)", "기타", 4.8, "사교댄스, 방송댄스 등"),
        ("댄스 (빠름, 케이팝 등)", "기타", 6.5, "활발한 댄스"),
        ("집안일 (청소, 걸레질)", "기타", 3.3, "활동적 집안일"),
        ("계단 내려가기", "기타", 3.0, "계단 내려오기"),
    ]

    added = 0
    for name, category, met, description in defaults:
        if name not in existing_names:
            db.add(ExerciseCalorie(name=name, category=category, met=met, description=description))
            added += 1

    db.commit()
    return {"message": f"운동 칼로리 데이터 {added}개가 추가되었습니다.", "added": added}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_dict(r: ExerciseCalorie) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "category": r.category,
        "met": r.met,
        "description": r.description,
    }


def _to_dict_admin(r: ExerciseCalorie) -> dict:
    return {
        **_to_dict(r),
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
