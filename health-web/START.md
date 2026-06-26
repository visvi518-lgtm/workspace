# 헬스케어 웹 - 시작 가이드

## 사전 요구사항
- Node.js 20+
- Python 3.11+
- PostgreSQL 15+

## 1단계: PostgreSQL 설치 및 DB 생성

```bash
# PostgreSQL 설치 후 DB 생성
psql -U postgres -c "CREATE DATABASE healthweb;"
```

또는 Docker로 DB만 실행:
```bash
docker-compose up -d db
```

## 2단계: 백엔드 설정

```bash
cd backend

# 가상환경 생성
python -m venv venv
venv\Scripts\activate      # Windows

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
copy .env.example .env
# .env 파일을 열어 DATABASE_URL, SECRET_KEY 등을 수정

# DB 테이블 생성 (Alembic 마이그레이션)
alembic revision --autogenerate -m "init"
alembic upgrade head

# 서버 실행
uvicorn main:app --reload --port 8000
```

## 3단계: 프론트엔드 설정

```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev
```

## 4단계: 접속

- 프론트엔드: http://localhost:3000
- 백엔드 API 문서: http://localhost:8000/docs

## 관리자 계정 생성

```python
# Python 셸에서 실행
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserProfile

db = SessionLocal()
admin = User(
    email="admin@example.com",
    password_hash=get_password_hash("Admin123!"),
    nickname="관리자",
    is_admin=True,
)
admin.profile = UserProfile()
db.add(admin)
db.commit()
print("관리자 계정 생성 완료")
```

## AI 기능 활성화 (건강상담, 칼로리 분석)

1. https://console.anthropic.com 에서 API 키 발급
2. `.env` 파일의 `ANTHROPIC_API_KEY=sk-ant-...` 설정

## 나중에 추가할 기능

- [ ] Google OAuth 연동 (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET 설정)
- [ ] Naver OAuth 연동 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 설정)
- [ ] 이메일 SMTP 설정 (휴면 복구 메일)
- [ ] 의료 논문 데이터 수집 (PubMed API 연동)
