from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from models import SysUser, Org
from services.permission import get_user_org_path
from services.embedding import get_embedding


async def search_chunks(
    db: AsyncSession,
    query: str,
    user: SysUser,
    kb_ids: List[int],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    if not kb_ids:
        return []

    query_vec_list = await get_embedding([query])
    query_vec = query_vec_list[0]
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    sql = text("""
        SELECT
            c.id, c.content, c.meta, c.doc_id, c.kb_id,
            d.name as doc_name,
            1 - (c.embedding <=> :query_vec) AS score
        FROM doc_chunk c
        JOIN kb_document d ON c.doc_id = d.id
        JOIN knowledge_base kb ON c.kb_id = kb.id
        WHERE c.kb_id = ANY(:kb_ids)
          AND d.status = 'ready'
          AND kb.status = 'published'
        ORDER BY c.embedding <=> :query_vec
        LIMIT :top_k
    """)

    result = await db.execute(sql, {
        "query_vec": vec_str,
        "kb_ids": kb_ids,
        "top_k": top_k,
    })

    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def filter_kb_by_permission(db: AsyncSession, user: SysUser, kb_ids: List[int]) -> List[int]:
    if not kb_ids:
        return []
    user_path = await get_user_org_path(db, user.scope_code)
    if not user_path:
        return []
    sql = text("""
        SELECT kb.id
        FROM knowledge_base kb
        JOIN org o ON kb.org_code = o.code
        WHERE kb.id = ANY(:kb_ids)
          AND kb.status = 'published'
          AND (o.path = :user_path OR o.path LIKE :user_path_prefix || '%')
    """)
    result = await db.execute(sql, {
        "kb_ids": kb_ids,
        "user_path": user_path,
        "user_path_prefix": user_path + "/",
    })
    return [row[0] for row in result.all()]
