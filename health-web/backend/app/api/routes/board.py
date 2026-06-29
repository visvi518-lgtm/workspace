from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.board import Comment, Post
from app.models.user import User

router = APIRouter(prefix="/board", tags=["board"])

VALID_BOARD_TYPES = {"health", "exercise", "free"}


def serialize_post(post: Post, short: bool = False) -> dict:
    data = {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "source_url": post.source_url,
        "board_type": post.board_type,
        "author": {"id": post.author_id, "nickname": post.author.nickname if post.author else "탈퇴한 사용자"},
        "tags": post.tags or [],
        "view_count": post.view_count,
        "comment_count": len([c for c in post.comments if not c.is_deleted]),
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
        "is_crawled": post.is_crawled,
    }
    if not short:
        data["content"] = post.content
    return data


def serialize_comment(comment: Comment) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "author": {"id": comment.author_id, "nickname": comment.author.nickname if comment.author else "탈퇴한 사용자"},
        "created_at": comment.created_at.isoformat(),
        "updated_at": comment.updated_at.isoformat(),
    }


class PostCreate(BaseModel):
    title: str
    content: str
    board_type: str
    summary: Optional[str] = None
    tags: list[str] = []


class CommentCreate(BaseModel):
    content: str


@router.get("/posts")
def list_posts(
    board_type: str = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    search: Optional[str] = None,
    tag: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    if board_type not in VALID_BOARD_TYPES:
        raise HTTPException(status_code=400, detail="유효하지 않은 게시판 유형입니다.")

    query = db.query(Post).filter(
        Post.board_type == board_type,
        Post.is_deleted.is_(False),
        # 크롤링 게시물은 관리자가 published 처리한 것만 노출
        or_(Post.is_crawled.is_(False), Post.crawl_status == "published"),
    )

    if search:
        query = query.filter(
            or_(Post.title.ilike(f"%{search}%"), Post.content.ilike(f"%{search}%"))
        )
    if tag:
        query = query.filter(Post.tags.contains([tag]))

    total = query.count()
    posts = query.order_by(Post.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": [serialize_post(p, short=True) for p in posts],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


@router.get("/posts/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    post.view_count += 1
    db.commit()
    return serialize_post(post)


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.board_type not in VALID_BOARD_TYPES:
        raise HTTPException(status_code=400, detail="유효하지 않은 게시판 유형입니다.")

    post = Post(
        title=data.title,
        content=data.content,
        board_type=data.board_type,
        summary=data.summary,
        tags=data.tags[:10],
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return serialize_post(post)


@router.put("/posts/{post_id}")
def update_post(
    post_id: int,
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="수정 권한이 없습니다.")

    post.title = data.title
    post.content = data.content
    post.tags = data.tags[:10]
    db.commit()
    return serialize_post(post)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    post.is_deleted = True
    db.commit()


@router.get("/posts/{post_id}/comments")
def list_comments(post_id: int, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    return [serialize_comment(c) for c in post.comments if not c.is_deleted]


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if not post or post.is_deleted:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    comment = Comment(post_id=post_id, author_id=current_user.id, content=data.content[:500])
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return serialize_comment(comment)


@router.delete("/posts/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    comment = db.get(Comment, comment_id)
    if not comment or comment.post_id != post_id or comment.is_deleted:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    comment.is_deleted = True
    db.commit()
