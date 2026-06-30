from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import SysUser, SysConfig
from schemas import LoginRequest, RegisterRequest, UserInfo, Token
from utils.security import verify_password, create_access_token, get_password_hash, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SysUser).where(SysUser.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已禁用")

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserInfo.model_validate(user),
    }


@router.post("/register", response_model=UserInfo)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # 检查注册开关
    cfg = await db.execute(select(SysConfig).where(SysConfig.key == "registration_switch"))
    reg_cfg = cfg.scalar_one_or_none()
    if reg_cfg and reg_cfg.value and reg_cfg.value.get("enabled") is False:
        raise HTTPException(status_code=403, detail="当前已关闭用户注册")

    existing = await db.execute(select(SysUser).where(SysUser.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = SysUser(
        username=req.username,
        password=get_password_hash(req.password),
        name=req.name,
        org_code=req.org_code,
        scope_code=req.scope_code,
        role="viewer",
        status="active",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserInfo.model_validate(user)


@router.get("/me", response_model=UserInfo)
async def me(current_user: SysUser = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)
