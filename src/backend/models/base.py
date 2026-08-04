"""
基础模型类

提供通用的模型功能，如时间戳
"""
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

# 创建基类
Base = declarative_base()


class TimestampMixin:
    """时间戳混入类，为模型添加 created_at 和 updated_at 字段"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, comment='创建时间')

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False, comment='更新时间')