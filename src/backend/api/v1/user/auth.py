"""
分析端认证 API
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.auth import LoginRequest, LoginResponse, Menu
from ....schemas.user import UserResponse
from ....schemas.common import Response
from ....models import User
from ....utils.security import create_access_token
from ....services.auth import authenticate_user, get_user_permissions, update_last_login
from ....core.config import settings

router = APIRouter()


@router.post("/login", response_model=Response[LoginResponse])
async def user_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    分析端登录

    Args:
        request: 登录请求
        db: 数据库会话

    Returns:
        Response[LoginResponse]: 登录响应，包含 token、用户信息和菜单
    """
    # 认证用户
    user = await authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 获取用户权限
    permissions = await get_user_permissions(db, user.id)

    # 根据记住我设置 token 有效期
    if request.remember_me:
        expire_hours = 7 * 24  # 7天
    else:
        expire_hours = settings.ACCESS_TOKEN_EXPIRE_MINUTES // 60

    # 生成 token
    token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "type": "user"},
        expires_delta=timedelta(hours=expire_hours)
    )

    # 更新最后登录时间
    await update_last_login(db, user.id)

    # 生成菜单（根据权限过滤）
    menus = generate_user_menus(permissions)

    # 构建响应
    user_response = UserResponse(
        id=user.id,
        username=user.username,
        real_name=user.real_name,
        email=user.email,
        role_ids=[role.id for role in user.roles],
        status=user.status,
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )

    return Response(
        data=LoginResponse(
            token=token,
            user=user_response,
            permissions=permissions,
            menus=menus
        )
    )


@router.post("/logout", response_model=Response)
async def user_logout():
    """
    分析端退出登录

    Returns:
        Response: 成功响应
    """
    # JWT 是无状态的，客户端删除 token 即可
    return Response(message="退出成功")


def generate_user_menus(permissions: list) -> list:
    """
    根据用户权限生成菜单

    Args:
        permissions: 用户权限列表

    Returns:
        list: 菜单列表
    """
    # 硬编码菜单配置
    MENU_CONFIG = [
        {
            "id": "stock_quote",
            "title": "关注的股票",
            "icon": "stock",
            "path": "/stock/quote",
            "permission": "stock:quote:read"
        },
        {
            "id": "fundamental",
            "title": "基本面分析",
            "icon": "chart",
            "path": "/analysis/fundamental",
            "permission": "analysis:fundamental:read"
        },
        {
            "id": "trend",
            "title": "趋势分析",
            "icon": "trend",
            "path": "/analysis/trend",
            "permission": "analysis:trend:read"
        },
        {
            "id": "fund_flow",
            "title": "资金趋势",
            "icon": "fund",
            "path": "/analysis/fund-flow",
            "permission": "analysis:fund:read"
        }
    ]

    # 根据权限过滤菜单
    menus = []
    for menu in MENU_CONFIG:
        if menu["permission"] in permissions:
            menus.append(Menu(
                id=menu["id"],
                title=menu["title"],
                icon=menu["icon"],
                path=menu["path"]
            ))

    return menus