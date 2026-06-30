from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from models import BotConfig, BotKnowledgeBase, BotAssignedUser
from services.permission import can_access


async def load_bot_config(db: AsyncSession, bot_id: int, user) -> Optional[BotConfig]:
    result = await db.execute(
        select(BotConfig).where(BotConfig.id == bot_id, BotConfig.status == "active")
    )
    bot = result.scalar_one_or_none()
    if not bot:
        return None

    if bot.is_official:
        return bot

    if bot.share_type == "public":
        return bot

    if bot.creator_id == user.id:
        return bot

    if bot.share_type == "assigned":
        assigned = await db.execute(
            select(BotAssignedUser).where(
                BotAssignedUser.bot_id == bot_id,
                BotAssignedUser.user_id == user.id
            )
        )
        if assigned.scalar_one_or_none():
            return bot
        return None

    return None


async def get_bot_kb_ids(db: AsyncSession, bot_id: int) -> list:
    result = await db.execute(
        select(BotKnowledgeBase.kb_id).where(BotKnowledgeBase.bot_id == bot_id)
    )
    return [row[0] for row in result.all()]


async def get_bot_with_kb_ids(db: AsyncSession, bot_id: int, user):
    bot = await load_bot_config(db, bot_id, user)
    if not bot:
        return None, []
    kb_ids = await get_bot_kb_ids(db, bot_id)
    return bot, kb_ids
