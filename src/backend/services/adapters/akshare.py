"""
AKShare 数据源适配器

与 Tushare（HTTP API）不同，AKShare 是 Python SDK，直接调用函数获取数据（pandas DataFrame）。
- 无需 Token（免费开源）
- 字段为中文，需映射为英文列名
- 同步库，用 asyncio.to_thread 包装避免阻塞事件循环
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from .base import DataSourceAdapter


# AKShare 接口元数据（func=akshare函数名, col_map=中文→英文列名映射）
AKSHARE_INTERFACE_META: Dict[str, dict] = {
    "board_industry_name": {
        "label": "行业板块列表",
        "target_table": "board_industry",
        "func": "stock_board_industry_name_em",
        "col_map": {
            "板块名称": "board_name", "板块代码": "board_code",
            "最新价": "latest_price", "涨跌额": "change_amount",
            "涨跌幅": "pct_chg", "总市值": "total_market_cap",
            "换手率": "turnover", "上涨家数": "up_count",
            "下跌家数": "down_count", "领涨股票": "leader_stock",
            "领涨股票-涨跌幅": "leader_pct_chg",
        },
        "fields": ["board_name", "board_code", "latest_price", "change_amount", "pct_chg",
                   "total_market_cap", "turnover", "up_count", "down_count", "leader_stock", "leader_pct_chg"],
        "params": [],  # 无参数（获取全部板块）
    },
    "board_industry_hist": {
        "label": "行业板块日线行情",
        "target_table": "board_industry_quotes",
        "func": "stock_board_industry_hist_em",
        "col_map": {
            "日期": "trade_date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "涨跌幅": "pct_chg",
            "涨跌额": "change", "成交量": "vol", "成交额": "amount",
            "振幅": "amplitude", "换手率": "turnover",
        },
        "fields": ["board_name", "trade_date", "period", "open", "high", "low", "close",
                   "pct_chg", "change", "vol", "amount", "amplitude", "turnover"],
        "params": [
            {"key": "symbol", "name": "板块名称", "type": "text", "required": True, "hint": "如 小金属（来自板块列表）"},
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False, "hint": "YYYYMMDD"},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False, "hint": "YYYYMMDD"},
            {"key": "period", "name": "周期", "type": "select", "required": False,
             "options": [("日k", "日K"), ("周k", "周K"), ("月k", "月K")], "default": "日k"},
            {"key": "adjust", "name": "复权", "type": "select", "required": False,
             "options": [("", "不复权"), ("qfq", "前复权"), ("hfq", "后复权")], "default": ""},
        ],
    },
}


class AKShareAdapter(DataSourceAdapter):
    """AKShare 数据源适配器（SDK 调用，无需 Token）"""

    @property
    def source_type(self) -> str:
        return "akshare"

    def get_credentials_schema(self) -> List[dict]:
        """AKShare 无需凭证"""
        return []

    async def test_connection(self, api_url: str, credentials: Dict[str, Any], timeout: int = 30) -> dict:
        """测试连接：调用板块列表接口验证 akshare 可用"""
        import time
        start = time.time()
        try:
            import akshare as ak
            df = await asyncio.to_thread(ak.stock_board_industry_name_em)
            return {
                "success": True,
                "message": f"AKShare 可用，获取到 {len(df)} 个行业板块",
                "response_time_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:
            return {"success": False, "message": f"AKShare 调用失败: {e}",
                    "response_time_ms": int((time.time() - start) * 1000)}

    async def fetch_data(
        self, api_url: str, credentials: Dict[str, Any], interface: str,
        params: Dict[str, Any], fields: Optional[List[str]] = None, timeout: int = 30,
    ) -> dict:
        """调用 AKShare SDK 获取数据，中文字段映射为英文"""
        import akshare as ak
        meta = AKSHARE_INTERFACE_META.get(interface)
        if not meta:
            return {"code": 1, "msg": f"AKShare 未知接口: {interface}", "records": [], "fatal": True}

        func = getattr(ak, meta["func"])
        call_params = self._build_call_params(interface, params)

        try:
            df = await asyncio.to_thread(func, **call_params)
        except Exception as e:
            return {"code": 1, "msg": f"AKShare 调用失败: {e}", "records": [], "fatal": False}

        if df is None or getattr(df, "empty", True):
            return {"code": 0, "msg": None, "records": [], "fatal": False}

        # 中文字段 → 英文列名
        df = df.rename(columns=meta["col_map"])

        # 日期格式统一为 YYYYMMDD（akshare 返回 "2021-12-01"）
        if "trade_date" in df.columns:
            df["trade_date"] = df["trade_date"].astype(str).str.replace("-", "")

        # 板块行情注入板块名（akshare hist 返回数据不含板块标识）
        if interface == "board_industry_hist":
            df["board_name"] = params.get("symbol", "")

        # 转 dict 列表（to_json 确保 numpy 类型转为原生 Python 类型）
        records = json.loads(df.to_json(orient="records", force_ascii=False))
        return {"code": 0, "msg": None, "records": records, "fatal": False}

    def _build_call_params(self, interface: str, params: Dict[str, Any]) -> dict:
        """构造 akshare 函数的调用参数"""
        params = params or {}
        if interface == "board_industry_hist":
            return {
                "symbol": params.get("symbol", ""),
                "period": params.get("period", "日k"),
                "start_date": params.get("start_date") or "20200101",
                "end_date": params.get("end_date") or "20991231",
                "adjust": params.get("adjust", "") or "",
            }
        # board_industry_name 无参数（使用默认）
        return {}

    def get_interfaces(self) -> List[dict]:
        return [
            {"value": k, "label": v["label"], "target_table": v["target_table"]}
            for k, v in AKSHARE_INTERFACE_META.items()
        ]

    def get_interface_params(self, interface: str) -> List[dict]:
        meta = AKSHARE_INTERFACE_META.get(interface)
        return meta["params"] if meta else []