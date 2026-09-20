"""
数据源适配器模块

通过适配器模式统一不同数据源的接口
"""
from .base import DataSourceAdapter
from .tushare import TushareAdapter
from .akshare import AKShareAdapter
from .ths import ThsAdapter
from .factory import DataSourceAdapterFactory

__all__ = ["DataSourceAdapter", "TushareAdapter", "AKShareAdapter", "ThsAdapter", "DataSourceAdapterFactory"]