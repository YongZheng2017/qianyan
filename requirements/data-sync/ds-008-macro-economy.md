# DS-008: 宏观经济数据同步

## 用户故事

作为系统管理员，我希望同步国内与国际宏观经济数据（利率、GDP、物价指数、PMI、货币供应量、美国国债利率），为分析端提供宏观背景数据，辅助判断大盘环境。

## 接口清单（10个，全部来自 Tushare）

### 国内宏观（7个）

| # | 接口 | 名称 | 频率 | 积分 | 目标表 | 唯一键 |
|---|------|------|------|------|--------|--------|
| 1 | `shibor_lpr` | LPR贷款基础利率 | 日 | 120 | macro_lpr | date |
| 2 | `shibor` | Shibor利率 | 日 | 120 | macro_shibor | date |
| 3 | `cn_gdp` | GDP数据 | 季 | 600 | macro_gdp | quarter |
| 4 | `cn_cpi` | 居民消费价格指数 | 月 | 600 | macro_cpi | month |
| 5 | `cn_ppi` | 工业生产者出厂价格指数 | 月 | 600 | macro_ppi | month |
| 6 | `cn_pmi` | 采购经理指数 | 月 | 600 | macro_pmi | month |
| 7 | `cn_m` | 货币供应量 | 月 | 600 | macro_m | month |

### 国际宏观（3个）

| # | 接口 | 名称 | 频率 | 积分 | 目标表 | 唯一键 |
|---|------|------|------|------|--------|--------|
| 8 | `us_tycr` | 美国债收益率曲线(日频) | 日 | 120 | macro_us_tycr | date |
| 9 | `us_tbr` | 美国短期国债利率 | 日 | 120 | macro_us_tbr | date |
| 10 | `us_tlr` | 美国国债长期利率 | 日 | 120 | macro_us_tlr | date |

> ✅ 积分门槛低（120~600），无需 `_vip`。参数统一为 `date/start_date/end_date`（日频）或 `month/start_m/end_m`（月频）或 `q/start_q/end_q`（季频）。

## 关键设计点

### 1. 无 ts_code（与股票类接口的根本差异）
宏观数据是**国家级/全球级**数据，每个日期一条记录，不含股票代码。表主键为业务键（date/month/quarter），**不设自增 id 主键**（保证执行器 UPSERT 的主键检测可通过）。

### 2. 字段名映射（field_alias）
Tushare 部分字段名以数字开头（如 Shibor 的 `1w`/`1m`/`1y`），非法 Python 标识符。适配器层做映射：

| Tushare 字段 | 模型列名 |
|--------------|----------|
| `on` | `on_rate`（避免歧义）|
| `1w` / `2w` | `w1` / `w2` |
| `1m` / `3m` / `6m` / `9m` | `m1` / `m3` / `m6` / `m9` |
| `1y` / `5y`（LPR）| `y1` / `y5` |

> us_tycr 的 `m1`~`y30` 合法，无需映射。

### 3. raw_data 兜底
PPI/PMI/M2/美短长期国债的精确字段存在不确定性，采用「典型字段建列 + raw_data(JSON) 存完整记录」策略，字段不全也不丢数据。

## 各接口字段摘要

| 接口 | 输入参数 | 核心输出字段 |
|------|----------|--------------|
| shibor_lpr | date/start_date/end_date | date, 1y, 5y |
| shibor | date/start_date/end_date | date, on, 1w, 2w, 1m, 3m, 6m, 9m, 1y |
| cn_gdp | q/start_q/end_q | quarter, gdp, gdp_yoy, pi, pi_yoy, si, si_yoy, ti, ti_yoy |
| cn_cpi | m/start_m/end_m | month, nt_val, nt_yoy, nt_mom, nt_accu（城乡明细入 raw_data）|
| cn_ppi | m/start_m/end_m | month, nt_val, nt_yoy（+raw_data）|
| cn_pmi | m/start_m/end_m | month, pmi（+raw_data）|
| cn_m | m/start_m/end_m | month, m0, m1, m2, m0_yoy, m1_yoy, m2_yoy |
| us_tycr | date/start_date/end_date | date, m1~y30（13个期限）|
| us_tbr | date/start_date/end_date | date（+raw_data）|
| us_tlr | date/start_date/end_date | date, y20, y30（+raw_data）|

## 数据库设计（10表）

统一模式：**业务主键 + 核心字段列 + raw_data(JSON)**：

```sql
-- 以 Shibor 为例（其余同模式）
CREATE TABLE macro_shibor (
    date VARCHAR(8) PRIMARY KEY COMMENT '日期',
    on_rate DECIMAL(10,4) COMMENT '隔夜',
    w1 DECIMAL(10,4), w2 DECIMAL(10,4),
    m1 DECIMAL(10,4), m3 DECIMAL(10,4), m6 DECIMAL(10,4), m9 DECIMAL(10,4),
    y1 DECIMAL(10,4),
    raw_data JSON COMMENT '完整记录',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 执行器增强（本需求引入）

1. **field_alias 支持**：TushareAdapter.fetch_data 解析记录后按 `field_alias` 重命名字段
2. **UPSERT 冲突列修正**：`_upsert` 的主键检测从「仅主键」扩展为「主键+唯一约束列」（排除自增 id），修复财务表（自增id主键+业务唯一键）此前无法写入的隐患

## 验收标准

- [ ] 10 个接口在管理端可选并创建同步任务
- [ ] 日频数据（LPR/Shibor/美债）按日期段同步
- [ ] 月频（CPI/PPI/PMI/M2）、季频（GDP）按月份/季度段同步
- [ ] 字段映射生效（1w→w1 等）
- [ ] 重复同步正确 UPSERT（业务主键冲突更新）
- [ ] raw_data 保留完整原始记录

## 相关文档

- [数据源管理](ds-001-data-source-management.md)
- [同步任务管理](ds-002-sync-task-management.md)