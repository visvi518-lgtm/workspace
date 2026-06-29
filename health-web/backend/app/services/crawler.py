"""
네이버 건강/운동 블로그·뉴스 크롤러 (2일 주기 자동 수집)
네이버 검색 OpenAPI → 원문 스크래핑 → Gemini 6~8줄 요약 순서로 처리합니다.
"""
import asyncio
import json
import logging
import re
from difflib import SequenceMatcher

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.board import Post
from app.models.user import User

logger = logging.getLogger(__name__)

# ─── 크롤링 상태 ───
_crawl_running: bool = False
_stop_requested: bool = False


def is_crawling() -> bool:
    return _crawl_running


def request_stop():
    global _stop_requested
    _stop_requested = True


# ─── 네이버 API 설정 ───
NAVER_BLOG_API = "https://openapi.naver.com/v1/search/blog.json"
NAVER_NEWS_API = "https://openapi.naver.com/v1/search/news.json"

HEALTH_KEYWORDS = [
    "건강관리 방법",
    "건강정보 최신",
    "혈압 관리",
    "당뇨 건강",
    "면역력 높이기",
    "수면 건강",
    "심혈관 건강",
    "영양 섭취",
]

EXERCISE_KEYWORDS = [
    "운동 방법 초보",
    "스트레칭 효과",
    "근력운동",
    "올바른 자세 교정",
    "유산소운동",
    "홈트레이닝",
    "체중감량 운동",
    "플랭크 효과",
]

# 원문 스크래핑용 모바일 UA (네이버 블로그 SSR 응답 유도)
_SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 사이트별 본문 CSS 셀렉터 (우선순위 순)
_CONTENT_SELECTORS = [
    ".se-main-container",        # 네이버 블로그 Smart Editor 3
    "#postViewArea",             # 네이버 블로그 구버전
    ".post-view",                # 네이버 블로그 구버전 테마
    "#articleBodyContents",      # 네이버 뉴스
    ".article_body",             # 네이버 뉴스 (일부)
    "[class*='news-article']",   # 일반 뉴스
    "[class*='article-body']",
    "[class*='article_body']",
    "[class*='article-content']",
    "article",                   # HTML5 시맨틱
    "main",
]


def _naver_headers() -> dict:
    return {
        "X-Naver-Client-Id": settings.NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": settings.NAVER_CLIENT_SECRET,
    }


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _normalize(title: str) -> str:
    return re.sub(r"[\s\W]+", "", title.lower())


def is_duplicate_title(new_title: str, existing_titles: list[str], threshold: float = 0.75) -> bool:
    new_norm = _normalize(new_title)
    if not new_norm:
        return False
    for existing in existing_titles:
        if SequenceMatcher(None, new_norm, _normalize(existing)).ratio() >= threshold:
            return True
    return False


async def fetch_article_content(url: str) -> str:
    """
    원문 URL에서 본문 텍스트를 추출합니다.
    여러 CSS 셀렉터를 시도하고, 실패 시 단락 텍스트를 수집합니다.
    """
    if not url:
        return ""
    try:
        async with httpx.AsyncClient(
            headers=_SCRAPE_HEADERS, timeout=12, follow_redirects=True
        ) as client:
            res = await client.get(url)
            res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")

        # 불필요한 태그 제거
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
            tag.decompose()

        # 셀렉터 순서대로 시도
        for selector in _CONTENT_SELECTORS:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(separator="\n", strip=True)
                text = re.sub(r"\n{3,}", "\n\n", text)
                if len(text) > 200:
                    logger.debug(f"본문 추출 성공 ({selector}): {len(text)}자")
                    return text[:5000]

        # 폴백: <p> 태그 수집
        paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
        if paras:
            joined = "\n\n".join(paras[:25])
            logger.debug(f"폴백 단락 추출: {len(joined)}자")
            return joined[:5000]

        return ""
    except Exception as e:
        logger.debug(f"원문 fetch 실패 ({url}): {e}")
        return ""


async def summarize_with_ai(title: str, content: str) -> tuple[str, list[str]]:
    """
    Gemini 2.5 Flash로 본문을 6~8줄로 요약하고 태그를 추출합니다.
    content가 충분하지 않으면 짧은 요약을 반환합니다.
    """
    if not settings.GEMINI_API_KEY:
        return content[:600], []

    from google import genai

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        prompt = (
            "다음 건강/운동 관련 글을 6~8문장으로 요약하세요.\n"
            "조건:\n"
            "- 각 문장은 반드시 줄바꿈(\\n)으로 구분하세요.\n"
            "- 핵심 수치, 방법, 효과를 구체적으로 포함하세요.\n"
            "- 독자가 실생활에서 바로 활용할 수 있는 정보 위주로 작성하세요.\n"
            "- 내용이 부족해도 반드시 6문장 이상 작성하세요.\n\n"
            f"제목: {title}\n"
            f"내용:\n{content[:3000]}\n\n"
            "아래 JSON 형식만 출력하세요 (마크다운, 코드블록 없이):\n"
            '{"summary": "문장1\\n문장2\\n문장3\\n문장4\\n문장5\\n문장6", "tags": ["태그1", "태그2"]}'
        )
        res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", res.text.strip(), flags=re.MULTILINE).strip()
        data = json.loads(text)
        summary = data.get("summary", "")
        # 최소 6줄 보장: 부족하면 content로 보완
        if summary.count("\n") < 5 and len(content) > 100:
            summary = summary + "\n" + content[:300]
        return summary, data.get("tags", [])
    except Exception as e:
        logger.error(f"AI 요약 실패 (title={title!r}): {e}")
        return content[:600], []


def get_or_create_crawler_user(db: Session) -> User:
    crawler = db.query(User).filter(User.email == "crawler@system.internal").first()
    if not crawler:
        import secrets

        from app.core.security import get_password_hash

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


async def search_naver(query: str, search_type: str = "blog", display: int = 5) -> list[dict]:
    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        return []
    url = NAVER_BLOG_API if search_type == "blog" else NAVER_NEWS_API
    params = {"query": query, "display": display, "sort": "date"}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            res = await client.get(url, headers=_naver_headers(), params=params)
            res.raise_for_status()
        return res.json().get("items", [])
    except Exception as e:
        logger.error(f"네이버 API 호출 실패 (query={query!r}, type={search_type}): {e}")
        return []


async def fetch_articles(board_type: str, per_keyword: int = 3) -> list[dict]:
    keywords = HEALTH_KEYWORDS if board_type == "health" else EXERCISE_KEYWORDS
    articles: list[dict] = []
    seen_urls: set[str] = set()

    for keyword in keywords:
        if _stop_requested:
            logger.info("크롤링 중단 요청 — 기사 수집 루프 종료")
            break

        for search_type in ("blog", "news"):
            items = await search_naver(keyword, search_type=search_type, display=per_keyword)
            for item in items:
                link = item.get("originallink") or item.get("link", "")
                if not link or link in seen_urls:
                    continue
                seen_urls.add(link)

                title = strip_html(item.get("title", ""))
                description = strip_html(item.get("description", ""))
                if not title:
                    continue

                articles.append({
                    "title": title,
                    "source_url": link,
                    "api_description": description,  # API 짧은 설명 (폴백용)
                    "source_type": search_type,
                })

    logger.info(f"[{board_type}] 검색 결과 수집: {len(articles)}개")
    return articles


async def run_crawl(board_type: str) -> dict:
    """
    크롤링 실행 진입점.
    반환: {"saved": int, "skipped_url": int, "skipped_dup": int, "stopped": bool}
    """
    global _crawl_running, _stop_requested

    if not settings.NAVER_CLIENT_ID or not settings.NAVER_CLIENT_SECRET:
        logger.warning("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정 — 크롤링 건너뜀")
        return {"saved": 0, "skipped_url": 0, "skipped_dup": 0, "stopped": False}

    _crawl_running = True
    _stop_requested = False
    saved = skipped_url = skipped_dup = 0

    logger.info(f"크롤링 시작: {board_type}")
    articles = await fetch_articles(board_type)

    db: Session = SessionLocal()
    try:
        crawler_user = get_or_create_crawler_user(db)

        existing_titles: list[str] = [
            row[0] for row in db.query(Post.title).filter(
                Post.board_type == board_type,
                Post.is_deleted.is_(False),
            ).all()
        ]

        for article in articles:
            if _stop_requested:
                db.rollback()
                logger.info(f"크롤링 중단 — 미저장 데이터 {saved}개 폐기")
                return {"saved": 0, "skipped_url": skipped_url, "skipped_dup": skipped_dup, "stopped": True}

            url = article.get("source_url")

            # 1) URL 중복
            if url and db.query(Post).filter(Post.source_url == url).first():
                skipped_url += 1
                continue

            # 2) 제목 유사도 중복
            if is_duplicate_title(article["title"], existing_titles):
                logger.debug(f"제목 중복 건너뜀: {article['title'][:50]}")
                skipped_dup += 1
                continue

            # 3) 원문 스크래핑 (실패 시 API description 사용)
            full_content = await fetch_article_content(url)
            source_text = full_content if len(full_content) > 200 else article.get("api_description", "")

            # 4) AI 6~8줄 요약
            summary, tags = await summarize_with_ai(article["title"], source_text)

            post = Post(
                title=article["title"],
                content=summary,       # 상세 페이지에 표시될 본문
                summary=summary,       # 목록 미리보기용
                source_url=url,
                board_type=board_type,
                author_id=crawler_user.id,
                tags=tags,
                is_crawled=True,
                crawl_status="draft",
            )
            db.add(post)
            existing_titles.append(article["title"])
            saved += 1

        db.commit()
        logger.info(
            f"크롤링 완료: {board_type} — "
            f"저장 {saved}개 / URL중복 {skipped_url}개 / 제목중복 {skipped_dup}개"
        )
        return {"saved": saved, "skipped_url": skipped_url, "skipped_dup": skipped_dup, "stopped": False}

    except Exception as e:
        logger.error(f"크롤링 저장 실패 ({board_type}): {e}")
        db.rollback()
        return {"saved": saved, "skipped_url": skipped_url, "skipped_dup": skipped_dup, "stopped": False}
    finally:
        db.close()
        _crawl_running = False
        _stop_requested = False


def crawl_health():
    asyncio.run(run_crawl("health"))


def crawl_exercise():
    asyncio.run(run_crawl("exercise"))
