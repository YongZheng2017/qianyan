"""分析端 API 模块（只读，面向终端用户）"""
from fastapi import APIRouter
from . import quote, fundamental, fundflow

router = APIRouter(prefix="/analysis", tags=["分析端"])

router.include_router(quote.router, tags=["行情"])
router.include_router(fundamental.router, prefix="/fundamental", tags=["基本面分析"])
router.include_router(fundflow.router, prefix="/fund-flow", tags=["资金趋势分析"])

__all__ = ["router"]