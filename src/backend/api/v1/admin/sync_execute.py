"""
同步执行与调度 API

包含：
- 手动触发同步 POST /sync-tasks/{task_id}/execute
- 调度配置 POST/GET /sync-tasks/{task_id}/schedule
- 调度启停 PUT /sync-tasks/{task_id}/schedule/toggle
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.sync_log import ManualSyncRequest, ManualSyncResponse
from ....schemas.sync_schedule import ScheduleCreate, ScheduleResponse, ScheduleToggleResult
from ....schemas.common import Response
from ....models import User
from ....services.sync_executor import SyncExecutor
from ....services.sync_scheduler import SyncSchedulerService
from ....api.deps import get_current_admin_user

router = APIRouter()


@router.post("/{task_id}/execute", response_model=Response[ManualSyncResponse])
async def execute_sync_task(
    task_id: int,
    payload: ManualSyncRequest = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """手动触发同步（立即执行，异步后台运行）"""
    try:
        override = payload.params if payload else None
        execution_id = await SyncExecutor.trigger(
            task_id=task_id,
            trigger_type="manual",
            override_params=override,
            user_id=current_user.id,
        )
        return Response(
            message="同步任务已触发",
            data=ManualSyncResponse(execution_id=execution_id, status="running"),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{task_id}/schedule", response_model=Response[ScheduleResponse])
async def set_schedule(
    task_id: int,
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """设置或更新任务的调度配置"""
    try:
        result = await SyncSchedulerService.upsert(db, task_id, data)
        return Response(message="调度配置已保存", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{task_id}/schedule/toggle", response_model=Response[ScheduleToggleResult])
async def toggle_schedule(
    task_id: int,
    enabled: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """启用/停用调度"""
    try:
        result = await SyncSchedulerService.toggle(db, task_id, enabled)
        return Response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{task_id}/schedule", response_model=Response[ScheduleResponse])
async def get_schedule(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取任务的调度配置"""
    result = await SyncSchedulerService.get_by_task(db, task_id)
    if not result:
        return Response(data=None)
    schedule, task_name = result
    return Response(data=SyncSchedulerService._to_response(schedule, task_name))