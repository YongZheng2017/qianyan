"""
板块数据模型（AKShare 来源）

- board_industry 行业板块列表
- board_industry_quotes 行业板块行情（日/周/月K）
参考：requirements/data-sync/ds-007-akshare-board.md
"""
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, UniqueConstraint, Index
from .base import Base, TimestampMixin


class BoardIndustry(Base, TimestampMixin):
    """行业板块列表"""
    __tablename__ = 'board_industry'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_name = Column(String(50), nullable=False, unique=True, comment='板块名称')
    board_code = Column(String(20), comment='板块代码')
    latest_price = Column(Numeric(10, 4), comment='最新价')
    change_amount = Column(Numeric(10, 4), comment='涨跌额')
    pct_chg = Column(Numeric(10, 4), comment='涨跌幅%')
    total_market_cap = Column(Numeric(20, 4), comment='总市值')
    turnover = Column(Numeric(10, 4), comment='换手率%')
    up_count = Column(Integer, comment='上涨家数')
    down_count = Column(Integer, comment='下跌家数')
    leader_stock = Column(String(50), comment='领涨股票')
    leader_pct_chg = Column(Numeric(10, 4), comment='领涨涨跌幅%')

    def __repr__(self):
        return f"<BoardIndustry(name='{self.board_name}', code='{self.board_code}')>"


class BoardIndustryQuote(Base, TimestampMixin):
    """行业板块行情（日/周/月K）"""
    __tablename__ = 'board_industry_quotes'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    board_name = Column(String(50), nullable=False, comment='板块名称')
    trade_date = Column(String(8), nullable=False, comment='交易日 YYYYMMDD')
    period = Column(String(4), default='日k', comment='周期:日k/周k/月k')
    open = Column(Numeric(10, 4), comment='开盘价')
    high = Column(Numeric(10, 4), comment='最高价')
    low = Column(Numeric(10, 4), comment='最低价')
    close = Column(Numeric(10, 4), comment='收盘价')
    pct_chg = Column(Numeric(10, 4), comment='涨跌幅%')
    # change 是 MySQL 保留字，显式指定列名
    change = Column('change', Numeric(10, 4), comment='涨跌额')
    vol = Column(BigInteger, comment='成交量(手)')
    amount = Column(Numeric(20, 4), comment='成交额(元)')
    amplitude = Column(Numeric(10, 4), comment='振幅%')
    turnover = Column(Numeric(10, 4), comment='换手率%')

    __table_args__ = (
        UniqueConstraint('board_name', 'trade_date', 'period', name='uk_board_quote'),
        Index('idx_bq_board_date', 'board_name', 'trade_date'),
    )

    def __repr__(self):
        return f"<BoardIndustryQuote(board='{self.board_name}', date='{self.trade_date}', period='{self.period}')>"