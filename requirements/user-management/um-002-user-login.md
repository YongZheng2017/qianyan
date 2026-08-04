# UM-002: 用户登录

## 用户故事

### 管理端登录
作为系统管理员，我希望能够登录管理后台，以便我能够进行系统配置和用户管理工作。

### 分析端登录
作为系统用户，我希望能够登录分析端，以便我能够使用股票分析功能查看关注的股票行情和进行各种分析。

## 验收标准

### 功能需求

#### AC1: 显示登录页面
**Given**: 访问登录地址
**When**: 页面加载完成
**Then**: 显示用户名和密码输入框
**And**: 显示登录按钮

#### AC2: 输入用户名和密码
**Given**: 在登录页面
**When**: 输入正确的用户名和密码
**Then**: 输入框正常接收输入

#### AC3: 管理端登录成功
**Given**: 输入正确的管理员用户名和密码
**When**: 点击管理端登录按钮
**Then**: 跳转到管理端主页
**And**: 保存登录状态
**And**: 返回包含管理员权限的 token

#### AC4: 分析端登录成功
**Given**: 输入正确的用户名和密码
**When**: 点击分析端登录按钮
**Then**: 跳转到分析端主页
**And**: 保存登录状态
**And**: 返回包含分析权限的 token
**And**: 返回用户菜单配置

#### AC5: 登录失败 - 用户不存在
**Given**: 输入不存在的用户名
**When**: 点击登录按钮
**Then**: 提示"用户名或密码错误"

#### AC6: 登录失败 - 密码错误
**Given**: 输入正确的用户名但密码错误
**When**: 点击登录按钮
**Then**: 提示"用户名或密码错误"

#### AC7: 记住密码功能（分析端）
**Given**: 在分析端登录页面
**When**: 勾选"记住我"并登录
**Then**: 下次访问自动填充用户名
**And**: Token 有效期延长

### 安全需求

#### SC1: 密码加密传输
- 使用 HTTPS 传输
- 密码在加密后传输

#### SC2: Token 安全
- 使用 JWT 令牌
- Token 包含过期时间
- Token 签名验证

#### SC3: 登录限流
- 限制同一 IP 的登录尝试次数
- 超过限制后锁定一段时间

## 技术实现

### 管理端登录页面

```jsx
// AdminLoginPage.jsx
function AdminLoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/v1/admin/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await response.json();

      if (data.code === 0) {
        localStorage.setItem('admin_token', data.data.token);
        localStorage.setItem('admin_user', JSON.stringify(data.data.user));
        window.location.href = '/admin/dashboard';
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('登录失败，请稍后重试');
    }
  };

  return (
    <div className="login-container">
      <form onSubmit={handleLogin}>
        <h1>管理后台登录</h1>
        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="用户名" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="密码" />
        {error && <div className="error">{error}</div>}
        <button type="submit">登录</button>
      </form>
    </div>
  );
}
```

### 分析端登录页面

```jsx
// UserLoginPage.jsx
function UserLoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const savedUser = localStorage.getItem('saved_user');
    if (savedUser) {
      const { username } = JSON.parse(savedUser);
      setUsername(username);
      setRememberMe(true);
    }
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('/api/v1/user/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, remember_me: rememberMe })
      });

      const data = await response.json();

      if (data.code === 0) {
        localStorage.setItem('user_token', data.data.token);
        localStorage.setItem('user_info', JSON.stringify(data.data.user));
        localStorage.setItem('user_menus', JSON.stringify(data.data.menus));

        if (rememberMe) {
          localStorage.setItem('saved_user', JSON.stringify({ username }));
        } else {
          localStorage.removeItem('saved_user');
        }

        navigate('/dashboard');
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('网络错误，请稍后重试');
    }
  };

  return (
    <div className="user-login-container">
      <div className="login-card">
        <h2>股票分析系统</h2>
        <form onSubmit={handleLogin}>
          <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} placeholder="请输入用户名" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="请输入密码" />
          <label>
            <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
            记住我
          </label>
          {error && <div className="error-message">{error}</div>}
          <button type="submit">登录</button>
        </form>
      </div>
    </div>
  );
}
```

### 后端 API 实现

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
username: str
    password: str
    remember_me: bool = False

class LoginResponse(BaseModel):
    token: str
    user: dict
    menus: Optional[list] = None
    permissions: list

# 管理端登录
@router.post("/admin/auth/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    # 1. 查询用户
    user = await get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 2. 验证密码
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3. 检查用户状态
    if user.status != 1:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 4. 获取用户权限
    permissions = await get_user_permissions(user.id)

    # 5. 检查是否有管理权限
    if not has_admin_permission(permissions):
        raise HTTPException(status_code=403, detail="无管理权限")

    # 6. 生成 token
    token = generate_token(user.id, user.username, "admin")

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name
        },
        "permissions": permissions
    }

# 分析端登录
@router.post("/user/auth/login", response_model=LoginResponse)
async def user_login(request: LoginRequest):
    # 1. 查询用户
    user = await get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 2. 验证密码
    if not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3. 检查用户状态
    if user.status != 1:
        raise HTTPException(status_code=403, detail="用户已被禁用")

    # 4. 获取用户权限
    permissions = await get_user_permissions(user.id)

    # 5. 记住我则延长有效期
    expire_hours = 7 * 24 if request.remember_me else 1
    token = generate_token(user.id, user.username, "user", expire_hours)

    # 6. 获取用户菜单
    menus = await get_user_menus(user.id, permissions)

    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "email": user.email
        },
        "menus": menus,
        "permissions": permissions
    }

def generate_token(user_id: int, username: str, token_type: str, expire_hours: int = 1) -> str:
    """生成 JWT token"""
    token_data = {
        "sub": str(user_id),
        "username": username,
        "type": token_type,
        "exp": datetime.utcnow() + timedelta(hours=expire_hours)
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_menus(user_id: int, permissions: list) -> list:
    """根据用户权限生成菜单配置"""
    menu_config = [
        {
            "id": "stock_quote",
            "title": "关注的股票",
            "icon": "stock",
            "path": "/stock/quote",
            "permission": "stock:quote:read"
        },
        {
            "id": "fundamental",
            "title": "基本面分析",
            "icon": "chart",
            "path": "/analysis/fundamental",
            "permission": "analysis:fundamental:read"
        },
        {
            "id": "trend",
            "title": "趋势分析",
            "icon": "trend",
            "path": "/analysis/trend",
            "permission": "analysis:trend:read"
        },
        {
            "id": "fund_flow",
            "title": "资金趋势",
            "icon": "fund",
            "path": "/analysis/fund-flow",
            "permission": "analysis:fund:read"
        }
    ]

    return [menu for menu in menu_config if menu["permission"] in permissions]
```

## API 接口

### POST /api/v1/admin/auth/login
管理端登录

**请求参数**:
```json
{
  "username": "admin",
  "password": "123456"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "real_name": "系统管理员"
    },
    "permissions": ["user:read", "user:write", "user:delete"]
  }
}
```

### POST /api/v1/user/auth/login
分析端登录

**请求参数**:
```json
{
  "username": "user001",
  "password": "password123",
  "remember_me": false
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 2,
      "username": "user001",
      "real_name": "张三",
      "email": "zhangsan@example.com"
    },
    "menus": [
      {
        "id": "stock_quote",
        "title": "关注的股票",
        "icon": "stock",
        "path": "/stock/quote"
      }
    ],
    "permissions": ["stock:quote:read", "analysis:fundamental:read"]
  }
}
```

### POST /api/v1/user/auth/logout
退出登录

**响应示例**:
```json
{
  "code": 0,
  "message": "退出成功"
}
```

## 测试用例

### 管理端登录
1. 访问管理端登录页面
2. 输入 admin 用户名和 123456 密码
3. 点击登录按钮
4. 验证跳转到管理端主页
5. 验证 token 已保存

### 分析端登录
1. 访问分析端登录页面
2. 输入正确的用户名和密码
3. 点击登录按钮
4. 验证跳转到分析端主页
5. 验证菜单已正确加载

### 记住我功能
1. 输入正确的用户名和密码
2. 勾选"记住我"
3. 登录成功后退出
4. 重新访问登录页面
5. 验证用户名已自动填充

### 错误场景
1. 输入不存在的用户名，验证提示错误
2. 输入错误的密码，验证提示错误

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: um-001-system-init.md
- 下一个 Story: um-003-user-management.md
