"""
基本面分析服务（只读）

从已同步的财务表聚合数据，供分析端展示。
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import (
    Stock, FinIncome, FinBalancesheet, FinCashflow, FinIndicator, DailyQuote,
)
from ..schemas.fundamental import (
    StockBrief, IndicatorCard, RiskAlert, LatestStatement,
    OverviewResponse, StatementResponse, IndicatorGroupResponse, ValuationResponse,
)


# ===== 报表科目定义（key=字段名, name=中文名）=====
STATEMENT_ITEMS = {
    "income": [
        ("total_revenue", "营业总收入"), ("revenue", "营业收入"),
        ("operate_profit", "营业利润"), ("total_profit", "利润总额"),
        ("n_income", "净利润"), ("n_income_attr_p", "归母净利润"),
        ("basic_eps", "基本每股收益"), ("diluted_eps", "稀释每股收益"),
        ("rd_exp", "研发费用"),
    ],
    "balancesheet": [
        ("total_assets", "资产总计"), ("total_liab", "负债合计"),
        ("total_hldr_eqy_inc_min_int", "股东权益合计"), ("money_cap", "货币资金"),
        ("accounts_receiv", "应收账款"), ("inventories", "存货"),
        ("fix_assets", "固定资产"), ("goodwill", "商誉"),
        ("st_borr", "短期借款"), ("lt_borr", "长期借款"),
    ],
    "cashflow": [
        ("net_profit", "净利润"), ("n_cashflow_act", "经营活动现金流净额"),
        ("n_cashflow_inv_act", "投资活动现金流净额"),
        ("n_cash_flows_fnc_act", "筹资活动现金流净额"),
        ("free_cashflow", "企业自由现金流"),
        ("c_fr_sale_sg", "销售商品提供劳务收到的现金"),
    ],
}
STATEMENT_MODEL = {"income": FinIncome, "balancesheet": FinBalancesheet, "cashflow": FinCashflow}

# ===== 能力指标分组 =====
INDICATOR_GROUPS = [
    ("profitability", "盈利能力", [
        ("roe", "净资产收益率(ROE)"), ("roe_waa", "加权平均ROE"),
        ("roa", "总资产报酬率(ROA)"),
        ("grossprofit_margin", "销售毛利率(%)"), ("netprofit_margin", "销售净利率(%)"),
    ]),
    ("growth", "成长能力", [
        ("or_yoy", "营业收入同比增长(%)"), ("netprofit_yoy", "归母净利润同比增长(%)"),
        ("basic_eps_yoy", "基本每股收益同比增长(%)"),
    ]),
    ("operation", "营运能力", [
        ("ar_turn", "应收账款周转率"), ("inv_turn", "存货周转率"),
        ("assets_turn", "总资产周转率"),
    ]),
    ("solvency", "偿债能力", [
        ("current_ratio", "流动比率"), ("quick_ratio", "速动比率"),
        ("debt_to_assets", "资产负债率"),
    ]),
]


class FundamentalService:
    """基本面分析服务"""

    @staticmethod
    async def _get_stock_brief(db: AsyncSession, ts_code: str) -> StockBrief:
        s = (await db.execute(select(Stock).where(Stock.ts_code == ts_code))).scalar_one_or_none()
        return StockBrief(ts_code=ts_code, name=(s.name if s and s.name else ts_code), industry=(s.industry if s else None))

    @staticmethod
    async def _latest_indicator(db: AsyncSession, ts_code: str, limit: int = 8) -> List[FinIndicator]:
        r = await db.execute(
            select(FinIndicator).where(FinIndicator.ts_code == ts_code)
            .order_by(FinIndicator.end_date.desc()).limit(limit)
        )
        return list(r.scalars().all())

    @staticmethod
    async def _latest_close(db: AsyncSession, ts_code: str) -> Optional[DailyQuote]:
        r = await db.execute(
            select(DailyQuote).where(DailyQuote.ts_code == ts_code)
            .order_by(DailyQuote.trade_date.desc()).limit(1)
        )
        return r.scalar_one_or_none()

    # ---------- 概览 ----------
    @staticmethod
    async def get_overview(db: AsyncSession, ts_code: str) -> OverviewResponse:
        brief = await FundamentalService._get_stock_brief(db, ts_code)
        inds = await FundamentalService._latest_indicator(db, ts_code, 8)
        if not inds:
            return OverviewResponse(
                stock=brief, latest_period=None, indicators=[], latest_statement=None,
                risk_alerts=[RiskAlert(level="warning", message="未同步该股票的财务数据，请先在管理端同步")],
            )

        latest = inds[0]
        prev = inds[1] if len(inds) > 1 else None

        # 最新财报摘要（合并 income/balancesheet/cashflow 最新期）
        inc = (await db.execute(select(FinIncome).where(FinIncome.ts_code == ts_code, FinIncome.end_date == latest.end_date).limit(1))).scalar_one_or_none()
        bs = (await db.execute(select(FinBalancesheet).where(FinBalancesheet.ts_code == ts_code, FinBalancesheet.end_date == latest.end_date).limit(1))).scalar_one_or_none()
        cf = (await db.execute(select(FinCashflow).where(FinCashflow.ts_code == ts_code, FinCashflow.end_date == latest.end_date).limit(1))).scalar_one_or_none()
        latest_statement = LatestStatement(
            end_date=latest.end_date,
            total_revenue=getattr(inc, "total_revenue", None) if inc else None,
            n_income=getattr(inc, "n_income", None) if inc else None,
            n_income_attr_p=getattr(inc, "n_income_attr_p", None) if inc else None,
            operate_profit=getattr(inc, "operate_profit", None) if inc else None,
            n_cashflow_act=getattr(cf, "n_cashflow_act", None) if cf else None,
            total_assets=getattr(bs, "total_assets", None) if bs else None,
            total_liab=getattr(bs, "total_liab", None) if bs else None,
        )

        # 指标卡片
        def card(key, name, val, yoy_val=None):
            return IndicatorCard(key=key, name=name, value=val, yoy=yoy_val)
        indicators = [
            card("roe", "ROE", latest.roe),
            card("grossprofit_margin", "毛利率(%)", latest.grossprofit_margin),
            card("netprofit_margin", "净利率(%)", latest.netprofit_margin),
            card("debt_to_assets", "资产负债率", latest.debt_to_assets),
            card("or_yoy", "营收增长(%)", latest.or_yoy),
            card("netprofit_yoy", "净利润增长(%)", latest.netprofit_yoy),
        ]

        # 风险检测
        risks: List[RiskAlert] = []
        if latest.debt_to_assets and latest.debt_to_assets > 0.75:
            risks.append(RiskAlert(level="warning", message=f"资产负债率 {latest.debt_to_assets:.1%}，偏高(>75%)，偿债压力较大"))
        if latest.netprofit_yoy is not None and latest.netprofit_yoy < 0:
            risks.append(RiskAlert(level="danger", message=f"净利润同比下降 {latest.netprofit_yoy:.1f}%，盈利下滑"))
        if prev and prev.roe and latest.roe and latest.roe < prev.roe:
            risks.append(RiskAlert(level="warning", message=f"ROE 由 {prev.roe:.2f} 降至 {latest.roe:.2f}，盈利能力下滑"))
        if latest_statement.n_income and latest_statement.n_cashflow_act is not None:
            if latest_statement.n_income > 0 and latest_statement.n_cashflow_act / latest_statement.n_income < 0.7:
                risks.append(RiskAlert(level="warning", message="经营现金流/净利润 < 0.7，关注利润质量"))

        return OverviewResponse(
            stock=brief, latest_period=latest.end_date,
            indicators=indicators, latest_statement=latest_statement, risk_alerts=risks,
        )

    # ---------- 三大报表 ----------
    @staticmethod
    async def get_statements(db: AsyncSession, ts_code: str, stmt_type: str, periods: int = 8) -> StatementResponse:
        model = STATEMENT_MODEL.get(stmt_type)
        items = STATEMENT_ITEMS.get(stmt_type, [])
        if not model:
            return StatementResponse(type=stmt_type, headers=[], rows=[])

        rows_orm = (await db.execute(
            select(model).where(model.ts_code == ts_code).order_by(model.end_date.desc()).limit(periods)
        )).scalars().all()
        rows_orm = list(reversed(rows_orm))  # 升序

        headers = [r.end_date for r in rows_orm]
        result_rows = []
        for key, name in items:
            values = [getattr(r, key, None) for r in rows_orm]
            result_rows.append({"key": key, "name": name, "values": values})
        return StatementResponse(type=stmt_type, headers=headers, rows=result_rows)

    # ---------- 能力指标 ----------
    @staticmethod
    async def get_indicators(db: AsyncSession, ts_code: str, periods: int = 12) -> IndicatorGroupResponse:
        inds = await FundamentalService._latest_indicator(db, ts_code, periods)
        inds = list(reversed(inds))  # 升序
        headers = [i.end_date for i in inds]
        groups = []
        for gkey, gname, items in INDICATOR_GROUPS:
            group_items = []
            for key, name in items:
                group_items.append({"key": key, "name": name, "values": [getattr(i, key, None) for i in inds]})
            groups.append({"key": gkey, "name": gname, "items": group_items})
        return IndicatorGroupResponse(headers=headers, groups=groups)

    # ---------- 估值 ----------
    @staticmethod
    async def get_valuation(db: AsyncSession, ts_code: str) -> ValuationResponse:
        brief = await FundamentalService._get_stock_brief(db, ts_code)
        dq = await FundamentalService._latest_close(db, ts_code)
        inds = await FundamentalService._latest_indicator(db, ts_code, 1)

        if not dq or not inds:
            return ValuationResponse(
                ts_code=ts_code, name=brief.name,
                note="缺少最新股价或财务数据，无法计算估值。请确保已同步该股票的日线行情和财务指标",
            )

        latest = inds[0]
        close = dq.close
        eps = latest.eps
        bps = latest.bps
        yoy = latest.netprofit_yoy

        pe = round(close / eps, 2) if (eps and eps != 0) else None
        pb = round(close / bps, 2) if (bps and bps != 0) else None
        peg = round(pe / yoy, 2) if (pe and yoy and yoy != 0) else None

        # 结论提示
        conclusion_parts = []
        if pb and pb < 1:
            conclusion_parts.append("PB<1（破净），账面价值高于股价")
        if pe and yoy and peg:
            if peg < 1:
                conclusion_parts.append(f"PEG={peg}(<1)，考虑成长性后估值偏低")
            elif peg > 2:
                conclusion_parts.append(f"PEG={peg}(>2)，估值可能偏高")
        if not conclusion_parts:
            conclusion_parts.append("估值处于合理区间，建议结合历史分位与同行业对比判断")
        conclusion = "；".join(conclusion_parts)

        return ValuationResponse(
            ts_code=ts_code, name=brief.name, close=close, trade_date=dq.trade_date,
            eps=eps, bps=bps, netprofit_yoy=yoy, pe=pe, pb=pb, peg=peg,
            conclusion=conclusion,
            note="历史分位与行业对比需更多数据，暂未提供" if pe else None,
        )