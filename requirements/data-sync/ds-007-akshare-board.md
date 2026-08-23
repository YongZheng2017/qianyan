# DS-007: AKShare 板块数据同步

## 用户故事

作为系统管理员，我希望通过 AKShare（开源免费财经数据库）同步**行业板块**数据，包括行业板块列表和板块日线/周线/月线行情，为分析端「行情-板块」标签提供数据，并支撑板块层面的资金/趋势分析。

## 数据源特性（与 Tushare 的差异）

| 维度 | Tushare | AKShare |
|------|---------|---------|
| 调用方式 | HTTP API（POST + JSON）| **Python SDK**（`import akshare as ak`）|
| 凭证 | 需要 Token（积分制）| **无需 Token**（免费开源）|
| 字段命名 | 英文 | **中文**（开盘/收盘/涨跌幅...）|
| 数据来源 | 自有 | 聚合东方财富/新浪等 |
| 异步 | httpx 异步 | 同步库（需 `asyncio.to_thread` 包装）|

> 适配器模式的体现：AKShareAdapter 与 TushareAdapter 实现同一接口，但底层调用方式完全不同。新增数据源只需实现适配器。

## 接口清单

### 1. 行业板块列表（stock_board_industry_name_em）

| 项 | 值 |
|----|-----|
| AKShare 函数 | `ak.stock_board_industry_name_em()` |
| 来源 | 东方财富 |
| 描述 | 获取东方财富-行业板块-所有板块的列表信息 |
| 限量 | 单次返回全部板块（约 100 个）|
| 凭证 | 无需 |

**输入参数**：无（可选 `symbol`/`standard`，默认全部）

**输出字段**（以实际为准，常见）：
- 板块名称、板块代码、最新价、涨跌额、涨跌幅、总市值、换手率、上涨家数、下跌家数、领涨股票、领涨涨跌幅

**目标表**：`board_industry`

### 2. 行业板块历史行情（stock_board_industry_hist_em）

| 项 | 值 |
|----|-----|
| AKShare 函数 | `ak.stock_board_industry_hist_em(symbol, period, start_date, end_date, adjust)` |
| 来源 | 东方财富 https://quote.eastmoney.com/bk/90.BK1027.html |
| 描述 | 行业板块的历史行情（日/周/月K）|
| 限量 | 单次返回指定板块的所有历史数据 |

**输入参数**：

| 参数 | 必填 | 说明 |
|------|------|------|
| `symbol` | **Y** | 板块名称（如"小金属"），来自板块列表 |
| `start_date` | N | 开始日期 YYYYMMDD |
| `end_date` | N | 结束日期 YYYYMMDD |
| `period` | N | `日k`/`周k`/`月k`（默认日k）|
| `adjust` | N | `""`不复权/`qfq`前复权/`hfq`后复权（默认""）|

**输出字段（中文→英文映射）**：

| 中文 | 英文列 | 说明 |
|------|--------|------|
| 日期 | trade_date | YYYYMMDD |
| 开盘 | open | |
| 收盘 | close | |
| 最高 | high | |
| 最低 | low | |
| 涨跌幅 | pct_chg | % |
| 涨跌额 | change | |
| 成交量 | vol | 手 |
| 成交额 | amount | 元 |
| 振幅 | amplitude | % |
| 换手率 | turnover | % |

**目标表**：`board_industry_quotes`

## 同步模式

### 板块列表
- 单次调用 `stock_board_industry_name_em()` 获取全部板块
- 全量覆盖（每次同步全量 UPSERT）

### 板块行情
- **单板块同步**：`symbol=小金属` + 日期范围 → 该板块历史行情
- **全板块同步**（需执行器增强）：先获取板块列表，循环每个板块调用 `stock_board_industry_hist_em`，按 `interval_ms` 间隔
  > v1 支持单板块，全板块循环作为执行器增强项（DS-002 扩展）

## 数据库设计

```sql
-- 行业板块列表
CREATE TABLE board_industry (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    board_name VARCHAR(50) NOT NULL COMMENT '板块名称',
    board_code VARCHAR(20) COMMENT '板块代码',
    latest_price DECIMAL(10,4) COMMENT '最新价',
    change_amount DECIMAL(10,4) COMMENT '涨跌额',
    pct_chg DECIMAL(10,4) COMMENT '涨跌幅%',
    total_market_cap DECIMAL(20,4) COMMENT '总市值',
    turnover DECIMAL(10,4) COMMENT '换手率%',
    up_count INT COMMENT '上涨家数',
    down_count INT COMMENT '下跌家数',
    leader_stock VARCHAR(50) COMMENT '领涨股票',
    leader_pct_chg DECIMAL(10,4) COMMENT '领涨涨跌幅%',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_board (board_name)
);

-- 行业板块行情（日/周/月K）
CREATE TABLE board_industry_quotes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    board_name VARCHAR(50) NOT NULL COMMENT '板块名称',
    trade_date VARCHAR(8) NOT NULL COMMENT '交易日',
    period VARCHAR(4) DEFAULT '日k' COMMENT '周期:日k/周k/月k',
    open DECIMAL(10,4), high DECIMAL(10,4), low DECIMAL(10,4), close DECIMAL(10,4),
    pct_chg DECIMAL(10,4) COMMENT '涨跌幅%',
    change DECIMAL(10,4) COMMENT '涨跌额',
    vol BIGINT COMMENT '成交量(手)',
    amount DECIMAL(20,4) COMMENT '成交额(元)',
    amplitude DECIMAL(10,4) COMMENT '振幅%',
    turnover DECIMAL(10,4) COMMENT '换手率%',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_board_quote (board_name, trade_date, period),
    INDEX idx_board_date (board_name, trade_date)
);
```

## 适配器实现要点

`AKShareAdapter`（与 TushareAdapter 同级）：
- `get_credentials_schema()` → `[]`（无需凭证）
- `test_connection()` → 调用 `stock_board_industry_name_em()` 验证 akshare 可用
- `fetch_data()` → 用 `asyncio.to_thread` 包装同步 SDK 调用，DataFrame 转字典列表，中文列名映射英文
- 注册到 `DataSourceAdapterFactory._adapters["akshare"]`

## 验收标准

- [ ] 能创建 AKShare 数据源（无需 token）
- [ ] 能同步行业板块列表（board_industry 表）
- [ ] 能同步单板块历史行情（board_industry_quotes 表）
- [ ] 中文字段正确映射为英文列
- [ ] 凭证 schema 返回空（前端不显示凭证配置区）

## 相关文档

- [数据源管理](ds-001-data-source-management.md)
- [同步任务管理](ds-002-sync-task-management.md)
- AKShare 文档：https://akshare.akfamily.xyz/data/stock/stock.html