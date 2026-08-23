"""
行情查询 API（分析端，只读）
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.quote import QuoteResponse, SymbolItem
from ....schemas.common import Response
from ....models import User
from ....services.quote import QuoteService
from ....api.deps import get_current_user

router = APIRouter()


@router.get("/symbols/search", response_model=Response[List[SymbolItem]])
async def search_symbols(
    q: Optional[str] = Query(None, description="搜索关键词（代码/名称）"),
    type: str = Query("stock", description="标的类型: stock/index/sector"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜索标的（当前支持股票）"""
    result = await QuoteService.search_symbols(db, q, type)
    return Response(data=[s for s in result])


@router.get("/quotes", response_model=Response[QuoteResponse])
async def get_quotes(
    symbol: str = Query(..., description="标的代码，如 000001.SZ"),
    type: str = Query("stock", description="标的类型: stock/index/sector"),
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="起始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    limit: int = Query(120, ge=1, le=1000, description="返回条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询行情（K线）数据"""
    try:
        result = await QuoteService.get_quotes(
            db, symbol, type, period, start_date, end_date, limit
        )
        return Response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))