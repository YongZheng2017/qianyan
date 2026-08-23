"""
基本面分析 API（分析端，只读）
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db
from ....schemas.fundamental import (
    OverviewResponse, StatementResponse, IndicatorGroupResponse, ValuationResponse
)
from ....schemas.common import Response
from ....models import User
from ....services.fundamental import FundamentalService
from ....api.deps import get_current_user

router = APIRouter()


@router.get("/overview", response_model=Response[OverviewResponse])
async def fundamental_overview(
    ts_code: str = Query(..., description="股票代码"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """基本面概览（核心指标 + 最新财报 + 风险提示）"""
    return Response(data=await FundamentalService.get_overview(db, ts_code))


@router.get("/statements", response_model=Response[StatementResponse])
async def fundamental_statements(
    ts_code: str = Query(...),
    type: str = Query("income", description="报表类型: income/balancesheet/cashflow"),
    periods: int = Query(8, ge=1, le=24, description="报告期数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """三大报表多期数据"""
    return Response(data=await FundamentalService.get_statements(db, ts_code, type, periods))


@router.get("/indicators", response_model=Response[IndicatorGroupResponse])
async def fundamental_indicators(
    ts_code: str = Query(...),
    periods: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """四大能力指标（多期）"""
    return Response(data=await FundamentalService.get_indicators(db, ts_code, periods))


@router.get("/valuation", response_model=Response[ValuationResponse])
async def fundamental_valuation(
    ts_code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """估值分析（PE/PB/PEG）"""
    return Response(data=await FundamentalService.get_valuation(db, ts_code))