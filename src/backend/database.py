"""
数据库连接模块

使用 SQLAlchemy 异步引擎连接 MySQL 数据库
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from .core.config import settings

logger = logging.getLogger(__name__)

# 创建异步数据库引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # 连接池预检查
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_recycle=3600,  # 连接回收时间（秒）
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖注入函数

    Yields:
        AsyncSession: 数据库会话对象
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_database_if_not_exists():
    """
    如果数据库不存在，则自动创建数据库

    连接到 MySQL 服务器（不指定数据库），检查并创建数据库
    """
    # 从 DATABASE_URL 中提取数据库名
    # 格式: mysql+aiomysql://user:password@host:port/database
    from urllib.parse import urlparse

    parsed = urlparse(settings.DATABASE_URL)
    database_name = parsed.path.lstrip('/')

    # 构建连接到 MySQL 服务器的 URL（不指定数据库）
    server_url = settings.DATABASE_URL.replace(f'/{database_name}', '')

    # 创建临时引擎连接到服务器
    temp_engine = create_async_engine(server_url, echo=settings.DB_ECHO)

    try:
        async with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = await conn.execute(
                text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'")
            )
            exists = result.scalar() is not None

            if not exists:
                # 创建数据库
                await conn.execute(
                    text(f"CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                )
                await conn.commit()
                logger.info(f"[OK] 数据库 '{database_name}' 创建成功")
            else:
                logger.info(f"[OK] 数据库 '{database_name}' 已存在")

    except Exception as e:
        logger.error(f"[ERROR] 创建数据库失败: {e}")
        raise
    finally:
        await temp_engine.dispose()


async def init_db():
    """
    初始化数据库

    1. 检查并创建数据库（如果不存在）
    2. 创建所有表结构
    """
    # 导入 Base（必须在函数内部导入，避免循环依赖）
    from .models.base import Base
    # 导入所有模型，确保它们被注册到 Base.metadata
    from .models import User, Role, Permission

    # 先创建数据库
    await create_database_if_not_exists()

    # 然后创建表结构
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("[OK] 数据库表初始化完成")