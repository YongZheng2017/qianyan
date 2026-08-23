"""
资金趋势分析服务（只读）

数据来源：moneyflow（个股资金流向，DS-006）
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, asc
from ..models import MoneyFlow, Stock, DailyQuote
from ..schemas.fundflow import (
    MfDailyItem, StockFlowResponse, MarketFlowItem, MarketFlowResponse,
    RankItem, RankResponse,
)


class FundFlowService:
    """资金趋势分析服务"""

    @staticmethod
    async def get_stock_flow(
        db: AsyncSession, ts_code: str, limit: int = 60
    ) -> StockFlowResponse:
        """个股资金流向时序（净流入 + 大单/特大单买卖 + 收盘价叠加）"""
        # 名称
        s = (await db.execute(select(Stock).where(Stock.ts_code == ts_code))).scalar_one_or_none()
        name = (s.name if s and s.name else ts_code)

        rows = (await db.execute(
            select(MoneyFlow, DailyQuote.close)
            .outerjoin(DailyQuote, and_(
                DailyQuote.ts_code == MoneyFlow.ts_code,
                DailyQuote.trade_date == MoneyFlow.trade_date,
            ))
            .where(MoneyFlow.ts_code == ts_code)
            .order_by(MoneyFlow.trade_date.desc()).limit(limit)
        )).all()
        rows.reverse()  # 升序

        items = [MfDailyItem(
            trade_date=mf.trade_date,
            net_mf_amount=float(mf.net_mf_amount) if mf.net_mf_amount is not None else None,
            buy_elg_amount=float(mf.buy_elg_amount) if mf.buy_elg_amount is not None else None,
            sell_elg_amount=float(mf.sell_elg_amount) if mf.sell_elg_amount is not None else None,
            buy_lg_amount=float(mf.buy_lg_amount) if mf.buy_lg_amount is not None else None,
            sell_lg_amount=float(mf.sell_lg_amount) if mf.sell_lg_amount is not None else None,
            close=float(close) if close is not None else None,
        ) for mf, close in rows]

        return StockFlowResponse(
            ts_code=ts_code, name=name,
            latest=(items[-1] if items else None), items=items,
        )

    @staticmethod
    async def get_market_flow(db: AsyncSession, limit: int = 30) -> MarketFlowResponse:
        """全市场资金总览（按交易日聚合净流入 + 涨跌家数近似）"""
        rows = (await db.execute(
            select(
                MoneyFlow.trade_date,
                func.sum(MoneyFlow.net_mf_amount).label('total_net'),
                func.sum(case_pos()).label('up_cnt'),
                func.sum(case_neg()).label('down_cnt'),
            )
            .group_by(MoneyFlow.trade_date)
            .order_by(MoneyFlow.trade_date.desc()).limit(limit)
        )).all()
        rows.reverse()

        items = [MarketFlowItem(
            trade_date=r[0],
            net_mf_amount=float(r[1] or 0),
            up_count=int(r[2] or 0),
            down_count=int(r[3] or 0),
        ) for r in rows]
        return MarketFlowResponse(items=items)

    @staticmethod
    async def get_rank(
        db: AsyncSession, trade_date: Optional[str] = None, top: int = 10
    ) -> RankResponse:
        """净流入/净流出排行（默认最新有数据的交易日）"""
        if not trade_date:
            latest = (await db.execute(
                select(MoneyFlow.trade_date).order_by(MoneyFlow.trade_date.desc()).limit(1)
            )).scalar_one_or_none()
            if not latest:
                return RankResponse()
            trade_date = latest

        base = (
            select(MoneyFlow, Stock.name, Stock.industry, DailyQuote.pct_chg, DailyQuote.close)
            .outerjoin(Stock, Stock.ts_code == MoneyFlow.ts_code)
            .outerjoin(DailyQuote, and_(
                DailyQuote.ts_code == MoneyFlow.ts_code,
                DailyQuote.trade_date == MoneyFlow.trade_date,
            ))
            .where(MoneyFlow.trade_date == trade_date)
        )

        def to_item(r) -> RankItem:
            mf, name, industry, pct, close = r
            return RankItem(
                ts_code=mf.ts_code, name=(name or mf.ts_code), industry=industry,
                net_mf_amount=float(mf.net_mf_amount or 0),
                pct_chg=(float(pct) if pct is not None else None),
                close=(float(close) if close is not None else None),
            )

        inflow = [to_item(r) for r in (await db.execute(
            base.order_by(desc(MoneyFlow.net_mf_amount)).limit(top)
        )).all()]
        outflow = [to_item(r) for r in (await db.execute(
            base.order_by(asc(MoneyFlow.net_mf_amount)).limit(top)
        )).all()]
        return RankResponse(trade_date=trade_date, inflow=inflow, outflow=outflow)


# MySQL 条件聚合（净流入正/负计数），避免依赖 sqlalchemy.case 的版本差异
from sqlalchemy import case as _sa_case, literal_column as _lit


def case_pos():
    return _sa_case((MoneyFlow.net_mf_amount > 0, 1), else_=0)


def case_neg():
    return _sa_case((MoneyFlow.net_mf_amount < 0, 1), else_=0)