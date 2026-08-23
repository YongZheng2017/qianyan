"""
用户管理服务

处理用户的增删改查业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from ..models import User, Role
from ..schemas.user import UserCreate, UserUpdate, ChangePassword
from ..utils.security import hash_password
from ..core.config import settings


class UserService:
    """用户管理服务类"""

    @staticmethod
    async def get_users_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[int] = None
    ) -> dict:
        """
        获取用户列表（分页、搜索、筛选）

        Args:
            db: 数据库会话
            page: 页码
            page_size: 每页数量
            search: 搜索关键词
            status: 状态筛选

        Returns:
            dict: 包含 list, page, page_size, total 的字典
        """
        # 构建查询条件
        query = select(User).options(selectinload(User.roles))

        if search:
            query = query.where(
                or_(
                    User.username.like(f"%{search}%"),
                    User.real_name.like(f"%{search}%")
                )
            )

        if status is not None:
            query = query.where(User.status == status)

        # 查询总数
        count_query = select(func.count()).select_from(query)
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页查询
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        users = result.scalars().all()

        # 转换为响应格式
        user_list = []
        for user in users:
            role_ids = [role.id for role in user.roles]
            user_list.append({
                "id": user.id,
                "username": user.username,
                "real_name": user.real_name,
                "email": user.email,
                "role_ids": role_ids,
                "status": user.status,
                "created_at": user.created_at,
                "last_login_at": user.last_login_at
            })

        return {
            "list": user_list,
            "page": page,
            "page_size": page_size,
            "total": total
        }

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        根据ID获取用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[User]: 用户对象
        """
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """
        根据用户名获取用户

        Args:
            db: 数据库会话
            username: 用户名

        Returns:
            Optional[User]: 用户对象
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """
        创建用户

        Args:
            db: 数据库会话
            user_data: 用户创建数据

        Returns:
            User: 创建的用户对象

        Raises:
            ValueError: 用户名已存在
        """
        # 检查用户名是否已存在
        existing_user = await UserService.get_user_by_username(db, user_data.username)
        if existing_user:
            raise ValueError("用户名已存在")

        # 查询角色
        roles = []
        for role_id in user_data.role_ids:
            result = await db.execute(select(Role).where(Role.id == role_id))
            role = result.scalar_one_or_none()
            if role:
                roles.append(role)

        if not roles:
            raise ValueError("至少需要选择一个有效角色")

        # 创建用户（直接设置角色）
        password_hash = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            password_hash=password_hash,
            real_name=user_data.real_name,
            email=user_data.email,
            status=user_data.status,
            roles=roles  # 直接在创建时设置角色
        )
        db.add(user)
        await db.commit()

        # 重新查询用户，预加载 roles 关系（避免异步懒加载问题）
        return await UserService.get_user_by_id(db, user.id)

    @staticmethod
    async def update_user(db: AsyncSession, user_id: int, user_data: UserUpdate) -> User:
        """
        更新用户

        Args:
            db: 数据库会话
            user_id: 用户ID
            user_data: 用户更新数据

        Returns:
            User: 更新后的用户对象

        Raises:
            ValueError: 用户不存在或admin账号角色为空
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("用户不存在")

        # admin账号至少需要保留一个角色
        if user.username == settings.ADMIN_DEFAULT_USERNAME and not user_data.role_ids:
            raise ValueError("管理员账号至少需要保留一个角色")

        # 查询角色
        roles = []
        for role_id in user_data.role_ids:
            result = await db.execute(select(Role).where(Role.id == role_id))
            role = result.scalar_one_or_none()
            if role:
                roles.append(role)

        if not roles:
            raise ValueError("至少需要选择一个有效角色")

        # 更新用户信息
        user.real_name = user_data.real_name
        user.email = user_data.email
        user.status = user_data.status
        user.roles = roles  # 直接设置角色

        await db.commit()

        # 重新查询用户，预加载 roles 关系（避免异步懒加载问题）
        return await UserService.get_user_by_id(db, user.id)

    @staticmethod
    async def change_password(db: AsyncSession, user_id: int, password_data: ChangePassword) -> None:
        """
        修改用户密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            password_data: 密码数据

        Raises:
            ValueError: 用户不存在
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("用户不存在")

        user.password_hash = hash_password(password_data.new_password)
        await db.commit()

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: int) -> None:
        """
        删除用户

        Args:
            db: 数据库会话
            user_id: 用户ID

        Raises:
            ValueError: 用户不存在或尝试删除admin账号
        """
        user = await UserService.get_user_by_id(db, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 不允许删除admin账号
        if user.username == settings.ADMIN_DEFAULT_USERNAME:
            raise ValueError("不能删除管理员账号")

        await db.delete(user)
        await db.commit()