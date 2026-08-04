"""
系统初始化服务

负责首次启动时创建默认管理员账号和权限
"""
import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import User, Role, Permission
from ..utils.security import hash_password
from ..core.config import settings

logger = logging.getLogger(__name__)

# 预定义的权限列表
DEFAULT_PERMISSIONS: List[Tuple[str, str, str, str]] = [
    # 用户管理权限
    ("user:read", "查看用户", "users", "read"),
    ("user:write", "新增/编辑用户", "users", "write"),
    ("user:delete", "删除用户", "users", "delete"),
    ("user:reset_password", "重置用户密码", "users", "write"),
    # 数据源管理权限
    ("data_source:manage", "管理数据源", "data_sources", "write"),
    # 股票管理权限
    ("stock:manage", "管理股票", "stocks", "write"),
    # 标签管理权限
    ("tag:manage", "管理标签", "tags", "write"),
    # 分析功能权限
    ("stock:quote:read", "查看股票行情", "stock/quote", "read"),
    ("analysis:fundamental:read", "基本面分析", "analysis/fundamental", "read"),
    ("analysis:trend:read", "趋势分析", "analysis/trend", "read"),
    ("analysis:fund:read", "资金分析", "analysis/fund-flow", "read"),
]


async def init_system(db: AsyncSession) -> None:
    """
    系统初始化

    创建默认管理员账号、角色和权限

    Args:
        db: 数据库会话
    """
    logger.info("开始系统初始化...")

    # 1. 检查是否已初始化
    result = await db.execute(
        select(User).where(User.username == settings.ADMIN_DEFAULT_USERNAME)
    )
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        logger.info("系统已初始化，跳过创建管理员")
        return

    # 2. 创建所有权限
    permissions = []
    for perm_name, perm_desc, resource, action in DEFAULT_PERMISSIONS:
        result = await db.execute(
            select(Permission).where(Permission.permission_name == perm_name)
        )
        perm = result.scalar_one_or_none()

        if not perm:
            perm = Permission(
                permission_name=perm_name,
                permission_desc=perm_desc,
                resource=resource,
                action=action
            )
            db.add(perm)
            await db.flush()

        permissions.append(perm)

    logger.info(f"已创建/确认 {len(permissions)} 个权限")

    # 3. 创建管理员角色
    result = await db.execute(
        select(Role).where(Role.role_name == "admin")
    )
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        admin_role = Role(
            role_name="admin",
            role_desc="系统管理员",
            permissions=permissions  # 直接在创建时设置权限
        )
        db.add(admin_role)
        await db.flush()
        logger.info("[OK] 已创建管理员角色")

    # 4. 创建 admin 用户
    password_hash = hash_password(settings.ADMIN_DEFAULT_PASSWORD)
    admin_user = User(
        username=settings.ADMIN_DEFAULT_USERNAME,
        password_hash=password_hash,
        real_name="系统管理员",
        status=1,
        roles=[admin_role]  # 直接在创建时设置角色
    )
    db.add(admin_user)
    await db.flush()

    await db.commit()

    logger.info(f"[OK] 系统初始化完成，管理员账号已创建（用户名: {settings.ADMIN_DEFAULT_USERNAME}，密码: {settings.ADMIN_DEFAULT_PASSWORD}）")