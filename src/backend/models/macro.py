"""
宏观经济数据模型（国内7个 + 国际3个）

设计要点：
- 无 ts_code（国家级数据），业务主键为 date/month/quarter
- 不设自增 id 主键（保证执行器 UPSERT 主键检测通过）
- 核心字段建列 + raw_data(JSON) 保留完整记录
参考：requirements/data-sync/ds-008-macro-economy.md
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, JSON, UniqueConstraint, Index
from datetime import datetime, timezone
from .base import Base


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MacroBase:
    """宏观表公共字段（不含自增主键）"""
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    raw_data = Column(JSON, comment='Tushare完整原始记录')


# ==================== 国内宏观 ====================

class MacroLpr(MacroBase, Base):
    """LPR贷款基础利率（日频）"""
    __tablename__ = 'macro_lpr'
    date = Column(String(8), primary_key=True, comment='日期')
    y1 = Column(Numeric(10, 4), comment='1年期贷款利率%')
    y5 = Column(Numeric(10, 4), comment='5年期贷款利率%')


class MacroShibor(MacroBase, Base):
    """Shibor利率（日频）"""
    __tablename__ = 'macro_shibor'
    date = Column(String(8), primary_key=True, comment='日期')
    on_rate = Column(Numeric(10, 4), comment='隔夜%')
    w1 = Column(Numeric(10, 4), comment='1周%')
    w2 = Column(Numeric(10, 4), comment='2周%')
    m1 = Column(Numeric(10, 4), comment='1个月%')
    m3 = Column(Numeric(10, 4), comment='3个月%')
    m6 = Column(Numeric(10, 4), comment='6个月%')
    m9 = Column(Numeric(10, 4), comment='9个月%')
    y1 = Column(Numeric(10, 4), comment='1年%')


class MacroGdp(MacroBase, Base):
    """GDP数据（季频）"""
    __tablename__ = 'macro_gdp'
    quarter = Column(String(8), primary_key=True, comment='季度 如2019Q1')
    gdp = Column(Numeric(20, 4), comment='GDP累计值(亿元)')
    gdp_yoy = Column(Numeric(10, 4), comment='当季同比增速%')
    pi = Column(Numeric(20, 4), comment='第一产业累计值')
    pi_yoy = Column(Numeric(10, 4), comment='第一产业同比%')
    si = Column(Numeric(20, 4), comment='第二产业累计值')
    si_yoy = Column(Numeric(10, 4), comment='第二产业同比%')
    ti = Column(Numeric(20, 4), comment='第三产业累计值')
    ti_yoy = Column(Numeric(10, 4), comment='第三产业同比%')


class MacroCpi(MacroBase, Base):
    """居民消费价格指数（月频）"""
    __tablename__ = 'macro_cpi'
    month = Column(String(6), primary_key=True, comment='月份 YYYYMM')
    nt_val = Column(Numeric(10, 4), comment='全国当月值')
    nt_yoy = Column(Numeric(10, 4), comment='全国同比%')
    nt_mom = Column(Numeric(10, 4), comment='全国环比%')
    nt_accu = Column(Numeric(10, 4), comment='全国累计值')


class MacroPpi(MacroBase, Base):
    """工业生产者出厂价格指数（月频）"""
    __tablename__ = 'macro_ppi'
    month = Column(String(6), primary_key=True, comment='月份 YYYYMM')
    nt_val = Column(Numeric(10, 4), comment='当月值')
    nt_yoy = Column(Numeric(10, 4), comment='同比%')
    nt_mom = Column(Numeric(10, 4), comment='环比%')
    nt_accu = Column(Numeric(10, 4), comment='累计值')


class MacroPmi(MacroBase, Base):
    """采购经理指数（月频）"""
    __tablename__ = 'macro_pmi'
    month = Column(String(6), primary_key=True, comment='月份 YYYYMM')
    pmi = Column(Numeric(10, 4), comment='制造业PMI')
    pmi_non_mfg = Column(Numeric(10, 4), comment='非制造业PMI（如有）')
    pmi_cain = Column(Numeric(10, 4), comment='财新制造业PMI（如有）')


class MacroM(MacroBase, Base):
    """货币供应量（月频）"""
    __tablename__ = 'macro_m'
    month = Column(String(6), primary_key=True, comment='月份 YYYYMM')
    m0 = Column(Numeric(20, 4), comment='M0(万亿元)')
    m1 = Column(Numeric(20, 4), comment='M1(万亿元)')
    m2 = Column(Numeric(20, 4), comment='M2(万亿元)')
    m0_yoy = Column(Numeric(10, 4), comment='M0同比%')
    m1_yoy = Column(Numeric(10, 4), comment='M1同比%')
    m2_yoy = Column(Numeric(10, 4), comment='M2同比%')


# ==================== 国际宏观（美国利率） ====================

class MacroUsTycr(MacroBase, Base):
    """美国国债收益率曲线（日频，13个期限）"""
    __tablename__ = 'macro_us_tycr'
    date = Column(String(8), primary_key=True, comment='日期')
    m1 = Column(Numeric(10, 4), comment='1月期%')
    m2 = Column(Numeric(10, 4), comment='2月期%')
    m3 = Column(Numeric(10, 4), comment='3月期%')
    m4 = Column(Numeric(10, 4), comment='4月期%')
    m6 = Column(Numeric(10, 4), comment='6月期%')
    y1 = Column(Numeric(10, 4), comment='1年期%')
    y2 = Column(Numeric(10, 4), comment='2年期%')
    y3 = Column(Numeric(10, 4), comment='3年期%')
    y5 = Column(Numeric(10, 4), comment='5年期%')
    y7 = Column(Numeric(10, 4), comment='7年期%')
    y10 = Column(Numeric(10, 4), comment='10年期%')
    y20 = Column(Numeric(10, 4), comment='20年期%')
    y30 = Column(Numeric(10, 4), comment='30年期%')


class MacroUsTbr(MacroBase, Base):
    """美国短期国债利率（日频，3月期/1年期为主）"""
    __tablename__ = 'macro_us_tbr'
    date = Column(String(8), primary_key=True, comment='日期')
    m3 = Column(Numeric(10, 4), comment='3月期%')
    m6 = Column(Numeric(10, 4), comment='6月期%')
    y1 = Column(Numeric(10, 4), comment='1年期%')


class MacroUsTlr(MacroBase, Base):
    """美国国债长期利率（日频，10/20/30年为主）"""
    __tablename__ = 'macro_us_tlr'
    date = Column(String(8), primary_key=True, comment='日期')
    y10 = Column(Numeric(10, 4), comment='10年期%')
    y20 = Column(Numeric(10, 4), comment='20年期%')
    y30 = Column(Numeric(10, 4), comment='30年期%')