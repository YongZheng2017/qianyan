"""
宏观经济指标查询服务（只读）

统一查询 10 张宏观表（macro_*），供分析端展示指标趋势。
表与指标映射：见 models/macro.py 与 ds-008 需求
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..models import (
    MacroLpr, MacroShibor, MacroGdp, MacroCpi, MacroPpi, MacroPmi, MacroM,
    MacroUsTycr, MacroUsTbr, MacroUsTlr,
)
from ..schemas.fundflow import MacroSeriesResponse


# 指标 → (模型, 日期列名, 可选值字段)
MACRO_INDICATORS = {
    "lpr": (MacroLpr, "date", ["y1", "y5"]),
    "shibor": (MacroShibor, "date", ["on_rate", "w1", "m1", "m3", "m6", "y1"]),
    "gdp": (MacroGdp, "quarter", ["gdp", "gdp_yoy", "pi_yoy", "si_yoy", "ti_yoy"]),
    "cpi": (MacroCpi, "month", ["nt_val", "nt_yoy", "nt_mom", "nt_accu"]),
    "ppi": (MacroPpi, "month", ["nt_val", "nt_yoy", "nt_mom", "nt_accu"]),
    "pmi": (MacroPmi, "month", ["pmi"]),
    "m": (MacroM, "month", ["m0", "m1", "m2", "m0_yoy", "m1_yoy", "m2_yoy"]),
    "us_tycr": (MacroUsTycr, "date", ["m3", "y1", "y2", "y5", "y10", "y30"]),
    "us_tbr": (MacroUsTbr, "date", ["m3", "m6", "y1"]),
    "us_tlr": (MacroUsTlr, "date", ["y10", "y20", "y30"]),
}

INDICATOR_NAMES = {
    "lpr": "LPR贷款基础利率", "shibor": "Shibor利率", "gdp": "GDP",
    "cpi": "CPI居民消费价格指数", "ppi": "PPI工业品出厂价格指数",
    "pmi": "PMI采购经理指数", "m": "货币供应量",
    "us_tycr": "美国国债收益率曲线", "us_tbr": "美国短期国债利率", "us_tlr": "美国国债长期利率",
}


class MacroService:
    """宏观指标查询服务"""

    @staticmethod
    def list_indicators() -> list:
        """所有可查询指标及字段"""
        return [
            {"key": k, "name": INDICATOR_NAMES[k], "date_key": v[1], "fields": v[2]}
            for k, v in MACRO_INDICATORS.items()
        ]

    @staticmethod
    async def get_series(
        db: AsyncSession, indicator: str, field: str, limit: int = 120
    ) -> MacroSeriesResponse:
        """查询指定指标的某字段时序（升序返回）"""
        cfg = MACRO_INDICATORS.get(indicator)
        if not cfg:
            raise ValueError(f"未知宏观指标: {indicator}")
        model, date_col_name, fields = cfg
        if field not in fields:
            raise ValueError(f"指标 {indicator} 不支持字段 {field}，可选: {fields}")

        date_col = getattr(model, date_col_name)
        val_col = getattr(model, field)
        rows = (await db.execute(
            select(date_col, val_col).order_by(date_col.desc()).limit(limit)
        )).all()
        rows.reverse()

        return MacroSeriesResponse(
            indicator=indicator, field=field,
            dates=[r[0] for r in rows],
            values=[(float(r[1]) if r[1] is not None else None) for r in rows],
        )