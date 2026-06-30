from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Org, SysUser, KnowledgeBase
from schemas import OrgCreate, OrgOut
from utils.security import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/org", tags=["org"])


@router.get("/tree", response_model=list[OrgOut])
async def get_org_tree(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Org).order_by(Org.level, Org.sort_order, Org.code))
    return [OrgOut.model_validate(o) for o in result.scalars().all()]


@router.post("", response_model=OrgOut)
async def create_org(req: OrgCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    existing = await db.execute(select(Org).where(Org.code == req.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="组织编码已存在")

    path = req.code
    if req.parent_code:
        parent = await db.execute(select(Org).where(Org.code == req.parent_code))
        parent_org = parent.scalar_one_or_none()
        if not parent_org:
            raise HTTPException(status_code=400, detail="父组织不存在")
        path = f"{parent_org.path}/{req.code}"

    org = Org(
        code=req.code,
        name=req.name,
        level=req.level,
        parent_code=req.parent_code,
        path=path,
        sort_order=req.sort_order,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return OrgOut.model_validate(org)


@router.put("/{id}", response_model=OrgOut)
async def update_org(id: int, req: OrgCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Org).where(Org.id == id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")
    org.name = req.name
    org.sort_order = req.sort_order
    await db.commit()
    await db.refresh(org)
    return OrgOut.model_validate(org)


@router.delete("/{id}")
async def delete_org(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(Org).where(Org.id == id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="组织不存在")

    # 检查是否被用户或知识库引用
    user_ref = await db.execute(select(SysUser).where(SysUser.org_code == org.code))
    if user_ref.scalars().first():
        raise HTTPException(status_code=400, detail="该组织下仍存在用户，无法删除")
    kb_ref = await db.execute(select(KnowledgeBase).where(KnowledgeBase.org_code == org.code))
    if kb_ref.scalars().first():
        raise HTTPException(status_code=400, detail="该组织下仍存在知识库，无法删除")

    await db.delete(org)
    await db.commit()
    return {"ok": True}
