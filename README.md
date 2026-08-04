# 钱眼投资分析系统

## 项目简介

钱眼投资分析系统是一个股票分析平台，专注于中国A股市场，提供基本面分析和资金趋势分析两大核心功能。

## 免责声明

本系统仅作为个人学习、技术交流之用途，不构成任何形式的投资建议。系统使用的数据来源于第三方公开接口或模拟环境，开发者不对数据的准确性、完整性作任何保证。任何依据本系统作出的投资决策，均由使用者自行承担风险。

## 许可证

本项目仅供学习和研究使用，未经授权不得用于商业目的。

## 核心功能

### 用户管理模块（已实现）
- ✅ 系统初始化（自动创建管理员账号）
- ✅ 用户认证（JWT Token）
- ✅ 用户管理（增删改查、分页、搜索）
- ✅ 权限管理（RBAC）
- ✅ 动态菜单（基于权限）

### 规划功能
- 📋 数据源管理
- 📋 股票管理
- 📋 标签管理
- 📋 基本面分析
- 📋 资金趋势分析

## 技术栈

### 后端
- **框架**：FastAPI 0.115.6
- **语言**：Python 3.12
- **数据库**：MySQL 8.0 + SQLAlchemy 2.0.35
- **认证**：JWT Token
- **加密**：bcrypt

### 前端
- **框架**：Vue 3.4.21
- **UI库**：Element Plus 2.6.3
- **构建**：Vite 5.2.0
- **状态管理**：Pinia 2.1.7
- **路由**：Vue Router 4.3.0

## 架构设计

### 双端架构
- **管理端**（端口 3000）：系统配置、用户管理、数据维护
- **分析端**（端口 5173）：股票分析、资金流向可视化

### API 端点
- 管理端 API：`/api/v1/admin/*`
- 分析端 API：`/api/v1/user/*`
- 系统 API：`/health`, `/api/v1/system/*`

## 快速开始

详细的启动指南请查看 **[STARTUP.md](STARTUP.md)** 文档。

### 最快启动
```bash
# 后端
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 管理端前端
cd src/frontend/admin && npm install && npm run dev

# 分析端前端
cd src/frontend/analysis && npm install && npm run dev
```

## 项目结构

```
qianyan/
├── src/
│   ├── backend/          # FastAPI 后端
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # 数据验证
│   │   ├── services/     # 业务逻辑
│   │   └── utils/        # 工具函数
│   │
│   └── frontend/         # Vue3 前端
│       ├── admin/        # 管理端
│       └── analysis/     # 分析端
│
├── test/                 # 测试文件
├── requirements/         # 需求文档
├── STARTUP.md            # 详细启动指南 ⭐
└── .env                  # 环境配置
```

## 开发进度

### 已完成
- ✅ 用户管理模块（100%）
  - 系统初始化
  - 用户认证
  - 用户管理
  - 权限管理
  - 前端界面

### 进行中
- 📋 其他业务模块规划


---

**详细启动指南请查看 [STARTUP.md](STARTUP.md)** 👈