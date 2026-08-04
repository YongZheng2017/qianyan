"""
用户模型

定义用户表结构
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin
from .rbac import user_roles


class User(Base, TimestampMixin):
    """用户模型"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    email = Column(String(100), comment='邮箱')
    real_name = Column(String(50), comment='真实姓名')
    status = Column(SmallInteger, default=1, comment='状态:1启用 0禁用')
    last_login_at = Column(DateTime, comment='最后登录时间')

    # 关系
    roles = relationship('Role', secondary=user_roles, back_populates='users')

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"