import os
import json
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from database import get_db
from models import KnowledgeBase, KbDocument, DocVersion
from schemas import DocumentOut, DocumentUpdate, DocVersionOut, OnlineDocCreate, OnlineDocUpdate, DocumentContentOut
from utils.security import get_current_user
from services.permission import can_access_kb
from services.file import save_upload_file, save_online_content, copy_for_version, validate_file
from services.parser import parse_file
from services.embedding import get_embedding

router = APIRouter(tags=["document"])


def file_type_from_name(filename: str) -> str:
    return os.path.splitext(filename)[1][1:].lower()


async def _can_access_kb(db, kb: KnowledgeBase, user) -> bool:
    return kb.status == "published" and await can_access_kb(db, kb.org_code, user.scope_code)


@router.get("/api/v1/kb/{kb_id}/documents", response_model=list[DocumentOut])
async def list_documents(
    kb_id: int,
    folder: str = "/",
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not await _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该知识库")

    result = await db.execute(
        select(KbDocument).where(
            KbDocument.kb_id == kb_id,
            KbDocument.folder_path == folder,
        ).order_by(KbDocument.created_at.desc())
    )
    return [DocumentOut.model_validate(d) for d in result.scalars().all()]


@router.post("/api/v1/kb/{kb_id}/documents", response_model=DocumentOut)
async def upload_document(
    kb_id: int,
    folder_path: str = Form("/"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该知识库")

    file_size = 0
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    ext = validate_file(file.filename or "unknown", file_size)

    doc = KbDocument(
        kb_id=kb_id,
        name=file.filename or "unknown",
        file_path="",
        file_size=file_size,
        file_type=file_type_from_name(file.filename or ""),
        folder_path=folder_path,
        org_code=kb.org_code,
        status="parsing",
        created_by=user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        file_path = await save_upload_file(kb_id, doc.id, file)
        doc.file_path = file_path
        await db.commit()

        version = DocVersion(
            doc_id=doc.id,
            version_no=1,
            file_path=file_path,
            change_note="初始上传",
            created_by=user.id,
        )
        db.add(version)
        await db.commit()

        await _parse_and_embed(db, doc, kb, user)
    except Exception as e:
        doc.status = "failed"
        doc.parse_error = str(e)
        await db.commit()

    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.post("/api/v1/kb/{kb_id}/online-documents", response_model=DocumentOut)
async def create_online_document(
    kb_id: int,
    req: OnlineDocCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if not await _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该知识库")

    content_bytes = req.content.encode("utf-8")
    doc = KbDocument(
        kb_id=kb_id,
        name=req.name,
        file_path="",
        file_size=len(content_bytes),
        file_type="online",
        folder_path=req.folder_path,
        scope_level=kb.scope_level,
        org_code=kb.org_code,
        status="parsing",
        created_by=user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    try:
        file_path = await save_online_content(kb_id, doc.id, req.content)
        doc.file_path = file_path
        await db.commit()

        version = DocVersion(
            doc_id=doc.id,
            version_no=1,
            file_path=file_path,
            change_note="创建在线文档",
            created_by=user.id,
        )
        db.add(version)
        await db.commit()

        await _parse_and_embed(db, doc, kb, user)
    except Exception as e:
        doc.status = "failed"
        doc.parse_error = str(e)
        await db.commit()

    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


async def _parse_and_embed(db: AsyncSession, doc: KbDocument, kb: KnowledgeBase, user, increment_doc_count: bool = True):
    try:
        chunks = await parse_file(doc.file_path, doc.file_type or "txt")
        if not chunks:
            doc.status = "ready"
            await db.commit()
            return

        texts = [c["content"] for c in chunks]
        embeddings = await get_embedding(texts)

        for c, emb in zip(chunks, embeddings):
            vec_str = "[" + ",".join(str(v) for v in emb) + "]"
            await db.execute(
                text("""
                    INSERT INTO doc_chunk (doc_id, kb_id, content, meta, embedding, scope_level, org_code)
                    VALUES (:doc_id, :kb_id, :content, :meta, CAST(:embedding AS vector), :scope_level, :org_code)
                """),
                {
                    "doc_id": doc.id,
                    "kb_id": kb.id,
                    "content": c["content"],
                    "meta": json.dumps(c["meta"]),
                    "embedding": vec_str,
                    "scope_level": doc.scope_level or kb.scope_level or 1,
                    "org_code": doc.org_code or kb.org_code,
                }
            )

        doc.status = "ready"
        doc.parse_error = None
        if increment_doc_count:
            kb.doc_count = (kb.doc_count or 0) + 1
        kb.last_updated = func.now()
        await db.commit()
    except Exception as e:
        doc.status = "failed"
        doc.parse_error = str(e)
        await db.commit()
        raise


@router.get("/api/v1/documents/{id}", response_model=DocumentOut)
async def get_document(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")
    return DocumentOut.model_validate(doc)


@router.put("/api/v1/documents/{id}", response_model=DocumentOut)
async def update_document(
    id: int,
    req: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")

    if doc.created_by != user.id and (not kb or kb.owner_id != user.id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该文档")

    if req.name is not None:
        doc.name = req.name
    if req.folder_path is not None:
        doc.folder_path = req.folder_path

    await db.commit()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/api/v1/documents/{id}/content", response_model=DocumentContentOut)
async def get_document_content(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")
    if doc.file_type != "online":
        raise HTTPException(status_code=400, detail="仅在线文档支持内容读取")
    try:
        with open(doc.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = ""
    return DocumentContentOut(id=doc.id, name=doc.name, content=content, file_type=doc.file_type)


@router.put("/api/v1/documents/{id}/content", response_model=DocumentContentOut)
async def update_document_content(
    id: int,
    req: OnlineDocUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")

    if doc.created_by != user.id and (not kb or kb.owner_id != user.id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权修改该文档")

    if doc.file_type != "online":
        raise HTTPException(status_code=400, detail="仅在线文档支持内容编辑")

    if req.name is not None:
        doc.name = req.name

    content = req.content if req.content is not None else None
    if content is not None:
        new_version_no = doc.current_version + 1
        file_path = await save_online_content(doc.kb_id, doc.id, content, version_no=new_version_no)
        doc.file_path = file_path
        doc.file_size = len(content.encode("utf-8"))
        doc.current_version = new_version_no
        doc.status = "parsing"
        await db.commit()

        version = DocVersion(
            doc_id=doc.id,
            version_no=new_version_no,
            file_path=file_path,
            change_note="编辑在线文档",
            created_by=user.id,
        )
        db.add(version)
        await db.commit()

        await db.execute(text("DELETE FROM doc_chunk WHERE doc_id = :doc_id"), {"doc_id": doc.id})
        await db.commit()

        await _parse_and_embed(db, doc, kb, user, increment_doc_count=False)
    else:
        await db.commit()

    await db.refresh(doc)
    try:
        with open(doc.file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        content = ""
    return DocumentContentOut(id=doc.id, name=doc.name, content=content, file_type=doc.file_type)


@router.get("/api/v1/documents/{id}/versions", response_model=list[DocVersionOut])
async def list_versions(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")

    result = await db.execute(
        select(DocVersion).where(DocVersion.doc_id == id).order_by(DocVersion.version_no.desc())
    )
    return [DocVersionOut.model_validate(v) for v in result.scalars().all()]


@router.post("/api/v1/documents/{id}/rollback")
async def rollback_version(id: int, version_no: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")

    ver_result = await db.execute(
        select(DocVersion).where(DocVersion.doc_id == id, DocVersion.version_no == version_no)
    )
    ver = ver_result.scalar_one_or_none()
    if not ver:
        raise HTTPException(status_code=404, detail="版本不存在")

    new_version_no = doc.current_version + 1
    new_path = copy_for_version(ver.file_path, new_version_no)

    new_ver = DocVersion(
        doc_id=id,
        version_no=new_version_no,
        file_path=new_path,
        change_note=f"回滚到版本 {version_no}",
        created_by=user.id,
    )
    db.add(new_ver)
    doc.file_path = new_path
    doc.current_version = new_version_no
    await db.commit()
    return {"ok": True, "current_version": new_version_no}


@router.get("/api/v1/documents/{id}/preview")
async def preview_document(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    from services.preview import generate_preview
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")
    return generate_preview(doc.file_path, doc.file_type or "")


@router.get("/api/v1/documents/{id}/download")
async def download_document(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文件不存在")
    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文件")
    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(doc.file_path, filename=doc.name)


@router.delete("/api/v1/documents/{id}")
async def delete_document(id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(KbDocument).where(KbDocument.id == id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    kb_result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == doc.kb_id))
    kb = kb_result.scalar_one_or_none()
    if not kb or not _can_access_kb(db, kb, user):
        raise HTTPException(status_code=403, detail="无权访问该文档")

    if doc.created_by != user.id and (not kb or kb.owner_id != user.id) and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该文档")

    try:
        dir_path = os.path.dirname(doc.file_path)
        if os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
    except Exception:
        pass

    if kb and doc.status == "ready" and kb.doc_count:
        kb.doc_count = max(0, kb.doc_count - 1)

    await db.delete(doc)
    await db.commit()
    return {"ok": True}
