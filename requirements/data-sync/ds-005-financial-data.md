# DS-005: 财务数据同步

## 用户故事

作为系统管理员，我希望能够同步上市公司的财务数据（利润表、资产负债表、现金流量表、财务指标、业绩预告/快报、分红送股、主营业务构成、财报披露计划），为后续基本面分析提供数据基础。

支持两种同步模式：
- **单股模式**：指定股票代码 + 时间段，同步该股票的历史财务数据
- **全市场模式**：不传股票代码，同步所选时间段（报告期）内所有股票的财务数据

## ⚠️ 关键约束：Tushare 接口的 ts_code 限制

Tushare 财务接口对"全市场同步"有积分门槛限制，这是实现全市场模式的**核心约束**：

| 接口 | 标准接口（2000积分）| 全市场接口（5000积分）|
|------|---------------------|------------------------|
| 利润表 income | `ts_code` **必填**（单股）| `income_vip`（按 period，全市场）|
| 资产负债表 balancesheet | `ts_code` **必填** | `balancesheet_vip` |
| 现金流量表 cashflow | `ts_code` **必填** | `cashflow_vip` |
| 财务指标 fina_indicator | `ts_code` **必填** | `fina_indicator_vip` |
| 主营构成 fina_mainbz | `ts_code` **必填** | `fina_mainbz_vip` |
| 财报披露计划 disclosure_date | ✅ 可全市场（end_date）| 无需 vip（500积分）|
| 分红送股 dividend | ✅ 可按日期全市场 | 无需 vip（2000积分）|
| 业绩预告 forecast | 参数同上（待确认 vip）| - |
| 业绩快报 express | 参数同上（待确认 vip）| - |

**全市场模式的实现方案**（二选一）：
- **方案A（推荐，需5000积分）**：直接调用 `xxx_vip` 接口，按 `period`（报告期）一次获取全市场数据
- **方案B（2000积分，慢）**：遍历 `stocks` 表所有 ts_code，循环调用标准接口（5500只 × 调用间隔，耗时极长）

> 同步任务配置时，根据是否填写 `ts_code` 自动选择模式：填了→标准接口单股同步；未填→若数据源积分≥5000用 `_vip`，否则提示限制。

## 接口清单

| # | 接口 | 中文名 | 目标表 | 主键 | 限量 | 积分 |
|---|------|--------|--------|------|------|------|
| 1 | income | 利润表 | fin_income | (ts_code, end_date, report_type) | 单股全历史 | 2000 |
| 2 | balancesheet | 资产负债表 | fin_balancesheet | (ts_code, end_date, report_type) | 单股全历史 | 2000 |
| 3 | cashflow | 现金流量表 | fin_cashflow | (ts_code, end_date, report_type) | 单股全历史 | 2000 |
| 4 | fina_indicator | 财务指标 | fin_indicator | (ts_code, end_date) | 100条/次 | 2000 |
| 5 | forecast | 业绩预告 | fin_forecast | (ts_code, ann_date, end_date) | - | 2000 |
| 6 | express | 业绩快报 | fin_express | (ts_code, ann_date, end_date) | - | 2000 |
| 7 | dividend | 分红送股 | fin_dividend | (ts_code, end_date, ann_date) | - | 2000 |
| 8 | fina_mainbz | 主营业务构成 | fin_mainbz | (ts_code, end_date, bz_item) | 100条/次 | 2000 |
| 9 | disclosure_date | 财报披露计划 | fin_disclosure | (ts_code, end_date) | 3000条/次 | 500 |

## 各接口输入参数

### 利润表 income / 资产负债表 balancesheet / 现金流量表 cashflow（参数一致）
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | **Y**（标准）/ N（vip） | 股票代码 |
| `period` | N | 报告期（如 20171231 年报，20170630 半年报）|
| `start_date` / `end_date` | N | 公告日起止 |
| `ann_date` / `f_ann_date` | N | 公告日/实际公告日 |
| `report_type` | N | 报告类型（1合并报表默认，详见下方）|
| `comp_type` | N | 公司类型（1工商业2银行3保险4证券）|

> 报告类型：1合并报表(默认) 2单季合并 4调整合并 5调整前合并 6母公司 等

### 财务指标 fina_indicator
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | **Y**（标准）/ N（vip） | 股票代码 |
| `period` | N | 报告期 |
| `start_date` / `end_date` | N | 报告期起止 |
| `ann_date` | N | 公告日 |

### 主营业务构成 fina_mainbz
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | **Y**（标准）/ N（vip） | 股票代码 |
| `period` | N | 报告期 |
| `type` | N | P按产品 / D按地区 / I按行业（大写）|
| `start_date` / `end_date` | N | 报告期起止 |

### 业绩预告 forecast / 业绩快报 express
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | N | 股票代码 |
| `period` | N | 报告期 |
| `ann_date` | N | 公告日 |
| `start_date` / `end_date` | N | 公告日起止 |

### 分红送股 dividend（至少一个参数）
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | N* | 股票代码 |
| `ann_date` | N* | 公告日 |
| `record_date` | N* | 股权登记日 |
| `ex_date` | N* | 除权除息日 |
| `imp_ann_date` | N* | 实施公告日 |

> *以上参数至少一个不为空

### 财报披露计划 disclosure_date
| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | N | 股票代码 |
| `end_date` | N | 财报周期（如 20181231）|
| `pre_date` | N | 计划披露日期 |
| `ann_date` | N | 最新披露公告日 |
| `actual_date` | N | 实际披露日期 |

## 数据库设计

由于财务字段极多（利润表90+、资产负债表140+、财务指标130+字段），采用**核心字段建列 + 完整数据存 JSON** 的混合策略：

```sql
-- 通用结构（以利润表为例，其他表同理）
CREATE TABLE fin_income (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    ann_date VARCHAR(8) COMMENT '公告日',
    end_date VARCHAR(8) NOT NULL COMMENT '报告期',
    report_type VARCHAR(2) DEFAULT '1' COMMENT '报告类型',
    -- 核心字段（便于查询/分析，列出常用指标）
    total_revenue DECIMAL(20,4) COMMENT '营业总收入',
    revenue DECIMAL(20,4) COMMENT '营业收入',
    operate_profit DECIMAL(20,4) COMMENT '营业利润',
    n_income DECIMAL(20,4) COMMENT '净利润',
    n_income_attr_p DECIMAL(20,4) COMMENT '归母净利润',
    basic_eps DECIMAL(20,4) COMMENT '基本每股收益',
    -- 完整原始数据（JSON，保留 Tushare 全部字段）
    raw_data JSON COMMENT '完整财务数据JSON',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_income (ts_code, end_date, report_type),
    INDEX idx_end_date (end_date),
    INDEX idx_ts_code (ts_code)
);
```

**策略说明**：
- 核心字段（10-15个常用指标）建独立列，便于 SQL 查询/筛选/排序/分析
- `raw_data` (JSON) 存 Tushare 返回的完整记录，保留所有字段（避免140列的宽表）
- 同步时：核心字段提取到列 + 完整记录写 JSON

> 各表核心字段建议见下节。

## 各表核心字段（建议）

| 表 | 核心字段 |
|----|----------|
| fin_income | total_revenue, revenue, operate_profit, total_profit, n_income, n_income_attr_p, basic_eps, diluted_eps, rd_exp |
| fin_balancesheet | total_assets, total_liab, total_hldr_eqy_inc_min_int, money_cap, accounts_receiv, inventories, fix_assets, goodwill, st_borr, lt_borr |
| fin_cashflow | net_profit, n_cashflow_act(经营现金流净额), n_cashflow_inv_act, n_cash_flows_fnc_act, free_cashflow, c_fr_sale_sg |
| fin_indicator | eps, bps, roe, roe_waa, roa, netprofit_margin, grossprofit_margin, debt_to_assets, netprofit_yoy, or_yoy, q_roe |
| fin_forecast | type(预增/预减), p_change_min, p_change_max, net_profit_min, net_profit_max, last_parent_net, summary, announce_time |
| fin_express | revenue, operate_profit, total_profit, n_income, total_assets, basic_eps, diluted_eps, yoy_net_profit |
| fin_dividend | div_proc, stk_div, cash_div, record_date, ex_date, pay_date |
| fin_mainbz | bz_item, bz_code, bz_sales, bz_profit, bz_cost, curr_type |
| fin_disclosure | ann_date, pre_date, actual_date, modify_date |

## 同步任务配置

复用 DS-002 同步任务框架，新增 9 个接口到 Tushare 适配器的 `INTERFACE_META`：

```python
# 单股同步示例（利润表）
{
    "ts_code": "000001.SZ",
    "period": "",  # 不指定则取全部报告期
    "start_date": "20200101",
    "end_date": "20261231"
}

# 全市场同步示例（利润表，需 _vip）
{
    "ts_code": "",  # 留空表示全市场
    "period": "20251231"  # 指定报告期
}
```

执行器逻辑：
- `ts_code` 非空 → 调用标准接口（`income`）
- `ts_code` 为空 → 检查数据源积分配置，≥5000 调用 `_vip` 接口（`income_vip`），否则报错提示

## 验收标准

- [ ] 能为单只股票同步完整的利润表/资产负债表/现金流量表/财务指标
- [ ] 能按报告期同步全市场财务数据（需5000积分）
- [ ] 分红送股、业绩预告/快报、主营构成、披露计划可同步
- [ ] 核心字段可 SQL 查询，完整数据保留在 raw_data
- [ ] 重复同步（相同报告期）能正确 UPSERT 更新

## 实现要点

1. **适配器扩展**：`TushareAdapter.INTERFACE_META` 新增 9 个财务接口（参数定义、目标表、核心字段）
2. **_vip 接口支持**：执行器检测 `ts_code` 为空时，自动切换 `_vip` 接口名
3. **数据写入**：UPSERT 时核心字段提列 + raw_data 写完整 JSON
4. **报告期循环**：全市场模式按 period 同步（一次一个报告期）

## 相关文档

- [数据源管理](ds-001-data-source-management.md)
- [同步任务管理](ds-002-sync-task-management.md)
- [Tushare 接口技术参考](tushare-api-reference.md)（待补充9个财务接口详情）