"""
通用响应模型

定义统一的 API 响应格式
"""
from typing import Generic, TypeVar, Optional, List
from pydantic import BaseModel

T = TypeVar('T')


class Response(BaseModel, Generic[T]):
    """统一响应格式"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PaginatedData(BaseModel, Generic[T]):
    """分页数据"""
    list: List[T]
    page: int
    page_size: int
    total: int


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = 0
    message: str = "success"
    data: PaginatedData[T]