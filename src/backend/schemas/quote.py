"""
行情相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel


class QuoteItem(BaseModel):
    """单根K线数据"""
    trade_date: str                              # 交易日 YYYYMMDD
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    pre_close: Optional[float] = None
    pct_chg: Optional[float] = None              # 涨跌幅 %
    vol: Optional[float] = None                  # 成交量
    amount: Optional[float] = None               # 成交额


class QuoteResponse(BaseModel):
    """行情查询响应"""
    symbol: str                                  # 标的代码
    name: str                                    # 标的名称
    type: str                                    # stock/index/sector
    period: str                                  # daily/weekly/monthly
    items: List[QuoteItem] = []


class SymbolItem(BaseModel):
    """标的信息（搜索结果）"""
    code: str
    name: str
    type: str                                    # stock/index/sector
    extra: Optional[str] = None                  # 附加信息（如行业）