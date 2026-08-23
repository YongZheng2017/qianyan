"""
数据源适配器抽象基类

定义统一的数据源接口，不同数据源实现各自的适配器
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DataSourceAdapter(ABC):
    """数据源适配器接口"""

    @property
    @abstractmethod
    def source_type(self) -> str:
        """数据源类型标识"""
        pass

    @abstractmethod
    def get_credentials_schema(self) -> List[dict]:
        """
        凭证字段定义（前端据此动态渲染配置表单）

        Returns:
            List[dict]: [{"key": "token", "name": "API Token", "type": "password",
                          "required": True, "hint": "..."}]
        """
        pass

    @abstractmethod
    async def test_connection(self, api_url: str, credentials: Dict[str, Any], timeout: int = 30) -> dict:
        """
        测试数据源连接

        Args:
            api_url: API 地址
            credentials: 明文凭证 dict（如 {"token": "xxx"}）
            timeout: 超时时间（秒）

        Returns:
            dict: {"success": bool, "message": str, "response_time_ms": int}
        """
        pass

    @abstractmethod
    async def fetch_data(
        self,
        api_url: str,
        credentials: Dict[str, Any],
        interface: str,
        params: Dict[str, Any],
        fields: Optional[List[str]] = None,
        timeout: int = 30
    ) -> dict:
        """
        获取数据

        Args:
            api_url: API 地址
            credentials: 明文凭证 dict
            interface: 数据接口名称
            params: 接口参数
            fields: 指定返回字段（可选）
            timeout: 超时时间（秒）

        Returns:
            dict: {"code": int, "msg": str, "records": list[dict], "fatal": bool}
        """
        pass

    @abstractmethod
    def get_interfaces(self) -> List[dict]:
        """
        获取该数据源支持的数据接口列表

        Returns:
            List[dict]: [{"value": "daily", "label": "日线行情", "target_table": "daily_quotes"}]
        """
        pass

    @abstractmethod
    def get_interface_params(self, interface: str) -> List[dict]:
        """
        获取指定接口的参数定义

        Args:
            interface: 接口名称

        Returns:
            List[dict]: 参数定义列表
        """
        pass