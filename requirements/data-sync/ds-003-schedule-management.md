# DS-003: 同步调度管理

## 用户故事

作为系统管理员，我希望能够为同步任务设置定时调度（例如每天收盘后特定时间自动执行），同时也能手动触发某个任务立即执行，以便数据能按时自动更新，必要时也能随时手动补数据。

## 验收标准

### 功能需求

#### AC1: 设置定时同步
**Given**: 在同步任务列表或详情页
**When**: 配置调度
**Then**: 可设置定时执行规则
**And**: 支持每天特定时间执行（如每天 18:00）
**And**: 支持自定义 Cron 表达式（高级模式）

#### AC2: 调度状态管理
**Given**: 已配置调度的任务
**When**: 查看调度状态
**Then**: 显示调度是否启用、下次执行时间、上次执行时间
**And**: 可启用/暂停调度

#### AC3: 手动触发同步
**Given**: 在同步任务列表
**When**: 点击"立即同步"按钮
**Then**: 任务立即开始执行（异步）
**And**: 返回执行任务ID，可查看执行进度

#### AC4: 调度模式选择
**Given**: 配置调度
**When**: 选择调度类型
**Then**: 支持以下模式：
- 每日定时（设置时间点）
- 每周定时（设置星期和时间点）
- 自定义 Cron（高级）

#### AC5: 调度优先级与并发控制
**Given**: 多个任务同时到点
**When**: 调度触发
**Then**: 按任务优先级排队执行
**And**: 可配置最大并发数，避免系统过载

#### AC6: 手动同步参数覆盖
**Given**: 手动触发同步
**When**: 设置临时参数
**Then**: 可覆盖任务的默认参数（如指定特定交易日）
**And**: 临时参数不影响任务原始配置

#### AC7: 调度执行预览
**Given**: 查看调度列表
**When**: 页面加载
**Then**: 显示每个任务的下次执行倒计时
**And**: 显示调度运行状态（运行中/等待/已暂停）

## 调度模式说明

### 每日定时
| 配置项 | 说明 | 示例 |
|--------|------|------|
| 执行时间 | 每天执行的时间点 | 18:00 |

**场景**: 每天收盘后同步当日日线行情

### 每周定时
| 配置项 | 说明 | 示例 |
|--------|------|------|
| 星期 | 每周哪几天执行 | 周一至周五 |
| 执行时间 | 执行时间点 | 18:00 |

**场景**: 工作日收盘后同步行情数据

### 自定义 Cron
| 配置项 | 说明 | 示例 |
|--------|------|------|
| Cron 表达式 | 标准5段式 Cron | `0 18 * * 1-5` |

**场景**: 复杂调度需求

## 技术实现

### 数据库模型

```sql
-- 同步调度配置表
CREATE TABLE sync_schedules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL UNIQUE COMMENT '关联任务ID(一对一)',
    schedule_type VARCHAR(20) NOT NULL COMMENT '调度类型:daily,weekly,cron',
    execute_time TIME COMMENT '执行时间(HH:MM:SS)',
    weekdays VARCHAR(20) COMMENT '星期(逗号分隔:1,2,3,4,5)',
    cron_expr VARCHAR(100) COMMENT 'Cron表达式',
    enabled TINYINT DEFAULT 0 COMMENT '是否启用:1启用 0停用',
    next_run_at DATETIME COMMENT '下次执行时间',
    last_run_at DATETIME COMMENT '上次执行时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES sync_tasks(id) ON DELETE CASCADE
);
```

### 调度器实现

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class SyncScheduler:
    """同步调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.max_concurrent = 3  # 最大并发数

    async def start(self):
        """启动调度器"""
        await self.load_all_schedules()
        self.scheduler.start()

    async def load_all_schedules(self):
        """从数据库加载所有启用的调度"""
        schedules = await get_enabled_schedules()
        for schedule in schedules:
            self.add_schedule(schedule)

    def add_schedule(self, schedule):
        """添加调度任务"""
        trigger = self._build_trigger(schedule)
        self.scheduler.add_job(
            self._execute_task,
            trigger=trigger,
            args=[schedule.task_id],
            id=f"sync_task_{schedule.task_id}",
            replace_existing=True
        )

    def _build_trigger(self, schedule):
        """构建触发器"""
        if schedule.schedule_type == 'daily':
            # 每天 execute_time 执行
            hour, minute = schedule.execute_time.split(':')
            return CronTrigger(hour=int(hour), minute=int(minute))
        elif schedule.schedule_type == 'weekly':
            # 每周指定星期执行
            hour, minute = schedule.execute_time.split(':')
            days = [int(d) for d in schedule.weekdays.split(',')]
            return CronTrigger(day_of_week=days, hour=int(hour), minute=int(minute))
        elif schedule.schedule_type == 'cron':
            # Cron 表达式
            return CronTrigger.from_crontab(schedule.cron_expr)

    async def execute_manual(self, task_id: int, params: dict = None):
        """手动执行任务（立即）"""
        # 加入执行队列
        pass
```

### Pydantic 模型

```python
class ScheduleCreate(BaseModel):
    task_id: int
    schedule_type: str = Field(..., pattern='^(daily|weekly|cron)$')
    execute_time: Optional[str] = Field(None, pattern='^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
    weekdays: Optional[str] = None  # "1,2,3,4,5"
    cron_expr: Optional[str] = None
    enabled: int = Field(0, ge=0, le=1)

class ManualSyncRequest(BaseModel):
    task_id: int
    params: Optional[dict] = None  # 临时覆盖参数

class ScheduleResponse(BaseModel):
    id: int
    task_id: int
    task_name: str
    schedule_type: str
    execute_time: Optional[str]
    weekdays: Optional[str]
    cron_expr: Optional[str]
    enabled: int
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
```

## API 接口

### POST /api/v1/admin/sync-tasks/{task_id}/schedule
设置/更新任务调度

**请求示例**:
```json
{
  "schedule_type": "daily",
  "execute_time": "18:00",
  "enabled": 1
}
```

### PUT /api/v1/admin/sync-tasks/{task_id}/schedule/toggle
启用/暂停调度

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "enabled": 1,
    "next_run_at": "2026-08-08T18:00:00"
  }
}
```

### POST /api/v1/admin/sync-tasks/{task_id}/execute
手动触发同步（立即执行）

**请求示例**:
```json
{
  "task_id": 1,
  "params": {
    "trade_date": "20260808"
  }
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "同步任务已触发",
  "data": {
    "execution_id": "exec_20260808_001",
    "status": "running"
  }
}
```

### GET /api/v1/admin/schedules
获取调度列表

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 1,
        "task_id": 1,
        "task_name": "同步日线行情",
        "schedule_type": "daily",
        "execute_time": "18:00",
        "enabled": 1,
        "next_run_at": "2026-08-08T18:00:00",
        "last_run_at": "2026-08-07T18:00:00"
      }
    ]
  }
}
```

## 测试用例

### 正常流程
1. 为"同步日线行情"任务设置每日 18:00 调度
2. 启用调度，验证下次执行时间正确
3. 点击"立即同步"，验证任务立即执行
4. 手动同步时覆盖参数（指定交易日），验证参数生效

### 边界情况
1. 暂停调度，验证不再自动执行
2. 设置无效的 Cron 表达式，验证报错
3. 多个任务同时到点，验证并发控制生效
4. 手动同步参数覆盖，验证原始配置不变

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: ds-002-sync-task-management.md
- 下一个 Story: ds-004-sync-execution-logs.md