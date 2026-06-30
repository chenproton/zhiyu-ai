from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from database import get_db
from models import BotConfig, BotKnowledgeBase, BotAssignedUser, SysUser
from schemas import BotCreate, BotOut, BotDetail, BotReviewRequest
from utils.security import get_current_user, require_admin
from services.llm import complete_deepseek
from pydantic import BaseModel
import json

router = APIRouter(prefix="/api/v1/bots", tags=["bot"])


class BotGenerateRequest(BaseModel):
    description: str


@router.get("", response_model=list[BotDetail])
async def list_bots(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(
        select(BotConfig).where(
            (BotConfig.creator_id == user.id) |
            (BotConfig.share_type == "public") |
            (BotConfig.is_official == True)
        ).order_by(BotConfig.is_official.desc(), BotConfig.created_at.desc())
    )
    bots = result.scalars().all()
    out = []
    for bot in bots:
        detail = BotDetail.model_validate(bot)
        kb_result = await db.execute(select(BotKnowledgeBase.kb_id).where(BotKnowledgeBase.bot_id == bot.id))
        detail.kb_ids = [row[0] for row in kb_result.all()]
        out.append(detail)
    return out


@router.get("/public", response_model=list[BotOut])
async def public_bots(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(BotConfig).where(
            ((BotConfig.share_type == "public") & (BotConfig.status == "active")) | (BotConfig.is_official == True)
        ).order_by(BotConfig.is_official.desc(), BotConfig.created_at.desc())
    )
    return [BotOut.model_validate(b) for b in result.scalars().all()]


@router.get("/official", response_model=list[BotOut])
async def official_bots(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(
        select(BotConfig).where(BotConfig.is_official == True).order_by(BotConfig.created_at.desc())
    )
    return [BotOut.model_validate(b) for b in result.scalars().all()]


@router.get("/all", response_model=list[BotDetail])
async def all_bots(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(
        select(BotConfig, SysUser.name.label("creator_name"))
        .outerjoin(SysUser, BotConfig.creator_id == SysUser.id)
        .order_by(BotConfig.created_at.desc())
    )
    out = []
    for bot, creator_name in result.all():
        detail = BotDetail.model_validate(bot)
        detail.creator_name = creator_name
        kb_result = await db.execute(select(BotKnowledgeBase.kb_id).where(BotKnowledgeBase.bot_id == bot.id))
        detail.kb_ids = [row[0] for row in kb_result.all()]
        out.append(detail)
    return out


@router.post("/{id}/review")
async def review_bot(id: int, req: BotReviewRequest, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(BotConfig).where(BotConfig.id == id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    if req.status not in ("active", "pending", "inactive"):
        raise HTTPException(status_code=400, detail="状态不合法")
    bot.status = req.status
    await db.commit()
    return {"ok": True}


@router.post("", response_model=BotOut)
async def create_bot(req: BotCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    status = req.status or "active"
    if user.role != "admin" and req.share_type == "public":
        status = "pending"
    bot = BotConfig(
        name=req.name,
        description=req.description,
        prompt=req.prompt,
        welcome_msg=req.welcome_msg,
        model=req.model,
        creator_id=user.id,
        share_type=req.share_type,
        status=status,
        avatar=req.avatar,
    )
    db.add(bot)
    await db.commit()
    await db.refresh(bot)

    for kb_id in req.kb_ids:
        db.add(BotKnowledgeBase(bot_id=bot.id, kb_id=kb_id))
    await db.commit()
    return BotOut.model_validate(bot)


@router.post("/generate")
async def generate_bot_config(req: BotGenerateRequest, _=Depends(get_current_user)):
    system_prompt = (
        "你是一位智能体配置助手。请根据用户的一句话描述，为校园 AI 对话机器人生成以下字段："
        "name（智能体名称，不超过 15 字）、description（智能体描述，一句话）、"
        "prompt（系统提示词，用于定义机器人的角色、能力、回答风格，200 字左右）、"
        "welcome_msg（欢迎语，30 字以内）。"
        "必须以 JSON 对象返回，且只返回 JSON，不要包含其他内容。"
    )
    content = await complete_deepseek(system_prompt, f"请为以下描述生成机器人配置：{req.description}")
    try:
        data = json.loads(content)
    except Exception:
        # 尝试从文本中提取 JSON 块
        try:
            start = content.index('{')
            end = content.rindex('}') + 1
            data = json.loads(content[start:end])
        except Exception:
            data = {}
    return {
        "name": data.get("name", ""),
        "description": data.get("description", ""),
        "prompt": data.get("prompt", ""),
        "welcome_msg": data.get("welcome_msg", ""),
    }


@router.get("/{id}", response_model=BotDetail)
async def get_bot(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BotConfig).where(BotConfig.id == id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    detail = BotDetail.model_validate(bot)
    kb_result = await db.execute(select(BotKnowledgeBase.kb_id).where(BotKnowledgeBase.bot_id == id))
    detail.kb_ids = [row[0] for row in kb_result.all()]
    return detail


@router.put("/{id}", response_model=BotOut)
async def update_bot(id: int, req: BotCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BotConfig).where(BotConfig.id == id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    if bot.creator_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改")

    data = req.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k in ("kb_ids",):
            continue
        setattr(bot, k, v)

    if user.role == "admin" and "status" in data:
        bot.status = data["status"]
    elif user.role != "admin" and data.get("share_type") == "public":
        bot.status = "pending"

    await db.commit()

    # 删除旧关联再重建
    await db.execute(delete(BotKnowledgeBase).where(BotKnowledgeBase.bot_id == id))
    await db.commit()

    for kb_id in data.get("kb_ids", req.kb_ids):
        db.add(BotKnowledgeBase(bot_id=bot.id, kb_id=kb_id))
    await db.commit()
    await db.refresh(bot)
    return BotOut.model_validate(bot)


@router.delete("/{id}")
async def delete_bot(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(BotConfig).where(BotConfig.id == id))
    bot = result.scalar_one_or_none()
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在")
    if bot.creator_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除")
    await db.delete(bot)
    await db.commit()
    return {"ok": True}


@router.post("/{id}/preview")
async def preview_bot(id: int, question: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from services.bot_engine import load_bot_config, get_bot_kb_ids
    from services.rag import search_chunks, filter_kb_by_permission
    bot = await load_bot_config(db, id, user)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在或无权访问")
    kb_ids = await get_bot_kb_ids(db, id)
    allowed = await filter_kb_by_permission(db, user, kb_ids)
    chunks = await search_chunks(db, question, user, allowed, top_k=3)
    return {"chunks": chunks}
