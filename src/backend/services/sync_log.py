"""
同步日志查询服务

提供日志列表、详情、实时进度、统计、清理等功能
"""
import json
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from ..models import SyncLog, SyncCallLog
from ..schemas.sync_log import (
    SyncLogResponse, SyncLogDetail, SyncCallLogResponse,
    SyncProgress, SyncStats,
)


def _parse_json(s: Optional[str]) -> Optional[dict]:
    if not s:
        return None
    try:
        return json.loads(s)
    except Exception:
        return None


class SyncLogService:
    """同步日志查询服务"""

    @staticmethod
    def _to_response(log: SyncLog) -> SyncLogResponse:
        return SyncLogResponse(
            id=log.id,
            execution_id=log.execution_id,
            task_id=log.task_id,
            task_name=log.task_name,
            source_name=log.source_name,
            trigger_type=log.trigger_type,
            trigger_user_id=log.trigger_user_id,
            status=log.status,
            total_records=log.total_records or 0,
            api_calls=log.api_calls or 0,
            start_at=log.start_at,
            end_at=log.end_at,
            duration_seconds=log.duration_seconds,
            params_snapshot=_parse_json(log.params_snapshot),
            error_message=log.error_message,
        )

    @staticmethod
    async def get_list(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        task_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """获取同步日志列表（分页、筛选）"""
        query = select(SyncLog)

        if task_id is not None:
            query = query.where(SyncLog.task_id == task_id)
        if status_filter:
            query = query.where(SyncLog.status == status_filter)
        if start_date:
            query = query.where(SyncLog.start_at >= start_date)
        if end_date:
            query = query.where(SyncLog.start_at <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(SyncLog.start_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "list": [SyncLogService._to_response(l).model_dump() for l in items],
            "page": page, "page_size": page_size, "total": total,
        }

    @staticmethod
    async def get_detail(db: AsyncSession, execution_id: str) -> Optional[SyncLogDetail]:
        """获取同步执行详情（含接口调用明细）"""
        result = await db.execute(
            select(SyncLog)
            .options(selectinload(SyncLog.call_logs))
            .where(SyncLog.execution_id == execution_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return None

        base = SyncLogService._to_response(log)
        call_logs = sorted(log.call_logs, key=lambda c: c.call_seq)
        return SyncLogDetail(
            **base.model_dump(),
            call_logs=[
                SyncCallLogResponse(
                    id=c.id, call_seq=c.call_seq,
                    request_params=_parse_json(c.request_params),
                    request_at=c.request_at, response_at=c.response_at,
                    duration_ms=c.duration_ms, status=c.status,
                    record_count=c.record_count or 0, retry_count=c.retry_count or 0,
                    error_message=c.error_message,
                )
                for c in call_logs
            ],
        )

    @staticmethod
    async def get_progress(db: AsyncSession, execution_id: str) -> Optional[SyncProgress]:
        """获取实时执行进度"""
        result = await db.execute(
            select(SyncLog).where(SyncLog.execution_id == execution_id)
        )
        log = result.scalar_one_or_none()
        if not log:
            return None

        elapsed = None
        if log.start_at:
            # 统一用 naive UTC 比较（DB 读出的时间为 naive）
            end = log.end_at or datetime.now(timezone.utc).replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.replace(tzinfo=None)
            elapsed = int((end - log.start_at).total_seconds())

        # 查最近一次调用时间
        call_result = await db.execute(
            select(func.max(SyncCallLog.request_at))
            .where(SyncCallLog.execution_id == execution_id)
        )
        last_call_at = call_result.scalar()

        return SyncProgress(
            execution_id=log.execution_id,
            status=log.status,
            total_records=log.total_records or 0,
            api_calls=log.api_calls or 0,
            elapsed_seconds=elapsed,
            last_call_at=last_call_at,
        )

    @staticmethod
    async def get_stats(db: AsyncSession, date_str: Optional[str] = None) -> SyncStats:
        """获取同步统计（默认今天）"""
        # 解析日期
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                day = datetime.now(timezone.utc).date()
        else:
            day = datetime.now(timezone.utc).date()

        start = datetime.combine(day, datetime.min.time()).replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        base_query = select(SyncLog).where(SyncLog.start_at >= start, SyncLog.start_at < end)
        total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
        today_count = total_result.scalar() or 0

        success_result = await db.execute(
            select(func.count()).select_from(
                select(SyncLog.id).where(SyncLog.start_at >= start, SyncLog.start_at < end,
                                          SyncLog.status == "success").subquery()
            )
        )
        success_count = success_result.scalar() or 0

        failed_count = today_count - success_count
        success_rate = round(success_count / today_count * 100, 1) if today_count else 0.0

        avg_result = await db.execute(
            select(func.avg(SyncLog.duration_seconds)).where(
                SyncLog.start_at >= start, SyncLog.start_at < end,
                SyncLog.duration_seconds.isnot(None)
            )
        )
        avg_duration = round(float(avg_result.scalar() or 0), 1)

        total_records_result = await db.execute(
            select(func.sum(SyncLog.total_records)).where(
                SyncLog.start_at >= start, SyncLog.start_at < end
            )
        )
        total_records = int(total_records_result.scalar() or 0)

        return SyncStats(
            today_count=today_count,
            success_count=success_count,
            failed_count=failed_count,
            success_rate=success_rate,
            avg_duration=avg_duration,
            total_records=total_records,
        )

    @staticmethod
    async def clean_before(db: AsyncSession, before_date: str) -> int:
        """清理指定日期之前的日志，返回删除条数"""
        try:
            day = datetime.strptime(before_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("日期格式应为 YYYY-MM-DD")

        result = await db.execute(
            delete(SyncLog).where(SyncLog.start_at < day)
        )
        await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def delete_by_execution_id(db: AsyncSession, execution_id: str) -> None:
        """根据 execution_id 删除单条日志（DB 外键 CASCADE 自动删除调用明细）"""
        result = await db.execute(select(SyncLog).where(SyncLog.execution_id == execution_id))
        log = result.scalar_one_or_none()
        if not log:
            raise ValueError("执行记录不存在")
        await db.delete(log)
        await db.commit()