"""
FastAPI 应用入口

创建 FastAPI 应用实例，配置路由、CORS、启动事件
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from .core.config import settings
from .database import init_db, async_session_maker
from .services.init import init_system
from .services.sync_scheduler import scheduler
from .api.v1 import admin, user, analysis
from .schemas.common import Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化数据库和系统
    """
    # 启动时执行
    print(f"{settings.PROJECT_NAME} v{settings.VERSION} 启动中...")

    # 初始化数据库表
    await init_db()
    print("[OK] 数据库表初始化完成")

    # 系统初始化（创建admin用户等）
    async with async_session_maker() as db:
        await init_system(db)
    print("[OK] 系统初始化完成")

    # 启动同步调度器
    await scheduler.start()
    print("[OK] 同步调度器已启动")

    yield

    # 关闭时执行
    await scheduler.shutdown()
    print("应用关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="钱眼投资分析系统 - 股票基本面分析和资金趋势分析平台",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(admin.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")


# 健康检查端点
@app.get("/health", response_model=Response[dict])
async def health_check():
    """
    健康检查

    Returns:
        Response[dict]: 健康状态
    """
    return Response(
        data={
            "status": "healthy",
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION
        }
    )


# 系统初始化端点（可选手动触发）
@app.post("/api/v1/system/init", response_model=Response)
async def manual_init():
    """
    手动触发系统初始化

    Returns:
        Response: 成功响应
    """
    async with async_session_maker() as db:
        await init_system(db)

    return Response(message="系统初始化成功")


# 数据库连接测试端点
@app.get("/api/v1/system/db-test", response_model=Response[dict])
async def test_db_connection():
    """
    测试数据库连接

    Returns:
        Response[dict]: 连接状态
    """
    try:
        async with async_session_maker() as db:
            # 执行简单查询
            result = await db.execute(text("SELECT 1"))
            result.scalar()

        return Response(
            data={
                "status": "connected",
                "message": "数据库连接正常"
            }
        )
    except Exception as e:
        return Response(
            code=1,
            message=f"数据库连接失败: {str(e)}",
            data={"status": "error"}
        )


if __name__ == "__main__":
    import uvicorn

    # 开发环境启动
    uvicorn.run(
        "src.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )