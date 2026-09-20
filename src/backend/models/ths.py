"""
同花顺（THS）数据模型

- ths_valuation_snapshot 估值快照（PE/PB/PS/PCF）
- ths_index 同花顺指数（行业/概念）
- ths_index_constituent 指数成分股
- ths_index_quotes 指数日K
参考：requirements/data-sync/ds-009-ths.md
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, SmallInteger, Numeric, DateTime, JSON,
    UniqueConstraint, Index, PrimaryKeyConstraint
)
from .base import Base, TimestampMixin


class ThsValuationSnapshot(Base, TimestampMixin):
    """同花顺估值快照"""
    __tablename__ = 'ths_valuation_snapshot'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thscode = Column(String(20), nullable=False, comment='同花顺代码 如600519.SH')
    trade_date = Column(String(8), nullable=False, comment='快照日 yyyyMMdd')
    pe_ttm = Column(Numeric(20, 4), comment='市盈率TTM')
    pe_mrq = Column(Numeric(20, 4), comment='市盈率MRQ')
    pb_mrq = Column(Numeric(20, 4), comment='市净率MRQ')
    ps_ttm = Column(Numeric(20, 4), comment='市销率TTM')
    pcf_ttm = Column(Numeric(20, 4), comment='市现率TTM')
    raw_data = Column(JSON, comment='完整原始记录')

    __table_args__ = (
        UniqueConstraint('thscode', 'trade_date', name='uk_ths_val'),
        Index('idx_ths_val_date', 'trade_date'),
    )


class ThsIndex(Base, TimestampMixin):
    """同花顺指数（行业/概念/标准指数）"""
    __tablename__ = 'ths_index'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thscode = Column(String(30), nullable=False, unique=True, comment='指数代码 如90.BK1027')
    name = Column(String(100), comment='指数名称')
    tag = Column(String(20), comment='分类:行业/概念/沪深300等')
    raw_data = Column(JSON, comment='完整原始记录')


class ThsIndexConstituent(Base, TimestampMixin):
    """同花顺指数成分股"""
    __tablename__ = 'ths_index_constituent'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    index_code = Column(String(30), nullable=False, comment='指数代码')
    stock_code = Column(String(20), nullable=False, comment='个股代码 如600519.SH')
    raw_data = Column(JSON, comment='完整原始记录')

    __table_args__ = (
        UniqueConstraint('index_code', 'stock_code', name='uk_ths_const'),
        Index('idx_ths_const_index', 'index_code'),
    )


class ThsIndexQuote(Base, TimestampMixin):
    """同花顺指数日K线"""
    __tablename__ = 'ths_index_quotes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    thscode = Column(String(30), nullable=False, comment='指数代码')
    trade_date = Column(String(8), nullable=False, comment='交易日 yyyyMMdd')
    open = Column(Numeric(20, 4), comment='开盘价')
    high = Column(Numeric(20, 4), comment='最高价')
    low = Column(Numeric(20, 4), comment='最低价')
    close = Column(Numeric(20, 4), comment='收盘价')
    vol = Column(BigInteger, comment='成交量(手)')
    amount = Column(Numeric(20, 4), comment='成交额(元)')
    pct_chg = Column(Numeric(10, 4), comment='涨跌幅%')
    raw_data = Column(JSON, comment='完整原始记录')

    __table_args__ = (
        UniqueConstraint('thscode', 'trade_date', name='uk_ths_idx_q'),
        Index('idx_ths_idx_q_code_date', 'thscode', 'trade_date'),
    )