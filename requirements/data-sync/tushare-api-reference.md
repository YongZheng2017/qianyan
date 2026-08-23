# Tushare 接口技术参考

> 本文档基于 Tushare 官方文档整理，作为数据同步模块（DS-002 ~ DS-004）的接口实现依据。
> 参考来源：
> - 调取数据：https://tushare.pro/document/1?doc_id=40
> - 股票列表：https://tushare.pro/document/2?doc_id=25
> - 历史日线行情：https://tushare.pro/document/2?doc_id=27
> - 历史周线行情：https://tushare.pro/document/2?doc_id=144
> - 历史月线行情：https://tushare.pro/document/2?doc_id=145

---

## 一、统一调用方式（HTTP）

Tushare Pro 接口采用 **POST + JSON Body** 方式，所有接口共用同一个请求地址。

- **请求地址**：`http://api.tushare.pro`
- **请求方法**：`POST`
- **Content-Type**：`application/json`

### 请求体结构

```json
{
  "api_name": "daily",
  "token": "你的tushare-token",
  "params": {
    "trade_date": "20180810"
  },
  "fields": "ts_code,trade_date,open,high,low,close,vol,amount"
}
```

| 字段 | 说明 |
|------|------|
| `api_name` | 接口名称（如 `stock_basic`、`daily`、`weekly`、`monthly`） |
| `token` | 用户唯一凭证，从 Tushare 个人主页获取 |
| `params` | 接口参数，键值对（如 `trade_date`、`start_date`、`ts_code`） |
| `fields` | 指定返回字段，逗号分隔（可选，省略则返回全部默认字段） |

### 响应结构

```json
{
  "code": 0,
  "msg": null,
  "data": {
    "fields": ["ts_code", "trade_date", "open", "high", "low", "close", "vol", "amount"],
    "items": [
      ["000001.SZ", "20180718", 8.75, 8.85, 8.69, 8.70, 525152.77, 460697.377],
      ["000001.SZ", "20180717", 8.74, 8.75, 8.66, 8.72, 375356.33, 326396.994]
    ]
  }
}
```

| 字段 | 说明 |
|------|------|
| `code` | 返回码，`0` 表示成功，`2002` 表示权限不足 |
| `msg` | 错误信息，成功时为 `null` |
| `data.fields` | 字段名列表（列头） |
| `data.items` | 数据行，与 `fields` **按位置一一对应**（注意是行式存储，非对象数组） |

> ⚠️ **关键点**：响应是 `fields` + `items` 的二维结构，需手动按位置映射成字典数组。

### Python SDK 调用（备选）

如使用官方 SDK，调用更简单（自动处理分页映射）：

```python
import tushare as ts
pro = ts.pro_api('your token')
df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')
# 等价于 pro.query('daily', ts_code='000001.SZ', start_date='20180701', end_date='20180718')
```

**建议**：本系统采用 **HTTP 方式**（避免依赖 SDK 的 pandas），便于精细控制调用间隔与超时。

---

## 二、股票列表 stock_basic

- **接口**：`stock_basic`
- **描述**：获取基础信息，包括股票代码、名称、上市日期、退市日期等
- **权限**：2000 积分起，**每分钟请求 50 次**
- **限量**：每次最多返回 **6000 行**（覆盖全市场 A 股，随股票总数增长）
- **建议**：基础信息调取一次即可拉完，建议保存到本地存储后使用

### 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|------|------|
| `ts_code` | str | N | TS 股票代码 |
| `name` | str | N | 名称 |
| `market` | str | N | 市场类别（主板/创业板/科创板/CDR/北交所） |
| `list_status` | str | N | 上市状态：L 上市 / D 退市 / P 暂停 / G 未交易，**默认 L** |
| `exchange` | str | N | 交易所：SSE 上交所 / SZSE 深交所 / BSE 北交所 |
| `is_hs` | str | N | 是否沪深港通标的：N 否 / H 沪股通 / S 深股通 |

### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
|------|------|----------|------|
| `ts_code` | str | Y | TS 代码 |
| `symbol` | str | Y | 股票代码 |
| `name` | str | Y | 股票名称 |
| `area` | str | Y | 地域 |
| `industry` | str | Y | 所属行业 |
| `fullname` | str | N | 股票全称 |
| `enname` | str | N | 英文全称 |
| `cnspell` | str | Y | 拼音缩写 |
| `market` | str | Y | 市场类型（主板/创业板/科创板/CDR） |
| `exchange` | str | N | 交易所代码 |
| `curr_type` | str | N | 交易货币 |
| `list_status` | str | N | 上市状态 L/D/G/P |
| `list_date` | str | Y | 上市日期 |
| `delist_date` | str | N | 退市日期 |
| `is_hs` | str | N | 是否沪深港通标的 |
| `act_name` | str | Y | 实控人名称 |
| `act_ent_type` | str | Y | 实控人企业性质 |

### 调用示例

```bash
curl -X POST -d '{"api_name": "stock_basic", "token": "xxx", "params": {"exchange":"", "list_status":"L"}, "fields": "ts_code,symbol,name,area,industry,list_date"}' http://api.tushare.pro
```

---

## 三、日线行情 daily

- **接口**：`daily`
- **描述**：获取 A 股日线行情（**未复权**，停牌期间无数据）
- **数据更新**：交易日每天 **15:00～16:00** 之间入库
- **权限**：基础积分，**每分钟 500 次**，每次 **6000 条**
- **限量**：单次最大 6000 行（一次请求 ≈ 提取一个股票 23 年历史）
- **重要建议**：**循环日期**提取全市场数据，**不要循环 ts_code** 拉历史

### 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|------|------|
| `ts_code` | str | N | 股票代码（支持多个，逗号分隔） |
| `trade_date` | str | N | 交易日期（YYYYMMDD） |
| `start_date` | str | N | 开始日期（YYYYMMDD） |
| `end_date` | str | N | 结束日期（YYYYMMDD） |

> 注：`ts_code` 与 `trade_date` 二选一；日期统一 YYYYMMDD 格式（如 20181010）。

### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
|------|------|----------|------|
| `ts_code` | str | Y | 股票代码 |
| `trade_date` | str | Y | 交易日期 |
| `open` | float | Y | 开盘价 |
| `high` | float | Y | 最高价 |
| `low` | float | Y | 最低价 |
| `close` | float | Y | 收盘价 |
| `pre_close` | float | Y | 昨收价【除权价】 |
| `change` | float | Y | 涨跌额 |
| `pct_chg` | float | Y | 涨跌幅（%）【基于除权后昨收计算】 |
| `vol` | float | Y | 成交量（**手**） |
| `amount` | float | Y | 成交额（**千元**） |
| `ah_vol` | float | N | 盘后成交量（手） |
| `ah_amount` | float | N | 盘后成交额（千元） |

### 调用示例

```bash
# 单个股票跨时间段历史日线
curl -X POST -d '{"api_name": "daily", "token": "xxx", "params": {"ts_code":"000001.SZ", "start_date":"20180701", "end_date":"20180718"}}' http://api.tushare.pro

# 某一天全市场历史
curl -X POST -d '{"api_name": "daily", "token": "xxx", "params": {"trade_date":"20180810"}}' http://api.tushare.pro
```

---

## 四、周线行情 weekly

- **接口**：`weekly`
- **描述**：获取 A 股周线行情（每周最后一个交易日更新）
- **权限**：2000 积分起
- **限量**：单次最大 **6000 行**，可用交易日期循环提取，总量不限

### 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|------|------|
| `ts_code` | str | N | TS 代码 |
| `trade_date` | str | N | 交易日期（**每周最后一个交易日**，YYYYMMDD） |
| `start_date` | str | N | 开始日期 |
| `end_date` | str | N | 结束日期 |

### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
|------|------|----------|------|
| `ts_code` | str | Y | 股票代码 |
| `trade_date` | str | Y | 交易日期 |
| `close` | float | Y | 周收盘价 |
| `open` | float | Y | 周开盘价 |
| `high` | float | Y | 周最高价 |
| `low` | float | Y | 周最低价 |
| `pre_close` | float | Y | 上一周收盘价 |
| `change` | float | Y | 周涨跌额 |
| `pct_chg` | float | Y | 周涨跌（**未 ×100**，复权请用通用行情接口，需 % 请 ×100） |
| `vol` | float | Y | 周成交量 |
| `amount` | float | Y | 周成交额 |

---

## 五、月线行情 monthly

- **接口**：`monthly`
- **描述**：获取 A 股月线行情
- **权限**：2000 积分起
- **限量**：单次最大 **4500 行**，总量不限

### 输入参数

| 名称 | 类型 | 必选 | 描述 |
|------|------|------|------|
| `ts_code` | str | N | TS 代码 |
| `trade_date` | str | N | 交易日期（**每月最后一个交易日**，YYYYMMDD） |
| `start_date` | str | N | 开始日期 |
| `end_date` | str | N | 结束日期 |

### 输出参数

| 名称 | 类型 | 默认显示 | 描述 |
|------|------|----------|------|
| `ts_code` | str | Y | 股票代码 |
| `trade_date` | str | Y | 交易日期 |
| `close` | float | Y | 月收盘价 |
| `open` | float | Y | 月开盘价 |
| `high` | float | Y | 月最高价 |
| `low` | float | Y | 月最低价 |
| `pre_close` | float | Y | 上月收盘价 |
| `change` | float | Y | 月涨跌额 |
| `pct_chg` | float | Y | 月涨跌幅（**未 ×100**） |
| `vol` | float | Y | 月成交量 |
| `amount` | float | Y | 月成交额 |

---

## 六、本系统对接要点（对接 DS-002 ~ DS-004）

### 1. 调用频率与限流（对应 DS-002 的 interval_ms）

| 接口 | 频率限制 | 建议 interval_ms |
|------|----------|------------------|
| stock_basic | 50 次/分钟 | ≥ 1200ms（即每分钟 ≤ 50 次） |
| daily | 500 次/分钟 | ≥ 130ms |
| weekly | 2000 积分限流 | ≥ 500ms（保守） |
| monthly | 2000 积分限流 | ≥ 500ms（保守） |

> 系统应按接口的频率限制设置默认调用间隔，并在配置中允许上调（不可低于限流值）。

### 2. 分页与单次限量（对应 DS-004 执行流程）

Tushare 的"分页"通过**循环 trade_date 或 offset 字段**实现，而非传统 page/page_size：

- **stock_basic**：单次 6000 行，一般一次拉完
- **daily**：单次 6000 行（≈1 只股票 23 年），**推荐按 trade_date 循环**全市场
- **weekly / monthly**：单次 6000/4500 行，按 trade_date 循环

> ⚠️ 执行器不应假设 `items` 为空即结束，需结合**返回行数 < 单次限量**判断是否还有数据；按日期循环的场景需遍历所有目标交易日。

### 3. 数据映射（fields + items → 对象）

```python
def parse_response(resp: dict) -> list[dict]:
    """将 Tushare 的 fields/items 结构转为字典列表"""
    data = resp.get("data") or {}
    fields = data.get("fields", [])
    items = data.get("items", [])
    return [dict(zip(fields, row)) for row in items]
```

### 4. 错误码处理（对应 DS-004 错误处理）

| code | 含义 | 处理 |
|------|------|------|
| 0 | 成功 | 正常处理 |
| 2002 | 权限/积分不足 | 标记失败，提示用户检查 Token 积分（**不应重试**） |
| 其它 | 网络/服务异常 | 按 retry_count 重试（指数退避） |

### 5. Token 配置（对应 DS-001）

- Token 通过数据源配置管理（DS-001），加密存储
- 测试连接可调用 `stock_basic` 验证 Token 有效性（返回 code=0 即有效，2002 即积分/Token 问题）

### 6. 目标表字段映射（对应 DS-002 target_table）

| 接口 | 目标表 | 主键/唯一键建议 |
|------|--------|------------------|
| stock_basic | `stocks` | `ts_code` |
| daily | `daily_quotes` | `(ts_code, trade_date)` |
| weekly | `weekly_quotes` | `(ts_code, trade_date)` |
| monthly | `monthly_quotes` | `(ts_code, trade_date)` |

> 字段单位注意：daily 的 `vol` 单位是"手"，`amount` 单位是"千元"，落库时建议保留原始单位并在文档注明，避免计算错误。

---

## 七、相关需求文档

- [DS-001 数据源管理](ds-001-data-source-management.md)
- [DS-002 同步任务管理](ds-002-sync-task-management.md)
- [DS-003 同步调度管理](ds-003-schedule-management.md)
- [DS-004 同步执行与日志](ds-004-sync-execution-logs.md)