# DS-006: 资金流向同步

## 用户故事

作为系统管理员，我希望同步个股资金流向数据（大单/小单成交、主力资金动向），为分析端的「资金趋势分析」模块提供数据基础，帮助用户判断资金进出动向。

## 接口信息

| 项 | 值 |
|----|-----|
| 接口 | `moneyflow` |
| 描述 | 获取沪深A股资金流向（大单/小单成交，判别资金动向），数据始于 2010 年 |
| 积分 | 2000 积分起（基础积分有流量控制）|
| 限量 | 单次最大 6000 行 |
| 文档 | https://tushare.pro/document/2?doc_id=170 |

## ✅ 关键特性：支持全市场同步

`ts_code` **非必填**，股票与时间参数至少输入一个：
- **单股同步**：`ts_code=000001.SZ` + `start_date`/`end_date`
- **全市场同步**：`trade_date=20260808`（某交易日全市场，单次≤6000行≈覆盖全A股）

> 与财务接口不同，资金流向**无需 `_vip` 接口**，2000 积分即可全市场同步。

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `ts_code` | N* | 股票代码 |
| `trade_date` | N* | 交易日期 YYYYMMDD |
| `start_date` | N* | 开始日期 |
| `end_date` | N* | 结束日期 |

> *股票与时间参数至少一个不为空

## 输出字段（20个）

| 字段 | 说明 | 单位 |
|------|------|------|
| `ts_code` / `trade_date` | 代码 / 交易日 | - |
| **小单**(sm, <5万) | `buy_sm_vol/amount`、`sell_sm_vol/amount` | 手/万元 |
| **中单**(md, 5~20万) | `buy_md_vol/amount`、`sell_md_vol/amount` | 手/万元 |
| **大单**(lg, 20~100万) | `buy_lg_vol/amount`、`sell_lg_vol/amount` | 手/万元 |
| **特大单**(elg, ≥100万) | `buy_elg_vol/amount`、`sell_elg_vol/amount` | 手/万元 |
| `net_mf_vol` | 净流入量 | 手 |
| `net_mf_amount` | 净流入额 | 万元 |

> 分类规则基于成交额：小单<5万 / 中单5~20万 / 大单20~100万 / 特大单≥100万。净流入为主动买卖单净值（基于L2订单，非大小单简单相减）。

## 数据库设计

字段不多（20个）且结构稳定，全部建独立列（无需 raw_data JSON）：

```sql
CREATE TABLE moneyflow (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ts_code VARCHAR(20) NOT NULL,
    trade_date VARCHAR(8) NOT NULL,
    -- 小单
    buy_sm_vol BIGINT, buy_sm_amount DECIMAL(20,4),
    sell_sm_vol BIGINT, sell_sm_amount DECIMAL(20,4),
    -- 中单
    buy_md_vol BIGINT, buy_md_amount DECIMAL(20,4),
    sell_md_vol BIGINT, sell_md_amount DECIMAL(20,4),
    -- 大单
    buy_lg_vol BIGINT, buy_lg_amount DECIMAL(20,4),
    sell_lg_vol BIGINT, sell_lg_amount DECIMAL(20,4),
    -- 特大单
    buy_elg_vol BIGINT, buy_elg_amount DECIMAL(20,4),
    sell_elg_vol BIGINT, sell_elg_amount DECIMAL(20,4),
    -- 净流入
    net_mf_vol BIGINT, net_mf_amount DECIMAL(20,4),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_mf (ts_code, trade_date),
    INDEX idx_trade_date (trade_date),
    INDEX idx_ts_code (ts_code)
);
```

## 同步任务配置

复用 DS-002 框架，Tushare 适配器 `INTERFACE_META` 新增 `moneyflow`：

```python
"moneyflow": {
    "label": "个股资金流向", "target_table": "moneyflow", "limit_per_request": 6000,
    "default_interval_ms": 500, "min_points": 2000,
    "requires_ts_code": False,  # 可按 trade_date 全市场
    "vip_api": None,
    "fields": [全部20字段],
    "params": [ts_code, trade_date, start_date, end_date],
}
```

**同步示例**：
- 单股：`ts_code=000001.SZ`, `start_date=20260101`, `end_date=20260808`
- 全市场某日：`trade_date=20260808`

## 验收标准

- [ ] 能为单只股票同步历史资金流向
- [ ] 能按交易日同步全市场资金流向
- [ ] 重复同步（相同交易日）能正确 UPSERT
- [ ] 数据正确写入 moneyflow 表

## 相关文档

- [数据源管理](ds-001-data-source-management.md)
- [同步任务管理](ds-002-sync-task-management.md)
- 分析端「资金趋势分析」模块（待 FA/FF 需求细化）