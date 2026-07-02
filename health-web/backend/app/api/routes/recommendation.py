from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_current_user, get_db
from app.models.recommendation import DietRecommendation, ExerciseRoutine
from app.models.user import User

router = APIRouter()

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ExerciseCreate(BaseModel):
    purpose: str
    name: str
    description: Optional[str] = None
    difficulty: Optional[str] = "beginner"
    sessions_per_week: int = 3
    exercises: list = []
    order_idx: int = 0

class ExerciseUpdate(BaseModel):
    purpose: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    sessions_per_week: Optional[int] = None
    exercises: Optional[list] = None
    order_idx: Optional[int] = None

class DietCreate(BaseModel):
    purpose: str
    name: str
    description: Optional[str] = None
    carb_ratio: int = 50
    protein_ratio: int = 25
    fat_ratio: int = 25
    calorie_note: Optional[str] = None
    nutrients: list = []
    order_idx: int = 0

class DietUpdate(BaseModel):
    purpose: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    carb_ratio: Optional[int] = None
    protein_ratio: Optional[int] = None
    fat_ratio: Optional[int] = None
    calorie_note: Optional[str] = None
    nutrients: Optional[list] = None
    order_idx: Optional[int] = None

class ToggleActive(BaseModel):
    is_active: bool


# ── User endpoints (auth required) ───────────────────────────────────────────

@router.get("/recommendations/exercise")
def get_exercise_recommendations(
    purpose: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(ExerciseRoutine).filter(ExerciseRoutine.is_active.is_(True))
    if purpose:
        q = q.filter(ExerciseRoutine.purpose == purpose)
    return [_exercise_dict(r) for r in q.order_by(ExerciseRoutine.order_idx).all()]


@router.get("/recommendations/diet")
def get_diet_recommendations(
    purpose: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(DietRecommendation).filter(DietRecommendation.is_active.is_(True))
    if purpose:
        q = q.filter(DietRecommendation.purpose == purpose)
    return [_diet_dict(r) for r in q.order_by(DietRecommendation.order_idx).all()]


# ── Admin: Exercise Routines ───────────────────────────────────────────────────

@router.get("/admin/recommendations/exercise")
def admin_list_exercise(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    rows = (
        db.query(ExerciseRoutine)
        .order_by(ExerciseRoutine.purpose, ExerciseRoutine.order_idx)
        .all()
    )
    return [_exercise_dict_admin(r) for r in rows]


@router.post("/admin/recommendations/exercise", status_code=201)
def admin_create_exercise(
    data: ExerciseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = ExerciseRoutine(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _exercise_dict_admin(row)


@router.put("/admin/recommendations/exercise/{rid}")
def admin_update_exercise(
    rid: int,
    data: ExerciseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseRoutine).filter(ExerciseRoutine.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="루틴을 찾을 수 없습니다.")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(row, key, val)
    db.commit()
    db.refresh(row)
    return _exercise_dict_admin(row)


@router.patch("/admin/recommendations/exercise/{rid}")
def admin_toggle_exercise(
    rid: int,
    data: ToggleActive,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseRoutine).filter(ExerciseRoutine.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="루틴을 찾을 수 없습니다.")
    row.is_active = data.is_active
    db.commit()
    return {"message": "업데이트되었습니다."}


@router.delete("/admin/recommendations/exercise/{rid}")
def admin_delete_exercise(
    rid: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(ExerciseRoutine).filter(ExerciseRoutine.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="루틴을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"message": "삭제되었습니다."}


# ── Admin: Diet Recommendations ───────────────────────────────────────────────

@router.get("/admin/recommendations/diet")
def admin_list_diet(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    rows = (
        db.query(DietRecommendation)
        .order_by(DietRecommendation.purpose, DietRecommendation.order_idx)
        .all()
    )
    return [_diet_dict_admin(r) for r in rows]


@router.post("/admin/recommendations/diet", status_code=201)
def admin_create_diet(
    data: DietCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = DietRecommendation(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _diet_dict_admin(row)


@router.put("/admin/recommendations/diet/{rid}")
def admin_update_diet(
    rid: int,
    data: DietUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(DietRecommendation).filter(DietRecommendation.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="식단 추천을 찾을 수 없습니다.")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(row, key, val)
    db.commit()
    db.refresh(row)
    return _diet_dict_admin(row)


@router.patch("/admin/recommendations/diet/{rid}")
def admin_toggle_diet(
    rid: int,
    data: ToggleActive,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(DietRecommendation).filter(DietRecommendation.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="식단 추천을 찾을 수 없습니다.")
    row.is_active = data.is_active
    db.commit()
    return {"message": "업데이트되었습니다."}


@router.delete("/admin/recommendations/diet/{rid}")
def admin_delete_diet(
    rid: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    row = db.query(DietRecommendation).filter(DietRecommendation.id == rid).first()
    if not row:
        raise HTTPException(status_code=404, detail="식단 추천을 찾을 수 없습니다.")
    db.delete(row)
    db.commit()
    return {"message": "삭제되었습니다."}


# ── Seed default data ─────────────────────────────────────────────────────────

@router.post("/admin/recommendations/seed")
def admin_seed(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    added = 0
    existing_exercise_names = {r.name for r in db.query(ExerciseRoutine.name).all()}
    existing_diet_names = {r.name for r in db.query(DietRecommendation.name).all()}

    exercise_defaults = [
            ExerciseRoutine(
                purpose="posture",
                name="코어 & 자세 교정 루틴",
                description="장시간 앉아있는 현대인을 위한 자세 교정 및 코어 강화 루틴입니다. 주 3회, 약 45분 소요.",
                difficulty="beginner",
                sessions_per_week=3,
                order_idx=0,
                exercises=[
                    {"name": "플랭크", "sets": 3, "reps": "30초", "rest": "30초", "notes": "허리를 일자로 유지, 엉덩이가 올라가지 않도록"},
                    {"name": "버드독", "sets": 3, "reps": "12회(양쪽)", "rest": "30초", "notes": "코어에 집중, 반대쪽 팔·다리를 동시에 뻗기"},
                    {"name": "고양이-소 스트레칭", "sets": 2, "reps": "10회", "rest": "20초", "notes": "천천히 호흡과 함께, 척추 움직임에 집중"},
                    {"name": "글루트 브릿지", "sets": 3, "reps": "15회", "rest": "45초", "notes": "엉덩이를 끝까지 수축, 허리가 과신전되지 않도록"},
                    {"name": "어깨 외회전 (밴드)", "sets": 3, "reps": "15회", "rest": "30초", "notes": "팔꿈치를 옆구리에 고정, 라운드숄더 교정"},
                    {"name": "페이스 풀 (밴드)", "sets": 3, "reps": "15회", "rest": "30초", "notes": "후면 삼각근·회전근개 강화, 자세 개선"},
                    {"name": "흉추 가동성 운동 (폼롤러)", "sets": 2, "reps": "1분", "rest": "30초", "notes": "날개뼈 사이 충분히 이완"},
                ],
            ),
            ExerciseRoutine(
                purpose="strength",
                name="초보자 전신 근력 루틴 (주 3회)",
                description="근력 향상을 목표로 하는 초·중급자를 위한 전신 근력 운동 루틴입니다. 복합 운동 중심으로 구성되어 있습니다.",
                difficulty="beginner",
                sessions_per_week=3,
                order_idx=0,
                exercises=[
                    {"name": "바벨 스쿼트", "sets": 4, "reps": "6-8회", "rest": "2분", "notes": "허벅지가 지면과 평행해질 때까지, 무릎이 발끝 방향"},
                    {"name": "바벨 벤치프레스", "sets": 4, "reps": "6-8회", "rest": "2분", "notes": "가슴 하부에 바가 닿도록, 견갑골 모아서 고정"},
                    {"name": "데드리프트", "sets": 3, "reps": "5회", "rest": "3분", "notes": "허리 중립 유지 필수, 바를 몸에 붙여서 당기기"},
                    {"name": "오버헤드 프레스", "sets": 3, "reps": "8-10회", "rest": "90초", "notes": "코어 긴장 유지, 바가 턱을 넘어갈 때 머리를 앞으로"},
                    {"name": "바벨 로우", "sets": 3, "reps": "8-10회", "rest": "90초", "notes": "45도 앞으로 숙인 자세, 배꼽 방향으로 당기기"},
                    {"name": "풀업 (또는 랫 풀다운)", "sets": 3, "reps": "최대 (또는 10-12회)", "rest": "2분", "notes": "광배근 수축 의식, 불가 시 밴드 보조"},
                ],
            ),
            ExerciseRoutine(
                purpose="weight_management",
                name="유산소 + 근력 복합 루틴 (주 4회)",
                description="체중 감량 및 체형 개선을 위한 유산소와 근력을 결합한 루틴입니다. 칼로리 소모와 기초대사율 향상을 동시에 노립니다.",
                difficulty="beginner",
                sessions_per_week=4,
                order_idx=0,
                exercises=[
                    {"name": "워밍업 (빠른 걷기 또는 사이클)", "sets": 1, "reps": "10분", "rest": "-", "notes": "심박수를 서서히 올리기"},
                    {"name": "점프 스쿼트", "sets": 3, "reps": "15회", "rest": "45초", "notes": "착지 시 무릎 부드럽게, 전신 근육 활성화"},
                    {"name": "버피", "sets": 3, "reps": "10회", "rest": "60초", "notes": "전신 유산소, 체력에 따라 횟수 조절"},
                    {"name": "케틀벨 스윙", "sets": 4, "reps": "15회", "rest": "45초", "notes": "고관절 힌지 동작, 팔로 당기지 않기"},
                    {"name": "마운틴 클라이머", "sets": 3, "reps": "20회(양쪽)", "rest": "30초", "notes": "코어 긴장 유지, 엉덩이가 올라가지 않도록"},
                    {"name": "런지 (또는 워킹 런지)", "sets": 3, "reps": "12회(양쪽)", "rest": "45초", "notes": "앞 무릎이 발끝을 넘지 않도록"},
                    {"name": "유산소 (러닝 또는 사이클)", "sets": 1, "reps": "20-30분", "rest": "-", "notes": "최대심박수의 65-75% 유지 (중강도)"},
                ],
            ),
            # ── 추가 루틴 ──────────────────────────────────────────
            ExerciseRoutine(
                purpose="posture",
                name="요가 기반 유연성 & 자세 루틴",
                description="요가 동작을 중심으로 유연성을 높이고 자세를 교정하는 루틴입니다. 도구 없이 어디서나 가능합니다.",
                difficulty="beginner",
                sessions_per_week=3,
                order_idx=1,
                exercises=[
                    {"name": "다운독 (Downward Dog)", "sets": 3, "reps": "30초", "rest": "15초", "notes": "등을 곧게 펴고, 발뒤꿈치를 지면 쪽으로"},
                    {"name": "차일드 포즈", "sets": 2, "reps": "45초", "rest": "15초", "notes": "등·어깨·엉덩이 이완"},
                    {"name": "코브라 스트레칭", "sets": 3, "reps": "20초", "rest": "20초", "notes": "허리 과신전 주의, 복부로 받치기"},
                    {"name": "피전 포즈 (비둘기 자세)", "sets": 2, "reps": "40초(양쪽)", "rest": "15초", "notes": "고관절 외회전 이완"},
                    {"name": "워리어 II", "sets": 3, "reps": "30초(양쪽)", "rest": "20초", "notes": "코어 안정, 무릎이 발끝 방향"},
                    {"name": "슈퍼맨 자세", "sets": 3, "reps": "15회", "rest": "30초", "notes": "척추 기립근 강화"},
                    {"name": "목·어깨 스트레칭", "sets": 2, "reps": "각 방향 20초", "rest": "10초", "notes": "천천히 부드럽게, 반동 금지"},
                ],
            ),
            ExerciseRoutine(
                purpose="strength",
                name="상체 집중 루틴 (Push/Pull 2분할)",
                description="가슴·어깨·삼두(Push)와 등·이두(Pull)를 격일로 훈련하는 상체 집중 루틴입니다.",
                difficulty="intermediate",
                sessions_per_week=4,
                order_idx=1,
                exercises=[
                    {"name": "[Push] 인클라인 덤벨 프레스", "sets": 4, "reps": "10-12회", "rest": "90초", "notes": "상부 가슴 집중"},
                    {"name": "[Push] 덤벨 숄더 프레스", "sets": 3, "reps": "10-12회", "rest": "90초", "notes": "삼각근 전면 집중"},
                    {"name": "[Push] 케이블 플라이", "sets": 3, "reps": "12-15회", "rest": "60초", "notes": "가슴 내측 수축 의식"},
                    {"name": "[Push] 라테럴 레이즈", "sets": 4, "reps": "15회", "rest": "60초", "notes": "측면 삼각근, 팔꿈치 살짝 구부림"},
                    {"name": "[Pull] 풀업 / 랫 풀다운", "sets": 4, "reps": "8-10회", "rest": "2분", "notes": "광배근 전체 수축"},
                    {"name": "[Pull] 시티드 케이블 로우", "sets": 4, "reps": "10-12회", "rest": "90초", "notes": "등 중앙·능형근 집중"},
                    {"name": "[Pull] 페이스 풀", "sets": 3, "reps": "15회", "rest": "60초", "notes": "후면 삼각근·회전근개"},
                ],
            ),
            ExerciseRoutine(
                purpose="strength",
                name="하체 집중 루틴 (Leg Day)",
                description="대퇴사두·햄스트링·둔근을 집중 훈련하는 하체 루틴입니다. 주 2회 실시를 권장합니다.",
                difficulty="intermediate",
                sessions_per_week=2,
                order_idx=2,
                exercises=[
                    {"name": "바벨 백 스쿼트", "sets": 5, "reps": "5-6회", "rest": "3분", "notes": "고중량 복합 운동, 허리 중립 필수"},
                    {"name": "루마니안 데드리프트", "sets": 4, "reps": "8-10회", "rest": "2분", "notes": "햄스트링 스트레칭 의식, 등 중립"},
                    {"name": "레그 프레스", "sets": 4, "reps": "10-12회", "rest": "90초", "notes": "발 간격으로 강조 부위 조절"},
                    {"name": "워킹 런지", "sets": 3, "reps": "12회(양쪽)", "rest": "90초", "notes": "둔근·대퇴사두 복합 자극"},
                    {"name": "레그 컬 (머신)", "sets": 4, "reps": "12-15회", "rest": "60초", "notes": "햄스트링 고립 운동"},
                    {"name": "카프 레이즈", "sets": 4, "reps": "20회", "rest": "45초", "notes": "종아리 근육, 끝에서 1-2초 수축"},
                    {"name": "힙 어브덕션 (머신 또는 밴드)", "sets": 3, "reps": "15-20회", "rest": "60초", "notes": "중둔근 강화"},
                ],
            ),
            ExerciseRoutine(
                purpose="weight_management",
                name="HIIT 고강도 인터벌 루틴 (주 3회)",
                description="짧은 시간에 최대 칼로리를 소모하는 HIIT 루틴입니다. 20초 전력·10초 휴식 타바타 방식.",
                difficulty="intermediate",
                sessions_per_week=3,
                order_idx=1,
                exercises=[
                    {"name": "점프 스쿼트", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "최대한 빠르게, 착지 소음 최소화"},
                    {"name": "버피", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "전신 폭발적 동작"},
                    {"name": "하이 니", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "무릎을 골반 높이까지 빠르게"},
                    {"name": "푸쉬업", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "가슴이 바닥에 닿도록"},
                    {"name": "마운틴 클라이머", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "코어 고정, 엉덩이 들리지 않게"},
                    {"name": "점프 런지", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "무릎 충격 주의, 착지 부드럽게"},
                    {"name": "플랭크 잭", "sets": 4, "reps": "20초 전력", "rest": "10초", "notes": "플랭크 자세에서 다리를 벌렸다 모으기"},
                ],
            ),
            ExerciseRoutine(
                purpose="weight_management",
                name="홈트레이닝 전신 루틴 (도구 없음)",
                description="헬스장 없이 집에서 할 수 있는 전신 체중 운동 루틴입니다. 초보자도 무리 없이 시작 가능합니다.",
                difficulty="beginner",
                sessions_per_week=4,
                order_idx=2,
                exercises=[
                    {"name": "스쿼트", "sets": 4, "reps": "15회", "rest": "45초", "notes": "체중으로, 허벅지가 지면과 평행"},
                    {"name": "푸쉬업 (무릎 변형 가능)", "sets": 3, "reps": "10-15회", "rest": "45초", "notes": "어깨 넓이로 손 짚기"},
                    {"name": "힙 레이즈 (글루트 브릿지)", "sets": 3, "reps": "20회", "rest": "30초", "notes": "엉덩이 끝까지 들어올리기"},
                    {"name": "사이드 런지", "sets": 3, "reps": "12회(양쪽)", "rest": "45초", "notes": "내측광근·둔근 자극"},
                    {"name": "인치웜", "sets": 3, "reps": "8회", "rest": "30초", "notes": "전신 이완 및 코어 강화"},
                    {"name": "플랭크", "sets": 3, "reps": "30-40초", "rest": "30초", "notes": "호흡 유지, 복부 수축"},
                    {"name": "점핑잭", "sets": 3, "reps": "30회", "rest": "30초", "notes": "가볍게 점프하며 전신 워밍업"},
                ],
            ),
        ]

    for r in exercise_defaults:
        if r.name not in existing_exercise_names:
            db.add(r)
            added += 1

    diet_defaults = [
            DietRecommendation(
                purpose="loss",
                name="고단백 칼로리 적자 식단",
                description="근육량을 유지하면서 체지방을 감량하는 식단입니다. TDEE 대비 약 400~500kcal 적자를 목표로 합니다.",
                carb_ratio=35,
                protein_ratio=40,
                fat_ratio=25,
                calorie_note="TDEE 대비 -400~500kcal (주당 0.3~0.5kg 감량 목표)",
                order_idx=0,
                nutrients=[
                    {"name": "단백질", "target": "체중 1kg당 2.0~2.5g", "unit": "g/일", "notes": "근육 유지 및 포만감 증진, 닭가슴살·두부·달걀 위주"},
                    {"name": "탄수화물", "target": "총 칼로리의 35%", "unit": "", "notes": "통곡물·고구마·현미 등 복합 탄수화물 위주, 정제당 최소화"},
                    {"name": "지방", "target": "총 칼로리의 25%", "unit": "", "notes": "아보카도·견과류·올리브유 등 불포화지방 중심"},
                    {"name": "식이섬유", "target": "25~30", "unit": "g/일", "notes": "채소·콩류로 포만감 유지 및 혈당 조절"},
                    {"name": "수분", "target": "체중 1kg당 30~35ml 이상", "unit": "ml/일", "notes": "대사 촉진 및 식욕 조절, 식사 전 물 한 잔 권장"},
                    {"name": "나트륨", "target": "2,000 이하", "unit": "mg/일", "notes": "부종 예방, 가공식품·외식 줄이기"},
                ],
            ),
            DietRecommendation(
                purpose="gain",
                name="클린 벌크업 식단",
                description="체지방 증가를 최소화하면서 근육량을 늘리는 식단입니다. TDEE 대비 약 300~500kcal 잉여를 유지합니다.",
                carb_ratio=50,
                protein_ratio=30,
                fat_ratio=20,
                calorie_note="TDEE 대비 +300~500kcal (주당 0.25~0.5kg 증량 목표)",
                order_idx=0,
                nutrients=[
                    {"name": "단백질", "target": "체중 1kg당 2.0~2.5g", "unit": "g/일", "notes": "근육 합성의 핵심, 운동 후 30분 내 섭취 권장"},
                    {"name": "탄수화물", "target": "총 칼로리의 50%", "unit": "", "notes": "운동 전후 탄수화물 집중 섭취, 글리코겐 보충"},
                    {"name": "지방", "target": "총 칼로리의 20%", "unit": "", "notes": "호르몬 생성에 필요한 필수 지방, 과도한 포화지방 제한"},
                    {"name": "크레아틴", "target": "3~5", "unit": "g/일", "notes": "근력 및 근육량 증가 보조, 물과 함께 꾸준히 복용"},
                    {"name": "수분", "target": "3,000 이상", "unit": "ml/일", "notes": "운동 중 손실 수분 보충, 근육 회복 촉진"},
                    {"name": "아연", "target": "8~11", "unit": "mg/일", "notes": "테스토스테론 생성 및 단백질 합성 관여"},
                ],
            ),
            DietRecommendation(
                purpose="maintain",
                name="균형 유지 식단",
                description="현재 체중과 체성분을 유지하면서 건강한 식습관을 형성하는 식단입니다. 장기적인 건강 유지에 초점을 맞춥니다.",
                carb_ratio=45,
                protein_ratio=30,
                fat_ratio=25,
                calorie_note="TDEE와 동일하게 유지 (주간 평균 기준)",
                order_idx=0,
                nutrients=[
                    {"name": "단백질", "target": "체중 1kg당 1.6~2.0g", "unit": "g/일", "notes": "근육량 유지에 충분한 양, 다양한 단백질 식품 활용"},
                    {"name": "탄수화물", "target": "총 칼로리의 45%", "unit": "", "notes": "정제 탄수화물 최소화, 혈당지수 낮은 식품 선택"},
                    {"name": "지방", "target": "총 칼로리의 25%", "unit": "", "notes": "포화지방은 전체 지방의 1/3 이내, 트랜스지방 배제"},
                    {"name": "비타민 D", "target": "800~2,000", "unit": "IU/일", "notes": "햇빛 노출 부족 시 보충제 고려, 면역력 및 뼈 건강"},
                    {"name": "오메가-3", "target": "1,000~2,000", "unit": "mg/일", "notes": "등 푸른 생선·아마씨 등으로 섭취, 심혈관 건강"},
                    {"name": "식이섬유", "target": "25~35", "unit": "g/일", "notes": "장 건강 유지, 채소와 통곡물로 자연스럽게 섭취"},
                ],
            ),
            DietRecommendation(
                purpose="medical",
                name="의료 목적 기본 식단 가이드",
                description="특정 질환이나 의료적 목적에 따른 기본 식단 가이드입니다. 반드시 담당 의사 또는 영양사와 상담 후 적용하시기 바랍니다.",
                carb_ratio=45,
                protein_ratio=25,
                fat_ratio=30,
                calorie_note="개인 상태 및 질환에 따라 의료진과 함께 설정",
                order_idx=0,
                nutrients=[
                    {"name": "나트륨", "target": "2,000 이하", "unit": "mg/일", "notes": "고혈압·신장질환 시 제한, 가공식품 최소화"},
                    {"name": "단백질", "target": "체중 1kg당 0.8~1.2g", "unit": "g/일", "notes": "신장 기능 감소 시 제한 필요, 의료진 지시에 따라"},
                    {"name": "식이섬유", "target": "25~35", "unit": "g/일", "notes": "혈당 조절 및 장 건강, 당뇨 환자 특히 중요"},
                    {"name": "포화지방", "target": "전체 칼로리의 7% 이하", "unit": "", "notes": "심혈관 질환 예방, 붉은 고기·버터 제한"},
                    {"name": "당류", "target": "총 칼로리의 10% 이하", "unit": "", "notes": "혈당 관리 및 당뇨 예방, 과당 시럽 특히 주의"},
                    {"name": "칼륨", "target": "3,500~4,700", "unit": "mg/일", "notes": "신장질환 시 제한 필요, 의료진 지시 필수"},
                ],
            ),
        ]

    for r in diet_defaults:
        if r.name not in existing_diet_names:
            db.add(r)
            added += 1

    db.commit()
    return {"message": f"기본 데이터 {added}개가 추가되었습니다.", "added": added}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _exercise_dict(r: ExerciseRoutine) -> dict:
    return {
        "id": r.id,
        "purpose": r.purpose,
        "name": r.name,
        "description": r.description,
        "difficulty": r.difficulty,
        "sessions_per_week": r.sessions_per_week,
        "exercises": r.exercises or [],
    }


def _exercise_dict_admin(r: ExerciseRoutine) -> dict:
    return {
        **_exercise_dict(r),
        "order_idx": r.order_idx,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _diet_dict(r: DietRecommendation) -> dict:
    return {
        "id": r.id,
        "purpose": r.purpose,
        "name": r.name,
        "description": r.description,
        "carb_ratio": r.carb_ratio,
        "protein_ratio": r.protein_ratio,
        "fat_ratio": r.fat_ratio,
        "calorie_note": r.calorie_note,
        "nutrients": r.nutrients or [],
    }


def _diet_dict_admin(r: DietRecommendation) -> dict:
    return {
        **_diet_dict(r),
        "order_idx": r.order_idx,
        "is_active": r.is_active,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }
