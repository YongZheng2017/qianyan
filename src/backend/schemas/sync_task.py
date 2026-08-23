"""
同步任务相关 Schema

定义同步任务的请求和响应模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class SyncParamIn(BaseModel):
    """同步参数（输入）"""
    param_key: str = Field(..., max_length=50, description='参数名')
    param_value: Optional[str] = Field(None, max_length=200, description='参数值')


class SyncParamOut(BaseModel):
    """同步参数（输出）"""
    param_key: str
    param_value: Optional[str] = None


class SyncTaskCreate(BaseModel):
    """创建同步任务请求模型"""
    name: str = Field(..., min_length=2, max_length=50, description='任务名称')
    source_id: int = Field(..., description='数据源ID')
    data_interface: str = Field(..., max_length=50, description='数据接口名')
    sync_mode: str = Field('full', pattern='^(full|incremental)$', description='同步模式')
    target_table: str = Field(..., max_length=50, description='目标数据表')
    params: List[SyncParamIn] = Field(default_factory=list, description='同步参数')
    interval_ms: int = Field(500, ge=100, le=60000, description='调用间隔(毫秒)')
    timeout_seconds: int = Field(30, ge=5, le=300, description='超时时间(秒)')
    retry_count: int = Field(3, ge=0, le=5, description='重试次数')
    description: Optional[str] = Field(None, max_length=200, description='描述')
    status: int = Field(1, ge=0, le=1, description='状态:1启用 0禁用')


class SyncTaskUpdate(BaseModel):
    """更新同步任务请求模型"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description='任务名称')
    sync_mode: Optional[str] = Field(None, pattern='^(full|incremental)$', description='同步模式')
    target_table: Optional[str] = Field(None, max_length=50, description='目标数据表')
    params: Optional[List[SyncParamIn]] = Field(None, description='同步参数（为None不修改）')
    interval_ms: Optional[int] = Field(None, ge=100, le=60000, description='调用间隔(毫秒)')
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300, description='超时时间(秒)')
    retry_count: Optional[int] = Field(None, ge=0, le=5, description='重试次数')
    description: Optional[str] = Field(None, max_length=200, description='描述')
    status: Optional[int] = Field(None, ge=0, le=1, description='状态')


class SyncTaskResponse(BaseModel):
    """同步任务响应模型"""
    id: int
    name: str
    source_id: int
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    data_interface: str
    interface_name: str = ''
    sync_mode: str
    target_table: str
    params: List[SyncParamOut] = []
    interval_ms: int
    timeout_seconds: int
    retry_count: int
    description: Optional[str] = None
    status: int
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_sync_records: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True