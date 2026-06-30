from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import UserLike, UserRating, UserComment, SysUser
from schemas import InteractionStats, CommentCreate, CommentOut, RatingCreate
from utils.security import get_current_user

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


VALID_TARGET_TYPES = {"kb", "bot", "news", "event"}


def _validate_target_type(target_type: str):
    if target_type not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail="不支持的互动对象类型")


@router.get("/{target_type}/{target_id}/stats", response_model=InteractionStats)
async def get_stats(
    target_type: str,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)

    likes_result = await db.execute(
        select(func.count(UserLike.id)).where(
            UserLike.target_type == target_type,
            UserLike.target_id == target_id
        )
    )
    likes = likes_result.scalar()

    user_liked_result = await db.execute(
        select(UserLike).where(
            UserLike.target_type == target_type,
            UserLike.target_id == target_id,
            UserLike.user_id == user.id
        )
    )
    user_liked = user_liked_result.scalar_one_or_none() is not None

    rating_stats = await db.execute(
        select(func.count(UserRating.id), func.avg(UserRating.score)).where(
            UserRating.target_type == target_type,
            UserRating.target_id == target_id
        )
    )
    rating_count, rating_avg = rating_stats.one()

    user_rating_result = await db.execute(
        select(UserRating.score).where(
            UserRating.target_type == target_type,
            UserRating.target_id == target_id,
            UserRating.user_id == user.id
        )
    )
    user_rating_row = user_rating_result.one_or_none()
    user_rating = user_rating_row[0] if user_rating_row else None

    comments_result = await db.execute(
        select(func.count(UserComment.id)).where(
            UserComment.target_type == target_type,
            UserComment.target_id == target_id
        )
    )
    comments = comments_result.scalar()

    return InteractionStats(
        likes=likes or 0,
        rating_count=rating_count or 0,
        rating_avg=round(rating_avg or 0, 1),
        comments=comments or 0,
        user_liked=user_liked,
        user_rating=user_rating
    )


@router.post("/{target_type}/{target_id}/like")
async def toggle_like(
    target_type: str,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)
    result = await db.execute(
        select(UserLike).where(
            UserLike.target_type == target_type,
            UserLike.target_id == target_id,
            UserLike.user_id == user.id
        )
    )
    like = result.scalar_one_or_none()
    if like:
        await db.delete(like)
        await db.commit()
        return {"liked": False}
    else:
        db.add(UserLike(target_type=target_type, target_id=target_id, user_id=user.id))
        await db.commit()
        return {"liked": True}


@router.post("/{target_type}/{target_id}/rating")
async def submit_rating(
    target_type: str,
    target_id: int,
    req: RatingCreate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)
    result = await db.execute(
        select(UserRating).where(
            UserRating.target_type == target_type,
            UserRating.target_id == target_id,
            UserRating.user_id == user.id
        )
    )
    rating = result.scalar_one_or_none()
    if rating:
        rating.score = req.score
    else:
        rating = UserRating(
            target_type=target_type,
            target_id=target_id,
            user_id=user.id,
            score=req.score
        )
        db.add(rating)
    await db.commit()
    return {"ok": True}


@router.get("/{target_type}/{target_id}/comments", response_model=list[CommentOut])
async def list_comments(
    target_type: str,
    target_id: int,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)
    result = await db.execute(
        select(UserComment, SysUser.name.label("user_name"))
        .outerjoin(SysUser, UserComment.user_id == SysUser.id)
        .where(
            UserComment.target_type == target_type,
            UserComment.target_id == target_id
        )
        .order_by(UserComment.created_at.desc())
    )
    out = []
    for comment, user_name in result.all():
        item = CommentOut.model_validate(comment)
        item.user_name = user_name
        out.append(item)
    return out


@router.post("/{target_type}/{target_id}/comments", response_model=CommentOut)
async def create_comment(
    target_type: str,
    target_id: int,
    req: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    comment = UserComment(
        target_type=target_type,
        target_id=target_id,
        user_id=user.id,
        content=req.content.strip()
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentOut.model_validate(comment)


@router.delete("/{target_type}/{target_id}/comments/{comment_id}")
async def delete_comment(
    target_type: str,
    target_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    _validate_target_type(target_type)
    result = await db.execute(
        select(UserComment).where(
            UserComment.id == comment_id,
            UserComment.target_type == target_type,
            UserComment.target_id == target_id
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")
    if comment.user_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该评论")
    await db.delete(comment)
    await db.commit()
    return {"ok": True}
