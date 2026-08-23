"""
数据源适配器工厂

根据数据源类型返回对应的适配器实例
"""
from .base import DataSourceAdapter
from .tushare import TushareAdapter
from .akshare import AKShareAdapter


class DataSourceAdapterFactory:
    """数据源适配器工厂"""

    _adapters = {
        "tushare": TushareAdapter,
        "akshare": AKShareAdapter,
    }

    @classmethod
    def get_adapter(cls, source_type: str) -> DataSourceAdapter:
        """
        获取适配器实例

        Args:
            source_type: 数据源类型

        Returns:
            DataSourceAdapter: 适配器实例

        Raises:
            ValueError: 不支持的数据源类型
        """
        adapter_cls = cls._adapters.get(source_type)
        if adapter_cls is None:
            raise ValueError(f"不支持的数据源类型：{source_type}")
        return adapter_cls()

    @classmethod
    def get_supported_types(cls) -> list:
        """获取支持的数据源类型列表"""
        return list(cls._adapters.keys())