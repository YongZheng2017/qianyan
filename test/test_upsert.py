"""独立测试 _upsert 逻辑：模拟部分字段缺失的股票数据"""
import asyncio
import sys
import os
# 将项目根目录加入 path，便于 import src.backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding="utf-8")
from src.backend.database import async_session_maker
from src.backend.models import Stock
from src.backend.services.sync_executor import SyncExecutor


async def test():
    async with async_session_maker() as db:
        # 模拟 Tushare 返回：部分股票有 act_ent_type，部分没有
        records = [
            {"ts_code": "TEST001", "symbol": "TEST001", "name": "测试股票1", "act_ent_type": "国企", "industry": "银行"},
            {"ts_code": "TEST002", "symbol": "TEST002", "name": "测试股票2", "industry": "地产"},  # 无 act_ent_type
            {"ts_code": "TEST003", "symbol": "TEST003", "name": "测试股票3"},  # 仅主键+名称
        ]
        try:
            n = await SyncExecutor._upsert(db, Stock, records)
            await db.commit()
            print(f"[OK] 写入 {n} 条")
        except Exception as e:
            print(f"[FAIL] {type(e).__name__}: {e}")
            await db.rollback()
        finally:
            # 清理测试数据
            from sqlalchemy import delete
            await db.execute(delete(Stock).where(Stock.ts_code.like("TEST%")))
            await db.commit()
            print("测试数据已清理")


asyncio.run(test())