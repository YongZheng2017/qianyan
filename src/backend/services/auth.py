"""
认证服务

处理用户登录、权限验证等认证相关业务逻辑
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from ..models import User, Role, Permission
from ..utils.security import verify_password


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str
) -> Optional[User]:
    """
    认证用户

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        Optional[User]: 用户对象，认证失败返回 None
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        return None

    # 验证密码
    if not verify_password(password, user.password_hash):
        return None

    # 检查用户状态
    if user.status != 1:
        return None

    return user


async def get_user_permissions(db: AsyncSession, user_id: int) -> List[str]:
    """
    获取用户的所有权限

    Args:
        db: 数据库会话
        user_id: 用户ID

    Returns:
        List[str]: 权限名称列表
    """
    # 查询用户及其角色和权限
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles).selectinload(Role.permissions))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        return []

    # 收集所有权限名称（去重）
    permissions = set()
    for role in user.roles:
        for permission in role.permissions:
            permissions.add(permission.permission_name)

    return list(permissions)


async def has_admin_permission(permissions: List[str]) -> bool:
    """
    检查是否有管理权限

    Args:
        permissions: 权限列表

    Returns:
        bool: 是否有管理权限
    """
    # 至少有一个用户管理权限就认为是管理员
    admin_permissions = [
        "user:read",
        "user:write",
        "user:delete",
        "user:reset_password"
    ]
    return any(perm in permissions for perm in admin_permissions)


async def update_last_login(db: AsyncSession, user_id: int) -> None:
    """
    更新用户最后登录时间

    Args:
        db: 数据库会话
        user_id: 用户ID
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if user:
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()