"""
同步日志与调度模型

- sync_logs：同步执行汇总记录
- sync_call_logs：单次接口调用明细记录
- sync_schedules：同步任务调度配置
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, SmallInteger, DateTime, Time, Text,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from .base import Base


class SyncLog(Base):
    """同步执行记录表（汇总）"""
    __tablename__ = 'sync_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(String(50), unique=True, nullable=False, comment='执行ID')
    task_id = Column(Integer, ForeignKey('sync_tasks.id', ondelete='CASCADE'), nullable=False, comment='关联任务ID')
    task_name = Column(String(50), comment='任务名称(冗余)')
    source_name = Column(String(50), comment='数据源名称(冗余)')
    trigger_type = Column(String(20), nullable=False, comment='触发方式:manual,schedule')
    trigger_user_id = Column(Integer, nullable=True, comment='手动触发的用户ID')
    status = Column(String(20), default='running', comment='状态:running,success,failed,timeout')
    total_records = Column(Integer, default=0, comment='总记录数')
    api_calls = Column(Integer, default=0, comment='API调用次数')
    start_at = Column(DateTime, nullable=False, comment='开始时间')
    end_at = Column(DateTime, comment='结束时间')
    duration_seconds = Column(Integer, comment='耗时(秒)')
    params_snapshot = Column(Text, comment='本次执行参数快照(JSON)')
    error_message = Column(Text, comment='错误信息')

    # 关系：调用明细
    call_logs = relationship('SyncCallLog', back_populates='sync_log', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_sync_log_task_time', 'task_id', 'start_at'),
        Index('idx_sync_log_status', 'status'),
    )

    def __repr__(self):
        return f"<SyncLog(execution_id='{self.execution_id}', status='{self.status}')>"


class SyncCallLog(Base):
    """同步接口调用记录表（明细）"""
    __tablename__ = 'sync_call_logs'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    execution_id = Column(
        String(50),
        ForeignKey('sync_logs.execution_id', ondelete='CASCADE'),
        nullable=False, comment='关联执行ID'
    )
    call_seq = Column(Integer, nullable=False, comment='调用序号')
    request_params = Column(Text, comment='请求参数(JSON)')
    request_at = Column(DateTime, nullable=False, comment='请求时间')
    response_at = Column(DateTime, comment='响应时间')
    duration_ms = Column(Integer, comment='耗时(毫秒)')
    status = Column(String(20), nullable=False, comment='状态:success,failed,timeout')
    record_count = Column(Integer, default=0, comment='返回记录数')
    retry_count = Column(Integer, default=0, comment='重试次数')
    error_message = Column(Text, comment='错误信息')

    sync_log = relationship('SyncLog', back_populates='call_logs')

    __table_args__ = (
        Index('idx_sync_call_execution', 'execution_id'),
    )

    def __repr__(self):
        return f"<SyncCallLog(execution_id='{self.execution_id}', seq={self.call_seq}, status='{self.status}')>"


class SyncSchedule(Base):
    """同步调度配置表（与任务一对一）"""
    __tablename__ = 'sync_schedules'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey('sync_tasks.id', ondelete='CASCADE'), unique=True, nullable=False, comment='关联任务ID')
    schedule_type = Column(String(20), nullable=False, comment='调度类型:daily,weekly,cron')
    execute_time = Column(Time, comment='执行时间(HH:MM:SS)')
    weekdays = Column(String(20), comment='星期(逗号分隔:1,2,3,4,5)')
    cron_expr = Column(String(100), comment='Cron表达式')
    enabled = Column(SmallInteger, default=0, comment='是否启用:1启用 0停用')
    next_run_at = Column(DateTime, comment='下次执行时间')
    last_run_at = Column(DateTime, comment='上次执行时间')

    task = relationship('SyncTask')

    def __repr__(self):
        return f"<SyncSchedule(task_id={self.task_id}, type='{self.schedule_type}', enabled={self.enabled})>"