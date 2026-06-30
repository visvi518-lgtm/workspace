import base64
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_admin_user, get_db
from app.models.banner import Banner
from app.models.user import User

router = APIRouter()


# ── Public ───────────────────────────────────────────────────────────────────

@router.get("/banners/")
def get_banners(db: Session = Depends(get_db)):
    banners = (
        db.query(Banner)
        .filter(Banner.is_active.is_(True))
        .order_by(Banner.order_idx)
        .limit(4)
        .all()
    )
    return [_to_dict(b) for b in banners]


@router.get("/banners/{banner_id}/image")
def get_banner_image(banner_id: int, db: Session = Depends(get_db)):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner or not banner.image_data:
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다.")
    return Response(
        content=base64.b64decode(banner.image_data),
        media_type=banner.image_type or "image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("/admin/banners/")
def admin_get_banners(
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    banners = db.query(Banner).order_by(Banner.order_idx).all()
    return [_to_dict_admin(b) for b in banners]


@router.post("/admin/banners/")
async def admin_create_banner(
    title: Optional[str] = Form(None),
    subtitle: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    count = db.query(Banner).count()
    if count >= 4:
        raise HTTPException(status_code=400, detail="배너는 최대 4개까지 등록 가능합니다.")

    image_data, image_type = None, None
    if image and image.filename:
        content = await image.read()
        if len(content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="이미지는 5MB 이하여야 합니다.")
        image_data = base64.b64encode(content).decode("utf-8")
        image_type = image.content_type or "image/jpeg"

    banner = Banner(
        title=title or None,
        subtitle=subtitle or None,
        image_data=image_data,
        image_type=image_type,
        order_idx=count,
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return {"id": banner.id, "message": "배너가 추가되었습니다."}


class BannerToggle(BaseModel):
    is_active: bool


@router.patch("/admin/banners/{banner_id}")
def admin_toggle_banner(
    banner_id: int,
    data: BannerToggle,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="배너를 찾을 수 없습니다.")
    banner.is_active = data.is_active
    db.commit()
    return {"message": "업데이트되었습니다."}


@router.delete("/admin/banners/{banner_id}")
def admin_delete_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_admin_user),
):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="배너를 찾을 수 없습니다.")
    db.delete(banner)
    db.commit()
    remaining = db.query(Banner).order_by(Banner.order_idx).all()
    for i, b in enumerate(remaining):
        b.order_idx = i
    db.commit()
    return {"message": "배너가 삭제되었습니다."}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_dict(b: Banner) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "has_image": bool(b.image_data),
    }


def _to_dict_admin(b: Banner) -> dict:
    return {
        "id": b.id,
        "title": b.title,
        "subtitle": b.subtitle,
        "has_image": bool(b.image_data),
        "order_idx": b.order_idx,
        "is_active": b.is_active,
    }
