# DS-004: 同步执行与日志

## 用户故事

作为系统管理员，我希望能够查看每次数据同步的执行情况，包括同步开始时间、结束时间、同步的数据量、成功或失败状态以及详细的错误信息，以便监控数据同步的健康状况，并在出现问题时能快速定位和修复。

## 验收标准

### 功能需求

#### AC1: 查看同步日志列表
**Given**: 管理员进入同步日志页面
**When**: 页面加载
**Then**: 显示同步执行记录列表
**And**: 包含任务名、开始时间、耗时、状态、记录数等信息
**And**: 支持按任务、状态、时间范围筛选

#### AC2: 查看同步详情
**Given**: 在同步日志列表
**When**: 点击某条记录
**Then**: 显示详细的执行过程
**And**: 包含每次接口调用的请求参数、响应状态、数据量、耗时

#### AC3: 实时执行进度
**Given**: 手动触发或定时触发的同步任务
**When**: 任务执行中
**Then**: 可查看实时进度（已处理/总数、当前状态）
**And**: 进度信息实时更新

#### AC4: 错误信息展示
**Given**: 同步失败的记录
**When**: 查看详情
**Then**: 显示详细的错误信息
**And**: 包含错误类型、错误消息、失败的接口调用

#### AC5: 同步统计
**Given**: 在同步日志页面
**When**: 查看统计区
**Then**: 显示今日同步次数、成功率、平均耗时、总记录数

#### AC6: 日志清理
**Given**: 同步日志累积过多
**When**: 执行日志清理
**Then**: 可按时间范围清理历史日志
**And**: 默认保留近30天日志

### 执行流程需求

#### AC7: 同步执行流程
**Given**: 任务开始执行
**When**: 执行同步
**Then**: 按以下流程执行：
1. 创建执行记录（状态：运行中）
2. 解析同步参数
3. 分页调用数据源接口（按 interval_ms 间隔）
4. 每页数据处理并写入目标表
5. 记录每次调用的详情
6. 更新执行记录（状态：成功/失败）

#### AC8: 重试机制
**Given**: 接口调用失败
**When**: 未超过重试次数
**Then**: 自动重试（按重试次数配置）
**And**: 重试间隔递增（指数退避）
**And**: 超过重试次数则标记失败

#### AC9: 间隔与超时控制
**Given**: 任务配置了 interval_ms 和 timeout_seconds
**When**: 执行同步
**Then**: 两次接口调用之间等待 interval_ms
**And**: 单次调用超过 timeout_seconds 则超时失败

## 日志记录要求

### 同步执行记录（汇总）
| 字段 | 说明 |
|------|------|
| 执行ID | 唯一标识 |
| 任务ID/名称 | 关联任务 |
| 触发方式 | manual(手动)/schedule(定时) |
| 开始时间 | 执行开始时间 |
| 结束时间 | 执行结束时间 |
| 耗时(秒) | 总耗时 |
| 状态 | running/success/failed/timeout |
| 总记录数 | 同步的数据总量 |
| API调用次数 | 接口调用总次数 |
| 错误信息 | 失败时的错误详情 |
| 触发用户 | 手动触发时的用户 |

### 接口调用记录（明细）
| 字段 | 说明 |
|------|------|
| 执行ID | 关联执行记录 |
| 调用序号 | 第几次调用 |
| 请求参数 | 本次调用的参数 |
| 请求时间 | 调用开始时间 |
| 响应时间 | 调用结束时间 |
| 耗时(毫秒) | 单次耗时 |
| 状态 | success/failed/timeout |
| 记录数 | 本次返回数据量 |
| 重试次数 | 本次重试了几次 |
| 错误信息 | 失败详情 |

## 技术实现

### 数据库模型

```sql
-- 同步执行记录表（汇总）
CREATE TABLE sync_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    execution_id VARCHAR(50) UNIQUE NOT NULL COMMENT '执行ID(exec_yyyymmdd_xxx)',
    task_id INT NOT NULL COMMENT '关联任务ID',
    task_name VARCHAR(50) COMMENT '任务名称(冗余)',
    source_name VARCHAR(50) COMMENT '数据源名称(冗余)',
    trigger_type VARCHAR(20) NOT NULL COMMENT '触发方式:manual,schedule',
    trigger_user_id INT COMMENT '手动触发的用户ID',
    status VARCHAR(20) DEFAULT 'running' COMMENT '状态:running,success,failed,timeout',
    total_records INT DEFAULT 0 COMMENT '总记录数',
    api_calls INT DEFAULT 0 COMMENT 'API调用次数',
    start_at DATETIME NOT NULL COMMENT '开始时间',
    end_at DATETIME COMMENT '结束时间',
    duration_seconds INT COMMENT '耗时(秒)',
    params_snapshot TEXT COMMENT '本次执行参数快照(JSON)',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES sync_tasks(id) ON DELETE CASCADE,
    INDEX idx_task_time (task_id, start_at),
    INDEX idx_status (status)
);

-- 同步接口调用记录表（明细）
CREATE TABLE sync_call_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    execution_id VARCHAR(50) NOT NULL COMMENT '关联执行ID',
    call_seq INT NOT NULL COMMENT '调用序号',
    request_params TEXT COMMENT '请求参数(JSON)',
    request_at DATETIME NOT NULL COMMENT '请求时间',
    response_at DATETIME COMMENT '响应时间',
    duration_ms INT COMMENT '耗时(毫秒)',
    status VARCHAR(20) NOT NULL COMMENT '状态:success,failed,timeout',
    record_count INT DEFAULT 0 COMMENT '返回记录数',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES sync_logs(execution_id) ON DELETE CASCADE,
    INDEX idx_execution (execution_id)
);
```

### 执行器实现

```python
class SyncExecutor:
    """同步任务执行器"""

    async def execute(self, task: SyncTask, trigger_type: str,
                      override_params: dict = None, user_id: int = None):
        """执行同步任务"""
        execution_id = self._gen_execution_id()
        params = self._merge_params(task, override_params)

        # 创建执行记录
        log = await self._create_log(execution_id, task, trigger_type, params, user_id)

        try:
            await self._update_log_status(execution_id, 'running')

            # 获取适配器
            adapter = DataSourceAdapterFactory.get_adapter(task.source.source_type)
            token = decrypt_token(task.source.token_encrypted)

            total_records = 0
            api_calls = 0
            page = 1

            while True:
                call_log = await self._execute_with_retry(
                    adapter, task, params, token, page, execution_id, api_calls
                )

                if call_log['status'] != 'success':
                    raise Exception(call_log['error_message'])

                data = call_log['data']
                if not data:
                    break

                # 写入目标表
                await self._write_to_target(task.target_table, data)
                total_records += len(data)
                api_calls += 1

                # 调用间隔
                await asyncio.sleep(task.interval_ms / 1000)

                # 是否最后一页
                if len(data) < PAGE_SIZE:
                    break
                page += 1

            # 更新执行记录为成功
            await self._complete_log(execution_id, 'success', total_records, api_calls)

        except Exception as e:
            await self._complete_log(execution_id, 'failed', total_records, api_calls, str(e))

    async def _execute_with_retry(self, adapter, task, params, token, page, ...):
        """带重试的接口调用"""
        for attempt in range(task.retry_count + 1):
            try:
                # 带超时的调用
                data = await asyncio.wait_for(
                    adapter.fetch_data(task.data_interface, params, token),
                    timeout=task.timeout_seconds
                )
                return {'status': 'success', 'data': data}
            except asyncio.TimeoutError:
                if attempt < task.retry_count:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                return {'status': 'timeout', 'error_message': '接口超时'}
            except Exception as e:
                if attempt < task.retry_count:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {'status': 'failed', 'error_message': str(e)}
```

### Pydantic 模型

```python
class SyncLogResponse(BaseModel):
    id: int
    execution_id: str
    task_id: int
    task_name: str
    source_name: str
    trigger_type: str
    status: str
    total_records: int
    api_calls: int
    start_at: datetime
    end_at: Optional[datetime]
    duration_seconds: Optional[int]
    error_message: Optional[str]

class SyncLogDetail(SyncLogResponse):
    params_snapshot: Optional[dict]
    trigger_user_id: Optional[int]
    call_logs: List[SyncCallLogResponse]  # 接口调用明细

class SyncCallLogResponse(BaseModel):
    call_seq: int
    request_params: Optional[dict]
    request_at: datetime
    response_at: Optional[datetime]
    duration_ms: Optional[int]
    status: str
    record_count: int
    retry_count: int
    error_message: Optional[str]

class SyncStats(BaseModel):
    today_count: int
    success_rate: float
    avg_duration: float
    total_records: int
```

## API 接口

### GET /api/v1/admin/sync-logs
获取同步日志列表

**请求参数**:
- `page`: 页码
- `page_size`: 每页数量
- `task_id`: 按任务筛选
- `status`: 按状态筛选（running/success/failed/timeout）
- `start_date`: 开始日期
- `end_date`: 结束日期

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 1,
        "execution_id": "exec_20260808_001",
        "task_id": 1,
        "task_name": "同步日线行情",
        "source_name": "Tushare主数据源",
        "trigger_type": "schedule",
        "status": "success",
        "total_records": 4500,
        "api_calls": 5,
        "start_at": "2026-08-08T18:00:00",
        "end_at": "2026-08-08T18:00:12",
        "duration_seconds": 12,
        "error_message": null
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 1
  }
}
```

### GET /api/v1/admin/sync-logs/{execution_id}
获取同步执行详情（含接口调用明细）

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "id": 1,
    "execution_id": "exec_20260808_001",
    "task_name": "同步日线行情",
    "status": "success",
    "total_records": 4500,
    "params_snapshot": {"trade_date": "20260808"},
    "call_logs": [
      {
        "call_seq": 1,
        "request_params": {"page": 1, "page_size": 1000},
        "request_at": "2026-08-08T18:00:00",
        "response_at": "2026-08-08T18:00:01",
        "duration_ms": 1050,
        "status": "success",
        "record_count": 1000,
        "retry_count": 0
      },
      {
        "call_seq": 2,
        "request_params": {"page": 2, "page_size": 1000},
        "request_at": "2026-08-08T18:00:02",
        "response_at": "2026-08-08T18:00:03",
        "duration_ms": 980,
        "status": "success",
        "record_count": 1000,
        "retry_count": 0
      }
    ]
  }
}
```

### GET /api/v1/admin/sync-logs/{execution_id}/progress
获取实时执行进度

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "execution_id": "exec_20260808_002",
    "status": "running",
    "current_records": 2000,
    "api_calls": 2,
    "elapsed_seconds": 5,
    "last_call_at": "2026-08-08T18:00:03"
  }
}
```

### GET /api/v1/admin/sync-stats
获取同步统计

**请求参数**:
- `date`: 统计日期，默认今天

**响应示例**:
```json
{
  "code": 0,
  "data": {
    "today_count": 15,
    "success_count": 14,
    "failed_count": 1,
    "success_rate": 93.3,
    "avg_duration": 18.5,
    "total_records": 25000
  }
}
```

### DELETE /api/v1/admin/sync-logs
清理历史日志

**请求参数**:
- `before_date`: 清理此日期之前的日志

**响应示例**:
```json
{
  "code": 0,
  "message": "清理完成",
  "data": {
    "deleted_count": 320
  }
}
```

## 同步执行流程图

```
任务触发（手动/定时）
       ↓
创建执行记录（running）
       ↓
解析同步参数
       ↓
获取数据源适配器 + 解密Token
       ↓
┌─────────────────────────┐
│  循环分页调用接口        │
│  ├─ 调用接口（带超时）   │
│  ├─ 失败则重试（退避）   │
│  ├─ 记录调用明细         │
│  ├─ 数据写入目标表       │
│  └─ 等待 interval_ms     │
└─────────────────────────┘
       ↓
更新执行记录（success/failed）
       ↓
更新任务最后同步信息
```

## 测试用例

### 正常流程
1. 手动触发同步任务，验证返回 execution_id
2. 查询进度接口，验证状态为 running 且记录数递增
3. 等待执行完成，验证状态变为 success
4. 查看详情，验证接口调用明细完整

### 错误处理
1. Token 错误触发同步，验证状态为 failed，错误信息正确
2. 接口超时（设较短 timeout），验证触发重试后标记 timeout
3. 数据源不可达，验证错误信息友好

### 日志管理
1. 同步多次后查看日志列表，验证筛选功能
2. 查看统计，验证数据准确
3. 清理历史日志，验证只删除指定日期之前的

### 并发场景
1. 同一任务多次手动触发，验证排队执行
2. 多任务并发执行，验证并发数控制

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: ds-002-sync-task-management.md, ds-003-schedule-management.md
- 上一个 Story: ds-003-schedule-management.md
