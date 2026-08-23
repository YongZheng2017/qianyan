"""
数据源模型

定义数据源配置表结构
"""
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Text
from .base import Base, TimestampMixin


class DataSource(Base, TimestampMixin):
    """数据源配置模型"""
    __tablename__ = 'data_sources'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment='数据源名称')
    source_type = Column(String(20), nullable=False, comment='类型:tushare,akshare,custom')
    api_url = Column(String(255), nullable=False, comment='API地址')
    # 凭证（加密 JSON，按数据源类型区分字段，如 Tushare 的 {"token": "xxx"}）
    credentials_encrypted = Column(Text, comment='加密后的凭证JSON')
    # 兼容旧字段（已废弃，仅读取迁移用）
    token_encrypted = Column(String(500), comment='[已废弃]加密后的Token')
    description = Column(String(200), comment='描述')
    status = Column(SmallInteger, default=1, comment='状态:1启用 0禁用')
    last_test_at = Column(DateTime, comment='最后测试时间')
    last_test_result = Column(SmallInteger, comment='最后测试结果:1成功 0失败')
    last_test_message = Column(String(500), comment='最后测试信息')

    def __repr__(self):
        return f"<DataSource(id={self.id}, name='{self.name}', type='{self.source_type}')>"