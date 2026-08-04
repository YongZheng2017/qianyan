"""
用户相关 Schema

定义用户相关的请求和响应模型
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=4, max_length=20, pattern='^[a-zA-Z0-9_]+$', description='用户名')
    real_name: Optional[str] = Field(None, max_length=50, description='真实姓名')
    email: Optional[str] = Field(None, max_length=100, description='邮箱')

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """验证邮箱格式，允许为空"""
        if v is None or v == '':
            return None
        # 简单的邮箱格式验证
        if '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


class UserCreate(UserBase):
    """创建用户请求模型"""
    password: str = Field(..., min_length=6, max_length=20, description='密码')
    confirm_password: str = Field(..., description='确认密码')
    role_ids: List[int] = Field(default=[2], min_length=1, description='角色ID列表，默认为普通用户角色')
    status: int = Field(1, ge=0, le=1, description='状态:1启用 0禁用')

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """验证两次密码是否一致"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    real_name: Optional[str] = Field(None, max_length=50, description='真实姓名')
    email: Optional[str] = Field(None, max_length=100, description='邮箱')
    role_ids: List[int] = Field(..., min_length=1, description='角色ID列表')
    status: int = Field(..., ge=0, le=1, description='状态:1启用 0禁用')

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """验证邮箱格式，允许为空"""
        if v is None or v == '':
            return None
        # 简单的邮箱格式验证
        if '@' not in v:
            raise ValueError('邮箱格式不正确')
        return v


class ChangePassword(BaseModel):
    """修改密码请求模型"""
    new_password: str = Field(..., min_length=6, max_length=20, description='新密码')
    confirm_password: str = Field(..., description='确认密码')

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info):
        """验证两次密码是否一致"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    role_ids: List[int] = []
    status: int
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True