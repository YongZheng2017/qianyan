# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

钱眼投资分析系统 - 一个股票分析平台，包含两大核心功能：
- **基本面分析**：通过公开财务数据分析股票
- **资金趋势分析**：追踪市场资金流向趋势

## 技术栈

- **后端**：FastAPI + Python 3.12
- **数据库**：MySQL + SQLAlchemy ORM
- **前端**：Vue3（双应用：管理端 + 分析端）
- **认证**：JWT 令牌认证

## 架构设计

系统采用**双端架构**：

### 后端结构（规划中）
```
src/backend/
├── admin/        # 管理端API（用户管理、数据源、标签、股票管理）
├── analysis/     # 分析端API（行情数据、基本面分析、趋势分析）
├── models/       # SQLAlchemy 数据模型
├── services/     # 业务逻辑层
└── utils/        # 工具函数
```

### 前端结构（规划中）
```
src/frontend/
├── admin/        # 管理端前端（系统配置、数据维护）
└── analysis/     # 分析端前端（股票分析、资金流向可视化）
```

### 数据库表结构
首次启动时自动初始化：
- `users`、`roles`、`permissions` - 权限管理系统
- `user_roles`、`role_permissions` - 关联表

## 开发命令

### 环境配置
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息

# 启动后端服务（开发模式，自动重载）
python -m src.backend.main

# 或使用 uvicorn 直接启动
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端启动（待实现）
```bash
cd src/frontend
npm install
npm start
```

### 访问地址
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API 设计原则

1. **RESTful 规范** - 基于资源的端点设计
2. **统一响应格式** - 包含错误码和错误信息
3. **Pydantic 验证** - 请求和响应数据校验
4. **分页支持** - 列表接口支持分页
5. **JWT 认证** - 需要令牌访问受保护端点

## 重要说明

- 本系统针对**中国A股市场**，数据源和金融术语均为中文环境
- 管理端和分析端是独立的用户界面，具有不同的权限要求
- 系统重视**数据安全**（密码加密、防SQL注入、请求频率限制）
- **免责声明**：本系统仅供学习和技术交流，不构成投资建议