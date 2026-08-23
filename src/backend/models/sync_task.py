"""
同步任务模型

定义同步任务配置表和任务参数表结构
"""
from sqlalchemy import (
    Column, Integer, String, SmallInteger, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class SyncTask(Base, TimestampMixin):
    """同步任务配置模型"""
    __tablename__ = 'sync_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment='任务名称')
    source_id = Column(
        Integer,
        ForeignKey('data_sources.id', ondelete='RESTRICT'),
        nullable=False, comment='关联数据源ID'
    )
    data_interface = Column(String(50), nullable=False, comment='数据接口名(stock_basic,daily等)')
    sync_mode = Column(String(20), default='full', comment='同步模式:full全量 incremental增量')
    target_table = Column(String(50), nullable=False, comment='目标数据表')
    interval_ms = Column(Integer, default=500, comment='调用间隔(毫秒)')
    timeout_seconds = Column(Integer, default=30, comment='超时时间(秒)')
    retry_count = Column(Integer, default=3, comment='重试次数')
    description = Column(String(200), comment='描述')
    status = Column(SmallInteger, default=1, comment='状态:1启用 0禁用')
    last_sync_at = Column(DateTime, comment='最后同步时间')
    last_sync_status = Column(String(20), comment='最后同步状态:success/failed/running')
    last_sync_records = Column(Integer, comment='最后同步记录数')

    # 关系：一对多 SyncParam
    params = relationship(
        'SyncParam',
        cascade='all, delete-orphan',
        back_populates='task',
        lazy='selectin',  # 默认预加载参数，避免异步懒加载
    )
    # 多对一 DataSource（不定义 back_populates，仅做查询用）
    source = relationship('DataSource', lazy='joined')

    def __repr__(self):
        return f"<SyncTask(id={self.id}, name='{self.name}', interface='{self.data_interface}')>"


class SyncParam(Base):
    """同步任务参数模型"""
    __tablename__ = 'sync_params'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(
        Integer,
        ForeignKey('sync_tasks.id', ondelete='CASCADE'),
        nullable=False, comment='关联任务ID'
    )
    param_key = Column(String(50), nullable=False, comment='参数名')
    param_value = Column(String(200), comment='参数值')

    # 关系
    task = relationship('SyncTask', back_populates='params')

    __table_args__ = (
        UniqueConstraint('task_id', 'param_key', name='uk_task_param'),
    )

    def __repr__(self):
        return f"<SyncParam(task_id={self.task_id}, key='{self.param_key}', value='{self.param_value}')>"