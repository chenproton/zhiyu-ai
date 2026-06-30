from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import SysUser, KnowledgeBase
from schemas import UserInfo, UserCreate
from utils.security import require_admin, get_password_hash

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=list[UserInfo])
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(SysUser).order_by(SysUser.id))
    return [UserInfo.model_validate(u) for u in result.scalars().all()]


@router.post("/users", response_model=UserInfo)
async def create_user(
    req: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin)
):
    existing = await db.execute(select(SysUser).where(SysUser.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    if req.role not in ("admin", "editor", "viewer"):
        raise HTTPException(status_code=400, detail="角色不合法")

    user = SysUser(
        username=req.username,
        password=get_password_hash(req.password),
        name=req.name,
        org_code=req.org_code,
        scope_code=req.scope_code,
        role=req.role,
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserInfo.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    owned_kbs = await db.execute(select(KnowledgeBase).where(KnowledgeBase.owner_id == user_id))
    if owned_kbs.scalars().first():
        raise HTTPException(status_code=400, detail="该用户仍拥有知识库，请先转移所有权")

    try:
        await db.delete(user)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"删除失败，该用户可能仍有关联数据：{e}")

    return {"ok": True}


@router.post("/users/reset-password")
async def reset_password(user_id: int, new_password: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(SysUser).where(SysUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password = get_password_hash(new_password)
    await db.commit()
    return {"ok": True}
