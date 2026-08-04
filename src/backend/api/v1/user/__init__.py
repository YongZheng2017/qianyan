"""分析端 API 模块"""
from fastapi import APIRouter
from . import auth, menus

router = APIRouter(prefix="/user", tags=["分析端"])

router.include_router(auth.router, prefix="/auth", tags=["分析端认证"])
router.include_router(menus.router, prefix="/menus", tags=["菜单"])

__all__ = ["router"]