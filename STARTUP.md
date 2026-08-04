# 钱眼投资分析系统 - 启动指南

## 🎯 快速开始（30秒启动）

### 最快启动方式

```bash
# 1. 后端启动
cd F:\github\qianyan
pip install -r requirements.txt
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 管理端前端（新终端）
cd F:\github\qianyan\src\frontend\admin
npm install && npm run dev

# 3. 分析端前端（新终端）
cd F:\github\qianyan\src\frontend\analysis
npm install && npm run dev
```

### 访问地址
- **后端 API 文档**：http://localhost:8000/docs
- **管理端前端**：http://localhost:3000
- **分析端前端**：http://localhost:5173


## 环境要求

### 必需软件
- **Python 3.12+**
- **Node.js 16+**
- **MySQL 8.0+**

### 数据库准备
创建 MySQL 数据库：
```sql
CREATE DATABASE qianyan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

或者系统会在首次启动时自动创建。

---

## 后端启动

### 1. 配置环境变量

编辑 `.env` 文件（从 `.env.example` 复制）：

```bash
# 数据库配置（根据实际情况修改）
DATABASE_URL=mysql+aiomysql://root:123456@localhost:3306/qianyan

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 管理员默认密码
ADMIN_DEFAULT_PASSWORD=123456
ADMIN_DEFAULT_USERNAME=admin
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动后端

#### 方式一：直接启动
```bash
python -m src.backend.main
```

#### 方式二：使用 uvicorn
```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问后端

- **API 文档**：http://localhost:8000/docs
- **ReDoc 文档**：http://localhost:8000/redoc
- **健康检查**：http://localhost:8000/health

### 5. 系统初始化

首次启动时会自动：
1. 创建数据库（如果不存在）
2. 创建所有表结构
3. 创建管理员角色和权限
4. 创建管理员账号

**默认管理员账号**：
- 用户名：`admin`
- 密码：`123456`

---

## 前端启动

系统包含两个前端应用，需要分别启动。

### 管理端（端口 3000）

#### 1. 安装依赖
```bash
cd src/frontend/admin
npm install
```

#### 2. 启动开发服务器
```bash
npm run dev
```

#### 3. 访问应用
浏览器打开：http://localhost:3000

#### 4. 登录
- 用户名：`admin`
- 密码：`123456`

### 分析端（端口 5173）

#### 1. 安装依赖
```bash
cd src/frontend/analysis
npm install
```

#### 2. 启动开发服务器
```bash
npm run dev
```

#### 3. 访问应用
浏览器打开：http://localhost:5173

#### 4. 登录
使用已创建的用户账号登录，或使用管理员账号。


## 项目结构

```
qianyan/
├── src/
│   ├── backend/           # 后端代码
│   │   ├── api/          # API 路由
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── services/     # 业务逻辑
│   │   ├── utils/        # 工具函数
│   │   └── main.py       # 应用入口
│   │
│   └── frontend/         # 前端代码
│       ├── admin/        # 管理端
│       │   └── src/
│       │       ├── views/    # 页面组件
│       │       ├── router/   # 路由配置
│       │       ├── store/    # 状态管理
│       │       └── api/      # API 封装
│       │
│       └── analysis/     # 分析端
│           └── src/
│               ├── views/    # 页面组件
│               ├── router/   # 路由配置
│               ├── store/    # 状态管理
│               └── api/      # API 封装
│
├── test/                 # 测试文件
│   ├── test_api.py      # API 测试
│   └── simple_test.py   # 简单测试
│
├── requirements/         # 需求文档
├── .env                 # 环境配置
└── requirements.txt     # Python 依赖
```

---

## 快速命令汇总

### 启动所有服务

```bash
# 后端
cd F:\github\qianyan
python -m uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload

# 管理端前端（新终端）
cd F:\github\qianyan\src\frontend\admin
npm run dev

# 分析端前端（新终端）
cd F:\github\qianyan\src\frontend\analysis
npm run dev
```

### 访问地址汇总

- **后端 API 文档**：http://localhost:8000/docs
- **管理端前端**：http://localhost:3000
- **分析端前端**：http://localhost:5173

### 默认账号

- **用户名**：admin
- **密码**：123456

---



