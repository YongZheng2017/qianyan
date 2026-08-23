"""
资金趋势分析相关 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class MfDailyItem(BaseModel):
    """单日资金流向"""
    trade_date: str
    net_mf_amount: Optional[float] = None          # 净流入额(万元)
    buy_elg_amount: Optional[float] = None          # 特大单买入(万元)
    sell_elg_amount: Optional[float] = None         # 特大单卖出(万元)
    buy_lg_amount: Optional[float] = None           # 大单买入
    sell_lg_amount: Optional[float] = None          # 大单卖出
    close: Optional[float] = None                   # 当日收盘价(叠加对比)


class StockFlowResponse(BaseModel):
    """个股资金流向（多日）"""
    ts_code: str
    name: str
    latest: Optional[MfDailyItem] = None           # 最新一日
    items: List[MfDailyItem] = []                  # 时间序列(升序)


class MarketFlowItem(BaseModel):
    """市场资金总览单日"""
    trade_date: str
    net_mf_amount: float = 0                       # 全市场净流入合计(万元)
    up_count: Optional[int] = None                 # 净流入为正的股票数
    down_count: Optional[int] = None               # 净流入为负的股票数


class MarketFlowResponse(BaseModel):
    items: List[MarketFlowItem] = []


class RankItem(BaseModel):
    """净流入排行"""
    ts_code: str
    name: str
    industry: Optional[str] = None
    net_mf_amount: float = 0
    pct_chg: Optional[float] = None                # 当日涨跌幅%
    close: Optional[float] = None


class RankResponse(BaseModel):
    trade_date: Optional[str] = None
    inflow: List[RankItem] = []                    # 净流入 TOP N
    outflow: List[RankItem] = []                   # 净流出 TOP N


class IndustryFlowItem(BaseModel):
    """行业资金流向"""
    industry: str
    net_mf_amount: float = 0
    stock_count: int = 0


class IndustryFlowResponse(BaseModel):
    trade_date: Optional[str] = None
    items: List[IndustryFlowItem] = []


class MacroSeriesResponse(BaseModel):
    """宏观指标时序"""
    indicator: str                                  # 如 shibor / cn_cpi / us_tycr
    field: str                                      # 如 y1 / nt_yoy / y10
    dates: List[str] = []
    values: List[Optional[float]] = []