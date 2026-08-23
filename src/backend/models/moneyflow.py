"""
资金流向模型

个股资金流向（大单/小单成交、主力资金动向）
参考：requirements/data-sync/ds-006-money-flow.md
"""
from sqlalchemy import Column, BigInteger, String, Numeric, UniqueConstraint, Index
from .base import Base, TimestampMixin


class MoneyFlow(Base, TimestampMixin):
    """个股资金流向"""
    __tablename__ = 'moneyflow'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    trade_date = Column(String(8), nullable=False, comment='交易日期')

    # 小单(<5万)
    buy_sm_vol = Column(BigInteger, comment='小单买入量(手)')
    buy_sm_amount = Column(Numeric(20, 4), comment='小单买入金额(万元)')
    sell_sm_vol = Column(BigInteger, comment='小单卖出量(手)')
    sell_sm_amount = Column(Numeric(20, 4), comment='小单卖出金额(万元)')

    # 中单(5~20万)
    buy_md_vol = Column(BigInteger, comment='中单买入量(手)')
    buy_md_amount = Column(Numeric(20, 4), comment='中单买入金额(万元)')
    sell_md_vol = Column(BigInteger, comment='中单卖出量(手)')
    sell_md_amount = Column(Numeric(20, 4), comment='中单卖出金额(万元)')

    # 大单(20~100万)
    buy_lg_vol = Column(BigInteger, comment='大单买入量(手)')
    buy_lg_amount = Column(Numeric(20, 4), comment='大单买入金额(万元)')
    sell_lg_vol = Column(BigInteger, comment='大单卖出量(手)')
    sell_lg_amount = Column(Numeric(20, 4), comment='大单卖出金额(万元)')

    # 特大单(>=100万)
    buy_elg_vol = Column(BigInteger, comment='特大单买入量(手)')
    buy_elg_amount = Column(Numeric(20, 4), comment='特大单买入金额(万元)')
    sell_elg_vol = Column(BigInteger, comment='特大单卖出量(手)')
    sell_elg_amount = Column(Numeric(20, 4), comment='特大单卖出金额(万元)')

    # 净流入
    net_mf_vol = Column(BigInteger, comment='净流入量(手)')
    net_mf_amount = Column(Numeric(20, 4), comment='净流入额(万元)')

    __table_args__ = (
        UniqueConstraint('ts_code', 'trade_date', name='uk_moneyflow'),
        Index('idx_mf_trade_date', 'trade_date'),
        Index('idx_mf_ts_code', 'ts_code'),
    )

    def __repr__(self):
        return f"<MoneyFlow(ts_code='{self.ts_code}', trade_date='{self.trade_date}', net={self.net_mf_amount})>"