"""管理端 API 模块"""
from fastapi import APIRouter
from . import auth, users

router = APIRouter(prefix="/admin", tags=["管理端"])

router.include_router(auth.router, prefix="/auth", tags=["管理端认证"])
router.include_router(users.router, prefix="/users", tags=["用户管理"])

__all__ = ["router"]