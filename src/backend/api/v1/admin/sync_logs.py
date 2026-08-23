"""
同步日志查询 API

包含：
- 日志列表 GET /sync-logs
- 统计 GET /sync-logs/stats
- 详情 GET /sync-logs/{execution_id}
- 进度 GET /sync-logs/{execution_id}/progress
- 清理 DELETE /sync-logs
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.sync_log import (
    SyncLogResponse, SyncLogDetail, SyncProgress, SyncStats
)
from ....schemas.common import Response, PaginatedResponse, PaginatedData
from ....models import User
from ....services.sync_log import SyncLogService
from ....api.deps import get_current_admin_user

router = APIRouter()


@router.get("/stats", response_model=Response[SyncStats])
async def get_sync_stats(
    date: Optional[str] = Query(None, description="统计日期 YYYY-MM-DD，默认今天"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取同步统计"""
    stats = await SyncLogService.get_stats(db, date)
    return Response(data=stats)


@router.get("", response_model=PaginatedResponse[SyncLogResponse])
async def get_sync_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    task_id: Optional[int] = Query(None, description="按任务筛选"),
    status: Optional[str] = Query(None, description="按状态筛选:running/success/failed/timeout"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取同步日志列表（分页、筛选）"""
    result = await SyncLogService.get_list(
        db=db, page=page, page_size=page_size, task_id=task_id,
        status_filter=status, start_date=start_date, end_date=end_date,
    )
    return PaginatedResponse(
        data=PaginatedData(
            list=[SyncLogResponse(**item) for item in result["list"]],
            page=result["page"], page_size=result["page_size"], total=result["total"],
        )
    )


@router.get("/{execution_id}", response_model=Response[SyncLogDetail])
async def get_sync_log_detail(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取同步执行详情（含接口调用明细）"""
    detail = await SyncLogService.get_detail(db, execution_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在")
    return Response(data=detail)


@router.get("/{execution_id}/progress", response_model=Response[SyncProgress])
async def get_sync_progress(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取实时执行进度"""
    progress = await SyncLogService.get_progress(db, execution_id)
    if not progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="执行记录不存在")
    return Response(data=progress)


@router.delete("", response_model=Response)
async def clean_sync_logs(
    before_date: str = Query(..., description="清理此日期之前的日志 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """清理历史日志"""
    try:
        count = await SyncLogService.clean_before(db, before_date)
        return Response(message="清理完成", data={"deleted_count": count})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{execution_id}", response_model=Response)
async def delete_sync_log(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """删除单条执行日志（含调用明细）"""
    try:
        await SyncLogService.delete_by_execution_id(db, execution_id)
        return Response(message="删除成功")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))