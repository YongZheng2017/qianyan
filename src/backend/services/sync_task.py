"""
同步任务管理服务

处理同步任务的增删改查及参数管理业务逻辑
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from ..models import SyncTask, SyncParam, DataSource
from ..schemas.sync_task import (
    SyncTaskCreate, SyncTaskUpdate, SyncTaskResponse, SyncParamOut
)
from .adapters import DataSourceAdapterFactory


class SyncTaskService:
    """同步任务管理服务类"""

    @staticmethod
    def _get_interface_name(source_type: str, interface: str) -> str:
        """获取接口中文名"""
        try:
            adapter = DataSourceAdapterFactory.get_adapter(source_type)
            for item in adapter.get_interfaces():
                if item["value"] == interface:
                    return item["label"]
        except ValueError:
            pass
        return interface

    @staticmethod
    def _to_response(task: SyncTask, source: Optional[DataSource] = None) -> SyncTaskResponse:
        """将 ORM 对象转为响应模型"""
        source = source or task.source
        source_type = source.source_type if source else None
        source_name = source.name if source else None
        return SyncTaskResponse(
            id=task.id,
            name=task.name,
            source_id=task.source_id,
            source_name=source_name,
            source_type=source_type,
            data_interface=task.data_interface,
            interface_name=SyncTaskService._get_interface_name(source_type, task.data_interface) if source_type else task.data_interface,
            sync_mode=task.sync_mode,
            target_table=task.target_table,
            params=[SyncParamOut(param_key=p.param_key, param_value=p.param_value) for p in task.params],
            interval_ms=task.interval_ms,
            timeout_seconds=task.timeout_seconds,
            retry_count=task.retry_count,
            description=task.description,
            status=task.status,
            last_sync_at=task.last_sync_at,
            last_sync_status=task.last_sync_status,
            last_sync_records=task.last_sync_records,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        source_id: Optional[int] = None,
        status: Optional[int] = None,
    ) -> dict:
        """获取同步任务列表（分页、搜索、筛选）"""
        query = select(SyncTask).options(selectinload(SyncTask.params))

        if search:
            query = query.where(
                or_(SyncTask.name.like(f"%{search}%"), SyncTask.data_interface.like(f"%{search}%"))
            )
        if source_id is not None:
            query = query.where(SyncTask.source_id == source_id)
        if status is not None:
            query = query.where(SyncTask.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(SyncTask.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "list": [SyncTaskService._to_response(t).model_dump() for t in items],
            "page": page, "page_size": page_size, "total": total,
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, task_id: int) -> Optional[SyncTask]:
        """根据 ID 获取任务（预加载参数）"""
        result = await db.execute(
            select(SyncTask)
            .options(selectinload(SyncTask.params))
            .where(SyncTask.id == task_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _validate_source_and_interface(db: AsyncSession, source_id: int, data_interface: str) -> DataSource:
        """
        校验数据源存在、启用，且支持该接口

        Raises:
            ValueError: 数据源不存在/禁用/不支持该接口
        """
        result = await db.execute(select(DataSource).where(DataSource.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise ValueError("数据源不存在")

        adapter = DataSourceAdapterFactory.get_adapter(source.source_type)
        valid_interfaces = {item["value"] for item in adapter.get_interfaces()}
        if data_interface not in valid_interfaces:
            raise ValueError(f"数据源类型 {source.source_type} 不支持接口：{data_interface}")

        return source

    @staticmethod
    async def create(db: AsyncSession, data: SyncTaskCreate) -> SyncTaskResponse:
        """
        创建同步任务

        Raises:
            ValueError: 数据源不存在或接口不支持
        """
        await SyncTaskService._validate_source_and_interface(db, data.source_id, data.data_interface)

        task = SyncTask(
            name=data.name,
            source_id=data.source_id,
            data_interface=data.data_interface,
            sync_mode=data.sync_mode,
            target_table=data.target_table,
            interval_ms=data.interval_ms,
            timeout_seconds=data.timeout_seconds,
            retry_count=data.retry_count,
            description=data.description,
            status=data.status,
            params=[
                SyncParam(param_key=p.param_key, param_value=p.param_value)
                for p in data.params
            ],
        )
        db.add(task)
        await db.commit()

        # 重新查询（预加载 params + source）
        task = await SyncTaskService.get_by_id(db, task.id)
        return SyncTaskService._to_response(task)

    @staticmethod
    async def update(db: AsyncSession, task_id: int, data: SyncTaskUpdate) -> SyncTaskResponse:
        """
        更新同步任务

        Raises:
            ValueError: 任务不存在
        """
        task = await SyncTaskService.get_by_id(db, task_id)
        if not task:
            raise ValueError("同步任务不存在")

        if data.name is not None:
            task.name = data.name
        if data.sync_mode is not None:
            task.sync_mode = data.sync_mode
        if data.target_table is not None:
            task.target_table = data.target_table
        if data.interval_ms is not None:
            task.interval_ms = data.interval_ms
        if data.timeout_seconds is not None:
            task.timeout_seconds = data.timeout_seconds
        if data.retry_count is not None:
            task.retry_count = data.retry_count
        if data.description is not None:
            task.description = data.description
        if data.status is not None:
            task.status = data.status

        # 参数为 None 不修改；为列表则全量替换
        if data.params is not None:
            task.params.clear()
            for p in data.params:
                task.params.append(SyncParam(param_key=p.param_key, param_value=p.param_value))

        await db.commit()
        task = await SyncTaskService.get_by_id(db, task_id)
        return SyncTaskService._to_response(task)

    @staticmethod
    async def delete(db: AsyncSession, task_id: int) -> None:
        """删除同步任务（级联删除参数）"""
        task = await SyncTaskService.get_by_id(db, task_id)
        if not task:
            raise ValueError("同步任务不存在")
        await db.delete(task)
        await db.commit()

    @staticmethod
    async def count_by_source(db: AsyncSession, source_id: int) -> int:
        """统计数据源下的任务数（供数据源删除时校验）"""
        result = await db.execute(
            select(func.count()).select_from(
                select(SyncTask.id).where(SyncTask.source_id == source_id).subquery()
            )
        )
        return result.scalar() or 0