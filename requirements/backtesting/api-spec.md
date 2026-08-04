# 回测系统 API 规范

**版本：** v1.0
**最后更新：** 2026-05-05

---

## 基础信息

**Base URL:** `http://localhost:8000/api/v1`

**认证方式:** Bearer Token

**通用响应格式:**
```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

---

## 1. Tushare 数据源管理

### 1.1 获取配置

**接口地址:** `GET /admin/tushare/config`

**权限要求:** 管理员

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "your_token_here",
    "sync_interval": 3600,
    "last_sync": "2026-05-05T10:00:00Z"
  }
}
```

### 1.2 更新配置

**接口地址:** `PUT /admin/tushare/config`

**权限要求:** 管理员

**请求参数:**
```json
{
  "token": "new_token",
  "sync_interval": 1800
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "配置更新成功",
  "data": null
}
```

### 1.3 同步股票列表

**接口地址:** `POST /admin/data/sync/stocks`

**权限要求:** 管理员

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "同步完成",
  "data": {
    "added": 5000,
    "updated": 100,
    "failed": 5,
    "duration": "2.5s"
  }
}
```

### 1.4 同步行情数据

**接口地址:** `POST /admin/data/sync/prices`

**权限要求:** 管理员

**请求参数:**
```json
{
  "ts_code": "000001.SZ",
  "start_date": "2025-01-01",
  "end_date": "2026-05-05",
  "frequency": "daily"
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "同步完成",
  "data": {
    "inserted": 320,
    "updated": 0
  }
}
```

---

## 2. 策略管理

### 2.1 获取策略列表

**接口地址:** `GET /user/strategies`

**权限要求:** 登录用户

**请求参数:**
```
page: int = 1
page_size: int = 10
search: string (可选)
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "双均线策略",
        "description": "基于5日和20日均线交叉",
        "created_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-05T10:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 25
  }
}
```

### 2.2 创建策略

**接口地址:** `POST /user/strategies`

**权限要求:** 登录用户

**请求参数:**
```json
{
  "name": "双均线策略",
  "description": "基于5日和20日均线交叉",
  "code": "from zipline.api import order, record...",
  "parameters": {
    "short_period": 5,
    "long_period": 20,
    "shares": 100
  }
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "策略创建成功",
  "data": {
    "id": 123
  }
}
```

### 2.3 更新策略

**接口地址:** `PUT /user/strategies/{id}`

**权限要求:** 策略所有者

**请求参数:** 同创建策略

**响应示例:**
```json
{
  "code": 0,
  "message": "策略更新成功",
  "data": null
}
```

### 2.4 删除策略

**接口地址:** `DELETE /user/strategies/{id}`

**权限要求:** 策略所有者

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "策略删除成功",
  "data": null
}
```

### 2.5 获取策略详情

**接口地址:** `GET /user/strategies/{id}`

**权限要求:** 策略所有者

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "双均线策略",
    "description": "基于5日和20日均线交叉",
    "code": "from zipline.api import order, record...",
    "parameters": {
      "short_period": 5,
      "long_period": 20,
      "shares": 100
    },
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-05T10:00:00Z"
  }
}
```

### 2.6 获取策略模板

**接口地址:** `GET /user/strategies/templates`

**权限要求:** 登录用户

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "templates": [
      {
        "id": "ma_crossover",
        "name": "双均线策略",
        "description": "基于短期和长期均线交叉",
        "code": "from zipline.api import...",
        "parameters": {
          "short_period": {"type": "int", "default": 5},
          "long_period": {"type": "int", "default": 20},
          "shares": {"type": "int", "default": 100}
        }
      },
      {
        "id": "macd",
        "name": "MACD 策略",
        "description": "基于 MACD 指标的交易策略",
        "code": "...",
        "parameters": {
          "fast_period": {"type": "int", "default": 12},
          "slow_period": {"type": "int", "default": 26},
          "signal_period": {"type": "int", "default": 9}
        }
      }
    ]
  }
}
```

---

## 3. 回测执行

### 3.1 提交回测任务

**接口地址:** `POST /user/backtest/run`

**权限要求:** 登录用户

**请求参数:**
```json
{
  "strategy_id": 1,
  "stock_codes": ["000001.SZ", "000002.SZ"],
  "start_date": "2025-01-01",
  "end_date": "2026-05-05",
  "initial_capital": 100000,
  "commission": 0.001,
  "slippage": 0.0001
}
```

**响应示例:**
```json
{
  "code": 0,
  "message": "回测任务已提交",
  "data": {
    "task_id": "bt_20260505_123456",
    "status": "pending"
  }
}
```

### 3.2 查询回测状态

**接口地址:** `GET /user/backtest/{task_id}/status`

**权限要求:** 任务所有者

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "bt_20260505_123456",
    "status": "running",
    "progress": 65,
    "start_time": "2026-05-05T10:00:00Z",
    "current_date": "2026-03-15"
  }
}
```

**状态值说明:**
- `pending`: 等待执行
- `running`: 执行中
- `completed`: 执行完成
- `failed`: 执行失败
- `cancelled`: 已取消

### 3.3 获取回测结果

**接口地址:** `GET /user/backtest/{task_id}/result`

**权限要求:** 任务所有者

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "bt_20260505_123456",
    "strategy_id": 1,
    "strategy_name": "双均线策略",
    "period": {
      "start_date": "2025-01-01",
      "end_date": "2026-05-05",
      "trading_days": 320
    },
    "capital": {
      "initial": 100000,
      "final": 125680,
      "max": 135000,
      "min": 95000
    },
    "returns": {
      "total": 0.2568,
      "annual": 0.2135,
      "daily_avg": 0.0008
    },
    "risk": {
      "max_drawdown": -0.125,
      "volatility": 0.15,
      "sharpe_ratio": 1.25,
      "sortino_ratio": 1.45
    },
    "trades": {
      "total": 45,
      "buy": 23,
      "sell": 22,
      "win_rate": 0.62,
      "avg_return": 0.023
    },
    "equity_curve": [
      {"date": "2025-01-01", "equity": 100000},
      {"date": "2025-01-02", "equity": 100500}
    ],
    "drawdown_curve": [
      {"date": "2025-01-01", "drawdown": 0},
      {"date": "2025-01-02", "drawdown": 0.005}
    ],
    "created_at": "2026-05-05T11:00:00Z"
  }
}
```

### 3.4 获取交易明细

**接口地址:** `GET /user/backtest/{task_id}/trades`

**权限要求:** 任务所有者

**请求参数:**
```
page: int = 1
page_size: int = 50
direction: "buy" | "sell" | "all" (可选)
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "task_id": "bt_20260505_123456",
        "ts_code": "000001.SZ",
        "direction": "buy",
        "price": 10.5,
        "shares": 100,
        "amount": 1050,
        "commission": 1.05,
        "trade_date": "2025-01-05"
      }
    ],
    "page": 1,
    "page_size": 50,
    "total": 45
  }
}
```

### 3.5 取消回测任务

**接口地址:** `POST /user/backtest/{task_id}/cancel`

**权限要求:** 任务所有者

**请求参数:** 无

**响应示例:**
```json
{
  "code": 0,
  "message": "回测任务已取消",
  "data": null
}
```

### 3.6 获取回测历史

**接口地址:** `GET /user/backtest/history`

**权限要求:** 登录用户

**请求参数:**
```
page: int = 1
page_size: int = 10
strategy_id: int (可选)
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "task_id": "bt_20260505_123456",
        "strategy_name": "双均线策略",
        "total_return": 0.2568,
        "annual_return": 0.2135,
        "max_drawdown": -0.125,
        "sharpe_ratio": 1.25,
        "status": "completed",
        "created_at": "2026-05-05T11:00:00Z"
      }
    ],
    "page": 1,
    "page_size": 10,
    "total": 15
  }
}
```

---

## 4. 数据查询

### 4.1 查询股票行情

**接口地址:** `GET /user/stock/prices`

**权限要求:** 登录用户

**请求参数:**
```
ts_code: string (必需)
start_date: string (可选)
end_date: string (可选)
frequency: "daily" | "weekly" | "monthly" (默认: daily)
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ts_code": "000001.SZ",
    "prices": [
      {
        "trade_date": "2026-05-01",
        "open": 10.5,
        "high": 10.8,
        "low": 10.3,
        "close": 10.7,
        "volume": 1000000,
        "amount": 10700000
      }
    ]
  }
}
```

### 4.2 查询财务数据

**接口地址:** `GET /user/stock/financials`

**权限要求:** 登录用户

**请求参数:**
```
ts_code: string (必需)
start_date: string (可选)
end_date: string (可选)
```

**响应示例:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "ts_code": "000001.SZ",
    "financials": [
      {
        "end_date": "2026-03-31",
        "eps": 0.5,
        "revenue": 1000000000,
        "net_profit": 500000000,
        "roe": 0.15
      }
    ]
  }
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 401 | 未授权 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |
| 1001 | 策略代码验证失败 |
| 1002 | 回测参数错误 |
| 1003 | 数据不足，无法回测 |
| 1004 | 策略执行超时 |
| 2001 | Tushare Token 无效 |
| 2002 | Tushare API 调用频率超限 |
| 2003 | 数据同步失败 |

---

**文档结束**