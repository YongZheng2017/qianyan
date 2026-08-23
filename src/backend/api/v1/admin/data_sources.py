"""
数据源管理 API
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.data_source import (
    DataSourceCreate, DataSourceUpdate, DataSourceResponse, DataSourceTestResult
)
from ....schemas.common import Response, PaginatedResponse, PaginatedData
from ....models import User
from ....services.data_source import DataSourceService
from ....services.adapters import DataSourceAdapterFactory
from ....api.deps import get_current_admin_user

router = APIRouter()


@router.get("/types", response_model=Response[list])
async def get_source_types():
    """获取支持的数据源类型"""
    types = DataSourceService.get_supported_types()
    return Response(data=types)


@router.get("/types/{source_type}/interfaces", response_model=Response[list])
async def get_interfaces_by_type(source_type: str):
    """获取指定数据源类型支持的接口列表"""
    try:
        adapter = DataSourceAdapterFactory.get_adapter(source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return Response(data=adapter.get_interfaces())


@router.get("/types/{source_type}/credentials-schema", response_model=Response[list])
async def get_credentials_schema(source_type: str):
    """获取指定数据源类型的凭证字段定义（前端据此动态渲染配置表单）"""
    try:
        adapter = DataSourceAdapterFactory.get_adapter(source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return Response(data=adapter.get_credentials_schema())


@router.get("/types/{source_type}/interfaces/{interface_name}/params", response_model=Response[list])
async def get_interface_params(source_type: str, interface_name: str):
    """获取指定接口的参数定义（前端用于动态生成参数表单）"""
    try:
        adapter = DataSourceAdapterFactory.get_adapter(source_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    params = adapter.get_interface_params(interface_name)
    if not params:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="接口不存在或无参数定义")

    return Response(data=params)


@router.get("", response_model=PaginatedResponse[DataSourceResponse])
async def get_data_sources(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status_filter: Optional[int] = Query(None, ge=0, le=1, alias="status", description="状态筛选"),
    source_type: Optional[str] = Query(None, description="类型筛选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取数据源列表（分页、搜索、筛选）"""
    result = await DataSourceService.get_list(
        db=db, page=page, page_size=page_size, search=search,
        status=status_filter, source_type=source_type,
    )
    return PaginatedResponse(
        data=PaginatedData(
            list=[DataSourceResponse(**item) for item in result["list"]],
            page=result["page"], page_size=result["page_size"], total=result["total"],
        )
    )


@router.post("", response_model=Response[DataSourceResponse])
async def create_data_source(
    data: DataSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """创建数据源"""
    try:
        result = await DataSourceService.create(db, data)
        return Response(message="创建成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{source_id}", response_model=Response[DataSourceResponse])
async def get_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """获取数据源详情"""
    ds = await DataSourceService.get_by_id(db, source_id)
    if not ds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="数据源不存在")
    return Response(data=DataSourceService._to_response(ds))


@router.put("/{source_id}", response_model=Response[DataSourceResponse])
async def update_data_source(
    source_id: int,
    data: DataSourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """更新数据源"""
    try:
        result = await DataSourceService.update(db, source_id, data)
        return Response(message="更新成功", data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{source_id}", response_model=Response)
async def delete_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """删除数据源（有关联同步任务时拒绝删除）"""
    try:
        await DataSourceService.delete(db, source_id)
        return Response(message="删除成功")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{source_id}/test", response_model=Response[DataSourceTestResult])
async def test_data_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """测试数据源连接"""
    try:
        result = await DataSourceService.test_connection(db, source_id)
        return Response(
            data=DataSourceTestResult(
                success=result["success"],
                message=result["message"],
                response_time_ms=result.get("response_time_ms"),
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
