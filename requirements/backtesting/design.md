# 回测系统技术设计文档

**创建日期：** 2026-05-05
**设计者：** Claude
**状态：** 待审核

---

## 1. 概述

本文档描述回测系统的技术架构和实现方案。系统通过 Tushare 获取中国股票市场数据，使用 Zipline-reloaded 作为回测引擎，为用户提供量化交易策略验证平台。

### 1.1 设计目标

- 提供完整的策略回测流程
- 支持多种数据类型和频率
- 实现高效的回测执行
- 提供详细的回测分析报告
- 保证系统安全和性能

### 1.2 技术栈

**后端扩展：**
- `tushare` >= 1.2.0 - 数据接口
- `zipline-reloaded` >= 0.3.0 - 回测框架
- `pandas` >= 2.0.0 - 数据处理
- `TA-Lib` >= 0.4.0 - 技术指标计算

**前端扩展：**
- `monaco-editor` - 代码编辑器
- `echarts` / `recharts` - 图表可视化
- `react-split-pane` - 分屏布局

---

## 2. 后端架构设计

### 2.1 模块结构

```
src/backend/
├── data/                      # 数据源模块
│   ├── tushare_client.py     # Tushare API 客户端
│   ├── data_sync_service.py  # 数据同步服务
│   └── cache_service.py      # 数据缓存服务
├── backtest/                   # 回测模块
│   ├── engine.py              # Zipline 引擎封装
│   ├── adapter.py             # 数据适配器
│   ├── executor.py            # 回测任务执行器
│   └── analyzer.py            # 结果分析器
├── strategy/                   # 策略模块
│   ├── manager.py             # 策略管理
│   ├── validator.py           # 策略验证
│   └── templates/            # 策略模板
│       ├── ma_crossover.py    # 双均线策略
│       ├── macd.py          # MACD 策略
│       └── bollinger.py      # 布林带策略
└── models/
    ├── stock.py              # 股票模型
    ├── strategy.py           # 策略模型
    └── backtest.py          # 回测模型
```

### 2.2 Tushare 数据集成

#### TushareClient 类设计

```python
class TushareClient:
    """Tushare API 客户端"""

    def __init__(self, token: str):
        self.token = token
        self.pro = ts.pro_api(token)

    async def get_stock_list(self) -> pd.DataFrame:
        """获取股票列表"""
        df = self.pro.stock_basic(exchange='', list_status='L')
        return df

    async def get_daily_data(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取日线行情"""
        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        return df

    async def get_financials(
        self,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """获取财务数据"""
        df = self.pro.income(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date
        )
        return df
```

#### 数据同步服务

```python
class DataSyncService:
    """数据同步服务"""

    @staticmethod
    async def sync_stocks(db: AsyncSession) -> dict:
        """同步股票列表"""
        # 从 Tushare 获取最新股票列表
        client = TushareClient(settings.TUSHARE_TOKEN)
        df = await client.get_stock_list()

        # 更新数据库
        # ... 实现逻辑

        return {"added": X, "updated": Y}

    @staticmethod
    async def sync_prices(
        db: AsyncSession,
        ts_code: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """同步行情数据"""
        client = TushareClient(settings.TUSHARE_TOKEN)
        df = await client.get_daily_data(ts_code, start_date, end_date)

        # 批量插入数据库
        # ... 实现逻辑

        return {"inserted": len(df)}
```

### 2.3 Zipline 集成

#### 数据适配器

```python
class ZiplineDataAdapter:
    """Zipline 数据适配器"""

    @staticmethod
    def to_bundle(
        db: AsyncSession,
        ts_codes: List[str],
        start_date: str,
        end_date: str
    ):
        """将数据库数据转换为 Zipline Bundle"""

        def load_data():
            # 从数据库加载数据
            data_dict = {}
            for code in ts_codes:
                df = await db.query_stock_prices(code, start_date, end_date)
                data_dict[code] = df

            return data_dict

        def get_pricing():
            # 返回价格数据
            return load_data()

        def get_splits():
            # 返回除权数据
            return pd.DataFrame()

        return {
            'get_pricing': get_pricing,
            'get_splits': get_splits
        }
```

#### 回测引擎

```python
class BacktestEngine:
    """回测引擎"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def run_backtest(
        self,
        strategy_code: str,
        bundle_data: dict,
        params: dict
    ) -> BacktestResult:
        """执行回测"""

        # 创建策略模块
        strategy_module = self._create_strategy_module(strategy_code)

        # 运行回测
        result = run_algorithm(
            start=params['start_date'],
            end=params['end_date'],
            initialize=strategy_module.initialize,
            handle_data=strategy_module.handle_data,
            capital_base=params['initial_capital'],
            bundle_data=bundle_data,
            commission=self._create_commission(params['commission'])
        )

        return BacktestResult.from_zipline(result)

    def _create_strategy_module(self, code: str):
        """动态创建策略模块"""
        # ... 实现逻辑
        pass
```

### 2.4 策略管理

#### 策略模板

```python
# templates/ma_crossover.py
TEMPLATE_MA_CROSSOVER = '''
from zipline.api import order, record, symbol

def initialize(context):
    context.short_period = {short_period}
    context.long_period = {long_period}
    context.stocks = {stock_codes}
    context.invested = {{}}

def handle_data(context, data):
    for stock in context.stocks:
        prices = data.history(stock, 'close',
                          max(context.short_period, context.long_period),
                          '1d')

        if len(prices) < context.long_period:
            continue

        short_ma = prices.rolling(context.short_period).mean()
        long_ma = prices.rolling(context.long_period).mean()

        # 金叉买入
        if (short_ma.iloc[-1] > long_ma.iloc[-1] and
            short_ma.iloc[-2] <= long_ma.iloc[-2]):
            order(stock, {shares})
            context.invested[stock] = True

        # 死叉卖出
        elif (short_ma.iloc[-1] < long_ma.iloc[-1] and
            short_ma.iloc[-2] >= long_ma.iloc[-2]):
            if context.invested.get(stock, False):
                order_target(stock, 0)
                context.invested[stock] = False

        record(price=prices.iloc[-1],
                short_ma=short_ma.iloc[-1],
                long_ma=long_ma.iloc[-1])
'''
```

---

## 3. 前端架构设计

### 3.1 页面结构

```
src/frontend/src/pages/backtest/
├── StrategyList.tsx       # 策略列表页
├── StrategyEditor.tsx      # 策略编辑器
├── BacktestRun.tsx        # 回测执行页
├── BacktestReport.tsx      # 回测报告页
└── components/
    ├── MonacoEditor.tsx    # Monaco 编辑器组件
    ├── ParameterForm.tsx   # 参数配置表单
    ├── ChartCard.tsx       # 图表卡片
    └── TradeTable.tsx      # 交易明细表格
```

### 3.2 策略编辑器

```typescript
interface StrategyEditorProps {
  strategyId?: number;
  template?: StrategyTemplate;
  onSave: (strategy: Strategy) => void;
  onCancel: () => void;
}

const StrategyEditor: React.FC<StrategyEditorProps> = ({
  strategyId,
  template,
  onSave,
  onCancel
}) => {
  const [code, setCode] = useState(template?.code || '');
  const [parameters, setParameters] = useState({});

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* 左侧：代码编辑器 */}
      <div style={{ flex: 1 }}>
        <MonacoEditor
          language="python"
          value={code}
          onChange={setCode}
          options={{
            minimap: { enabled: true },
            automaticLayout: true,
          }}
        />
      </div>

      {/* 右侧：参数配置 */}
      <div style={{ width: 300, padding: 16 }}>
        <Form>
          <Form.Item label="策略名称" name="name">
            <Input />
          </Form.Item>
          <Form.Item label="策略描述" name="description">
            <TextArea rows={4} />
          </Form.Item>
          <ParameterForm
            parameters={parameters}
            onChange={setParameters}
          />
          <Button type="primary" onClick={handleSave}>
            保存策略
          </Button>
        </Form>
      </div>
    </div>
  );
};
```

### 3.3 回测报告图表

```typescript
const BacktestReport: React.FC = ({ backtestId }) => {
  const { data } = useBacktestResult(backtestId);

  return (
    <div>
      {/* 收益曲线 */}
      <ChartCard title="收益曲线">
        <LineChart
          data={data.equity_curve}
          xAxis="date"
          yAxis="equity"
          line={[
            { data: 'equity', name: '策略收益' },
            { data: 'benchmark', name: '基准收益' }
          ]}
        />
      </ChartCard>

      {/* 回撤曲线 */}
      <ChartCard title="回撤分析">
        <AreaChart
          data={data.drawdown_curve}
          xAxis="date"
          yAxis="drawdown"
          area="drawdown"
        />
      </ChartCard>

      {/* 持仓分布 */}
      <ChartCard title="持仓分布">
        <PieChart data={data.position_distribution} />
      </ChartCard>
    </div>
  );
};
```

---

## 4. API 接口设计

### 4.1 数据源管理

```python
# GET /api/v1/admin/tushare/config
{
    "token": "your_token_here",
    "sync_interval": 3600  # 同步间隔（秒）
}

# PUT /api/v1/admin/tushare/config
{
    "token": "new_token",
    "sync_interval": 1800
}
```

### 4.2 策略管理

```python
# GET /api/v1/user/strategies
{
    "code": 0,
    "message": "success",
    "data": {
        "list": [...],
        "page": 1,
        "page_size": 10,
        "total": 25
    }
}

# POST /api/v1/user/strategies
{
    "code": 0,
    "message": "创建成功",
    "data": {
        "id": 123
    }
}
```

### 4.3 回测执行

```python
# POST /api/v1/user/backtest/run
{
    "code": 0,
    "message": "回测已启动",
    "data": {
        "task_id": "bt_20260505_001",
        "status": "running"
    }
}
```

---

## 5. 数据存储策略

### 5.1 分区存储

```sql
-- 按年份分区，提升查询性能
CREATE TABLE stock_prices_2026 (
    ...
) PARTITION BY RANGE (YEAR(trade_date));

CREATE TABLE stock_prices_2025 (
    ...
) PARTITION BY RANGE (YEAR(trade_date));
```

### 5.2 索引策略

```sql
-- 复合索引
CREATE INDEX idx_code_date ON stock_prices(ts_code, trade_date);

-- 覆盖索引
CREATE INDEX idx_cover ON stock_prices(
    ts_code, trade_date,
    close, volume
);
```

---

## 6. 性能优化

### 6.1 缓存策略

- Redis 缓存热点股票数据
- Tushare API 响应缓存（TTL: 1小时）
- 策略计算结果缓存

### 6.2 数据库优化

- 使用连接池管理数据库连接
- 批量插入替代单条插入
- 异步任务队列处理耗时操作

### 6.3 回测优化

- 使用进程池并行执行回测
- 预加载数据到内存
- 结果增量写入数据库

---

## 7. 安全考虑

### 7.1 策略执行安全

- 使用受限环境执行策略代码
- 禁用危险的 Python 函数
- 限制执行时间和内存使用

### 7.2 API 安全

- Tushare Token 加密存储
- 回测任务队列防止 DoS
- 用户数据隔离

---

**文档结束**
