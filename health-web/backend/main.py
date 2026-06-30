import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text

from app.api.routes import auth, board, health, chat, admin, banner
from app.core.config import settings
from app.core.database import Base, engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

scheduler = BackgroundScheduler(timezone="Asia/Seoul")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)

    # 신규 컬럼 마이그레이션 (이미 존재하면 무시)
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE posts ADD COLUMN crawl_status VARCHAR(20)",
            "ALTER TABLE banners ADD COLUMN link_url VARCHAR(500)",
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass

    # Setup schedules
    from app.services.crawler import crawl_health, crawl_exercise
    from app.services.dormancy import mark_dormant_accounts

    scheduler.add_job(crawl_health, "interval", days=2, id="crawl_health")
    scheduler.add_job(crawl_exercise, "interval", days=2, id="crawl_exercise")
    scheduler.add_job(mark_dormant_accounts, "cron", hour=3, minute=0, id="dormancy")
    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(board.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(banner.router, prefix="/api/v1")


@app.get("/api/v1/health-check")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}
