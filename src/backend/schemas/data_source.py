"""
数据源相关 Schema

定义数据源的请求和响应模型
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DataSourceBase(BaseModel):
    """数据源基础模型"""
    name: str = Field(..., min_length=2, max_length=50, description='数据源名称')
    source_type: str = Field(..., pattern='^(tushare|akshare|ths|custom)$', description='类型:tushare,akshare,ths,custom')
    api_url: str = Field(..., max_length=255, description='API地址')
    # 凭证（按数据源类型区分字段，如 Tushare 的 {"token": "xxx"}，明文仅写入时使用）
    credentials: Optional[Dict[str, Any]] = Field(None, description='凭证（明文，仅写入时使用）')
    description: Optional[str] = Field(None, max_length=200, description='描述')
    status: int = Field(1, ge=0, le=1, description='状态:1启用 0禁用')


class DataSourceCreate(DataSourceBase):
    """创建数据源请求模型"""
    pass


class DataSourceUpdate(BaseModel):
    """更新数据源请求模型"""
    name: Optional[str] = Field(None, min_length=2, max_length=50, description='数据源名称')
    source_type: Optional[str] = Field(None, pattern='^(tushare|akshare|ths|custom)$', description='类型')
    api_url: Optional[str] = Field(None, max_length=255, description='API地址')
    credentials: Optional[Dict[str, Any]] = Field(None, description='凭证（None不修改，空dict清空）')
    description: Optional[str] = Field(None, max_length=200, description='描述')
    status: Optional[int] = Field(None, ge=0, le=1, description='状态')


class DataSourceResponse(BaseModel):
    """数据源响应模型"""
    id: int
    name: str
    source_type: str
    api_url: str
    # 凭证脱敏（每个字段值脱敏，如 {"token": "abcd****1234"}）
    credentials_masked: Dict[str, str] = Field(default_factory=dict, description='脱敏后的凭证')
    has_credentials: bool = Field(False, description='是否已配置凭证')
    description: Optional[str] = None
    status: int
    last_test_at: Optional[datetime] = None
    last_test_result: Optional[int] = None
    last_test_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataSourceTestResult(BaseModel):
    """数据源连接测试结果"""
    success: bool
    message: str
    response_time_ms: Optional[int] = None