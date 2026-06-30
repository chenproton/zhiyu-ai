from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from database import get_db
from models import SysUser, KnowledgeBase, BotConfig, Org
from schemas import SearchRequest, SearchResponse, SearchResult, PlazaSearchResponse, PlazaSearchItem
from utils.security import get_current_user
from services.rag import search_chunks, filter_kb_by_permission
from services.permission import get_user_org_path

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(req: SearchRequest, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    allowed_kb_ids = await filter_kb_by_permission(db, user, req.kb_ids)
    if not allowed_kb_ids:
        raise HTTPException(status_code=403, detail="没有可搜索的知识库权限")

    chunks = await search_chunks(db, req.query, user, allowed_kb_ids, req.top_k)
    return SearchResponse(
        chunks=[SearchResult.model_validate(c) for c in chunks],
        total=len(chunks),
    )


@router.get("/plaza", response_model=PlazaSearchResponse)
async def search_plaza(
    q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(get_current_user)
):
    user_path = await get_user_org_path(db, user.scope_code)
    keyword = f"%{q}%"

    kb_result = await db.execute(
        select(KnowledgeBase)
        .join(Org, KnowledgeBase.org_code == Org.code)
        .where(
            KnowledgeBase.status == "published",
            (Org.path == user_path) | (Org.path.like(f"{user_path}/%")),
            or_(KnowledgeBase.name.ilike(keyword), KnowledgeBase.description.ilike(keyword))
        )
        .order_by(KnowledgeBase.created_at.desc())
    )
    kbs = kb_result.scalars().all()

    bot_result = await db.execute(
        select(BotConfig).where(
            BotConfig.status == "active",
            or_(
                BotConfig.is_official == True,
                BotConfig.share_type == "public",
                BotConfig.creator_id == user.id
            ),
            or_(BotConfig.name.ilike(keyword), BotConfig.description.ilike(keyword))
        ).order_by(BotConfig.is_official.desc(), BotConfig.created_at.desc())
    )
    bots = bot_result.scalars().all()

    results = []
    for kb in kbs:
        results.append(PlazaSearchItem(
            id=kb.id, type="kb", name=kb.name, description=kb.description,
            org_code=kb.org_code
        ))
    for bot in bots:
        results.append(PlazaSearchItem(
            id=bot.id, type="bot", name=bot.name, description=bot.description,
            is_official=bot.is_official
        ))

    return PlazaSearchResponse(results=results, total=len(results))
