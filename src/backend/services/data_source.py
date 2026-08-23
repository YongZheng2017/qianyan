"""
数据源管理服务

处理数据源的增删改查及连接测试业务逻辑
"""
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from ..models import DataSource
from ..schemas.data_source import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from ..utils.crypto import encrypt_json, decrypt_json, decrypt_token, mask_credentials
from .adapters import DataSourceAdapterFactory


class DataSourceService:
    """数据源管理服务类"""

    @staticmethod
    def _get_plain_credentials(ds: DataSource) -> dict:
        """解密凭证 dict（兼容旧 token_encrypted 字段，用于读取历史数据）"""
        if ds.credentials_encrypted:
            return decrypt_json(ds.credentials_encrypted)
        # 兼容旧数据：把单个 token 包装为 {"token": ...}
        if ds.token_encrypted:
            token = decrypt_token(ds.token_encrypted)
            return {"token": token} if token else {}
        return {}

    @staticmethod
    def _to_response(ds: DataSource) -> DataSourceResponse:
        """将 ORM 对象转为响应模型（凭证脱敏）"""
        creds = DataSourceService._get_plain_credentials(ds)
        return DataSourceResponse(
            id=ds.id,
            name=ds.name,
            source_type=ds.source_type,
            api_url=ds.api_url,
            credentials_masked=mask_credentials(creds),
            has_credentials=bool(creds),
            description=ds.description,
            status=ds.status,
            last_test_at=ds.last_test_at,
            last_test_result=ds.last_test_result,
            last_test_message=ds.last_test_message,
            created_at=ds.created_at,
            updated_at=ds.updated_at,
        )

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        status: Optional[int] = None,
        source_type: Optional[str] = None,
    ) -> dict:
        """获取数据源列表（分页、搜索、筛选）"""
        query = select(DataSource)

        if search:
            query = query.where(
                or_(DataSource.name.like(f"%{search}%"), DataSource.description.like(f"%{search}%"))
            )
        if status is not None:
            query = query.where(DataSource.status == status)
        if source_type:
            query = query.where(DataSource.source_type == source_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(DataSource.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "list": [DataSourceService._to_response(ds).model_dump() for ds in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_by_id(db: AsyncSession, source_id: int) -> Optional[DataSource]:
        """根据 ID 获取数据源"""
        result = await db.execute(select(DataSource).where(DataSource.id == source_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_name(db: AsyncSession, name: str) -> Optional[DataSource]:
        """根据名称获取数据源"""
        result = await db.execute(select(DataSource).where(DataSource.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_enabled(db: AsyncSession) -> List[DataSource]:
        """获取所有启用的数据源"""
        result = await db.execute(select(DataSource).where(DataSource.status == 1))
        return list(result.scalars().all())

    @staticmethod
    async def create(db: AsyncSession, data: DataSourceCreate) -> DataSourceResponse:
        """创建数据源（凭证加密存储）"""
        if await DataSourceService.get_by_name(db, data.name):
            raise ValueError("数据源名称已存在")

        ds = DataSource(
            name=data.name,
            source_type=data.source_type,
            api_url=data.api_url,
            credentials_encrypted=encrypt_json(data.credentials) if data.credentials else None,
            description=data.description,
            status=data.status,
        )
        db.add(ds)
        await db.commit()
        await db.refresh(ds)
        return DataSourceService._to_response(ds)

    @staticmethod
    async def update(db: AsyncSession, source_id: int, data: DataSourceUpdate) -> DataSourceResponse:
        """更新数据源"""
        ds = await DataSourceService.get_by_id(db, source_id)
        if not ds:
            raise ValueError("数据源不存在")

        if data.name is not None and data.name != ds.name:
            if await DataSourceService.get_by_name(db, data.name):
                raise ValueError("数据源名称已存在")
            ds.name = data.name

        if data.source_type is not None:
            ds.source_type = data.source_type
        if data.api_url is not None:
            ds.api_url = data.api_url
        if data.description is not None:
            ds.description = data.description
        if data.status is not None:
            ds.status = data.status
        # credentials：None 不修改；空 dict 清空；非空 dict 加密覆盖
        if data.credentials is not None:
            ds.credentials_encrypted = encrypt_json(data.credentials) if data.credentials else None

        await db.commit()
        await db.refresh(ds)
        return DataSourceService._to_response(ds)

    @staticmethod
    async def delete(db: AsyncSession, source_id: int) -> None:
        """删除数据源（有关联同步任务时拒绝）"""
        ds = await DataSourceService.get_by_id(db, source_id)
        if not ds:
            raise ValueError("数据源不存在")

        from .sync_task import SyncTaskService
        count = await SyncTaskService.count_by_source(db, source_id)
        if count > 0:
            raise ValueError(f"该数据源存在 {count} 个关联的同步任务，无法删除")

        await db.delete(ds)
        await db.commit()

    @staticmethod
    async def test_connection(db: AsyncSession, source_id: int) -> dict:
        """测试数据源连接"""
        ds = await DataSourceService.get_by_id(db, source_id)
        if not ds:
            raise ValueError("数据源不存在")

        creds = DataSourceService._get_plain_credentials(ds)
        adapter = DataSourceAdapterFactory.get_adapter(ds.source_type)
        result = await adapter.test_connection(ds.api_url, creds, timeout=30)

        ds.last_test_at = datetime.now(timezone.utc)
        ds.last_test_result = 1 if result["success"] else 0
        ds.last_test_message = result["message"]
        await db.commit()

        return result

    @staticmethod
    def get_supported_types() -> list:
        """获取支持的数据源类型"""
        return DataSourceAdapterFactory.get_supported_types()