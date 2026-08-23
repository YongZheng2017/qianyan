"""管理端 API 模块"""
from fastapi import APIRouter
from . import auth, users, data_sources, sync_tasks, sync_execute, sync_logs

router = APIRouter(prefix="/admin", tags=["管理端"])

router.include_router(auth.router, prefix="/auth", tags=["管理端认证"])
router.include_router(users.router, prefix="/users", tags=["用户管理"])
router.include_router(data_sources.router, prefix="/data-sources", tags=["数据源管理"])
router.include_router(sync_tasks.router, prefix="/sync-tasks", tags=["同步任务管理"])
router.include_router(sync_execute.router, prefix="/sync-tasks", tags=["同步执行与调度"])
router.include_router(sync_logs.router, prefix="/sync-logs", tags=["同步日志"])

__all__ = ["router"]