"""
行情业务数据模型

Tushare 同步数据落库的目标表：
- stocks 股票列表（stock_basic）
- daily_quotes 日线行情（daily）
- weekly_quotes 周线行情（weekly）
- monthly_quotes 月线行情（monthly）

字段与 Tushare 接口对齐，参考 requirements/data-sync/tushare-api-reference.md
注意：vol 单位为"手"，amount 单位为"千元"，落库保留原始单位
"""
from sqlalchemy import Column, Integer, String, Float, PrimaryKeyConstraint
from .base import Base


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = 'stocks'

    ts_code = Column(String(20), primary_key=True, comment='TS代码')
    symbol = Column(String(20), comment='股票代码')
    name = Column(String(50), comment='股票名称')
    area = Column(String(20), comment='地域')
    industry = Column(String(50), comment='所属行业')
    market = Column(String(20), comment='市场类型')
    exchange = Column(String(20), comment='交易所代码')
    list_status = Column(String(2), comment='上市状态 L/D/G/P')
    list_date = Column(String(8), comment='上市日期 YYYYMMDD')
    delist_date = Column(String(8), comment='退市日期 YYYYMMDD')
    is_hs = Column(String(2), comment='是否沪深港通标的')
    act_name = Column(String(100), comment='实控人名称')
    act_ent_type = Column(String(100), comment='实控人企业性质')

    def __repr__(self):
        return f"<Stock(ts_code='{self.ts_code}', name='{self.name}')>"


class QuoteBase:
    """行情表公共字段（日线/周线/月线共用）"""

    ts_code = Column(String(20), nullable=False, comment='股票代码')
    trade_date = Column(String(8), nullable=False, comment='交易日期 YYYYMMDD')
    open = Column(Float, comment='开盘价')
    high = Column(Float, comment='最高价')
    low = Column(Float, comment='最低价')
    close = Column(Float, comment='收盘价')
    pre_close = Column(Float, comment='昨收价/上期收价')
    # change 是 MySQL 保留字，显式指定列名并依赖 SQLAlchemy 自动引用
    change = Column('change', Float, comment='涨跌额')
    pct_chg = Column(Float, comment='涨跌幅(%)')
    vol = Column(Float, comment='成交量(手)')
    amount = Column(Float, comment='成交额(千元)')


class DailyQuote(Base, QuoteBase):
    """日线行情表"""
    __tablename__ = 'daily_quotes'
    __table_args__ = (
        PrimaryKeyConstraint('ts_code', 'trade_date', name='pk_daily'),
    )


class WeeklyQuote(Base, QuoteBase):
    """周线行情表"""
    __tablename__ = 'weekly_quotes'
    __table_args__ = (
        PrimaryKeyConstraint('ts_code', 'trade_date', name='pk_weekly'),
    )


class MonthlyQuote(Base, QuoteBase):
    """月线行情表"""
    __tablename__ = 'monthly_quotes'
    __table_args__ = (
        PrimaryKeyConstraint('ts_code', 'trade_date', name='pk_monthly'),
    )