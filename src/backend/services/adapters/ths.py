"""
同花顺（THS）数据源适配器

与 Tushare（POST+body）/ AKShare（SDK）不同，THS 使用 REST GET + X-api-key 请求头。
- 统一响应信封：HTTP 恒 200，业务码 code=0 成功
- 错误码分类：fatal（认证/参数，不可重试）与可重试（QPS/服务端）
- 时间戳：毫秒 Unix（Asia/Shanghai），入库前转换为 yyyyMMdd
文档：https://fuyao.aicubes.cn/docs/api-reference/overview/
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from .base import DataSourceAdapter

# fatal 错误码（认证/权限/参数/标的问题，重试无意义）
THS_FATAL_CODES = {2001, 2003, 1001, 1002, 1003, 1004, 3001, 3004}
# 3002 数据未就绪：视为空数据而非错误
THS_EMPTY_CODES = {3002}


def _ms_to_date(ms) -> Optional[str]:
    """毫秒时间戳 → yyyyMMdd（Asia/Shanghai）"""
    if ms is None:
        return None
    try:
        from zoneinfo import ZoneInfo
        dt = datetime.fromtimestamp(int(ms) / 1000, tz=ZoneInfo("Asia/Shanghai"))
        return dt.strftime("%Y%m%d")
    except Exception:
        return None


def _date_to_ms(date_str) -> Optional[int]:
    """yyyyMMdd → 毫秒 Unix 时间戳（Asia/Shanghai 当日 00:00）"""
    if date_str in (None, ""):
        return None
    try:
        from zoneinfo import ZoneInfo
        s = str(date_str).replace("-", "").strip()
        dt = datetime.strptime(s, "%Y%m%d").replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        return int(dt.timestamp() * 1000)
    except Exception:
        return None


# 参数值转换器（同步任务参数值 → THS query 参数值）
_PARAM_TRANSFORMS = {
    "date_to_ms": _date_to_ms,       # yyyyMMdd → 毫秒
}

# 字段值转换器（应用于 alias 重命名后的列）
_FIELD_TRANSFORMS = {
    "div100": lambda v: (v / 100) if isinstance(v, (int, float)) else v,  # 股→手
}


def _rename_ms_date(rec: Dict[str, Any], date_keys: List[str], out_key: str):
    """将记录中第一个存在且非空的毫秒时间戳字段转为日期，写入 out_key"""
    for k in date_keys:
        v = rec.get(k)
        if v is not None:
            d = _ms_to_date(v)
            if d:
                rec[out_key] = d
                return


# THS 接口元数据
# endpoint: REST 路径（相对 Base URL）
# param_map: 同步任务参数key → THS query参数key（None 表示直接同名）
# date_fields: 参与生成 trade_date 的毫秒时间戳字段（按优先级）
# field_alias: THS 字段 → 现有表列名
# ts_code_param: 标的参数名（thscode；thscodes 表示支持逗号分隔多标的）
THS_INTERFACE_META: Dict[str, dict] = {
    "prices_historical": {
        "label": "历史K线(日K)", "target_table": "daily_quotes",
        "endpoint": "/api/a-share/prices/historical",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"ts_code": "thscode", "start_date": "start", "end_date": "end", "adjust": "adjust"},
        "param_transform": {"start": "date_to_ms", "end": "date_to_ms"},
        "default_params": {"interval": "1d"},
        "date_fields": ["date_ms"],
        "stock_code_field": "thscode",
        "stock_code_alias": "ts_code",
        "field_alias": {"open_price": "open", "high_price": "high", "low_price": "low",
                        "close_price": "close", "volume": "vol", "turnover": "amount"},
        "field_transform": {"vol": "div100"},  # 股→手，与Tushare同表一致
        "records_key": "item",
    },
    "valuation_snapshot": {
        "label": "估值快照(PE/PB/PS/PCF)", "target_table": "ths_valuation_snapshot",
        "endpoint": "/api/a-share/valuations/snapshot",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"ts_code": "thscode"},
        "date_fields": ["timestamp", "time"],
        "stock_code_field": "thscode",
        "field_alias": {},
        "records_key": "item",
    },
    "financials_indicators": {
        "label": "财务指标(五类)", "target_table": "fin_indicator",
        "endpoint": "/api/a-share/financials/indicators",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"ts_code": "thscode", "period": "period"},
        "date_fields": ["endDate", "reportDate", "time"],
        "date_out_key": "end_date",
        "stock_code_field": "thscode",
        "stock_code_alias": "ts_code",
        "field_alias": {"thscode": "ts_code"},
        "records_key": "item",
    },
    "index_list": {
        "label": "同花顺指数列表", "target_table": "ths_index",
        "endpoint": "/api/a-share-index/list",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"tag": "tag"},
        "date_fields": [],
        "stock_code_field": "thscode",
        "field_alias": {},
        "records_key": "item",
    },
    "index_constituents": {
        "label": "同花顺指数成分股", "target_table": "ths_index_constituent",
        "endpoint": "/api/a-share-index/constituents",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"ts_code": "thscode"},
        "date_fields": [],
        "index_code_field": "indexThscode",
        "stock_code_field": "stockThscode",
        "field_alias": {"indexThscode": "index_code", "stockThscode": "stock_code"},
        "records_key": "item",
    },
    "index_prices_historical": {
        "label": "同花顺指数日K", "target_table": "ths_index_quotes",
        "endpoint": "/api/a-share-index/prices/historical",
        "default_interval_ms": 600, "min_points": None,
        "param_map": {"ts_code": "thscode", "start_date": "start", "end_date": "end"},
        "param_transform": {"start": "date_to_ms", "end": "date_to_ms"},
        "default_params": {"interval": "1d"},
        "date_fields": ["date_ms"],
        "stock_code_field": "thscode",
        "field_alias": {"open_price": "open", "high_price": "high", "low_price": "low",
                        "close_price": "close", "volume": "vol", "turnover": "amount"},
        "field_transform": {"vol": "div100"},  # 股→手
        "records_key": "item",
    },
}


class ThsAdapter(DataSourceAdapter):
    """同花顺数据源适配器（REST GET + X-api-key）"""

    DEFAULT_API_URL = "https://fuyao.aicubes.cn"

    @property
    def source_type(self) -> str:
        return "ths"

    CREDENTIALS_SCHEMA = [
        {"key": "api_key", "name": "API Key", "type": "password", "required": True,
         "hint": "从 fuyao.aicubes.cn 控制台获取"},
    ]

    def get_credentials_schema(self) -> List[dict]:
        return self.CREDENTIALS_SCHEMA

    def _get_api_key(self, credentials: Dict[str, Any]) -> str:
        return (credentials or {}).get("api_key", "") or ""

    async def _get(self, api_url: str, endpoint: str, api_key: str,
                   query: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{api_url}{endpoint}",
                params={k: v for k, v in query.items() if v not in (None, "")},
                headers={"X-api-key": api_key},
            )
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self, api_url: str, credentials: Dict[str, Any], timeout: int = 30) -> dict:
        """测试连接：调用交易日历（轻量无参）验证 API Key"""
        start = time.time()
        api_url = api_url or self.DEFAULT_API_URL
        api_key = self._get_api_key(credentials)
        if not api_key:
            return {"success": False, "message": "未配置 API Key", "response_time_ms": 0}
        try:
            body = await self._get(api_url, "/api/a-share/calendar/trading-days", api_key, {}, timeout)
            elapsed = int((time.time() - start) * 1000)
            code = body.get("code", -1)
            if code == 0:
                items = (body.get("data") or {}).get("item") or []
                return {"success": True, "message": f"API Key 有效，交易日历返回 {len(items)} 天",
                        "response_time_ms": elapsed}
            return {"success": False, "message": f"code={code}: {body.get('message')}",
                    "response_time_ms": elapsed}
        except Exception as e:
            return {"success": False, "message": f"连接异常: {e}",
                    "response_time_ms": int((time.time() - start) * 1000)}

    async def fetch_data(
        self, api_url: str, credentials: Dict[str, Any], interface: str,
        params: Dict[str, Any], fields: Optional[List[str]] = None, timeout: int = 30,
    ) -> dict:
        """调用 THS REST 接口并解析信封"""
        meta = THS_INTERFACE_META.get(interface)
        if not meta:
            return {"code": 1, "msg": f"THS 未知接口: {interface}", "records": [], "fatal": True}

        api_url = api_url or self.DEFAULT_API_URL
        api_key = self._get_api_key(credentials)
        if not api_key:
            return {"code": 2001, "msg": "未配置 API Key", "records": [], "fatal": True}

        # 同步任务参数 → THS query 参数（含参数值转换 + 自动附加默认参数）
        param_map = meta.get("param_map") or {}
        param_transform = meta.get("param_transform") or {}
        query: Dict[str, Any] = {}
        for task_key, ths_key in param_map.items():
            v = (params or {}).get(task_key)
            if v in (None, ""):
                continue
            ths_key = ths_key or task_key
            tfn = param_transform.get(ths_key)
            if tfn and tfn in _PARAM_TRANSFORMS:
                v = _PARAM_TRANSFORMS[tfn](v)
            if v not in (None, ""):
                query[ths_key] = v
        query.update(meta.get("default_params") or {})

        try:
            body = await self._get(api_url, meta["endpoint"], api_key, query, timeout)
        except Exception as e:
            return {"code": 1, "msg": f"请求失败: {e}", "records": [], "fatal": False}

        code = body.get("code", -1)
        if code in THS_EMPTY_CODES:
            return {"code": 0, "msg": None, "records": [], "fatal": False}
        if code != 0:
            fatal = code in THS_FATAL_CODES
            return {"code": code, "msg": f"THS code={code}: {body.get('message')}",
                    "records": [], "fatal": fatal}

        items = ((body.get("data") or {}).get(meta.get("records_key", "item"))) or []

        # 记录加工：时间戳→日期、字段重命名、标的代码对齐
        date_fields = meta.get("date_fields") or []
        date_out = meta.get("date_out_key", "trade_date")
        alias = meta.get("field_alias") or {}
        transforms = meta.get("field_transform") or {}
        code_field = meta.get("stock_code_field")
        code_alias = meta.get("stock_code_alias")

        records: List[dict] = []
        for raw in items:
            rec = dict(raw)
            if date_fields:
                _rename_ms_date(rec, date_fields, date_out)
            # 生成与现有表一致的标的代码列（如 daily_quotes.ts_code / fin_indicator.ts_code）
            if code_field and code_alias and code_field in rec:
                rec[code_alias] = rec[code_field]
            for old, new in alias.items():
                if old in rec and new != old:
                    rec[new] = rec.pop(old)
            # 字段值转换（应用于 alias 后的列名，如 volume÷100 → vol）
            for col, tfn in transforms.items():
                if col in rec and rec[col] is not None and tfn in _FIELD_TRANSFORMS:
                    rec[col] = _FIELD_TRANSFORMS[tfn](rec[col])
            records.append(rec)

        return {"code": 0, "msg": None, "records": records, "fatal": False}

    def get_interfaces(self) -> List[dict]:
        return [
            {"value": k, "label": v["label"], "target_table": v["target_table"]}
            for k, v in THS_INTERFACE_META.items()
        ]

    def get_interface_params(self, interface: str) -> List[dict]:
        meta = THS_INTERFACE_META.get(interface)
        if not meta:
            return []
        # 依据 param_map 生成参数定义（ths 特定的参数说明）
        defs = {
            "ts_code": {"key": "ts_code", "name": "标的代码", "type": "text", "required": True,
                        "hint": "如 600519.SH / 90.BK1027(指数)"},
            "start_date": {"key": "start_date", "name": "开始日期", "type": "date", "required": True},
            "end_date": {"key": "end_date", "name": "结束日期", "type": "date", "required": True,
                         "hint": "窗口≤10年"},
            "period": {"key": "period", "name": "报告期", "type": "date", "required": False, "hint": "如20251231"},
            "adjust": {"key": "adjust", "name": "复权方式", "type": "select", "required": False,
                       "options": [("forward", "前复权(默认)"), ("none", "不复权"), ("backward", "后复权")]},
            "tag": {"key": "tag", "name": "指数分类", "type": "select", "required": False,
                    "options": [("", "全部"), ("行业", "行业"), ("概念", "概念")]},
        }
        return [defs[k] for k in (meta.get("param_map") or {}) if k in defs]