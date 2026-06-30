from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Org


def get_level_from_scope(scope_code: str) -> int:
    """已废弃：仅保留兼容旧数据解析，新业务不再使用权限层级。"""
    parts = scope_code.split('-')
    if len(parts) != 4:
        return 4
    if parts[1] == '00' and parts[2] == '00' and parts[3] == '00':
        return 1
    elif parts[2] == '00' and parts[3] == '00':
        return 2
    elif parts[3] == '00':
        return 3
    else:
        return 4


def get_org_prefix(scope_code: str, level: int) -> str:
    """已废弃：仅保留兼容旧调用。"""
    parts = scope_code.split('-')
    if level == 1:
        return parts[0]
    elif level == 2:
        return f"{parts[0]}-{parts[1]}"
    elif level == 3:
        return f"{parts[0]}-{parts[1]}-{parts[2]}"
    else:
        return scope_code


def can_access(user_scope: str, target_scope: str) -> bool:
    """已废弃：旧的双 scope 比较逻辑。"""
    user_level = get_level_from_scope(user_scope)
    target_level = get_level_from_scope(target_scope)

    if user_level < target_level:
        return target_scope.startswith(get_org_prefix(user_scope, user_level))
    elif user_level == target_level:
        return user_scope == target_scope
    else:
        return False


def build_permission_filter(user_scope: str):
    """已废弃：返回旧格式，避免遗留调用报错。"""
    user_level = get_level_from_scope(user_scope)
    user_org_prefix = get_org_prefix(user_scope, user_level)
    return user_level, user_org_prefix


async def get_org_path(db: AsyncSession, code: str) -> str | None:
    result = await db.execute(select(Org.path).where(Org.code == code))
    return result.scalar_one_or_none()


async def can_access_kb(db: AsyncSession, kb_org_code: str, user_scope_code: str) -> bool:
    """判断用户所在组织是否在知识库选定组织节点及其子树下。"""
    kb_path = await get_org_path(db, kb_org_code)
    user_path = await get_org_path(db, user_scope_code)
    if not kb_path or not user_path:
        return False
    # 完全相等，或用户路径以知识库路径加 / 开头
    return user_path == kb_path or user_path.startswith(kb_path + "/")


async def get_user_org_path(db: AsyncSession, user_scope_code: str) -> str | None:
    return await get_org_path(db, user_scope_code)
