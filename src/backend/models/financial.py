"""
财务数据模型

Tushare 财务接口同步数据落库的目标表：
- fin_income 利润表
- fin_balancesheet 资产负债表
- fin_cashflow 现金流量表
- fin_indicator 财务指标
- fin_forecast 业绩预告
- fin_express 业绩快报
- fin_dividend 分红送股
- fin_mainbz 主营业务构成
- fin_disclosure 财报披露计划

策略：核心字段建独立列（便于查询），raw_data(JSON) 存 Tushare 完整记录
参考：requirements/data-sync/ds-005-financial-data.md
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, BigInteger, String, Numeric, DateTime, JSON,
    UniqueConstraint, Index
)
from .base import Base, TimestampMixin


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class FinBase(Base, TimestampMixin):
    """财务表公共字段（抽象基类，不建表，子类继承列）"""
    __abstract__ = True
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, comment='股票代码')
    raw_data = Column(JSON, comment='Tushare完整原始记录JSON')


class FinIncome(FinBase):
    """利润表"""
    __tablename__ = 'fin_income'
    end_date = Column(String(8), nullable=False, comment='报告期')
    report_type = Column(String(2), default='1', comment='报告类型')
    ann_date = Column(String(8), comment='公告日')
    total_revenue = Column(Numeric(20, 4), comment='营业总收入')
    revenue = Column(Numeric(20, 4), comment='营业收入')
    operate_profit = Column(Numeric(20, 4), comment='营业利润')
    total_profit = Column(Numeric(20, 4), comment='利润总额')
    n_income = Column(Numeric(20, 4), comment='净利润')
    n_income_attr_p = Column(Numeric(20, 4), comment='归母净利润')
    basic_eps = Column(Numeric(20, 4), comment='基本每股收益')
    diluted_eps = Column(Numeric(20, 4), comment='稀释每股收益')
    rd_exp = Column(Numeric(20, 4), comment='研发费用')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', 'report_type', name='uk_income'),
        Index('idx_income_end', 'end_date'),
    )


class FinBalancesheet(FinBase):
    """资产负债表"""
    __tablename__ = 'fin_balancesheet'
    end_date = Column(String(8), nullable=False, comment='报告期')
    report_type = Column(String(2), default='1', comment='报告类型')
    ann_date = Column(String(8), comment='公告日')
    total_assets = Column(Numeric(20, 4), comment='资产总计')
    total_liab = Column(Numeric(20, 4), comment='负债合计')
    total_hldr_eqy_inc_min_int = Column(Numeric(20, 4), comment='股东权益合计(含少数)')
    money_cap = Column(Numeric(20, 4), comment='货币资金')
    accounts_receiv = Column(Numeric(20, 4), comment='应收账款')
    inventories = Column(Numeric(20, 4), comment='存货')
    fix_assets = Column(Numeric(20, 4), comment='固定资产')
    goodwill = Column(Numeric(20, 4), comment='商誉')
    st_borr = Column(Numeric(20, 4), comment='短期借款')
    lt_borr = Column(Numeric(20, 4), comment='长期借款')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', 'report_type', name='uk_balancesheet'),
        Index('idx_bs_end', 'end_date'),
    )


class FinCashflow(FinBase):
    """现金流量表"""
    __tablename__ = 'fin_cashflow'
    end_date = Column(String(8), nullable=False, comment='报告期')
    report_type = Column(String(2), default='1', comment='报告类型')
    ann_date = Column(String(8), comment='公告日')
    net_profit = Column(Numeric(20, 4), comment='净利润')
    n_cashflow_act = Column(Numeric(20, 4), comment='经营活动现金流量净额')
    n_cashflow_inv_act = Column(Numeric(20, 4), comment='投资活动现金流量净额')
    n_cash_flows_fnc_act = Column(Numeric(20, 4), comment='筹资活动现金流量净额')
    free_cashflow = Column(Numeric(20, 4), comment='企业自由现金流量')
    c_fr_sale_sg = Column(Numeric(20, 4), comment='销售商品提供劳务收到的现金')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', 'report_type', name='uk_cashflow'),
        Index('idx_cf_end', 'end_date'),
    )


class FinIndicator(FinBase):
    """财务指标"""
    __tablename__ = 'fin_indicator'
    end_date = Column(String(8), nullable=False, comment='报告期')
    ann_date = Column(String(8), comment='公告日')
    eps = Column(Numeric(20, 4), comment='基本每股收益')
    bps = Column(Numeric(20, 4), comment='每股净资产')
    roe = Column(Numeric(20, 4), comment='净资产收益率')
    roe_waa = Column(Numeric(20, 4), comment='加权平均净资产收益率')
    roa = Column(Numeric(20, 4), comment='总资产报酬率')
    netprofit_margin = Column(Numeric(20, 4), comment='销售净利率')
    grossprofit_margin = Column(Numeric(20, 4), comment='销售毛利率')
    debt_to_assets = Column(Numeric(20, 4), comment='资产负债率')
    netprofit_yoy = Column(Numeric(20, 4), comment='归母净利润同比增长率%')
    or_yoy = Column(Numeric(20, 4), comment='营业收入同比增长率%')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', name='uk_indicator'),
        Index('idx_ind_end', 'end_date'),
    )


class FinForecast(FinBase):
    """业绩预告"""
    __tablename__ = 'fin_forecast'
    end_date = Column(String(8), nullable=False, comment='报告期')
    ann_date = Column(String(8), comment='公告日')
    type = Column(String(20), comment='业绩预告类型(预增/预减/续盈/略增/略减等)')
    p_change_min = Column(Numeric(20, 4), comment='预告净利润变动幅度下限%')
    p_change_max = Column(Numeric(20, 4), comment='预告净利润变动幅度上限%')
    net_profit_min = Column(Numeric(20, 4), comment='预告净利润下限(万元)')
    net_profit_max = Column(Numeric(20, 4), comment='预告净利润上限(万元)')
    last_parent_net = Column(Numeric(20, 4), comment='上年同期归属母公司净利润')
    summary = Column(String(500), comment='业绩预告内容')
    __table_args__ = (
        UniqueConstraint('ts_code', 'ann_date', 'end_date', name='uk_forecast'),
        Index('idx_fc_end', 'end_date'),
    )


class FinExpress(FinBase):
    """业绩快报"""
    __tablename__ = 'fin_express'
    end_date = Column(String(8), nullable=False, comment='报告期')
    ann_date = Column(String(8), comment='公告日')
    revenue = Column(Numeric(20, 4), comment='营业收入')
    operate_profit = Column(Numeric(20, 4), comment='营业利润')
    total_profit = Column(Numeric(20, 4), comment='利润总额')
    n_income = Column(Numeric(20, 4), comment='净利润')
    total_assets = Column(Numeric(20, 4), comment='总资产')
    basic_eps = Column(Numeric(20, 4), comment='基本每股收益')
    diluted_eps = Column(Numeric(20, 4), comment='稀释每股收益')
    yoy_net_profit = Column(Numeric(20, 4), comment='同比净利润增长率%')
    __table_args__ = (
        UniqueConstraint('ts_code', 'ann_date', 'end_date', name='uk_express'),
        Index('idx_exp_end', 'end_date'),
    )


class FinDividend(FinBase):
    """分红送股"""
    __tablename__ = 'fin_dividend'
    end_date = Column(String(8), nullable=False, comment='分红年度')
    ann_date = Column(String(8), comment='公告日')
    div_proc = Column(String(20), comment='实施进度')
    stk_div = Column(Numeric(20, 4), comment='每股送转股')
    cash_div = Column(Numeric(20, 4), comment='每股分红(税后)')
    record_date = Column(String(8), comment='股权登记日')
    ex_date = Column(String(8), comment='除权除息日')
    pay_date = Column(String(8), comment='派息日')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', 'ann_date', name='uk_dividend'),
        Index('idx_div_end', 'end_date'),
    )


class FinMainbz(FinBase):
    """主营业务构成"""
    __tablename__ = 'fin_mainbz'
    end_date = Column(String(8), nullable=False, comment='报告期')
    bz_item = Column(String(100), nullable=False, comment='主营业务来源')
    bz_code = Column(String(2), comment='类型(P产品/D地区/I行业)')
    bz_sales = Column(Numeric(20, 4), comment='主营业务收入')
    bz_profit = Column(Numeric(20, 4), comment='主营业务利润')
    bz_cost = Column(Numeric(20, 4), comment='主营业务成本')
    curr_type = Column(String(10), comment='货币代码')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', 'bz_item', name='uk_mainbz'),
        Index('idx_mb_end', 'end_date'),
    )


class FinDisclosure(FinBase):
    """财报披露计划"""
    __tablename__ = 'fin_disclosure'
    end_date = Column(String(8), nullable=False, comment='报告期')
    ann_date = Column(String(8), comment='最新披露公告日')
    pre_date = Column(String(8), comment='预计披露日期')
    actual_date = Column(String(8), comment='实际披露日期')
    modify_date = Column(String(500), comment='披露日期修正记录')
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', name='uk_disclosure'),
        Index('idx_disc_end', 'end_date'),
    )