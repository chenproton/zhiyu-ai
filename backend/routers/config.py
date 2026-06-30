from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from database import get_db
from models import SysConfig, SysUser
from schemas import SysConfigItem, SysConfigUpdate, SysConfigOut
from utils.security import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/config", tags=["config"])

DEFAULT_CONFIGS = {
    "site_announcement": {
        "value": {"enabled": False, "content": ""},
        "description": "站点公告配置"
    },
    "registration_switch": {
        "value": {"enabled": True},
        "description": "用户注册开关"
    },
    "llm_settings": {
        "value": {
            "default_model": "deepseek-chat",
            "available_models": ["deepseek-chat", "qwen-turbo", "gpt-3.5-turbo"],
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 1.0
        },
        "description": "大语言模型参数配置"
    },
    "recommendation_slots": {
        "value": {
            "home_banners": [],
            "featured_kbs": [],
            "featured_bots": []
        },
        "description": "首页推荐位配置"
    },
    "file_upload_settings": {
        "value": {
            "max_size_mb": 50,
            "allowed_types": [".pdf", ".doc", ".docx", ".txt", ".md", ".markdown", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"]
        },
        "description": "文件上传限制配置"
    }
}


async def _ensure_config(db: AsyncSession, key: str):
    result = await db.execute(select(SysConfig).where(SysConfig.key == key))
    cfg = result.scalar_one_or_none()
    if not cfg:
        default = DEFAULT_CONFIGS.get(key)
        if not default:
            return None
        cfg = SysConfig(key=key, value=default["value"], description=default["description"])
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
    return cfg


@router.get("", response_model=list[SysConfigOut])
async def list_configs(db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    result = await db.execute(select(SysConfig))
    configs = {c.key: c for c in result.scalars().all()}
    out = []
    for key, default in DEFAULT_CONFIGS.items():
        cfg = configs.get(key) or await _ensure_config(db, key)
        out.append(SysConfigOut.model_validate(cfg))
    return out


@router.get("/{key}", response_model=SysConfigOut)
async def get_config(key: str, db: AsyncSession = Depends(get_db), user: SysUser = Depends(get_current_user)):
    # 部分配置允许普通用户读取
    public_keys = {"site_announcement", "llm_settings", "file_upload_settings", "recommendation_slots"}
    if key not in public_keys and user.role != "admin":
        raise HTTPException(status_code=403, detail="无权查看该配置")
    cfg = await _ensure_config(db, key)
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    return SysConfigOut.model_validate(cfg)


@router.put("/{key}", response_model=SysConfigOut)
async def update_config(
    key: str,
    req: SysConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(require_admin)
):
    cfg = await _ensure_config(db, key)
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    if req.value is not None:
        cfg.value = req.value
    if req.description is not None:
        cfg.description = req.description
    cfg.updated_by = user.id
    cfg.updated_at = datetime.now()
    await db.commit()
    await db.refresh(cfg)
    return SysConfigOut.model_validate(cfg)


@router.put("")
async def batch_update_configs(
    items: list[SysConfigItem],
    db: AsyncSession = Depends(get_db),
    user: SysUser = Depends(require_admin)
):
    for item in items:
        cfg = await _ensure_config(db, item.key)
        if cfg:
            cfg.value = item.value
            cfg.updated_by = user.id
            cfg.updated_at = datetime.now()
    await db.commit()
    return {"ok": True}


@router.post("/{key}/reset")
async def reset_config(key: str, db: AsyncSession = Depends(get_db), _=Depends(require_admin)):
    default = DEFAULT_CONFIGS.get(key)
    if not default:
        raise HTTPException(status_code=404, detail="配置不存在")
    cfg = await _ensure_config(db, key)
    cfg.value = default["value"]
    cfg.description = default["description"]
    await db.commit()
    return SysConfigOut.model_validate(cfg)
