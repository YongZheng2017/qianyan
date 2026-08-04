# 回测系统功能地图

## 功能概述

回测系统扩展原有股票分析功能，提供数据获取、策略创建和回测执行的完整流程。系统通过 Tushare 获取真实市场数据，使用 Zipline 进行策略回测，为用户提供量化交易策略的验证工具。

## 核心功能

### 1. Tushare 数据集成
- 数据源配置和管理（Token 管理、接口调用频率控制）
- 股票列表获取和维护
- 历史行情数据同步（日线、周线、月线）
- 财务数据获取
- 指数数据获取
- 增量数据更新机制

### 2. 策略管理
- 策略代码编辑器（支持 Python 语法高亮）
- 策略模板库（双均线、MACD、布林带等经典策略）
- 策略保存和版本管理
- 策略参数配置（买入条件、卖出条件、止盈止损等）
- 策略分享和导入导出

### 3. 回测执行
- 基于 Zipline 的回测引擎集成
- 回测参数配置（时间范围、初始资金、手续费设置）
- 回测任务调度和队列管理
- 实时回测进度显示
- 多策略并发回测支持

### 4. 回测报告
- 收益曲线图表展示
- 回撤分析（最大回撤、平均回撤）
- 年化收益率、夏普比率等指标
- 交易明细列表（买入卖出记录）
- 月度/年度收益统计
- 与基准指数对比

## 功能分解

| Story ID | Story 名称 | 优先级 | 状态 |
|----------|------------|--------|------|
| BT-001 | Tushare 数据源管理 | P0 | 待开发 |
| BT-002 | 股票行情数据同步 | P0 | 待开发 |
| BT-003 | 策略编辑器 | P1 | 待开发 |
| BT-004 | 策略模板库 | P1 | 待开发 |
| BT-005 | 回测引擎集成 | P0 | 待开发 |
| BT-006 | 回测报告展示 | P1 | 待开发 |
| BT-007 | 回测任务管理 | P2 | 待开发 |

## 依赖关系

```
Tushare 数据源管理 (BT-001)
    ↓
股票行情数据同步 (BT-002) ← 策略编辑器 (BT-003)
    ↓                           ↓
回测引擎集成 (BT-005) ← 策略模板库 (BT-004)
    ↓
回测报告展示 (BT-006)
    ↓
回测任务管理 (BT-007)
```

## 技术架构

### 后端架构

#### 数据源层
- Tushare API 客户端封装
- 数据缓存机制（Redis 或内存缓存）
- 数据存储扩展（stock_prices, stock_financials 等表）

#### 回测引擎层
- Zipline-reloaded 集成
- 自定义数据适配器（将本地数据转换为 Zipline 格式）
- 回测任务执行器
- 结果数据持久化

#### 策略管理层
- 策略代码存储（数据库或文件系统）
- 策略验证和安全检查（沙箱执行）
- 策略参数管理

### 前端架构

#### 策略编辑界面
- Monaco Editor 代码编辑器
- 语法高亮和自动补全
- 代码验证和错误提示
- 策略预览和调试

#### 回测界面
- 回测参数配置表单
- 回测进度条和日志输出
- 回测结果展示区域
- 图表可视化（使用 ECharts 或 Recharts）

#### 回测报告界面
- 收益曲线、回撤曲线、K 线对比图表
- 关键指标卡片展示
- 交易明细表格（分页、筛选）
- 导出功能（CSV、Excel）

## 数据库设计扩展

### 新增表结构

#### stock_prices（股票行情表）
```sql
CREATE TABLE stock_prices (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  ts_code VARCHAR(10) NOT NULL COMMENT '股票代码',
  trade_date DATE NOT NULL COMMENT '交易日期',
  open DECIMAL(10,2) NOT NULL COMMENT '开盘价',
  high DECIMAL(10,2) NOT NULL COMMENT '最高价',
  low DECIMAL(10,2) NOT NULL COMMENT '最低价',
  close DECIMAL(10,2) NOT NULL COMMENT '收盘价',
  volume BIGINT NOT NULL COMMENT '成交量',
  amount DECIMAL(15,2) NOT NULL COMMENT '成交额',
  INDEX idx_ts_code_date (ts_code, trade_date)
);
```

#### stock_financials（财务数据表）
```sql
CREATE TABLE stock_financials (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  ts_code VARCHAR(10) NOT NULL COMMENT '股票代码',
  ann_date DATE NOT NULL COMMENT '公告日期',
  end_date DATE NOT NULL COMMENT '报告期',
  eps DECIMAL(10,4) COMMENT '每股收益',
  total_revenue DECIMAL(15,2) COMMENT '营业总收入',
  net_profit DECIMAL(15,2) COMMENT '净利润',
  INDEX idx_code_date (ts_code, end_date)
);
```

#### strategies（策略表）
```sql
CREATE TABLE strategies (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(100) NOT NULL COMMENT '策略名称',
  description TEXT COMMENT '策略描述',
  code TEXT NOT NULL COMMENT '策略代码',
  parameters JSON COMMENT '策略参数配置',
  user_id INT NOT NULL COMMENT '创建用户ID',
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);
```

#### backtest_results（回测结果表）
```sql
CREATE TABLE backtest_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  strategy_id INT NOT NULL COMMENT '策略ID',
  stock_codes VARCHAR(500) COMMENT '股票代码列表',
  start_date DATE NOT NULL COMMENT '回测开始日期',
  end_date DATE NOT NULL COMMENT '回测结束日期',
  initial_capital DECIMAL(15,2) NOT NULL COMMENT '初始资金',
  final_capital DECIMAL(15,2) NOT NULL COMMENT '最终资金',
  total_return DECIMAL(10,4) COMMENT '总收益率',
  annual_return DECIMAL(10,4) COMMENT '年化收益率',
  max_drawdown DECIMAL(10,4) COMMENT '最大回撤',
  sharpe_ratio DECIMAL(10,4) COMMENT '夏普比率',
  status VARCHAR(20) COMMENT '状态: running/completed/failed',
  created_at DATETIME NOT NULL,
  INDEX idx_strategy (strategy_id)
);
```

#### backtest_trades（回测交易表）
```sql
CREATE TABLE backtest_trades (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  backtest_id BIGINT NOT NULL COMMENT '回测ID',
  ts_code VARCHAR(10) NOT NULL COMMENT '股票代码',
  direction VARCHAR(4) NOT NULL COMMENT '方向: buy/sell',
  price DECIMAL(10,2) NOT NULL COMMENT '成交价格',
  shares INT NOT NULL COMMENT '成交数量',
  amount DECIMAL(15,2) NOT NULL COMMENT '成交金额',
  trade_date DATE NOT NULL COMMENT '交易日期',
  INDEX idx_backtest (backtest_id)
);
```

## API 设计

### Tushare 数据接口

```python
# 数据源配置
GET /api/v1/admin/tushare/config
PUT /api/v1/admin/tushare/config

# 股票列表同步
POST /api/v1/admin/data/sync/stocks

# 行情数据同步
POST /api/v1/admin/data/sync/prices
  params: {
    ts_code: string,      # 股票代码
    start_date: date,      # 开始日期
    end_date: date,        # 结束日期
    frequency: string       # 日线/daily, 周线/weekly, 月线/monthly
  }

# 财务数据同步
POST /api/v1/admin/data/sync/financials
```

### 策略管理接口

```python
# 策略列表
GET /api/v1/user/strategies
  params: { page, page_size, search }

# 创建策略
POST /api/v1/user/strategies
  body: {
    name: string,
    description: string,
    code: string,
    parameters: object
  }

# 更新策略
PUT /api/v1/user/strategies/:id

# 删除策略
DELETE /api/v1/user/strategies/:id

# 策略模板列表
GET /api/v1/user/strategies/templates
```

### 回测执行接口

```python
# 执行回测
POST /api/v1/user/backtest/run
  body: {
    strategy_id: int,
    stock_codes: string[],
    start_date: date,
    end_date: date,
    initial_capital: decimal,
    commission: decimal,      # 佣金率
    slippage: decimal        # 滑点
  }

# 获取回测状态
GET /api/v1/user/backtest/:id/status

# 获取回测结果
GET /api/v1/user/backtest/:id/result

# 获取交易明细
GET /api/v1/user/backtest/:id/trades
```

## 页面设计

### 分析端页面

#### 策略管理页（/user/strategies）
- **左侧**：策略列表（搜索、筛选）
- **右侧**：策略详情/编辑器
- **功能**：
  - 新建策略（从模板创建或空白）
  - 编辑策略（代码编辑器）
  - 策略参数配置
  - 删除策略
  - 策略导出（JSON）

#### 回测执行页（/user/backtest/run）
- **策略选择器**：选择要回测的策略
- **参数配置**：
  - 股票池选择（输入代码或从自选导入）
  - 时间范围选择（日期选择器）
  - 初始资金设置
  - 佣金设置
  - 滑点设置
- **执行按钮**：开始回测
- **实时输出**：回测进度和日志

#### 回测报告页（/user/backtest/report/:id）
- **概览卡片**：
  - 总收益率
  - 年化收益率
  - 最大回撤
  - 夏普比率
  - 总交易次数
  - 胜率
- **图表区域**：
  - 收益曲线（累计收益 vs 时间）
  - 回撤曲线（回撤 vs 时间）
  - 持仓价值（持仓价值 vs 时间）
- **交易明细**：
  - 买入记录（时间、代码、价格、数量）
  - 卖出记录（时间、代码、价格、盈亏）
  - 分页和筛选

## 技术栈扩展

### 后端新增依赖

```python
# requirements/backend.txt 追加
tushare>=1.2.0           # Tushare 数据接口
zipline-reloaded>=0.3.0     # Zipline 回测框架
pandas>=2.0.0              # 数据处理
numpy>=1.24.0               # 数值计算
scipy>=1.10.0              # 科学计算
pytz>=2023.3                # 时区处理
```

### 前端新增依赖

```json
// package.json 追加
{
  "dependencies": {
    "monaco-editor": "^0.45.0",    // 代码编辑器
    "@monaco-editor/react": "^4.6.0",
    "echarts": "^5.4.0",            // 图表库
    "echarts-for-react": "^3.0.0"
  }
}
```

## Zipline 策略示例

### 双均线策略模板

```python
from zipline.api import order, record, symbol
import talib

def initialize(context):
    """初始化函数，设置参数"""
    context.short_ma = 5      # 短期均线
    context.long_ma = 20       # 长期均线
    context.stocks = ['000001.SZ']  # 股票池

def handle_data(context, data):
    """数据处理函数，每个 bar 调用一次"""
    for stock in context.stocks:
        # 获取价格数据
        prices = data.history(stock, 'close', 20, '1d')

        # 计算均线
        short_ma = talib.SMA(prices[-5:], context.short_ma)
        long_ma = talib.SMA(prices, context.long_ma)

        # 金叉买入
        if short_ma[-1] > long_ma[-1] and short_ma[-2] <= long_ma[-2]:
            order(stock, 100)
            context.invested[stock] = True

        # 死叉卖出
        elif short_ma[-1] < long_ma[-1] and short_ma[-2] >= long_ma[-2]:
            if context.invested.get(stock, False):
                order_target(stock, 0)
                context.invested[stock] = False

        # 记录指标
        record(price=data.current(stock, 'close'),
                short_ma=short_ma[-1],
                long_ma=long_ma[-1])
```

## 验收标准

### 数据集成验收
- [ ] 能成功配置 Tushare Token
- [ ] 能获取并存储股票列表
- [ ] 能同步历史行情数据
- [ ] 增量数据更新正常工作

### 策略管理验收
- [ ] 能创建新策略
- [ ] 能编辑现有策略
- [ ] 策略模板可用且正确加载
- [ ] 策略代码保存成功

### 回测执行验收
- [ ] 能成功执行回测
- [ ] 回测进度正确显示
- [ ] 支持多策略并发回测

### 回测报告验收
- [ ] 收益曲线正确显示
- [ ] 关键指标计算正确
- [ ] 交易明细准确
- [ ] 图表交互正常

## 风险和注意事项

### 性能风险
- Tushare API 调用频率限制
- 大量数据同步可能影响数据库性能
- 回测计算资源消耗大

### 安全风险
- 用户策略代码可能包含恶意代码
- 需要沙箱环境执行策略
- 数据访问权限控制

### 缓解措施
- 实现 API 调用队列和限流
- 使用 Redis 缓存热点数据
- 数据库索引优化
- 回测任务资源限制

## 下一步

1. 数据源管理模块开发
2. Tushare 数据适配器开发
3. Zipline 集成和自定义数据源
4. 策略编辑器前端开发
5. 回测报告可视化实现
6. 性能优化和测试

---

**文档结束**
