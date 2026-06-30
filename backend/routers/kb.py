from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import KnowledgeBase, KbCollaborator, SysUser, KbDocument, Org
from schemas import KbCreate, KbOut, KbDetail, KbAdminOut, KbReviewRequest, CollaboratorCreate, CollaboratorOut, DocumentOut
from utils.security import get_current_user, require_admin
from services.permission import can_access_kb, get_user_org_path

router = APIRouter(prefix="/api/v1/kb", tags=["knowledge-base"])


async def filter_visible_kbs(db: AsyncSession, user: SysUser):
    user_path = await get_user_org_path(db, user.scope_code)
    if not user_path:
        return []
    result = await db.execute(
        select(KnowledgeBase)
        .join(Org, KnowledgeBase.org_code == Org.code)
        .where(
            KnowledgeBase.status == "published",
            (Org.path == user_path) | (Org.path.like(f"{user_path}/%"))
        )
        .order_by(KnowledgeBase.created_at.desc())
    )
    return result.scalars().all()


@router.get("", response_model=list[KbOut])
async def list_kbs(db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    kbs = await filter_visible_kbs(db, user)
    out = []
    for kb in kbs:
        item = KbOut.model_validate(kb)
        org = await db.execute(select(Org.name).where(Org.code == kb.org_code))
        item.org_name = org.scalar_one_or_none()
        out.append(item)
    return out


@router.post("", response_model=KbOut)
async def create_kb(req: KbCreate, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    kb = KnowledgeBase(
        name=req.name,
        description=req.description,
        org_code=req.org_code,
        owner_id=user.id,
        status="pending",
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return KbOut.model_validate(kb)


@router.get("/my", response_model=list[KbOut])
async def list_my_kbs(db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    owned = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.owner_id == user.id).order_by(KnowledgeBase.created_at.desc())
    )
    collab_kb_ids = await db.execute(
        select(KbCollaborator.kb_id).where(KbCollaborator.user_id == user.id)
    )
    collab_ids = [r[0] for r in collab_kb_ids.all()]
    collab_kbs = []
    if collab_ids:
        collab_kbs = (await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id.in_(collab_ids)).order_by(KnowledgeBase.created_at.desc())
        )).scalars().all()
    result = list(owned.scalars().all()) + list(collab_kbs)
    out = []
    for kb in result:
        item = KbOut.model_validate(kb)
        org = await db.execute(select(Org.name).where(Org.code == kb.org_code))
        item.org_name = org.scalar_one_or_none()
        out.append(item)
    return out


@router.get("/all", response_model=list[KbAdminOut])
async def list_all_kbs(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(
        select(KnowledgeBase, SysUser.name.label("owner_name"), Org.name.label("org_name"))
        .join(SysUser, KnowledgeBase.owner_id == SysUser.id)
        .outerjoin(Org, KnowledgeBase.org_code == Org.code)
        .order_by(KnowledgeBase.created_at.desc())
    )
    rows = result.all()
    out = []
    for kb, owner_name, org_name in rows:
        item = KbAdminOut.model_validate(kb)
        item.owner_name = owner_name
        item.org_name = org_name
        out.append(item)
    return out


@router.get("/{id}", response_model=KbDetail)
async def get_kb(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == id)
    )
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 所有者、协作者或管理员始终可访问；其他用户只能访问已发布且在自己权限范围内的知识库
    is_owner = kb.owner_id == user.id
    collab_result = await db.execute(
        select(KbCollaborator).where(KbCollaborator.kb_id == id, KbCollaborator.user_id == user.id)
    )
    is_collab = collab_result.scalar_one_or_none() is not None
    is_admin = user.role == "admin"

    if not (is_owner or is_collab or is_admin):
        if kb.status != "published":
            raise HTTPException(status_code=403, detail="无权访问该知识库")
        if not await can_access_kb(db, kb.org_code, user.scope_code):
            raise HTTPException(status_code=403, detail="无权访问该知识库")

    docs_result = await db.execute(
        select(KbDocument).where(KbDocument.kb_id == id).order_by(KbDocument.created_at.desc())
    )
    docs = docs_result.scalars().all()

    kb_out = KbOut.model_validate(kb)
    org = await db.execute(select(Org.name).where(Org.code == kb.org_code))
    kb_out.org_name = org.scalar_one_or_none()
    detail = KbDetail(**kb_out.model_dump())
    detail.documents = [DocumentOut.model_validate(d) for d in docs]
    return detail


@router.post("/{id}/review")
async def review_kb(id: int, req: KbReviewRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if req.status not in ("published", "pending", "archived", "draft"):
        raise HTTPException(status_code=400, detail="状态不合法")
    kb.status = req.status
    await db.commit()
    return {"ok": True}


@router.delete("/{id}")
async def delete_kb(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if kb.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除")
    await db.delete(kb)
    await db.commit()
    return {"ok": True}


@router.get("/{id}/collaborators", response_model=list[CollaboratorOut])
async def list_collaborators(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if kb.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权管理协作者")

    collab_result = await db.execute(select(KbCollaborator).where(KbCollaborator.kb_id == id))
    return [CollaboratorOut.model_validate(c) for c in collab_result.scalars().all()]


@router.post("/{id}/collaborators", response_model=CollaboratorOut)
async def add_collaborator(id: int, req: CollaboratorCreate, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if kb.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权管理协作者")

    target = await db.execute(select(SysUser).where(SysUser.id == req.user_id))
    if not target.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户不存在")

    collab = KbCollaborator(kb_id=id, user_id=req.user_id, role=req.role)
    db.add(collab)
    await db.commit()
    await db.refresh(collab)
    return CollaboratorOut.model_validate(collab)


@router.delete("/{id}/collaborators/{user_id}")
async def remove_collaborator(id: int, user_id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == id))
    kb = result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if kb.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权管理协作者")

    collab_result = await db.execute(
        select(KbCollaborator).where(
            KbCollaborator.kb_id == id,
            KbCollaborator.user_id == user_id
        )
    )
    collab = collab_result.scalar_one_or_none()
    if collab:
        await db.delete(collab)
        await db.commit()
    return {"ok": True}
