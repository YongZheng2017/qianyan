"""
用户菜单 API
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.auth import Menu
from ....schemas.common import Response
from ....models import User
from ....api.deps import get_current_user
from ....services.auth import get_user_permissions

router = APIRouter()


@router.get("", response_model=Response[List[Menu]])
async def get_user_menus(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户菜单

    Args:
        current_user: 当前用户
        db: 数据库会话

    Returns:
        Response[List[Menu]]: 用户菜单列表
    """
    # 获取用户权限
    permissions = await get_user_permissions(db, current_user.id)

    # 生成菜单
    menus = generate_user_menus(permissions)

    return Response(data=menus)


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
            "id": "market",
            "title": "行情",
            "icon": "trend",
            "path": "/market",
            "permission": "stock:quote:read"
        },
        {
            "id": "fundamental",
            "title": "基本面分析",
            "icon": "chart",
            "path": "/fundamental",
            "permission": "analysis:fundamental:read"
        },
        {
            "id": "fund_flow",
            "title": "资金趋势分析",
            "icon": "fund",
            "path": "/fund-flow",
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