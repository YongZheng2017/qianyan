"""
同步执行器

负责实际的同步执行流程：
1. 创建执行记录（running）
2. 调用数据源适配器获取数据（带超时 + 指数退避重试）
3. 记录每次接口调用明细
4. 数据写入目标业务表（UPSERT）
5. 更新执行记录状态（success/failed/timeout）

执行器作为异步后台任务运行，使用独立 DB Session。
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Float, UniqueConstraint
from sqlalchemy.dialects.mysql import insert as mysql_insert

from ..models import (
    SyncTask, DataSource, SyncLog, SyncCallLog,
    Stock, DailyQuote, WeeklyQuote, MonthlyQuote,
    FinIncome, FinBalancesheet, FinCashflow, FinIndicator,
    FinForecast, FinExpress, FinDividend, FinMainbz, FinDisclosure,
    MoneyFlow,
    BoardIndustry, BoardIndustryQuote,
    MacroLpr, MacroShibor, MacroGdp, MacroCpi, MacroPpi, MacroPmi, MacroM,
    MacroUsTycr, MacroUsTbr, MacroUsTlr,
    ThsValuationSnapshot, ThsIndex, ThsIndexConstituent, ThsIndexQuote,
)
from ..database import async_session_maker
from .adapters import DataSourceAdapterFactory

logger = logging.getLogger(__name__)

# 目标表 → ORM 模型映射
TARGET_MODEL_MAP = {
    "stocks": Stock,
    "daily_quotes": DailyQuote,
    "weekly_quotes": WeeklyQuote,
    "monthly_quotes": MonthlyQuote,
    # 财务数据表（DS-005）
    "fin_income": FinIncome,
    "fin_balancesheet": FinBalancesheet,
    "fin_cashflow": FinCashflow,
    "fin_indicator": FinIndicator,
    "fin_forecast": FinForecast,
    "fin_express": FinExpress,
    "fin_dividend": FinDividend,
    "fin_mainbz": FinMainbz,
    "fin_disclosure": FinDisclosure,
    # 资金流向（DS-006）
    "moneyflow": MoneyFlow,
    # 板块数据（DS-007，AKShare）
    "board_industry": BoardIndustry,
    "board_industry_quotes": BoardIndustryQuote,
    # 宏观经济（DS-008，Tushare）
    "macro_lpr": MacroLpr,
    "macro_shibor": MacroShibor,
    "macro_gdp": MacroGdp,
    "macro_cpi": MacroCpi,
    "macro_ppi": MacroPpi,
    "macro_pmi": MacroPmi,
    "macro_m": MacroM,
    "macro_us_tycr": MacroUsTycr,
    "macro_us_tbr": MacroUsTbr,
    "macro_us_tlr": MacroUsTlr,
    # 同花顺（DS-009）
    "ths_valuation_snapshot": ThsValuationSnapshot,
    "ths_index": ThsIndex,
    "ths_index_constituent": ThsIndexConstituent,
    "ths_index_quotes": ThsIndexQuote,
}

# 运行中的后台任务强引用集合（防止 asyncio.create_task 返回的 Task 被 GC 回收导致静默取消）
_running_tasks: set = set()


def _now() -> datetime:
    """当前 UTC 时间（naive，与 MySQL DATETIME 存储一致，避免 aware/naive 相减报错）"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _gen_execution_id() -> str:
    return f"exec_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"


class SyncExecutor:
    """同步任务执行器"""

    @staticmethod
    async def trigger(
        task_id: int,
        trigger_type: str = "manual",
        override_params: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> str:
        """
        触发同步执行

        创建执行记录（running），启动后台任务，立即返回 execution_id。

        Raises:
            ValueError: 任务或数据源不存在
        """
        from .sync_task import SyncTaskService

        # 同步创建执行记录（确保 API 能立即返回 id）
        async with async_session_maker() as db:
            task = await SyncTaskService.get_by_id(db, task_id)
            if not task:
                raise ValueError("同步任务不存在")

            source = await db.get(DataSource, task.source_id)
            if not source:
                raise ValueError("数据源不存在")
            if source.status != 1:
                raise ValueError("数据源已禁用")
            if task.status != 1:
                raise ValueError("同步任务已禁用")

            execution_id = _gen_execution_id()

            # 合并参数：任务默认参数 + 临时覆盖参数
            params: Dict[str, Any] = {
                p.param_key: p.param_value for p in task.params if p.param_value not in (None, "")
            }
            if override_params:
                params.update({k: v for k, v in override_params.items() if v not in (None, "")})

            log = SyncLog(
                execution_id=execution_id,
                task_id=task_id,
                task_name=task.name,
                source_name=source.name,
                trigger_type=trigger_type,
                trigger_user_id=user_id,
                status="running",
                start_at=_now(),
                params_snapshot=json.dumps(params, ensure_ascii=False),
            )
            db.add(log)
            await db.commit()

        # 启动后台执行任务（保存强引用，防止 Task 被 GC 回收）
        task = asyncio.create_task(SyncExecutor._run(execution_id, task_id, params))
        _running_tasks.add(task)
        task.add_done_callback(_running_tasks.discard)

        logger.info(f"同步任务已触发: execution_id={execution_id}, task_id={task_id}")
        return execution_id

    @staticmethod
    async def _run(execution_id: str, task_id: int, params: Dict[str, Any]) -> None:
        """后台执行同步（独立 Session）"""
        from .sync_task import SyncTaskService

        total_records = 0
        api_calls = 0
        try:
            async with async_session_maker() as db:
                task = await SyncTaskService.get_by_id(db, task_id)
                source = await db.get(DataSource, task.source_id)

                adapter = DataSourceAdapterFactory.get_adapter(source.source_type)
                from .data_source import DataSourceService
                credentials = DataSourceService._get_plain_credentials(source)

                # 调用接口（带超时 + 重试）
                records, call_info = await SyncExecutor._call_with_retry(
                    adapter, source.api_url, credentials,
                    task.data_interface, params,
                    task.timeout_seconds, task.retry_count,
                )
                api_calls += 1

                # 记录调用明细并立即提交（确保失败时调用明细也持久化）
                await SyncExecutor._log_call(db, execution_id, api_calls, params, call_info)
                await db.commit()

                # 接口调用失败则终止
                if call_info["status"] != "success":
                    raise Exception(call_info.get("error_message") or "接口调用失败")

                # 写入目标表
                if records:
                    model = TARGET_MODEL_MAP.get(task.target_table)
                    if model:
                        total_records = await SyncExecutor._upsert(db, model, records)
                        # 间隔等待（符合任务配置，此处单次调用后无后续，但保留语义）
                        await asyncio.sleep(0)
                    else:
                        logger.warning(f"未找到目标表模型: {task.target_table}")

                await db.commit()

            await SyncExecutor._complete(execution_id, "success", total_records, api_calls)
            logger.info(f"同步完成: {execution_id}, records={total_records}, calls={api_calls}")

        except Exception as e:
            logger.exception(f"同步执行失败 {execution_id}: {e}")
            # 失败时也提交调用明细（已在上文 commit 范围外，单独处理）
            await SyncExecutor._complete(execution_id, "failed", total_records, api_calls, str(e))

    @staticmethod
    async def _call_with_retry(
        adapter, api_url: str, credentials: Dict[str, Any], interface: str,
        params: Dict[str, Any], timeout: int, retry_count: int,
    ) -> Tuple[List[dict], dict]:
        """
        带超时和指数退避重试的接口调用

        Returns:
            (records, call_info) 其中 call_info 包含状态/耗时/重试次数等
        """
        last_call_info: dict = {}
        last_error: Optional[str] = None

        for attempt in range(retry_count + 1):
            request_at = _now()
            error_msg: Optional[str] = None
            records: List[dict] = []

            try:
                result = await asyncio.wait_for(
                    adapter.fetch_data(api_url, credentials, interface, params, timeout=timeout),
                    timeout=timeout,
                )
                response_at = _now()
                duration_ms = int((response_at - request_at).total_seconds() * 1000)
                code = result.get("code", -1)

                if code == 0:
                    records = result.get("records", [])
                    return records, {
                        "status": "success", "record_count": len(records),
                        "duration_ms": duration_ms, "request_at": request_at,
                        "response_at": response_at, "retry_count": attempt,
                        "error_message": None,
                    }
                else:
                    error_msg = result.get("msg") or f"接口返回错误 code={code}"
                    last_call_info = {
                        "status": "failed", "record_count": 0, "duration_ms": duration_ms,
                        "request_at": request_at, "response_at": response_at,
                        "retry_count": attempt, "error_message": error_msg,
                    }
                    # 不可重试错误（Token/积分），立即返回
                    if result.get("fatal"):
                        return [], last_call_info
                    last_error = error_msg

            except asyncio.TimeoutError:
                response_at = _now()
                error_msg = f"接口超时({timeout}秒)"
                last_call_info = {
                    "status": "timeout", "record_count": 0,
                    "duration_ms": int((response_at - request_at).total_seconds() * 1000),
                    "request_at": request_at, "response_at": response_at,
                    "retry_count": attempt, "error_message": error_msg,
                }
                last_error = error_msg

            except Exception as e:
                response_at = _now()
                error_msg = str(e)
                last_call_info = {
                    "status": "failed", "record_count": 0,
                    "duration_ms": int((response_at - request_at).total_seconds() * 1000),
                    "request_at": request_at, "response_at": response_at,
                    "retry_count": attempt, "error_message": error_msg,
                }
                last_error = error_msg

            # 指数退避重试
            if attempt < retry_count:
                logger.warning(f"接口调用失败，{2 ** attempt}秒后重试({attempt + 1}/{retry_count}): {last_error}")
                await asyncio.sleep(2 ** attempt)

        return [], last_call_info

    @staticmethod
    async def _log_call(
        db: AsyncSession, execution_id: str, call_seq: int,
        params: Dict[str, Any], call_info: dict,
    ) -> None:
        """记录单次接口调用明细"""
        call_log = SyncCallLog(
            execution_id=execution_id,
            call_seq=call_seq,
            request_params=json.dumps(params, ensure_ascii=False),
            request_at=call_info["request_at"],
            response_at=call_info.get("response_at"),
            duration_ms=call_info.get("duration_ms"),
            status=call_info["status"],
            record_count=call_info.get("record_count", 0),
            retry_count=call_info.get("retry_count", 0),
            error_message=call_info.get("error_message"),
        )
        db.add(call_log)
        await db.flush()

    @staticmethod
    async def _upsert(db: AsyncSession, model, records: List[dict]) -> int:
        """UPSERT 写入目标表（INSERT ... ON DUPLICATE KEY UPDATE）"""
        if not records:
            return 0

        columns = {c.name: c for c in model.__table__.columns}
        # 冲突检测列 = 主键 + 唯一约束列（排除自增 id）。
        # 财务/资金/板块表主键是自增 id、业务唯一键在 UniqueConstraint；
        # 宏观表主键直接是业务键(date/month/quarter)。
        pk_cols = {c.name for c in model.__table__.primary_key.columns if not c.autoincrement}
        for uc in model.__table__.constraints:
            if isinstance(uc, UniqueConstraint):
                pk_cols.update(c.name for c in uc.columns)

        has_raw = 'raw_data' in columns  # 财务表含 raw_data 列
        clean: List[dict] = []
        for r in records:
            full = dict(r)  # 完整原始记录（用于写入 raw_data JSON）
            row: Dict[str, Any] = {}
            for k, v in r.items():
                if k not in columns:
                    continue
                if v is None or v == "":
                    continue
                # 数值字段类型转换（Tushare 可能返回字符串数字）
                if isinstance(columns[k].type, Float):
                    try:
                        v = float(v)
                    except (ValueError, TypeError):
                        continue
                row[k] = v
            # 财务表：完整记录写入 raw_data（保留 Tushare 全部字段）
            if has_raw:
                row['raw_data'] = full
            # 必须包含所有主键字段
            if all(pk in row for pk in pk_cols):
                clean.append(row)

        if not clean:
            return 0

        # 统一所有行的字段集合（缺失补 None），避免批量插入字段不一致
        present_cols = set()
        for row in clean:
            present_cols.update(row.keys())
        for row in clean:
            for c in present_cols:
                if c not in row:
                    row[c] = None

        stmt = mysql_insert(model).values(clean)
        # 只对数据中实际出现的非主键列做 ON DUPLICATE KEY UPDATE
        # （避免引用未在 VALUES 中出现的列，导致 "explicitly rendered as bound parameter" 错误）
        update_cols = {name: stmt.inserted[name] for name in present_cols if name not in pk_cols}
        stmt = stmt.on_duplicate_key_update(**update_cols)
        await db.execute(stmt)
        return len(clean)

    @staticmethod
    async def _complete(
        execution_id: str, status_str: str,
        total_records: int, api_calls: int,
        error_message: Optional[str] = None,
    ) -> None:
        """更新执行记录状态"""
        async with async_session_maker() as db:
            from sqlalchemy import select
            result = await db.execute(select(SyncLog).where(SyncLog.execution_id == execution_id))
            log = result.scalar_one_or_none()
            if log:
                log.status = status_str
                log.total_records = total_records
                log.api_calls = api_calls
                log.end_at = _now()
                if log.start_at:
                    log.duration_seconds = int((log.end_at - log.start_at).total_seconds())
                log.error_message = error_message
                await db.commit()
            logger.info(f"执行记录已更新: {execution_id} -> {status_str}")