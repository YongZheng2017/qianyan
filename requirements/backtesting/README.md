# 回测系统功能说明

## 概述

回测系统是知行股票分析系统的扩展功能，为用户提供量化交易策略回测能力。系统集成了 Tushare 数据源和 Zipline 回测框架，支持策略创建、回测执行和结果分析的完整流程。

## 核心价值

1. **数据真实性** - 使用 Tushare 获取真实中国股票市场数据
2. **策略灵活性** - 支持自定义策略和经典策略模板
3. **专业回测** - 基于 Zipline-reloaded 框架，业界标准
4. **详细分析** - 提供全面的回测报告和指标分析

## 文档目录

| 文档 | 说明 |
|------|------|
| [feature-map.md](./feature-map.md) | 功能地图和用户故事 |
| [design.md](./design.md) | 技术架构设计 |
| [api-spec.md](./api-spec.md) | API 接口规范 |
| [implementation-plan.md](./implementation-plan.md) | 实现计划和时间表 |

## 技术参考

- **Tushare Pro**: https://tushare.pro/document/1
- **Tushare API**: https://tushare.pro/document/2?doc_id=14
- **Zipline-reloaded**: https://zipline.ml4trading.io/
- **Zipline GitHub**: https://github.com/stefan-jansen/zipline-reloaded

## 快速开始

### 1. 查看功能规划

```bash
# 查看功能地图
cat requirements/backtesting/feature-map.md
```

### 2. 了解技术设计

```bash
# 查看架构设计
cat requirements/backtesting/design.md
```

### 3. 参考 API 规范

```bash
# 查看 API 接口规范
cat requirements/backtesting/api-spec.md
```

### 4. 跟进实施进度

```bash
# 查看实施计划
cat requirements/backtesting/implementation-plan.md
```

## 主要功能模块

### 1. 数据源管理
- Tushare Token 配置
- 股票列表同步
- 历史行情数据获取
- 财务数据获取

### 2. 策略管理
- 策略创建和编辑
- 策略模板库
- 策略参数配置
- 策略导入导出

### 3. 回测执行
- 回测任务提交
- 实时进度显示
- 并发回测支持
- 任务取消功能

### 4. 回测报告
- 收益曲线展示
- 风险指标分析
- 交易明细查询
- 报告导出

## 数据资源

### 官方文档
- Tushare Pro 数据接口文档
- Zipline-reloaded 回测框架文档
- Python 数据分析最佳实践

### 示例代码
- 双均线策略示例
- MACD 策略示例
- 布林带策略示例

## 开发建议

1. **先从简单策略开始** - 如双均线策略
2. **逐步增加复杂度** - 先实现核心功能，再添加优化
3. **充分测试数据层** - 确保数据同步稳定可靠
4. **关注回测准确性** - 结果验证和交叉验证
5. **性能优先** - 数据量大时性能至关重要

## 常见问题

### Q: Tushare Token 如何获取？
A: 注册 Tushare Pro 账号，在个人中心获取 Token

### Q: 回测需要多少数据？
A: 至少需要1年的历史数据，建议使用2-3年

### Q: 可以实时回测吗？
A: 回测是对历史数据的模拟，不支持实时交易。实时功能需要单独的行情推送模块。

### Q: 策略支持哪些指标？
A: 支持 TA-Lib 提供的所有技术指标，以及自定义计算的指标。

### Q: 回测速度如何？
A: 取决于数据量和策略复杂度。一般情况下，1年日线数据回测可在数分钟内完成。

## 联系和支持

- 技术问题：查看设计文档和 API 规范
- Bug 反馈：提交 Issue 到项目仓库
- 功能建议：查看功能地图，添加用户故事

---

**文档版本:** v1.0
**最后更新:** 2026-05-05