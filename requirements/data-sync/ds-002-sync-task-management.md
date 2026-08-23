# DS-002: 同步任务管理

## 用户故事

作为系统管理员，我希望能够为每个数据源创建同步任务，配置要同步的数据类型（如股票列表、日线行情、周线行情、月线行情等），并为每个任务设置同步参数（如"交易日"）、接口调用间隔时间和超时时间，以便灵活控制数据同步行为。

## 验收标准

### 功能需求

#### AC1: 查看同步任务列表
**Given**: 管理员进入同步任务管理页面
**When**: 选择某个数据源
**Then**: 显示该数据源下的所有同步任务
**And**: 包含任务名称、数据类型、目标数据、状态、最后同步时间等信息

#### AC2: 新增同步任务
**Given**: 在同步任务管理页面
**When**: 点击新增任务按钮
**Then**: 显示新增同步任务表单
**And**: 包含任务名称、数据源、数据接口、同步参数、目标表、调用间隔、超时时间等字段

#### AC3: 配置同步数据类型
**Given**: 新增同步任务
**When**: 选择数据接口
**Then**: 根据数据源类型显示可用的数据接口
**And**: 如 Tushare 显示：股票列表(stock_basic)、日线(daily)、周线(weekly)、月线(monthly)等

#### AC4: 配置同步参数
**Given**: 新增同步任务，已选择数据接口
**When**: 配置同步参数
**Then**: 显示该接口支持的参数（动态生成）
**And**: 例如日线/周线/月线行情可配置"交易日(trade_date)"或"起止日期"
**And**: 股票列表可配置"上市状态(list_status)"

#### AC5: 配置调用间隔
**Given**: 新增或编辑同步任务
**When**: 设置调用间隔时间
**Then**: 保存接口两次调用之间的等待时间（毫秒）
**And**: 同步执行时按此间隔调用接口，避免触发数据源限流

#### AC6: 配置超时时间
**Given**: 新增或编辑同步任务
**When**: 设置接口超时时间
**Then**: 保存超时时间（秒）
**And**: 接口调用超过此时间则判定为超时失败

#### AC7: 编辑同步任务
**Given**: 在同步任务列表
**When**: 点击编辑按钮
**Then**: 显示编辑表单
**And**: 数据源和数据接口为只读（修改可能影响数据结构）

#### AC8: 删除同步任务
**Given**: 在同步任务列表
**When**: 点击删除按钮
**Then**: 显示确认对话框
**And**: 确认后删除任务（同时删除调度配置）

#### AC9: 启用/禁用同步任务
**Given**: 在同步任务列表
**When**: 切换任务状态
**Then**: 禁用的任务不会被自动调度执行

## 表单字段要求

### 新增同步任务表单

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| 任务名称 | 文本 | 是 | 2-50字符 |
| 数据源 | 选择 | 是 | 关联数据源 |
| 数据接口 | 选择 | 是 | 根据数据源动态显示 |
| 同步模式 | 选择 | 是 | 全量同步/增量同步 |
| 同步参数 | 动态表单 | 否 | 根据接口动态生成 |
| 目标数据表 | 文本 | 是 | 自动填充（可修改） |
| 调用间隔(ms) | 数字 | 是 | 100-60000，默认500 |
| 超时时间(秒) | 数字 | 是 | 5-300，默认30 |
| 重试次数 | 数字 | 是 | 0-5，默认3 |
| 描述 | 文本 | 否 | 最多200字符 |
| 状态 | 开关 | 是 | 启用/禁用，默认启用 |

### 同步参数（动态生成示例）

> 各接口的完整字段定义、频率限制、限量请参考 **[Tushare 接口技术参考](tushare-api-reference.md)**。

#### 股票列表（stock_basic）
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `list_status` | 选择 | 否 | 上市状态：L上市/D退市/P暂停/G未交易，默认 L |
| `exchange` | 选择 | 否 | 交易所：SSE/SZSE/BSE |
| `market` | 选择 | 否 | 市场：主板/创业板/科创板/CDR/北交所 |
| `ts_code` | 文本 | 否 | TS 股票代码 |
| `is_hs` | 选择 | 否 | 沪深港通标的：N否/H沪股通/S深股通 |

#### 日线行情（daily）
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `trade_date` | 日期 | 否 | 交易日（YYYYMMDD），与 ts_code 二选一 |
| `ts_code` | 文本 | 否 | 股票代码（支持多个逗号分隔） |
| `start_date` | 日期 | 否 | 起始日期（YYYYMMDD） |
| `end_date` | 日期 | 否 | 结束日期（YYYYMMDD） |

> ⚠️ **最佳实践**：全市场同步建议**循环 trade_date**，不要循环 ts_code。

#### 周线行情（weekly）
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `trade_date` | 日期 | 否 | **每周最后一个交易日**（YYYYMMDD） |
| `ts_code` | 文本 | 否 | TS 代码 |
| `start_date` | 日期 | 否 | 起始日期 |
| `end_date` | 日期 | 否 | 结束日期 |

#### 月线行情（monthly）
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `trade_date` | 日期 | 否 | **每月最后一个交易日**（YYYYMMDD） |
| `ts_code` | 文本 | 否 | TS 代码 |
| `start_date` | 日期 | 否 | 起始日期 |
| `end_date` | 日期 | 否 | 结束日期 |

> 注：所有日期参数统一 **YYYYMMDD** 格式（如 20181010）。

## 技术实现

### 数据库模型

```sql
-- 同步任务配置表
CREATE TABLE sync_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '任务名称',
    source_id INT NOT NULL COMMENT '关联数据源ID',
    data_interface VARCHAR(50) NOT NULL COMMENT '数据接口名(stock_basic,daily等)',
    sync_mode VARCHAR(20) DEFAULT 'full' COMMENT '同步模式:full增量 incremental',
    target_table VARCHAR(50) NOT NULL COMMENT '目标数据表',
    interval_ms INT DEFAULT 500 COMMENT '调用间隔(毫秒)',
    timeout_seconds INT DEFAULT 30 COMMENT '超时时间(秒)',
    retry_count INT DEFAULT 3 COMMENT '重试次数',
    description VARCHAR(200) COMMENT '描述',
    status TINYINT DEFAULT 1 COMMENT '状态:1启用 0禁用',
    last_sync_at DATETIME COMMENT '最后同步时间',
    last_sync_status VARCHAR(20) COMMENT '最后同步状态:success/failed/running',
    last_sync_records INT COMMENT '最后同步记录数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES data_sources(id) ON DELETE RESTRICT
);

-- 同步任务参数表
CREATE TABLE sync_params (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id INT NOT NULL COMMENT '关联任务ID',
    param_key VARCHAR(50) NOT NULL COMMENT '参数名',
    param_value VARCHAR(200) COMMENT '参数值',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES sync_tasks(id) ON DELETE CASCADE,
    UNIQUE KEY uk_task_param (task_id, param_key)
);
```

### 接口元数据定义

> 接口的请求/响应结构、字段定义、频率限制详见 **[Tushare 接口技术参考](tushare-api-reference.md)**。
> 关键点：响应为 `fields`+`items` 二维结构（按位置对应）；日期统一 YYYYMMDD；`code=2002` 表示积分/Token 问题（不重试）。

```python
# 数据接口元数据（预定义每个接口支持的参数、目标表、频率限制）
# 字段定义以 tushare-api-reference.md 为准
INTERFACE_META = {
    "tushare": {
        "stock_basic": {
            "name": "股票列表",
            "target_table": "stocks",
            "unique_key": "ts_code",
            "limit_per_request": 6000,       # 单次最大行数
            "rate_limit_per_min": 50,        # 每分钟调用上限
            "default_interval_ms": 1200,     # 建议调用间隔(≥1000ms)
            "fields": [
                "ts_code", "symbol", "name", "area", "industry",
                "market", "exchange", "list_status", "list_date", "delist_date",
                "is_hs", "act_name", "act_ent_type"
            ],
            "params": [
                {"key": "list_status", "name": "上市状态", "type": "select",
                 "options": [("L", "上市"), ("D", "退市"), ("P", "暂停"), ("G", "未交易")], "default": "L"},
                {"key": "exchange", "name": "交易所", "type": "select",
                 "options": [("", "全部"), ("SSE", "上交所"), ("SZSE", "深交所"), ("BSE", "北交所")]},
                {"key": "ts_code", "name": "股票代码", "type": "text", "required": False}
            ]
        },
        "daily": {
            "name": "日线行情",
            "target_table": "daily_quotes",
            "unique_key": "(ts_code, trade_date)",
            "limit_per_request": 6000,
            "rate_limit_per_min": 500,
            "default_interval_ms": 130,
            "data_update_time": "交易日15:00~16:00入库(未复权)",
            "vol_unit": "手", "amount_unit": "千元",
            "fields": [
                "ts_code", "trade_date", "open", "high", "low", "close",
                "pre_close", "change", "pct_chg", "vol", "amount"
            ],
            "params": [
                {"key": "trade_date", "name": "交易日", "type": "date", "required": False,
                 "hint": "YYYYMMDD，推荐循环日期同步全市场"},
                {"key": "ts_code", "name": "股票代码", "type": "text", "required": False,
                 "hint": "与trade_date二选一，支持逗号分隔多个"},
                {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
                {"key": "end_date", "name": "结束日期", "type": "date", "required": False}
            ]
        },
        "weekly": {
            "name": "周线行情",
            "target_table": "weekly_quotes",
            "unique_key": "(ts_code, trade_date)",
            "limit_per_request": 6000,
            "min_points": 2000,
            "default_interval_ms": 500,
            "data_update_time": "每周最后一个交易日更新",
            "fields": [
                "ts_code", "trade_date", "open", "high", "low", "close",
                "pre_close", "change", "pct_chg", "vol", "amount"
            ],
            "params": [
                {"key": "trade_date", "name": "交易日", "type": "date", "required": False,
                 "hint": "每周最后一个交易日，YYYYMMDD"},
                {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
                {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
                {"key": "end_date", "name": "结束日期", "type": "date", "required": False}
            ]
        },
        "monthly": {
            "name": "月线行情",
            "target_table": "monthly_quotes",
            "unique_key": "(ts_code, trade_date)",
            "limit_per_request": 4500,
            "min_points": 2000,
            "default_interval_ms": 500,
            "fields": [
                "ts_code", "trade_date", "open", "high", "low", "close",
                "pre_close", "change", "pct_chg", "vol", "amount"
            ],
            "params": [
                {"key": "trade_date", "name": "交易日", "type": "date", "required": False,
                 "hint": "每月最后一个交易日，YYYYMMDD"},
                {"key": "ts_code", "name": "股票代码", "type": "text", "required": False},
                {"key": "start_date", "name": "起始日期", "type": "date", "required": False},
                {"key": "end_date", "name": "结束日期", "type": "date", "required": False}
            ]
        }
    }
}
```

### Pydantic 模型

```python
class SyncParam(BaseModel):
    param_key: str
    param_value: Optional[str] = None

class SyncTaskCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    source_id: int
    data_interface: str
    sync_mode: str = Field('full', pattern='^(full|incremental)$')
    target_table: str
    params: List[SyncParam] = []
    interval_ms: int = Field(500, ge=100, le=60000)
    timeout_seconds: int = Field(30, ge=5, le=300)
    retry_count: int = Field(3, ge=0, le=5)
    description: Optional[str] = None
    status: int = Field(1, ge=0, le=1)

class SyncTaskResponse(BaseModel):
    id: int
    name: str
    source_id: int
    source_name: str  # 关联数据源名称
    data_interface: str
    interface_name: str  # 接口中文名
    sync_mode: str
    target_table: str
    params: List[dict]
    interval_ms: int
    timeout_seconds: int
    retry_count: int
    status: int
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    last_sync_records: Optional[int]
```

## API 接口

### GET /api/v1/admin/data-sources/{source_id}/interfaces
获取数据源支持的接口列表（前端用于动态生成接口下拉框）

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {"value": "stock_basic", "label": "股票列表", "target_table": "stocks"},
    {"value": "daily", "label": "日线行情", "target_table": "daily_quotes"},
    {"value": "weekly", "label": "周线行情", "target_table": "weekly_quotes"},
    {"value": "monthly", "label": "月线行情", "target_table": "monthly_quotes"}
  ]
}
```

### GET /api/v1/admin/interfaces/{interface_name}/params
获取接口的参数定义（前端用于动态生成参数表单）

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {"key": "trade_date", "name": "交易日", "type": "date", "required": false},
    {"key": "start_date", "name": "起始日期", "type": "date", "required": false}
  ]
}
```

### GET /api/v1/admin/sync-tasks
获取同步任务列表（支持按数据源筛选）

### POST /api/v1/admin/sync-tasks
创建同步任务

**请求示例**:
```json
{
  "name": "同步日线行情",
  "source_id": 1,
  "data_interface": "daily",
  "sync_mode": "incremental",
  "target_table": "daily_quotes",
  "params": [
    {"param_key": "start_date", "param_value": "20260101"},
    {"param_key": "end_date", "param_value": "20260808"}
  ],
  "interval_ms": 500,
  "timeout_seconds": 30,
  "retry_count": 3,
  "status": 1
}
```

### PUT /api/v1/admin/sync-tasks/{task_id}
更新同步任务

### DELETE /api/v1/admin/sync-tasks/{task_id}
删除同步任务

## 测试用例

### 正常流程
1. 选择 Tushare 数据源，新增"同步股票列表"任务
2. 验证接口下拉框显示 stock_basic、daily 等
3. 选择 daily 接口，验证参数表单显示交易日、起止日期
4. 设置调用间隔 500ms，超时 30秒
5. 保存任务，验证配置正确

### 边界情况
1. 调用间隔设为 100ms（最小值），验证可保存
2. 超时时间设为 5秒（最小值），验证可保存
3. 删除数据源时，验证有关联任务被拒绝
4. 禁用任务，验证不被调度执行

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: ds-001-data-source-management.md
- 下一个 Story: ds-003-schedule-management.md