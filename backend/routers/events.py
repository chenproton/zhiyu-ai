from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from database import get_db
from models import Event, EventRegistration, SysUser
from schemas import EventCreate, EventUpdate, EventOut, EventDetail, EventRegistrationCreate, EventRegistrationOut
from utils.security import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("", response_model=list[EventOut])
async def list_events(
    category: Optional[str] = None,
    status: str = "published",
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    query = select(Event)
    if status != "all":
        query = query.where(Event.status == status)
    if category:
        query = query.where(Event.category == category)
    query = query.order_by(Event.created_at.desc())
    result = await db.execute(query)
    return [EventOut.model_validate(e) for e in result.scalars().all()]


@router.get("/admin", response_model=list[EventOut])
async def list_all_events(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin)
):
    query = select(Event)
    if category:
        query = query.where(Event.category == category)
    query = query.order_by(Event.created_at.desc())
    result = await db.execute(query)
    return [EventOut.model_validate(e) for e in result.scalars().all()]


@router.get("/{id}", response_model=EventDetail)
async def get_event(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(
        select(Event).options(selectinload(Event.registrations)).where(Event.id == id)
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    if event.status != "published" and event.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看该活动")

    detail = EventDetail.model_validate(event)
    detail.registration_count = len([r for r in event.registrations if r.status != "cancelled"])
    user_reg = next((r for r in event.registrations if r.user_id == user.id and r.status != "cancelled"), None)
    detail.is_registered = user_reg is not None
    return detail


@router.post("", response_model=EventOut)
async def create_event(
    req: EventCreate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    if user.role not in ("admin", "editor"):
        raise HTTPException(status_code=403, detail="无权发布活动")
    if req.category not in ("competition", "lecture", "recruitment", "activity"):
        raise HTTPException(status_code=400, detail="活动类型不合法")

    event = Event(
        title=req.title,
        summary=req.summary,
        content=req.content,
        cover=req.cover,
        category=req.category,
        organizer=req.organizer,
        location=req.location,
        start_time=req.start_time,
        end_time=req.end_time,
        registration_open=req.registration_open,
        max_participants=req.max_participants,
        created_by=user.id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return EventOut.model_validate(event)


@router.put("/{id}", response_model=EventOut)
async def update_event(
    id: int,
    req: EventUpdate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    result = await db.execute(select(Event).where(Event.id == id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    if event.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该活动")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    event.updated_at = datetime.now()
    await db.commit()
    await db.refresh(event)
    return EventOut.model_validate(event)


@router.delete("/{id}")
async def delete_event(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(select(Event).where(Event.id == id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    if event.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该活动")
    await db.delete(event)
    await db.commit()
    return {"ok": True}


@router.post("/{id}/register", response_model=EventRegistrationOut)
async def register_event(
    id: int,
    req: EventRegistrationCreate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    event_result = await db.execute(select(Event).where(Event.id == id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    if event.status != "published" or not event.registration_open:
        raise HTTPException(status_code=400, detail="活动未开放报名")
    if event.max_participants:
        count_result = await db.execute(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == id,
                EventRegistration.status != "cancelled"
            )
        )
        if count_result.scalar() >= event.max_participants:
            raise HTTPException(status_code=400, detail="报名人数已满")

    existing = await db.execute(
        select(EventRegistration).where(
            EventRegistration.event_id == id,
            EventRegistration.user_id == user.id,
            EventRegistration.status != "cancelled"
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已报名该活动")

    reg = EventRegistration(
        event_id=id,
        user_id=user.id,
        contact_info=req.contact_info,
        remark=req.remark,
    )
    db.add(reg)
    await db.commit()
    await db.refresh(reg)
    return EventRegistrationOut.model_validate(reg)


@router.post("/{id}/cancel")
async def cancel_registration(id: int, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    result = await db.execute(
        select(EventRegistration).where(
            EventRegistration.event_id == id,
            EventRegistration.user_id == user.id
        )
    )
    reg = result.scalar_one_or_none()
    if not reg:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    reg.status = "cancelled"
    await db.commit()
    return {"ok": True}


@router.get("/{id}/registrations", response_model=list[EventRegistrationOut])
async def list_registrations(
    id: int,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    event_result = await db.execute(select(Event).where(Event.id == id))
    event = event_result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="活动不存在")
    if event.created_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看报名名单")

    result = await db.execute(
        select(EventRegistration).where(EventRegistration.event_id == id).order_by(EventRegistration.created_at.desc())
    )
    return [EventRegistrationOut.model_validate(r) for r in result.scalars().all()]
