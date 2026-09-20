# DS-009: 同花顺（THS）数据源接入

## 用户故事

作为系统管理员，我希望接入同花顺金融数据 API 作为第三个数据源，获取 A 股行情、财务、估值、板块指数及特色数据（热榜/龙虎榜/涨停池），弥补现有数据源缺口（尤其估值快照与同花顺板块），并作为 Tushare 的备份与交叉校验来源。

## 数据源特性（与现有两源对比）

| 维度 | Tushare | AKShare | **同花顺 (THS)** |
|------|---------|---------|------------------|
| 调用方式 | HTTP POST + JSON body | Python SDK | **REST GET + X-api-key 请求头** |
| 凭证 | Token（积分制）| 无 | **API Key（按 capability 授权 + QPS 限制）** |
| 标的代码 | ts_code (`600519.SH`) | 各异 | **thscode（同 ts_code 格式，如 `600519.SH`）** ✅ |
| 响应结构 | fields+items 行式 | DataFrame | **统一信封 `{code, message, data:{item:[...]}}`** |
| 成功判定 | code=0 | 无异常 | **HTTP 恒 200，业务码 code=0** |
| 时间 | 字符串日期 | 混合 | **毫秒时间戳（Asia/Shanghai）**，日期字段 `yyyyMMdd` |

### 通用约定（来自官方文档）

- **Base URL**：`https://fuyao.aicubes.cn`
- **认证**：请求头 `X-api-key: <key>`；缺失/无效 `code=2001`，无权限 `code=2003`
- **错误码（fatal 不可重试 vs 可重试）**：
  - 不可重试：2001/2003（认证）、1001-1004（参数）、3001/3004（标的）
  - 可重试：4001（QPS 超限）、5001/5002/5003（服务端）
  - 3002（数据未就绪）视为空数据而非错误
- 一次可传多个 thscode 的接口以逗号分隔（部分接口禁止逗号，按端点参数表）

## 接口能力全景与分期

### Phase 1（本期实现，6 个）

| # | 能力 | 端点 | 对应能力 | 目标表（复用/新增）| 说明 |
|---|------|------|----------|--------------------|------|
| 1 | 历史K线 | `/api/a-share/prices/historical` | 日K | **复用 `daily_quotes`** | 单标的日K序列，与 Tushare daily 交叉校验 |
| 2 | 估值快照 | `/api/a-share/valuations/snapshot` | 估值 | **新增 `ths_valuation_snapshot`** | PE(TTM/MRQ)、PB(MRQ)、PS(TTM)、PCF(TTM)——补 FA-001 估值分析缺口 |
| 3 | 财务指标 | `/api/a-share/financials/indicators` | 财务 | **复用 `fin_indicator` + raw_data** | 成长/盈利/偿债/营运/现金流五类 |
| 4 | 同花顺指数列表 | `/api/a-share-index/list` | 板块 | **新增 `ths_index`** | 同花顺行业/概念指数目录（按 tag 过滤）|
| 5 | 同花顺指数成分股 | `/api/a-share-index/constituents` | 板块 | **新增 `ths_index_constituent`** | 板块→个股映射 |
| 6 | 指数历史K线 | `/api/a-share-index/prices/historical` | 板块行情 | **新增 `ths_index_quotes`** | 板块/行业指数日K（补行情-板块）|

### Phase 2（后续，特色数据）

| 能力 | 端点 | 用途 |
|------|------|------|
| 热股榜/飙升榜 | `/api/a-share/special-data/hot-list` | 市场情绪 |
| 涨停池/跌停池/炸板池/连板天梯 | `/api/a-share/special-data/limit-*` | 打板/情绪分析 |
| 龙虎榜（全/机构/游资） | `/api/a-share/special-data/dragon-tiger` | 游资动向 |
| 个股异动原因 | `/api/a-share/special-data/anomaly` | 异动归因 |
| 除复权事件流 | `/api/a-share/corporate-actions` | 复权因子 |
| 交易日历 | `/api/a-share/calendar` | 交易日驱动调度 |
| 标的检索/代码表 | `/api/meta/tickers/*` | 标的主数据 |
| 全市场 Parquet 导出 | `/api/dump/market-dumps` | 10年全量日K初始化 |

> 基金类接口（约 20 个）暂不纳入范围。

## 关键设计点

### 1. THS 适配器（ThsAdapter）
- `get_credentials_schema()` → `[{"key":"api_key","type":"password","required":true}]`
- `fetch_data`：GET + `X-api-key` 头；按接口元数据拼接 query 参数
- 响应解析：读信封 `code`；`code=0` 取 `data.item`；错误码按 fatal/可重试分类（执行器已有该机制，天然兼容）
- **时间戳转换**：毫秒时间戳 → `yyyyMMdd`（写入与现有表一致的字符串日期）

### 2. 复用既有表 + 字段映射
历史K线/财务指标映射到现有列（ths 字段名→现有列名 alias，复用 DS-008 引入的 `field_alias` 机制）；估值与同花顺指数为新增表。

### 3. QPS 与间隔
默认 `interval_ms` ≥ 600（保守，具体以套餐 QPS 为准）；4001 超限时由执行器指数退避重试。

## 新增数据库设计（3 张）

```sql
-- 同花顺估值快照（多股一次查询）
CREATE TABLE ths_valuation_snapshot (
    id BIGINT PK AUTO_INCREMENT,
    thscode VARCHAR(20) NOT NULL,
    trade_date VARCHAR(8) NOT NULL,          -- 快照日(由时间戳转换)
    pe_ttm DECIMAL(20,4), pe_mrq DECIMAL(20,4),
    pb_mrq DECIMAL(20,4), ps_ttm DECIMAL(20,4), pcf_ttm DECIMAL(20,4),
    raw_data JSON,
    UNIQUE KEY uk_ths_val (thscode, trade_date)
);

-- 同花顺指数（行业/概念/标准指数）
CREATE TABLE ths_index (
    id BIGINT PK AUTO_INCREMENT,
    thscode VARCHAR(20) UNIQUE NOT NULL,     -- 如 90.BK1027
    name VARCHAR(50), tag VARCHAR(20),       -- 行业/概念/沪深300等
    raw_data JSON
);

-- 同花顺指数日K
CREATE TABLE ths_index_quotes (
    id BIGINT PK AUTO_INCREMENT,
    thscode VARCHAR(20) NOT NULL,
    trade_date VARCHAR(8) NOT NULL,
    open/high/low/close DECIMAL(20,4), vol BIGINT, amount DECIMAL(20,4),
    pct_chg DECIMAL(10,4),
    raw_data JSON,
    UNIQUE KEY uk_ths_idx_q (thscode, trade_date)
);
-- 成分股
CREATE TABLE ths_index_constituent (
    id BIGINT PK AUTO_INCREMENT,
    index_code VARCHAR(20) NOT NULL, stock_code VARCHAR(20) NOT NULL,
    raw_data JSON,
    UNIQUE KEY uk_ths_const (index_code, stock_code)
);
```

## 验收标准

- [ ] 管理端可选「同花顺」数据源类型，凭证区显示 API Key 输入框
- [ ] 测试连接：用轻量接口（交易日历/标的检索）验证 Key
- [ ] Phase 1 六个接口可建任务同步：日K入 daily_quotes、财务指标入 fin_indicator、估值/指数入新表
- [ ] 毫秒时间戳正确转换为 yyyyMMdd
- [ ] 4001 QPS 超限自动退避重试；2001/2003 明确报错不重试
- [ ] 与 Tushare 同表数据可交叉（同 thscode/ts_code UPSERT 更新）

## 相关文档

- 官方文档：https://fuyao.aicubes.cn/docs/api-reference/overview/
- [数据源管理 DS-001](ds-001-data-source-management.md)（适配器模式已预留扩展点）
- [Tushare 接口参考](tushare-api-reference.md)（field_alias/执行器机制来源）