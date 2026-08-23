"""
同步调度相关 Schema
"""
from typing import Optional
from datetime import datetime, time
from pydantic import BaseModel, Field


class ScheduleCreate(BaseModel):
    """调度配置请求"""
    schedule_type: str = Field(..., pattern='^(daily|weekly|cron)$', description='调度类型')
    execute_time: Optional[str] = Field(None, pattern='^([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?$',
                                        description='执行时间 HH:MM 或 HH:MM:SS')
    weekdays: Optional[str] = Field(None, description='星期(逗号分隔:0-6, 0=周一)')
    cron_expr: Optional[str] = Field(None, max_length=100, description='Cron表达式')
    enabled: int = Field(0, ge=0, le=1, description='是否启用')


class ScheduleResponse(BaseModel):
    """调度配置响应"""
    id: int
    task_id: int
    task_name: Optional[str] = None
    schedule_type: str
    execute_time: Optional[str] = None
    weekdays: Optional[str] = None
    cron_expr: Optional[str] = None
    enabled: int
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None


class ScheduleToggleResult(BaseModel):
    """调度启停结果"""
    enabled: int
    next_run_at: Optional[datetime] = None