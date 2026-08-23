"""
资金趋势分析 API（分析端，只读）

- 个股资金流向 / 市场总览 / 净流入排行
- 宏观经济指标时序（10类）
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.fundflow import (
    StockFlowResponse, MarketFlowResponse, RankResponse, MacroSeriesResponse
)
from ....schemas.common import Response
from ....models import User
from ....services.fundflow import FundFlowService
from ....services.macro_query import MacroService
from ....api.deps import get_current_user

router = APIRouter()


# ==================== 资金流向 ====================

@router.get("/stock", response_model=Response[StockFlowResponse])
async def get_stock_flow(
    ts_code: str = Query(..., description="股票代码"),
    limit: int = Query(60, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """个股资金流向时序（净流入+大单/特大单，叠加收盘价）"""
    return Response(data=await FundFlowService.get_stock_flow(db, ts_code, limit))


@router.get("/market", response_model=Response[MarketFlowResponse])
async def get_market_flow(
    limit: int = Query(30, ge=1, le=250),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """全市场资金总览（按交易日聚合）"""
    return Response(data=await FundFlowService.get_market_flow(db, limit))


@router.get("/rank", response_model=Response[RankResponse])
async def get_flow_rank(
    trade_date: Optional[str] = Query(None, description="交易日YYYYMMDD，默认最新"),
    top: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """净流入/净流出排行"""
    return Response(data=await FundFlowService.get_rank(db, trade_date, top))


# ==================== 宏观经济 ====================

@router.get("/macro/indicators", response_model=Response[list])
async def list_macro_indicators():
    """所有宏观指标及可选字段"""
    return Response(data=MacroService.list_indicators())


@router.get("/macro/series", response_model=Response[MacroSeriesResponse])
async def get_macro_series(
    indicator: str = Query(..., description="指标key，如 shibor/cpi/us_tycr"),
    field: str = Query(..., description="字段名，如 y1/nt_yoy/y10"),
    limit: int = Query(120, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """宏观指标时序查询"""
    try:
        result = await MacroService.get_series(db, indicator, field, limit)
        return Response(data=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))