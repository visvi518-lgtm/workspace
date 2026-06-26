"""
네이버 건강/운동 기사 크롤러 (2일 주기 자동 수집)
APScheduler로 main.py에서 스케줄링됩니다.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.board import Post
from app.models.user import User

logger = logging.getLogger(__name__)

CRAWL_SOURCES = {
    "health": [
        "https://m.blog.naver.com/PostList.nhn?blogId=nhis_2022&categoryNo=1",
    ],
    "exercise": [
        "https://blog.naver.com/PostList.nhn?blogId=exercise_official",
    ],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


async def fetch_naver_health_articles(board_type: str) -> list[dict]:
    """네이버 건강/운동 RSS 피드에서 기사를 가져옵니다."""
    rss_urls = {
        "health": "https://news.naver.com/rss/section_005.xml",
        "exercise": "https://news.naver.com/rss/section_005.xml",
    }
    url = rss_urls.get(board_type, rss_urls["health"])
    articles = []

    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=30) as client:
            res = await client.get(url)
            res.raise_for_status()

        soup = BeautifulSoup(res.text, "lxml-xml")
        items = soup.find_all("item")[:5]

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            desc_tag = item.find("description")

            if not title_tag:
                continue

            articles.append({
                "title": title_tag.get_text(strip=True),
                "source_url": link_tag.get_text(strip=True) if link_tag else None,
                "summary": (
                    BeautifulSoup(desc_tag.get_text(strip=True), "html.parser").get_text()[:300]
                    if desc_tag else None
                ),
            })
    except Exception as e:
        logger.error(f"크롤링 실패 ({board_type}): {e}")

    return articles


async def summarize_with_ai(title: str, content: str) -> tuple[str, list[str]]:
    """Claude API로 기사를 요약하고 태그를 추출합니다."""
    from app.core.config import settings
    if not settings.ANTHROPIC_API_KEY:
        return content[:200], []

    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    try:
        res = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"다음 건강 기사를 3문장으로 요약하고, 관련 태그를 최대 5개 추출해 주세요.\n\n"
                        f"제목: {title}\n내용: {content[:1000]}\n\n"
                        '형식 (JSON): {"summary": "요약문", "tags": ["태그1", "태그2"]}'
                    ),
                }
            ],
        )
        import json
        data = json.loads(res.content[0].text)
        return data.get("summary", content[:200]), data.get("tags", [])
    except Exception as e:
        logger.error(f"AI 요약 실패: {e}")
        return content[:200], []


def get_or_create_crawler_user(db: Session) -> User:
    crawler = db.query(User).filter(User.email == "crawler@system.internal").first()
    if not crawler:
        from app.core.security import get_password_hash
        import secrets
        crawler = User(
            email="crawler@system.internal",
            password_hash=get_password_hash(secrets.token_hex(32)),
            nickname="시스템",
            is_active=True,
        )
        db.add(crawler)
        db.commit()
        db.refresh(crawler)
    return crawler


async def run_crawl(board_type: str):
    logger.info(f"크롤링 시작: {board_type}")
    articles = await fetch_naver_health_articles(board_type)

    db: Session = SessionLocal()
    try:
        crawler_user = get_or_create_crawler_user(db)

        for article in articles:
            existing = db.query(Post).filter(Post.source_url == article["source_url"]).first()
            if existing:
                continue

            summary, tags = await summarize_with_ai(article["title"], article.get("summary") or "")

            post = Post(
                title=article["title"],
                content=article.get("summary") or article["title"],
                summary=summary,
                source_url=article.get("source_url"),
                board_type=board_type,
                author_id=crawler_user.id,
                tags=tags,
                is_crawled=True,
            )
            db.add(post)

        db.commit()
        logger.info(f"크롤링 완료: {board_type} ({len(articles)}개)")
    except Exception as e:
        logger.error(f"크롤링 저장 실패: {e}")
        db.rollback()
    finally:
        db.close()


def crawl_health():
    asyncio.run(run_crawl("health"))


def crawl_exercise():
    asyncio.run(run_crawl("exercise"))
