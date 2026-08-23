"""
行情查询服务

从已同步的业务表读取行情数据（只读），供分析端展示。
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from ..models import Stock, DailyQuote, WeeklyQuote, MonthlyQuote
from ..schemas.quote import QuoteItem, QuoteResponse, SymbolItem


class QuoteService:
    """行情查询服务（只读）"""

    # (标的类型, 周期) → ORM 模型
    QUOTE_TABLES = {
        ("stock", "daily"): DailyQuote,
        ("stock", "weekly"): WeeklyQuote,
        ("stock", "monthly"): MonthlyQuote,
        # ("index", "daily"): IndexQuote,  # 待新增表
    }

    @staticmethod
    async def search_symbols(
        db: AsyncSession, keyword: Optional[str], qtype: str = "stock", limit: int = 20
    ) -> List[SymbolItem]:
        """
        搜索标的（当前只支持股票）

        Args:
            keyword: 关键词（代码/名称/拼音），为空则返回前 limit 只
            qtype: 标的类型（stock/index/sector），当前只支持 stock
            limit: 返回条数
        """
        if qtype != "stock":
            return []  # 板块/市场待后续支持

        query = select(Stock).where(Stock.list_status == "L")
        if keyword:
            query = query.where(
                or_(
                    Stock.ts_code.like(f"%{keyword}%"),
                    Stock.symbol.like(f"%{keyword}%"),
                    Stock.name.like(f"%{keyword}%"),
                )
            )
        query = query.limit(limit)
        rows = (await db.execute(query)).scalars().all()
        return [
            SymbolItem(code=s.ts_code, name=s.name or s.ts_code, type="stock", extra=s.industry)
            for s in rows
        ]

    @staticmethod
    async def get_stock_name(db: AsyncSession, symbol: str) -> str:
        """获取股票名称"""
        s = (await db.execute(select(Stock).where(Stock.ts_code == symbol))).scalar_one_or_none()
        return s.name if (s and s.name) else symbol

    @staticmethod
    async def get_quotes(
        db: AsyncSession, symbol: str, qtype: str, period: str,
        start_date: Optional[str] = None, end_date: Optional[str] = None,
        limit: int = 120,
    ) -> QuoteResponse:
        """
        查询行情数据

        Raises:
            ValueError: 不支持的类型/周期
        """
        model = QuoteService.QUOTE_TABLES.get((qtype, period))
        if model is None:
            raise ValueError(f"不支持的类型/周期: {qtype}/{period}")

        query = select(model).where(model.ts_code == symbol)
        if start_date:
            query = query.where(model.trade_date >= start_date)
        if end_date:
            query = query.where(model.trade_date <= end_date)
        # 取最近 limit 条后倒序，再反转为升序（便于图表绘制）
        query = query.order_by(model.trade_date.desc()).limit(limit)
        rows = list((await db.execute(query)).scalars().all())
        rows.reverse()

        name = symbol
        if qtype == "stock":
            name = await QuoteService.get_stock_name(db, symbol)

        items = [
            QuoteItem(
                trade_date=r.trade_date, open=r.open, high=r.high, low=r.low, close=r.close,
                pre_close=r.pre_close, pct_chg=r.pct_chg, vol=r.vol, amount=r.amount,
            )
            for r in rows
        ]
        return QuoteResponse(symbol=symbol, name=name, type=qtype, period=period, items=items)