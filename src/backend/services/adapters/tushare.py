"""
Tushare 数据源适配器

基于 Tushare HTTP 接口实现（POST http://api.tushare.pro）
接口技术参考：requirements/data-sync/tushare-api-reference.md
"""
from typing import Any, Dict, List, Optional
import time
import httpx
from .base import DataSourceAdapter


# Tushare 接口元数据（字段定义以 tushare-api-reference.md 为准）
TUSHARE_INTERFACE_META: Dict[str, dict] = {
    "stock_basic": {
        "label": "股票列表",
        "target_table": "stocks",
        "limit_per_request": 6000,
        "rate_limit_per_min": 50,
        "default_interval_ms": 1200,
        "fields": [
            "ts_code", "symbol", "name", "area", "industry",
            "market", "exchange", "list_status", "list_date", "delist_date",
            "is_hs", "act_name", "act_ent_type",
        ],
        "params": [
            {"key": "list_status", "name": "上市状态", "type": "select", "required": False,
             "options": [("L", "上市"), ("D", "退市"), ("P", "暂停"), ("G", "未交易")], "default": "L"},
            {"key": "exchange", "name": "交易所", "type": "select", "required": False,
             "options": [("", "全部"), ("SSE", "上交所"), ("SZSE", "深交所"), ("BSE", "北交所")]},
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
        ],
    },
    "daily": {
        "label": "日线行情",
        "target_table": "daily_quotes",
        "limit_per_request": 6000,
        "rate_limit_per_min": 500,
        "default_interval_ms": 130,
        "fields": [
            "ts_code", "trade_date", "open", "high", "low", "close",
            "pre_close", "change", "pct_chg", "vol", "amount",
        ],
        "params": [
            {"key": "trade_date", "name": "交易日", "type": "date", "required": False, "hint": "YYYYMMDD"},
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "weekly": {
        "label": "周线行情",
        "target_table": "weekly_quotes",
        "limit_per_request": 6000,
        "default_interval_ms": 500,
        "fields": [
            "ts_code", "trade_date", "open", "high", "low", "close",
            "pre_close", "change", "pct_chg", "vol", "amount",
        ],
        "params": [
            {"key": "trade_date", "name": "交易日", "type": "date", "required": False, "hint": "每周最后交易日 YYYYMMDD"},
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "monthly": {
        "label": "月线行情",
        "target_table": "monthly_quotes",
        "limit_per_request": 4500,
        "default_interval_ms": 500,
        "fields": [
            "ts_code", "trade_date", "open", "high", "low", "close",
            "pre_close", "change", "pct_chg", "vol", "amount",
        ],
        "params": [
            {"key": "trade_date", "name": "交易日", "type": "date", "required": False, "hint": "每月最后交易日 YYYYMMDD"},
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    # ===== 财务数据接口（DS-005）=====
    # requires_ts_code=True: 标准接口 ts_code 必填，留空时执行器自动切换 vip_api（需5000积分）
    "income": {
        "label": "利润表", "target_table": "fin_income", "limit_per_request": 10000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": "income_vip", "requires_ts_code": True,
        "fields": ["ts_code", "ann_date", "end_date", "report_type", "total_revenue", "revenue",
                   "operate_profit", "total_profit", "n_income", "n_income_attr_p", "basic_eps", "diluted_eps", "rd_exp"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场(需5000积分)"},
            {"key": "period", "name": "报告期", "type": "date", "required": False, "hint": "如20171231年报"},
            {"key": "start_date", "name": "公告起始日", "type": "date", "required": False},
            {"key": "end_date", "name": "公告结束日", "type": "date", "required": False},
            {"key": "report_type", "name": "报告类型", "type": "text", "required": False, "hint": "1合并(默认)"},
        ],
    },
    "balancesheet": {
        "label": "资产负债表", "target_table": "fin_balancesheet", "limit_per_request": 10000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": "balancesheet_vip", "requires_ts_code": True,
        "fields": ["ts_code", "ann_date", "end_date", "report_type", "total_assets", "total_liab",
                   "total_hldr_eqy_inc_min_int", "money_cap", "accounts_receiv", "inventories",
                   "fix_assets", "goodwill", "st_borr", "lt_borr"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场(需5000积分)"},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "start_date", "name": "公告起始日", "type": "date", "required": False},
            {"key": "end_date", "name": "公告结束日", "type": "date", "required": False},
            {"key": "report_type", "name": "报告类型", "type": "text", "required": False},
        ],
    },
    "cashflow": {
        "label": "现金流量表", "target_table": "fin_cashflow", "limit_per_request": 10000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": "cashflow_vip", "requires_ts_code": True,
        "fields": ["ts_code", "ann_date", "end_date", "report_type", "net_profit", "n_cashflow_act",
                   "n_cashflow_inv_act", "n_cash_flows_fnc_act", "free_cashflow", "c_fr_sale_sg"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场(需5000积分)"},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "start_date", "name": "公告起始日", "type": "date", "required": False},
            {"key": "end_date", "name": "公告结束日", "type": "date", "required": False},
            {"key": "report_type", "name": "报告类型", "type": "text", "required": False},
        ],
    },
    "fina_indicator": {
        "label": "财务指标", "target_table": "fin_indicator", "limit_per_request": 100,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": "fina_indicator_vip", "requires_ts_code": True,
        "fields": ["ts_code", "ann_date", "end_date", "eps", "bps", "roe", "roe_waa", "roa",
                   "netprofit_margin", "grossprofit_margin", "debt_to_assets", "netprofit_yoy", "or_yoy"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场(需5000积分)"},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "start_date", "name": "报告期起始", "type": "date", "required": False},
            {"key": "end_date", "name": "报告期结束", "type": "date", "required": False},
        ],
    },
    "forecast": {
        "label": "业绩预告", "target_table": "fin_forecast", "limit_per_request": 1000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": None, "requires_ts_code": False,
        "fields": ["ts_code", "ann_date", "end_date", "type", "p_change_min", "p_change_max",
                   "net_profit_min", "net_profit_max", "last_parent_net", "summary"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场"},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "start_date", "name": "公告起始日", "type": "date", "required": False},
            {"key": "end_date", "name": "公告结束日", "type": "date", "required": False},
        ],
    },
    "express": {
        "label": "业绩快报", "target_table": "fin_express", "limit_per_request": 1000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": None, "requires_ts_code": False,
        "fields": ["ts_code", "ann_date", "end_date", "revenue", "operate_profit", "total_profit",
                   "n_income", "total_assets", "basic_eps", "diluted_eps", "yoy_net_profit"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "start_date", "name": "公告起始日", "type": "date", "required": False},
            {"key": "end_date", "name": "公告结束日", "type": "date", "required": False},
        ],
    },
    "dividend": {
        "label": "分红送股", "target_table": "fin_dividend", "limit_per_request": 1000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": None, "requires_ts_code": False,
        "fields": ["ts_code", "end_date", "ann_date", "div_proc", "stk_div", "cash_div",
                   "record_date", "ex_date", "pay_date"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "ann_date", "name": "公告日", "type": "date", "required": False},
            {"key": "record_date", "name": "股权登记日", "type": "date", "required": False},
            {"key": "ex_date", "name": "除权除息日", "type": "date", "required": False},
        ],
    },
    "fina_mainbz": {
        "label": "主营业务构成", "target_table": "fin_mainbz", "limit_per_request": 100,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": "fina_mainbz_vip", "requires_ts_code": True,
        "fields": ["ts_code", "end_date", "bz_item", "bz_code", "bz_sales", "bz_profit", "bz_cost", "curr_type"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空=全市场(需5000积分)"},
            {"key": "period", "name": "报告期", "type": "date", "required": False},
            {"key": "type", "name": "构成类型", "type": "select", "required": False,
             "options": [("", "全部"), ("P", "按产品"), ("D", "按地区"), ("I", "按行业")]},
            {"key": "start_date", "name": "报告期起始", "type": "date", "required": False},
            {"key": "end_date", "name": "报告期结束", "type": "date", "required": False},
        ],
    },
    "disclosure_date": {
        "label": "财报披露计划", "target_table": "fin_disclosure", "limit_per_request": 3000,
        "default_interval_ms": 500, "min_points": 500,
        "vip_api": None, "requires_ts_code": False,
        "fields": ["ts_code", "end_date", "ann_date", "pre_date", "actual_date", "modify_date"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
            {"key": "end_date", "name": "财报周期", "type": "date", "required": False, "hint": "如20181231"},
        ],
    },
    # ===== 资金流向（DS-006）=====
    "moneyflow": {
        "label": "个股资金流向", "target_table": "moneyflow", "limit_per_request": 6000,
        "default_interval_ms": 500, "min_points": 2000,
        "vip_api": None, "requires_ts_code": False,  # 可按 trade_date 全市场
        "fields": ["ts_code", "trade_date",
                   "buy_sm_vol", "buy_sm_amount", "sell_sm_vol", "sell_sm_amount",
                   "buy_md_vol", "buy_md_amount", "sell_md_vol", "sell_md_amount",
                   "buy_lg_vol", "buy_lg_amount", "sell_lg_vol", "sell_lg_amount",
                   "buy_elg_vol", "buy_elg_amount", "sell_elg_vol", "sell_elg_amount",
                   "net_mf_vol", "net_mf_amount"],
        "params": [
            {"key": "ts_code", "name": "股票代码", "type": "text", "required": False, "hint": "留空+trade_date=全市场"},
            {"key": "trade_date", "name": "交易日期", "type": "date", "required": False, "hint": "YYYYMMDD"},
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    # ===== 宏观经济-国内（DS-008）=====
    "shibor_lpr": {
        "label": "LPR贷款基础利率", "target_table": "macro_lpr", "limit_per_request": 4000,
        "default_interval_ms": 500, "min_points": 120, "vip_api": None, "requires_ts_code": False,
        "fields": ["date", "1y", "5y"],
        "field_alias": {"1y": "y1", "5y": "y5"},
        "date_key": "date",
        "params": [
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "shibor": {
        "label": "Shibor利率", "target_table": "macro_shibor", "limit_per_request": 2000,
        "default_interval_ms": 500, "min_points": 120, "vip_api": None, "requires_ts_code": False,
        "fields": ["date", "on", "1w", "2w", "1m", "3m", "6m", "9m", "1y"],
        "field_alias": {"on": "on_rate", "1w": "w1", "2w": "w2", "1m": "m1", "3m": "m3", "6m": "m6", "9m": "m9", "1y": "y1"},
        "date_key": "date",
        "params": [
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "cn_gdp": {
        "label": "GDP数据", "target_table": "macro_gdp", "limit_per_request": 10000,
        "default_interval_ms": 500, "min_points": 600, "vip_api": None, "requires_ts_code": False,
        "fields": ["quarter", "gdp", "gdp_yoy", "pi", "pi_yoy", "si", "si_yoy", "ti", "ti_yoy"],
        "date_key": "quarter",
        "params": [
            {"key": "start_q", "name": "开始季度", "type": "text", "required": False, "hint": "如2018Q1"},
            {"key": "end_q", "name": "结束季度", "type": "text", "required": False, "hint": "如2019Q3"},
        ],
    },
    "cn_cpi": {
        "label": "居民消费价格指数CPI", "target_table": "macro_cpi", "limit_per_request": 5000,
        "default_interval_ms": 500, "min_points": 600, "vip_api": None, "requires_ts_code": False,
        "fields": ["month", "nt_val", "nt_yoy", "nt_mom", "nt_accu"],
        "date_key": "month",
        "params": [
            {"key": "start_m", "name": "开始月份", "type": "text", "required": False, "hint": "如201801"},
            {"key": "end_m", "name": "结束月份", "type": "text", "required": False},
        ],
    },
    "cn_ppi": {
        "label": "工业生产者出厂价格指数PPI", "target_table": "macro_ppi", "limit_per_request": 5000,
        "default_interval_ms": 500, "min_points": 600, "vip_api": None, "requires_ts_code": False,
        "fields": ["month", "nt_val", "nt_yoy", "nt_mom", "nt_accu"],
        "date_key": "month",
        "params": [
            {"key": "start_m", "name": "开始月份", "type": "text", "required": False, "hint": "如201801"},
            {"key": "end_m", "name": "结束月份", "type": "text", "required": False},
        ],
    },
    "cn_pmi": {
        "label": "采购经理指数PMI", "target_table": "macro_pmi", "limit_per_request": 5000,
        "default_interval_ms": 500, "min_points": 600, "vip_api": None, "requires_ts_code": False,
        "fields": ["month", "pmi"],
        "date_key": "month",
        "params": [
            {"key": "start_m", "name": "开始月份", "type": "text", "required": False, "hint": "如201801"},
            {"key": "end_m", "name": "结束月份", "type": "text", "required": False},
        ],
    },
    "cn_m": {
        "label": "货币供应量M0/M1/M2", "target_table": "macro_m", "limit_per_request": 5000,
        "default_interval_ms": 500, "min_points": 600, "vip_api": None, "requires_ts_code": False,
        "fields": ["month", "m0", "m1", "m2", "m0_yoy", "m1_yoy", "m2_yoy"],
        "date_key": "month",
        "params": [
            {"key": "start_m", "name": "开始月份", "type": "text", "required": False, "hint": "如201801"},
            {"key": "end_m", "name": "结束月份", "type": "text", "required": False},
        ],
    },
    # ===== 宏观经济-国际（美国利率）=====
    "us_tycr": {
        "label": "美国国债收益率曲线(日频)", "target_table": "macro_us_tycr", "limit_per_request": 2000,
        "default_interval_ms": 500, "min_points": 120, "vip_api": None, "requires_ts_code": False,
        "fields": ["date", "m1", "m2", "m3", "m4", "m6", "y1", "y2", "y3", "y5", "y7", "y10", "y20", "y30"],
        "date_key": "date",
        "params": [
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "us_tbr": {
        "label": "美国短期国债利率", "target_table": "macro_us_tbr", "limit_per_request": 2000,
        "default_interval_ms": 500, "min_points": 120, "vip_api": None, "requires_ts_code": False,
        "fields": ["date", "m3", "m6", "y1"],
        "date_key": "date",
        "params": [
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
    "us_tlr": {
        "label": "美国国债长期利率", "target_table": "macro_us_tlr", "limit_per_request": 2000,
        "default_interval_ms": 500, "min_points": 120, "vip_api": None, "requires_ts_code": False,
        "fields": ["date", "y10", "y20", "y30"],
        "date_key": "date",
        "params": [
            {"key": "start_date", "name": "开始日期", "type": "date", "required": False},
            {"key": "end_date", "name": "结束日期", "type": "date", "required": False},
        ],
    },
}

# 权限/Token 不足错误码（不可重试）
# 2002: 积分不足；40101: token 不正确
TUSHARE_FATAL_CODES = {2002, 40101}


class TushareAdapter(DataSourceAdapter):
    """Tushare 数据源适配器"""

    DEFAULT_API_URL = "http://api.tushare.pro"

    @property
    def source_type(self) -> str:
        return "tushare"

    # Tushare 凭证字段定义（仅 API Token）
    CREDENTIALS_SCHEMA = [
        {"key": "token", "name": "API Token", "type": "password", "required": True,
         "hint": "从 tushare.pro 个人主页获取"},
    ]

    def get_credentials_schema(self) -> List[dict]:
        return self.CREDENTIALS_SCHEMA

    def _get_token(self, credentials: Dict[str, Any]) -> str:
        """从凭证 dict 中提取 token"""
        return (credentials or {}).get("token", "") or ""

    def _build_request(self, token: str, api_name: str, params: Dict[str, Any],
                       fields: Optional[List[str]] = None) -> dict:
        """构建 Tushare 请求体"""
        body: Dict[str, Any] = {
            "api_name": api_name,
            "token": token,
            "params": params or {},
        }
        if fields:
            body["fields"] = ",".join(fields)
        return body

    @staticmethod
    def _parse_response(resp_json: dict) -> dict:
        """
        解析 Tushare 响应

        将 fields + items 二维结构转为字典列表
        """
        code = resp_json.get("code", -1)
        msg = resp_json.get("msg")
        data = resp_json.get("data") or {}
        fields = data.get("fields", [])
        items = data.get("items", [])
        records = [dict(zip(fields, row)) for row in items]
        return {
            "code": code,
            "msg": msg,
            "records": records,
            "fields": fields,
        }

    async def _post(self, api_url: str, body: dict, timeout: int) -> dict:
        """发送 POST 请求"""
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(api_url, json=body)
            resp.raise_for_status()
            return resp.json()

    async def test_connection(self, api_url: str, credentials: Dict[str, Any], timeout: int = 30) -> dict:
        """
        测试连接：调用 stock_basic 验证 Token 有效性
        """
        api_url = api_url or self.DEFAULT_API_URL
        token = self._get_token(credentials)
        if not token:
            return {"success": False, "message": "未配置 Token", "response_time_ms": 0}
        start = time.time()
        try:
            body = self._build_request(token, "stock_basic", {"list_status": "L"}, ["ts_code"])
            resp_json = await self._post(api_url, body, timeout)
            elapsed = int((time.time() - start) * 1000)
            parsed = self._parse_response(resp_json)

            if parsed["code"] == 0:
                return {"success": True, "message": "Token 验证成功", "response_time_ms": elapsed}
            elif parsed["code"] in TUSHARE_FATAL_CODES:
                return {"success": False, "message": f"Token 无效或积分不足（code={parsed['code']}）：{parsed['msg']}",
                        "response_time_ms": elapsed}
            else:
                return {"success": False, "message": f"连接失败（code={parsed['code']}）：{parsed['msg']}",
                        "response_time_ms": elapsed}
        except httpx.TimeoutException:
            return {"success": False, "message": f"连接超时（{timeout}秒）", "response_time_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            return {"success": False, "message": f"连接异常：{str(e)}", "response_time_ms": int((time.time() - start) * 1000)}

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

        Returns:
            {"code": int, "msg": str, "records": list[dict], "fatal": bool}
        """
        api_url = api_url or self.DEFAULT_API_URL
        token = self._get_token(credentials)
        meta = TUSHARE_INTERFACE_META.get(interface, {})
        # 默认返回接口定义的全部字段
        if fields is None:
            fields = meta.get("fields")

        # _vip 接口切换：标准接口要求 ts_code 但未提供时，切换到 _vip 接口（全市场，需5000积分）
        api_name = interface
        if meta.get("requires_ts_code") and not (params or {}).get("ts_code"):
            vip = meta.get("vip_api")
            if vip:
                api_name = vip
            else:
                raise ValueError(f"接口 {interface} 要求指定股票代码(ts_code)，且无 _vip 全市场接口，不支持全市场同步")

        body = self._build_request(token, api_name, params, fields)
        resp_json = await self._post(api_url, body, timeout)
        parsed = self._parse_response(resp_json)
        parsed["fatal"] = parsed["code"] in TUSHARE_FATAL_CODES

        # 宏观接口：字段重命名（如 1w→w1，on→on_rate），避免非法标识符列名
        field_alias = meta.get("field_alias")
        if field_alias and parsed["records"]:
            for rec in parsed["records"]:
                for old_key, new_key in field_alias.items():
                    if old_key in rec:
                        rec[new_key] = rec.pop(old_key)
        return parsed

    def get_interfaces(self) -> List[dict]:
        """获取支持的接口列表"""
        return [
            {"value": k, "label": v["label"], "target_table": v["target_table"]}
            for k, v in TUSHARE_INTERFACE_META.items()
        ]

    def get_interface_params(self, interface: str) -> List[dict]:
        """获取接口参数定义"""
        meta = TUSHARE_INTERFACE_META.get(interface)
        return meta["params"] if meta else []

    def get_interface_meta(self, interface: str) -> Optional[dict]:
        """获取接口完整元数据"""
        return TUSHARE_INTERFACE_META.get(interface)