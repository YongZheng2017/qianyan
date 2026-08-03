# 钱眼投资分析系统

## 声明

本系统仅作为个人学习、技术交流之用途，不构成任何形式的投资建议、买卖推荐或操作指导。系统所使用的数据来源于第三方公开接口或模拟环境，可能存在延迟、错误、遗漏或不完整的情况。开发者不对数据的及时性、准确性、完整性及可靠性作任何保证。任何依据本系统输出结果所作出的投资决策，均由使用者自行承担全部风险与后果，开发者不承担任何形式的损失或责任。

本系统的源代码、界面设计及相关文档版权归开发者所有，未经授权不得用于商业目的或对外公开发布。

## ## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接信息。

### 3. 启动应用

```bash
python -m src.backend.main
```

或使用 uvicorn：

```bash
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问 API

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
  
  

## 数据库初始化

系统使用 MySQL 数据库，首次启动会自动创建以下表：

- users - 用户表
- roles - 角色表
- permissions - 权限表
- user_roles - 用户角色关联表
- role_permissions - 角色权限关联表
  
  

## 开发说明

### 代码规范

- 使用 FastAPI 构建 RESTful API
- 使用 SQLAlchemy ORM 操作数据库
- 使用 Pydantic 进行数据验证
- 使用 JWT 进行身份认证
