import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import SysUser, ChatHistory
from schemas import ChatRequest, ChatMessage
from utils.security import get_current_user
from services.rag import search_chunks, filter_kb_by_permission
from services.bot_engine import load_bot_config, get_bot_kb_ids
from services.llm import stream_deepseek

router = APIRouter(tags=["chat"])


def format_sse(event_type: str, content: str) -> str:
    return f"data: {json.dumps({'type': event_type, 'content': content}, ensure_ascii=False)}\n\n"


def _build_system_prompt(name=None, description=None, system_prompt=None, welcome_msg=None, default=None):
    parts = []
    if name:
        parts.append(f"你是「{name}」。")
    if description:
        parts.append(f"角色定位：{description}")
    if system_prompt:
        parts.append(system_prompt)
    if welcome_msg:
        parts.append(f"用户进入对话时，你的第一句话必须是：{welcome_msg}")
    if parts:
        return "\n".join(parts)
    return default or "你是一位学校智能助手。基于以下资料回答问题。"


@router.post("/api/v1/chat")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    allowed_kb_ids = await filter_kb_by_permission(db, user, req.kb_ids or [])
    system_prompt = _build_system_prompt(
        req.name, req.description, req.system_prompt, req.welcome_msg
    )
    return StreamingResponse(
        _chat_stream(db, user, req.question, allowed_kb_ids, req.history or [], system_prompt),
        media_type="text/event-stream"
    )


@router.post("/api/v1/chat/bot/{bot_id}")
async def chat_bot(bot_id: int, req: ChatRequest, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    bot = await load_bot_config(db, bot_id, user)
    if not bot:
        raise HTTPException(status_code=404, detail="机器人不存在或无权访问")
    kb_ids = await get_bot_kb_ids(db, bot_id)
    allowed_kb_ids = await filter_kb_by_permission(db, user, kb_ids)
    system_prompt = _build_system_prompt(bot.name, bot.description, bot.prompt, bot.welcome_msg)

    async def stream():
        async for item in _chat_stream(db, user, req.question, allowed_kb_ids, req.history or [], system_prompt, bot_id=bot_id):
            yield item

    return StreamingResponse(stream(), media_type="text/event-stream")


async def _chat_stream(
    db: AsyncSession,
    user: SysUser,
    question: str,
    kb_ids: list,
    history: list,
    system_prompt: str = "你是一位学校智能助手。基于以下资料回答问题。",
    bot_id: int = None
):
    yield format_sse("thinking", "正在检索相关资料...")

    chunks = []
    if kb_ids:
        chunks = await search_chunks(db, question, user, kb_ids, top_k=5)

    if not chunks:
        full_answer = ""
        async for token in stream_deepseek(system_prompt, question, [h.model_dump() for h in history]):
            full_answer += token
            yield format_sse("answer", token)
        yield format_sse("done", json.dumps({"sources": []}))
        await _save_history(db, user, bot_id, kb_ids, question, full_answer, [])
        return

    sources = [{
        "doc_name": c["doc_name"],
        "page": c["meta"].get("page"),
        "content": c["content"],
        "doc_id": c["doc_id"],
        "kb_id": c["kb_id"],
    } for c in chunks]
    yield format_sse("source", json.dumps(sources, ensure_ascii=False))

    context = "\n\n".join([
        f"[来源：{c['doc_name']} 第{c['meta'].get('page', 'N')}页]\n{c['content']}"
        for c in chunks
    ])

    full_prompt = f"""{system_prompt}

规则：
1. 必须基于提供的资料回答，不确定时明确告知
2. 每个关键信息必须标注来源，格式：【来源：《文档名》第X页】
3. 如果资料不足以回答，说"根据现有资料无法完全回答"

资料：
{context}"""

    full_answer = ""
    async for token in stream_deepseek(full_prompt, question, [h.model_dump() for h in history]):
        full_answer += token
        yield format_sse("answer", token)

    yield format_sse("done", json.dumps({"sources": sources}, ensure_ascii=False))

    source_records = [{
        "doc_name": c["doc_name"],
        "page": c["meta"].get("page"),
        "content": c["content"][:200]
    } for c in chunks]
    await _save_history(db, user, bot_id, kb_ids, question, full_answer, source_records)


async def _save_history(db, user, bot_id, kb_ids, question, answer, sources):
    history = ChatHistory(
        bot_id=bot_id,
        kb_id=kb_ids[0] if kb_ids else None,
        user_id=user.id,
        question=question,
        answer=answer,
        sources=sources,
    )
    db.add(history)
    await db.commit()
