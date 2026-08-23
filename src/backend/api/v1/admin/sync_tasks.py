"""
同步任务管理 API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.sync_task import SyncTaskCreate, SyncTaskUpdate, SyncTaskResponse
from ....schemas.common import Response, PaginatedResponse, PaginatedData
from ....models import User
from ....services.sync_task import SyncTaskService
from ....api.deps import get_current_admin_user

router = APIRouter()


@router.get("", response_model=PaginatedResponse[SyncTaskResponse])
async def get_sync_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    source_id: Optional[int] = Query(None, description="数据源ID筛选"),
    status_filter: Optional[int] = Query(None, ge=0, le=1, alias="status", description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取同步任务列表（分页、搜索、按数据源筛选）"""
    result = await SyncTaskService.get_list(
        db=db, page=page, page_size=page_size, search=search,
        source_id=source_id, status=status_filter,
    )
    return PaginatedResponse(
        data=PaginatedData(
            list=[SyncTaskResponse(**item) for item in result["list"]],
            page=result["page"], page_size=result["page_size"], total=result["total"],
        )
    )


@router.post("", response_model=Response[SyncTaskResponse])
async def create_sync_task(
    data: SyncTaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """创建同步任务"""
    try:
        result = await SyncTaskService.create(db, data)
        return Response(message="创建成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{task_id}", response_model=Response[SyncTaskResponse])
async def get_sync_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取同步任务详情"""
    task = await SyncTaskService.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="同步任务不存在")
    return Response(data=SyncTaskService._to_response(task))


@router.put("/{task_id}", response_model=Response[SyncTaskResponse])
async def update_sync_task(
    task_id: int,
    data: SyncTaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """更新同步任务"""
    try:
        result = await SyncTaskService.update(db, task_id, data)
        return Response(message="更新成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}", response_model=Response)
async def delete_sync_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """删除同步任务（级联删除参数）"""
    try:
        await SyncTaskService.delete(db, task_id)
        return Response(message="删除成功")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))