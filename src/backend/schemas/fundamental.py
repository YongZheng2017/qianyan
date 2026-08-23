"""
基本面分析相关 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class StockBrief(BaseModel):
    ts_code: str
    name: str
    industry: Optional[str] = None


class IndicatorCard(BaseModel):
    """指标卡片"""
    key: str
    name: str
    value: Optional[float] = None
    yoy: Optional[float] = None        # 同比变化
    industry_avg: Optional[float] = None  # 行业均值（后续补充）


class RiskAlert(BaseModel):
    level: str                          # warning / danger
    message: str


class LatestStatement(BaseModel):
    """最新财报摘要"""
    end_date: str
    total_revenue: Optional[float] = None
    n_income: Optional[float] = None
    n_income_attr_p: Optional[float] = None
    operate_profit: Optional[float] = None
    n_cashflow_act: Optional[float] = None     # 经营现金流（来自cashflow）
    total_assets: Optional[float] = None
    total_liab: Optional[float] = None


class OverviewResponse(BaseModel):
    stock: StockBrief
    latest_period: Optional[str] = None
    indicators: List[IndicatorCard] = []
    latest_statement: Optional[LatestStatement] = None
    risk_alerts: List[RiskAlert] = []


class StatementResponse(BaseModel):
    """三大报表多期数据"""
    type: str                              # income/balancesheet/cashflow
    headers: List[str] = []                # 报告期列表
    rows: List[Dict[str, Any]] = []        # [{key, name, values:[...]}]


class IndicatorGroupResponse(BaseModel):
    """能力指标（四类，多期）"""
    headers: List[str] = []                # 报告期
    groups: List[Dict[str, Any]] = []      # [{key:'profitability', name:'盈利能力', items:[{key,name,values}]}]


class ValuationResponse(BaseModel):
    """估值"""
    ts_code: str
    name: str
    close: Optional[float] = None          # 最新股价
    trade_date: Optional[str] = None
    eps: Optional[float] = None
    bps: Optional[float] = None
    netprofit_yoy: Optional[float] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    peg: Optional[float] = None
    conclusion: Optional[str] = None       # 结论提示
    note: Optional[str] = None             # 数据不足说明