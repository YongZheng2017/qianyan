"""
同步调度服务与调度器

- SyncSchedulerService：调度配置 CRUD（与 sync_schedules 表交互）
- SyncScheduler：基于 APScheduler 的调度器（管理定时任务的注册与执行）

调度触发后调用 SyncExecutor.trigger(task_id, 'schedule') 执行同步。
"""
import logging
from datetime import datetime, timezone, time
from typing import Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..models import SyncSchedule, SyncTask
from ..schemas.sync_schedule import ScheduleCreate, ScheduleResponse, ScheduleToggleResult

logger = logging.getLogger(__name__)

# APScheduler job ID 前缀
JOB_ID_PREFIX = "sync_task_"


class SyncSchedulerService:
    """调度配置 CRUD 服务"""

    @staticmethod
    def _to_response(schedule: SyncSchedule, task_name: Optional[str] = None) -> ScheduleResponse:
        return ScheduleResponse(
            id=schedule.id,
            task_id=schedule.task_id,
            task_name=task_name,
            schedule_type=schedule.schedule_type,
            execute_time=schedule.execute_time.strftime("%H:%M:%S") if schedule.execute_time else None,
            weekdays=schedule.weekdays,
            cron_expr=schedule.cron_expr,
            enabled=schedule.enabled or 0,
            next_run_at=schedule.next_run_at,
            last_run_at=schedule.last_run_at,
        )

    @staticmethod
    async def get_by_task(db: AsyncSession, task_id: int) -> Optional[tuple]:
        """获取任务的调度配置（返回 schedule, task_name）"""
        result = await db.execute(
            select(SyncSchedule)
            .options(selectinload(SyncSchedule.task))
            .where(SyncSchedule.task_id == task_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            return None
        task_name = schedule.task.name if schedule.task else None
        return schedule, task_name

    @staticmethod
    async def list_all(db: AsyncSession) -> List[tuple]:
        """获取所有调度配置（含任务名）"""
        result = await db.execute(
            select(SyncSchedule).options(selectinload(SyncSchedule.task))
        )
        schedules = result.scalars().all()
        return [(s, s.task.name if s.task else None) for s in schedules]

    @staticmethod
    async def list_enabled(db: AsyncSession) -> List[tuple]:
        """获取所有启用的调度（含任务名），供调度器启动加载"""
        result = await db.execute(
            select(SyncSchedule)
            .options(selectinload(SyncSchedule.task))
            .where(SyncSchedule.enabled == 1)
        )
        schedules = result.scalars().all()
        return [(s, s.task.name if s.task else None) for s in schedules]

    @staticmethod
    def _validate(schedule_type: str, execute_time: Optional[str],
                  weekdays: Optional[str], cron_expr: Optional[str]) -> None:
        """校验调度配置完整性"""
        if schedule_type in ("daily", "weekly") and not execute_time:
            raise ValueError(f"{schedule_type} 类型必须指定 execute_time")
        if schedule_type == "weekly" and not weekdays:
            raise ValueError("weekly 类型必须指定 weekdays")
        if schedule_type == "cron" and not cron_expr:
            raise ValueError("cron 类型必须指定 cron_expr")
        # 校验 cron 表达式
        if schedule_type == "cron":
            try:
                CronTrigger.from_crontab(cron_expr)
            except Exception as e:
                raise ValueError(f"无效的 Cron 表达式：{e}")

    @staticmethod
    def _parse_time(execute_time: Optional[str]):
        """HH:MM(:SS) → datetime.time"""
        if not execute_time:
            return None
        parts = execute_time.split(":")
        if len(parts) == 2:
            h, m = int(parts[0]), int(parts[1])
            return time(h, m)
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            return time(h, m, s)
        return None

    @staticmethod
    async def upsert(db: AsyncSession, task_id: int, data: ScheduleCreate) -> ScheduleResponse:
        """
        创建或更新任务的调度配置

        Raises:
            ValueError: 任务不存在或调度配置无效
        """
        # 校验任务存在
        task_result = await db.execute(select(SyncTask).where(SyncTask.id == task_id))
        task = task_result.scalar_one_or_none()
        if not task:
            raise ValueError("同步任务不存在")

        SyncSchedulerService._validate(data.schedule_type, data.execute_time, data.weekdays, data.cron_expr)

        # 查找已有调度
        result = await db.execute(select(SyncSchedule).where(SyncSchedule.task_id == task_id))
        schedule = result.scalar_one_or_none()

        if schedule:
            schedule.schedule_type = data.schedule_type
            schedule.execute_time = SyncSchedulerService._parse_time(data.execute_time)
            schedule.weekdays = data.weekdays
            schedule.cron_expr = data.cron_expr
            schedule.enabled = data.enabled
        else:
            schedule = SyncSchedule(
                task_id=task_id,
                schedule_type=data.schedule_type,
                execute_time=SyncSchedulerService._parse_time(data.execute_time),
                weekdays=data.weekdays,
                cron_expr=data.cron_expr,
                enabled=data.enabled,
            )
            db.add(schedule)

        await db.commit()
        await db.refresh(schedule)

        # 动态更新调度器中的 job
        await scheduler.apply_schedule(schedule, task.name)

        # 回填下次执行时间
        if schedule.enabled == 1:
            schedule.next_run_at = await scheduler.get_next_run_time(task_id)
            await db.commit()
            await db.refresh(schedule)

        return SyncSchedulerService._to_response(schedule, task.name)

    @staticmethod
    async def toggle(db: AsyncSession, task_id: int, enabled: int) -> ScheduleToggleResult:
        """启用/停用调度"""
        result = await db.execute(select(SyncSchedule).where(SyncSchedule.task_id == task_id))
        schedule = result.scalar_one_or_none()
        if not schedule:
            raise ValueError("调度配置不存在")

        schedule.enabled = enabled
        await db.commit()
        await db.refresh(schedule)

        # 更新调度器 job
        if enabled == 1:
            await scheduler.apply_schedule(schedule)
            schedule.next_run_at = await scheduler.get_next_run_time(task_id)
        else:
            await scheduler.remove_job(task_id)
            schedule.next_run_at = None
        await db.commit()

        next_run = schedule.next_run_at
        return ScheduleToggleResult(enabled=enabled, next_run_at=next_run)


class SyncScheduler:
    """APScheduler 调度器封装"""

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None

    @property
    def scheduler(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        return self._scheduler

    async def start(self) -> None:
        """启动调度器并加载所有启用的调度"""
        from ..database import async_session_maker

        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("调度器已启动")

        # 加载启用的调度
        async with async_session_maker() as db:
            schedules = await SyncSchedulerService.list_enabled(db)

        for schedule, task_name in schedules:
            await self.apply_schedule(schedule, task_name)

        logger.info(f"已加载 {len(schedules)} 个启用的调度任务")

    async def shutdown(self) -> None:
        """关闭调度器"""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("调度器已关闭")

    def _build_trigger(self, schedule: SyncSchedule) -> CronTrigger:
        """构建 CronTrigger"""
        if schedule.schedule_type == "daily":
            t = schedule.execute_time
            return CronTrigger(hour=t.hour, minute=t.minute, second=t.second if t.second else 0)
        elif schedule.schedule_type == "weekly":
            t = schedule.execute_time
            days = [int(d) for d in schedule.weekdays.split(",")]
            return CronTrigger(day_of_week=days, hour=t.hour,
                               minute=t.minute, second=t.second if t.second else 0)
        else:  # cron
            return CronTrigger.from_crontab(schedule.cron_expr)

    async def apply_schedule(self, schedule: SyncSchedule, task_name: Optional[str] = None) -> None:
        """应用调度配置（启用则注册/更新 job，禁用则移除）"""
        job_id = f"{JOB_ID_PREFIX}{schedule.task_id}"

        # 先移除已有 job
        self.scheduler.remove_job(job_id) if self.scheduler.get_job(job_id) else None

        if schedule.enabled != 1:
            return

        trigger = self._build_trigger(schedule)
        self.scheduler.add_job(
            self._execute,
            trigger=trigger,
            args=[schedule.task_id],
            id=job_id,
            name=task_name or f"同步任务{schedule.task_id}",
            replace_existing=True,
        )
        logger.info(f"调度已注册: task_id={schedule.task_id}, type={schedule.schedule_type}")

    async def remove_job(self, task_id: int) -> None:
        """移除调度 job"""
        job_id = f"{JOB_ID_PREFIX}{task_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"调度已移除: task_id={task_id}")

    async def get_next_run_time(self, task_id: int) -> Optional[datetime]:
        """获取下次执行时间（naive UTC，与 DB 存储一致）"""
        job_id = f"{JOB_ID_PREFIX}{task_id}"
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            nrt = job.next_run_time
            # APScheduler 用 Asia/Shanghai 时区，统一转 naive UTC 存储
            if nrt.tzinfo is not None:
                nrt = nrt.astimezone(timezone.utc).replace(tzinfo=None)
            return nrt
        return None

    @staticmethod
    async def _execute(task_id: int) -> None:
        """调度触发的执行回调"""
        from .sync_executor import SyncExecutor
        from ..database import async_session_maker

        logger.info(f"调度触发同步: task_id={task_id}")
        try:
            # 更新 last_run_at
            async with async_session_maker() as db:
                result = await db.execute(
                    select(SyncSchedule).where(SyncSchedule.task_id == task_id)
                )
                schedule = result.scalar_one_or_none()
                if schedule:
                    schedule.last_run_at = datetime.now(timezone.utc)
                    await db.commit()

            await SyncExecutor.trigger(task_id, trigger_type="schedule")
        except Exception as e:
            logger.exception(f"调度执行失败 task_id={task_id}: {e}")


# 全局调度器单例
scheduler = SyncScheduler()