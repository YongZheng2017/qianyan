"""
RBAC（基于角色的访问控制）模型

定义角色、权限及其关联关系
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Table, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base


# 角色权限关联表（多对多）
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint('role_id', 'permission_id', name='uk_role_permission')
)

# 用户角色关联表（多对多）
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint('user_id', 'role_id', name='uk_user_role')
)


class Role(Base):
    """角色模型"""
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False, comment='角色名称')
    role_desc = Column(String(200), comment='角色描述')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, comment='创建时间')

    # 关系
    users = relationship('User', secondary=user_roles, back_populates='roles')
    permissions = relationship('Permission', secondary=role_permissions, back_populates='roles')

    def __repr__(self):
        return f"<Role(id={self.id}, role_name='{self.role_name}')>"


class Permission(Base):
    """权限模型"""
    __tablename__ = 'permissions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    permission_name = Column(String(100), unique=True, nullable=False, comment='权限名称')
    permission_desc = Column(String(200), comment='权限描述')
    resource = Column(String(100), comment='资源路径')
    action = Column(String(20), comment='操作:read,write,delete')

    # 关系
    roles = relationship('Role', secondary=role_permissions, back_populates='permissions')

    def __repr__(self):
        return f"<Permission(id={self.id}, permission_name='{self.permission_name}')>"