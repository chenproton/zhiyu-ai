from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import ExternalAgent
from schemas import ExternalAgentCreate, ExternalAgentUpdate, ExternalAgentOut
from utils.security import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/external-agents", tags=["external-agent"])


@router.get("", response_model=list[ExternalAgentOut])
async def list_agents(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(ExternalAgent).where(ExternalAgent.is_active == True).order_by(ExternalAgent.sort_order)
    )
    return [ExternalAgentOut.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=ExternalAgentOut)
async def create_agent(req: ExternalAgentCreate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    agent = ExternalAgent(**req.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return ExternalAgentOut.model_validate(agent)


@router.get("/{id}", response_model=ExternalAgentOut)
async def get_agent(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(ExternalAgent).where(ExternalAgent.id == id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    return ExternalAgentOut.model_validate(agent)


@router.put("/{id}", response_model=ExternalAgentOut)
async def update_agent(id: int, req: ExternalAgentUpdate, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(ExternalAgent).where(ExternalAgent.id == id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    await db.commit()
    await db.refresh(agent)
    return ExternalAgentOut.model_validate(agent)


@router.delete("/{id}")
async def delete_agent(id: int, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(ExternalAgent).where(ExternalAgent.id == id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    await db.delete(agent)
    await db.commit()
    return {"ok": True}
