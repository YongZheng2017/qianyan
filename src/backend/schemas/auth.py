"""
认证相关 Schema

定义登录请求和响应模型
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from .user import UserResponse


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description='用户名')
    password: str = Field(..., description='密码')
    remember_me: bool = Field(False, description='记住我')


class Menu(BaseModel):
    """菜单项模型"""
    id: str
    title: str
    icon: str
    path: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    token: str = Field(..., description='JWT令牌')
    user: UserResponse = Field(..., description='用户信息')
    permissions: List[str] = Field(default_factory=list, description='权限列表')
    menus: Optional[List[Menu]] = Field(None, description='菜单列表（分析端登录时返回）')


class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    real_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True