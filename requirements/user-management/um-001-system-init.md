# UM-001: 系统初始化

## 用户故事

作为系统维护人员，我希望系统在首次启动时自动创建管理员账号，以便我能够登录系统并进行后续配置。

## 验收标准

### 功能需求

#### AC1: 自动创建管理员账号
**Given**: 系统数据库为空或未初始化
**When**: 系统首次启动
**Then**: 系统自动创建 admin 账号

#### AC2: 设置默认密码
**Given**: admin 账号已创建
**When**: 查看用户信息
**Then**: 密码为 123456

#### AC3: 设置最大权限
**Given**: admin 账号已创建
**When**: 查看用户权限
**Then**: 用户拥有系统的所有权限

#### AC4: 避免重复创建
**Given**: admin 账号已存在
**When**: 系统再次启动
**Then**: 不会重复创建 admin 账号

### 技术需求

#### TC1: 密码加密存储
- 使用 bcrypt 或类似加密算法
- 不存储明文密码

#### TC2: 数据库迁移
- 创建 users 表
- 创建 roles 表
- 创建 permissions 表
- 创建 user_roles 表
- 创建 role_permissions 表

#### TC3: 初始化脚本
- 在应用启动时执行
- 具有幂等性（可重复执行）
- 记录初始化日志

## 技术实现

### 数据库模型

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    real_name VARCHAR(50),
    status TINYINT DEFAULT 1 COMMENT '1:启用 0:禁用',
    last_login_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 角色表
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    role_desc VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    permission_name VARCHAR(100) UNIQUE NOT NULL,
    permission_desc VARCHAR(200),
    resource VARCHAR(100) COMMENT '资源路径',
    action VARCHAR(20) COMMENT '操作:read,write,delete'
);

-- 用户角色关联表
CREATE TABLE user_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    role_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_role (user_id, role_id)
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_id INT NOT NULL,
    permission_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
    UNIQUE KEY uk_role_permission (role_id, permission_id)
);
```

### Pydantic 模型

```python
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    real_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    status: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 初始化脚本

```python
async def init_system():
    """系统初始化，创建默认管理员账号"""

    # 1. 检查是否已初始化
    existing_admin = await get_user_by_username("admin")
    if existing_admin:
        logger.info("系统已初始化，跳过创建管理员")
        return

    # 2. 创建管理员角色
    admin_role = await create_role("admin", "系统管理员")

    # 3. 创建所有权限
    permissions = [
        ("user:read", "查看用户"),
        ("user:write", "新增/编辑用户"),
        ("user:delete", "删除用户"),
        ("user:reset_password", "重置用户密码"),
        ("data_source:manage", "管理数据源"),
        ("stock:manage", "管理股票"),
        ("tag:manage", "管理标签"),
        ("stock:quote:read", "查看股票行情"),
        ("analysis:fundamental:read", "基本面分析"),
        ("analysis:trend:read", "趋势分析"),
        ("analysis:fund:read", "资金分析")
    ]

    for perm_name, perm_desc in permissions:
        perm = await create_permission(perm_name, perm_desc)
        await assign_permission_to_role(admin_role.id, perm.id)

    # 4. 创建 admin 用户
    admin_user = await create_user(
        username="admin",
        password="123456",
        real_name="系统管理员"
    )

    # 5. 分配管理员角色
    await assign_role_to_user(admin_user.id, admin_role.id)

    logger.info("系统初始化完成，管理员账号已创建")
```

## API 接口

### POST /api/v1/system/init
系统初始化接口（可选手动触发）

**请求参数**: 无

**响应示例**:
```json
{
  "code": 0,
  "message": "系统初始化成功"
}
```

## 测试用例

### 正常流程
1. 清空数据库
2. 启动系统
3. 验证 admin 账号存在
4. 验证密码为 123456
5. 验证具有管理员权限

### 边界情况
1. 数据库已存在 admin 账号，验证不会重复创建
2. 数据库连接失败时的处理
3. 密码加密失败时的处理

## 相关文档

- Feature Map: feature-map.md
- 下一个 Story: um-002-user-login.md
