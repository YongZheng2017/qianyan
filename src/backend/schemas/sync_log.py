"""
同步日志相关 Schema
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SyncCallLogResponse(BaseModel):
    """接口调用明细响应"""
    id: int
    call_seq: int
    request_params: Optional[Dict[str, Any]] = None
    request_at: datetime
    response_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str
    record_count: int = 0
    retry_count: int = 0
    error_message: Optional[str] = None


class SyncLogResponse(BaseModel):
    """同步执行记录响应"""
    id: int
    execution_id: str
    task_id: int
    task_name: Optional[str] = None
    source_name: Optional[str] = None
    trigger_type: str
    trigger_user_id: Optional[int] = None
    status: str
    total_records: int = 0
    api_calls: int = 0
    start_at: datetime
    end_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    params_snapshot: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class SyncLogDetail(SyncLogResponse):
    """同步执行详情（含调用明细）"""
    call_logs: List[SyncCallLogResponse] = []


class SyncProgress(BaseModel):
    """实时执行进度"""
    execution_id: str
    status: str
    total_records: int = 0
    api_calls: int = 0
    elapsed_seconds: Optional[int] = None
    last_call_at: Optional[datetime] = None


class SyncStats(BaseModel):
    """同步统计"""
    today_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0
    avg_duration: float = 0.0
    total_records: int = 0


class ManualSyncRequest(BaseModel):
    """手动触发同步请求"""
    params: Optional[Dict[str, Any]] = Field(None, description='临时覆盖参数（不影响任务配置）')


class ManualSyncResponse(BaseModel):
    """手动触发同步响应"""
    execution_id: str
    status: str = 'running'