import os
import shutil
import aiofiles
from pathlib import Path
from fastapi import UploadFile
from config import settings


ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".md", ".markdown", ".png", ".jpg", ".jpeg", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".bmp", ".gif", ".webp", ".tiff"}
FORBIDDEN_EXTENSIONS = {".exe", ".bat", ".sh", ".cmd", ".com", ".msi"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def ensure_storage_path() -> Path:
    path = Path(settings.FILE_STORAGE_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return path


def validate_file(filename: str, file_size: int):
    ext = Path(filename).suffix.lower()
    if ext in FORBIDDEN_EXTENSIONS:
        raise ValueError(f"禁止上传可执行文件: {ext}")
    if file_size > MAX_FILE_SIZE:
        raise ValueError("单文件最大 50MB")
    return ext


async def save_upload_file(kb_id: int, doc_id: int, file: UploadFile) -> str:
    ensure_storage_path()
    ext = Path(file.filename or "unknown").suffix
    dir_path = Path(settings.FILE_STORAGE_PATH) / str(kb_id) / str(doc_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"v1{ext}"

    async with aiofiles.open(file_path, "wb") as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)

    return str(file_path)


def copy_for_version(src_path: str, version_no: int) -> str:
    src = Path(src_path)
    dst = src.parent / f"v{version_no}{src.suffix}"
    shutil.copy2(src, dst)
    return str(dst)


async def save_online_content(kb_id: int, doc_id: int, content: str, version_no: int = 1) -> str:
    ensure_storage_path()
    dir_path = Path(settings.FILE_STORAGE_PATH) / str(kb_id) / str(doc_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"v{version_no}.html"
    async with aiofiles.open(file_path, "w", encoding="utf-8") as out_file:
        await out_file.write(content)
    return str(file_path)
