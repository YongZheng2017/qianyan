# MQ-001: 行情查看

## 用户故事

作为分析端用户，我希望在「行情」页面选择一个标的（某只股票、某个行业板块、或某个市场指数），查看它的 K 线图，并能在日线、周线、月线之间切换，以便分析标的的历史走势。

## 验收标准

### 功能需求

#### AC1: 一级菜单「行情」入口
**Given**: 用户登录分析端
**When**: 查看左侧菜单
**Then**: 显示「行情」一级菜单项
**And**: 点击进入行情页面

#### AC2: 标的类型切换
**Given**: 在行情页面
**When**: 查看顶部选择区
**Then**: 提供三种标的类型切换：股票 / 板块 / 市场
**And**: 切换类型后，搜索框和推荐列表相应变化

#### AC3: 选择股票
**Given**: 标的类型为「股票」
**When**: 在搜索框输入股票代码或名称（如 "000001" 或 "平安"）
**Then**: 实时返回匹配的股票列表（代码、名称、行业）
**And**: 选中后展示该股票行情

#### AC4: 选择市场指数
**Given**: 标的类型为「市场」
**When**: 查看市场列表
**Then**: 显示主要市场指数（上证指数、深证成指、创业板指、科创50 等）
**And**: 选中后展示该指数行情

#### AC5: 选择板块
**Given**: 标的类型为「板块」
**When**: 查看板块列表
**Then**: 显示行业板块列表（如银行、地产、半导体等）
**And**: 选中后展示该板块行情
> 注：板块数据来源方案见「数据需求」章节，待确认。

#### AC6: 周期切换（日/周/月）
**Given**: 已选择某个标的
**When**: 切换周期标签（日线 / 周线 / 月线）
**Then**: K 线图相应更新为该周期的数据
**And**: 默认展示近 6 个月日线（或最近 120 根 K 线）

#### AC7: K 线图展示
**Given**: 已选择标的和周期
**When**: 加载行情数据
**Then**: 主图显示 K 线（阳线红/阴线绿）
**And**: 副图显示成交量柱状图
**And**: 支持 MA5 / MA10 / MA20 移动均线（可切换显示）

#### AC8: K 线图交互
**Given**: K 线图已渲染
**When**: 鼠标悬停
**Then**: 显示十字光标和该日详细数据（开高低收、涨跌幅、成交量）
**And**: 支持鼠标滚轮缩放、拖拽平移查看历史
**And**: 支持切换前复权/后复权（可选，后续迭代）

### 非功能需求

#### NFR1: 数据时效
- 行情数据来自数据库（已同步），不实时调用外部接口
- 数据新鲜度取决于数据同步周期（如日线每天收盘后同步）

#### NFR2: 性能
- 单次行情查询响应 < 1 秒（120 根 K 线）
- 前端图表渲染流畅，缩放/平移无明显卡顿

## 技术实现

### 数据需求

| 标的类型 | 数据来源 | 同步接口 | 状态 |
|----------|----------|----------|------|
| 股票 | `stocks` + `daily_quotes`/`weekly_quotes`/`monthly_quotes` | `daily`/`weekly`/`monthly` | ✅ 已支持 |
| 市场指数 | `index_quotes`（待新增） | `index_daily`/`index_weekly`/`index_monthly` | ⏳ 需扩展 |
| 板块 | 待定（见下方方案） | 待定 | ⏳ 需扩展 |

#### 市场指数（新增 index_quotes 表）
```sql
CREATE TABLE index_quotes (
    ts_code VARCHAR(20) NOT NULL COMMENT '指数代码(如 000001.SH 上证指数)',
    trade_date VARCHAR(8) NOT NULL COMMENT '交易日 YYYYMMDD',
    open FLOAT, high FLOAT, low FLOAT, close FLOAT,
    pre_close FLOAT, pct_chg FLOAT,
    vol FLOAT COMMENT '成交量(万手)',
    amount FLOAT COMMENT '成交额(亿元)',
    PRIMARY KEY (ts_code, trade_date)
);
```
对应 Tushare 接口：`index_daily` / `index_weekly` / `index_monthly`（参考 [Tushare 文档](https://tushare.pro/document/2?doc_id=172)）

#### 板块数据方案（待确认，二选一）

**方案 A：按行业聚合（无需新数据）**
- 板块行情 = `stocks.industry` 下所有个股的市值加权均价/成交量聚合
- 优点：数据已有（stocks 表），无需扩展同步
- 缺点：实时聚合计算量大，板块定义不标准

**方案 B：同步申万板块（推荐）**
- 新增 `sector_basic`（板块列表）、`sector_quotes`（板块行情）表
- 同步 Tushare 申万板块接口（`index_classify` + `index_member` + `sw_daily`）
- 优点：官方板块定义，行情准确
- 缺点：需扩展数据同步模块

> 建议：首期先上线「股票」+「市场指数」（方案明确），板块按方案 B 在下一迭代补充。

### Pydantic 模型

```python
class QuoteItem(BaseModel):
    trade_date: str          # 交易日 YYYYMMDD
    open: float
    high: float
    low: float
    close: float
    pre_close: Optional[float]
    pct_chg: Optional[float] # 涨跌幅 %
    vol: float               # 成交量
    amount: float            # 成交额

class QuoteResponse(BaseModel):
    symbol: str              # 标的代码
    name: str                # 标的名称
    type: str                # stock/index/sector
    period: str              # daily/weekly/monthly
    items: List[QuoteItem]

class SymbolItem(BaseModel):
    code: str                # 标的代码
    name: str                # 名称
    type: str                # stock/index/sector
    extra: Optional[str]     # 附加信息（如股票的行业）
```

### 行情查询服务（后端）

```python
class QuoteService:
    # 标的类型 → (模型表, 代码字段)
    QUOTE_TABLES = {
        ("stock", "daily"): DailyQuote,
        ("stock", "weekly"): WeeklyQuote,
        ("stock", "monthly"): MonthlyQuote,
        ("index", "daily"): IndexQuote,  # 待新增
        # ...
    }

    @staticmethod
    async def get_quotes(db, symbol: str, qtype: str, period: str,
                         start_date: str = None, end_date: str = None) -> dict:
        """查询标的行情"""
        model = QuoteService.QUOTE_TABLES.get((qtype, period))
        # 默认近 120 个交易日
        query = select(model).where(model.ts_code == symbol).order_by(model.trade_date.desc()).limit(120)
        rows = (await db.execute(query)).scalars().all()
        items = [QuoteItem(...) for r in reversed(rows)]  # 时间升序返回
        return {"symbol": symbol, "name": ..., "type": qtype, "period": period, "items": items}

    @staticmethod
    async def search_symbols(db, keyword: str, qtype: str = None) -> list:
        """搜索标的（股票从 stocks 表，指数从配置列表）"""
        ...
```

## API 接口

> 前缀：`/api/v1/analysis`（分析端独立前缀，需 JWT 认证）

### GET /api/v1/analysis/symbols/search
搜索标的

**请求参数**：
- `q`: 搜索关键词（代码或名称）
- `type`: 标的类型（stock/index/sector，可选，默认全部）

**响应示例**：
```json
{
  "code": 0,
  "data": [
    {"code": "000001.SZ", "name": "平安银行", "type": "stock", "extra": "银行"},
    {"code": "000001.SH", "name": "上证指数", "type": "index", "extra": null}
  ]
}
```

### GET /api/v1/analysis/quotes
查询行情数据（K线）

**请求参数**：
- `symbol`: 标的代码（如 `000001.SZ`、`000001.SH`）
- `type`: 标的类型（stock/index/sector）
- `period`: 周期（daily/weekly/monthly）
- `start_date`: 起始日期（可选，YYYYMMDD）
- `end_date`: 结束日期（可选，YYYYMMDD）
- `limit`: 返回条数（可选，默认 120）

**响应示例**：
```json
{
  "code": 0,
  "data": {
    "symbol": "000001.SZ",
    "name": "平安银行",
    "type": "stock",
    "period": "daily",
    "items": [
      {"trade_date": "20260801", "open": 10.5, "high": 10.8, "low": 10.4, "close": 10.7, "pre_close": 10.5, "pct_chg": 1.9, "vol": 525152, "amount": 460697}
    ]
  }
}
```

### GET /api/v1/analysis/markets
获取主要市场指数列表（快捷选择）

**响应示例**：
```json
{
  "code": 0,
  "data": [
    {"code": "000001.SH", "name": "上证指数"},
    {"code": "399001.SZ", "name": "深证成指"},
    {"code": "399006.SZ", "name": "创业板指"},
    {"code": "000688.SH", "name": "科创50"}
  ]
}
```

### GET /api/v1/analysis/sectors
获取板块列表（板块方案确定后实现）

## 前端实现

### 页面布局

```
┌─────────────────────────────────────────────┐
│ [股票] [板块] [市场]   搜索框 [____]        │  ← 标的类型切换 + 搜索
├─────────────────────────────────────────────┤
│ 平安银行(000001.SZ)                         │
│ [日线] [周线] [月线]   ☑MA5 ☑MA10 ☑MA20   │  ← 周期 + 均线
├─────────────────────────────────────────────┤
│                                             │
│           K 线主图 + 移动均线               │
│                                             │
├─────────────────────────────────────────────┤
│           成交量副图                        │
└─────────────────────────────────────────────┘
```

### K 线图技术方案

- **图表库**：ECharts（`candlestick` K线 + `line` 均线 + `bar` 成交量，双 Y 轴 + dataZoom 缩放）
- **数据更新**：切换标的/周期时调用 `/analysis/quotes` 重新加载
- **交互**：内置 tooltip、dataZoom、十字光标

```javascript
// ECharts K线配置要点
{
  xAxis: { type: 'category', data: dates },
  yAxis: [
    { scale: true, name: '价位' },           // 主图 Y 轴
    { scale: true, name: '成交量(手)' }      // 副图 Y 轴
  ],
  dataZoom: [                                  // 缩放
    { type: 'inside', xAxisIndex: [0, 1] },
    { type: 'slider', xAxisIndex: [0, 1] }
  ],
  series: [
    { type: 'candlestick', data: ohlc },       // K线
    { type: 'line', name: 'MA5', data: ma5 },  // 均线
    { type: 'bar', yAxisIndex: 1, data: vol }  // 成交量
  ]
}
```

## 测试用例

### 正常流程
1. 进入行情页面，默认展示某股票日线
2. 切换为周线/月线，验证 K 线更新
3. 搜索"平安"，选择平安银行，验证行情加载
4. 切换到「市场」，选择上证指数，验证指数 K 线
5. 鼠标悬停 K 线，验证 tooltip 显示详细数据
6. 滚轮缩放、拖拽平移，验证交互正常

### 边界情况
1. 搜索无结果，提示"无匹配标的"
2. 标的无行情数据（未同步），提示"暂无数据"
3. 周期切换时显示 loading，避免闪烁
4. 数据量较大（如月线全历史），分页/限制条数

### 权限
1. 未登录访问 analysis API 返回 401
2. 普通用户（非管理员）可访问 analysis API

## 实施依赖与建议

### 前置依赖
- ✅ `stocks`、`daily_quotes`、`weekly_quotes`、`monthly_quotes` 表已就绪（DS 模块）
- ⏳ `index_quotes` 表需新增（市场指数行情）

### 建议实施顺序
1. **第一步**：实现「股票」行情（个股搜索 + 日/周/月 K 线）—— 数据已就绪，可立即开发
2. **第二步**：扩展数据同步，新增 `index_quotes`（同步 `index_daily/weekly/monthly`）
3. **第三步**：实现「市场」指数行情
4. **第四步**：确定板块方案（A 或 B），实现「板块」行情

## 相关文档

- Feature Map: feature-map.md
- 上游数据：[数据同步管理](../data-sync/feature-map.md)
- Tushare 接口参考：[tushare-api-reference.md](../data-sync/tushare-api-reference.md)
- 指数接口：https://tushare.pro/document/2?doc_id=172