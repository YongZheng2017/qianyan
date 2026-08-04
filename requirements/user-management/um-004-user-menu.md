# UM-004: 分析端菜单展示

## 用户故事

作为系统用户，我希望登录后能够看到我拥有权限的菜单，以便我能够访问系统功能。

## 验收标准

### 功能需求

#### AC1: 显示用户菜单
**Given**: 用户登录分析端
**When**: 进入主页
**Then**: 左侧显示用户的一级菜单

#### AC2: 根据权限过滤菜单
**Given**: 用户有部分功能权限
**When**: 查看菜单
**Then**: 只显示有权限的菜单项

#### AC3: 菜单项包含图标
**Given**: 显示菜单
**When**: 查看菜单项
**Then**: 每个菜单项有对应的图标

#### AC4: 菜单点击跳转
**Given**: 显示菜单
**When**: 点击菜单项
**Then**: 跳转到对应的页面

#### AC5: 菜单高亮状态
**Given**: 在某个页面
**When**: 查看菜单
**Then**: 当前页面对应的菜单项高亮显示

#### AC6: 响应式菜单
**Given**: 在小屏幕设备
**When**: 查看菜单
**Then**: 菜单折叠或以抽屉形式显示

#### AC7: 用户信息展示
**Given**: 用户登录分析端
**When**: 查看顶部导航栏
**Then**: 显示当前用户信息
**And**: 提供退出登录按钮

## 菜单配置

### 标准用户菜单

| 菜单ID | 菜单名称 | 图标 | 路径 | 权限要求 |
|--------|----------|------|------|----------|
| stock_quote | 关注的股票 | stock | /stock/quote | stock:quote:read |
| fundamental | 基本面分析 | chart | /analysis/fundamental | analysis:fundamental:read |
| trend | 趋势分析 | trend | /analysis/trend | analysis:trend:read |
| fund_flow | 资金趋势 | fund | /analysis/fund-flow | analysis:fund:read |

## 技术实现

### 前端主页面实现

```jsx
// DashboardPage.jsx
function DashboardPage() {
  const [menus, setMenus] = useState([]);
  const [activeMenu, setActiveMenu] = useState('');
  const [collapsed, setCollapsed] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // 从 localStorage 获取菜单和用户信息
    const savedMenus = localStorage.getItem('user_menus');
    const savedUserInfo = localStorage.getItem('user_info');
    if (savedMenus) {
      setMenus(JSON.parse(savedMenus));
    }
    if (savedUserInfo) {
      setUserInfo(JSON.parse(savedUserInfo));
    }

    // 设置当前激活的菜单
    const currentPath = location.pathname;
    const activeMenuId = menus.find(m => currentPath.startsWith(m.path))?.id || '';
    setActiveMenu(activeMenuId);
  }, [location.pathname]);

  const handleMenuClick = (menu) => {
    setActiveMenu(menu.id);
    navigate(menu.path);
  };

  const handleLogout = () => {
    Modal.confirm({
      title: '确认退出',
      content: '确定要退出登录吗？',
      onOk: async () => {
        try {
          await fetch('/api/v1/user/auth/logout', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('user_token')}` }
          });
        } catch (err) {
          // 即使接口失败也清除本地状态
        }

        // 清除本地状态
        localStorage.removeItem('user_token');
        localStorage.removeItem('user_info');
        localStorage.removeItem('user_menus');
        navigate('/login');
      }
    });
  };

  const renderMenuItem = (menu) => {
    const icons = {
      stock: <StockOutlined />,
      chart: <LineChartOutlined />,
      trend: <RiseOutlined />,
      fund: <DollarOutlined />
    };

    return (
      <Menu.Item
        key={menu.id}
        icon={icons[menu.icon]}
        onClick={() => handleMenuClick(menu)}
        className={activeMenu === menu.id ? 'active' : ''}
      >
        {menu.title}
      </Menu.Item>
    );
  };

  const userMenu = (
    <Menu>
      <Menu.Item icon={<UserOutlined />}>
        {userInfo?.real_name || userInfo?.username}
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item icon={<ProfileOutlined />}>个人中心</Menu.Item>
      <Menu.Item icon={<SettingOutlined />}>设置</Menu.Item>
      <Menu.Divider />
      <Menu.Item icon={<LogoutOutlined />} onClick={handleLogout} danger>
        退出登录
      </Menu.Item>
    </Menu>
  );

  return (
    <div className="dashboard-layout">
      {/* 左侧菜单 */}
      <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="logo">
          <StockOutlined />
          {!collapsed && <span>股票分析系统</span>}
        </div>

        <Menu mode="inline" selectedKeys={[activeMenu]}>
          {menus.map(renderMenuItem)}
        </Menu>

        <Button
          className="collapse-btn"
          type="text"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
        </Button>
      </div>

      {/* 主内容区 */}
      <div className="main-content">
        <Header>
          <div className="header-left">
            <Breadcrumb>
              <Breadcrumb.Item>首页</Breadcrumb.Item>
              {menus.find(m => m.id === activeMenu) && (
                <Breadcrumb.Item>
                  {menus.find(m => m.id === activeMenu).title}
                </Breadcrumb.Item>
              )}
            </Breadcrumb>
          </div>

          <div className="header-right">
            <Dropdown overlay={userMenu} trigger={['click']}>
              <Button type="text">
                <UserOutlined />
                <span>{userInfo?.real_name || userInfo?.username}</span>
                <DownOutlined />
              </Button>
            </Dropdown>
          </div>
        </Header>

        <Content className="content-area">
          <Routes>
            <Route path="/stock/quote" element={<StockQuotePage />} />
            <Route path="/analysis/fundamental" element={<FundamentalAnalysisPage />} />
            <Route path="/analysis/trend" element={<TrendAnalysisPage />} />
            <Route path="/analysis/fund-flow" element={<FundFlowPage />} />
            <Route path="/" element={<WelcomePage />} />
          </Routes>
        </Content>
      </div>
    </div>
  );
}

// 欢迎页面组件
function WelcomePage() {
  return (
    <div className="welcome-page">
      <Result
        status="success"
        title="欢迎使用股票分析系统"
        subTitle="请从左侧菜单选择功能"
        extra={
          <Button type="primary" onClick={() => window.location.href = '/stock/quote'}>
            开始使用
          </Button>
        }
      />
    </div>
  );
}
```

### 后端菜单获取接口

```python
from fastapi import APIRouter, Depends
from typing import List

router = APIRouter()

class MenuItem(BaseModel):
    id: str
    title: str
    icon: str
    path: str

@router.get("/user/menus", response_model=List[MenuItem])
async def get_user_menus(current_user: User = Depends(get_current_user)):
    """获取用户菜单配置"""

    # 获取用户权限
    permissions = await get_user_permissions(current_user.id)

    # 菜单配置
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

    # 根据权限过滤菜单
    user_menus = []
    for menu in menu_config:
        if menu["permission"] in permissions:
            user_menus.append({
                "id": menu["id"],
                "title": menu["title"],
                "icon": menu["icon"],
                "path": menu["path"]
            })

    return user_menus
```

### CSS 样式

```css
.dashboard-layout {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}

.sidebar {
  width: 240px;
  background: #001529;
  color: white;
  transition: width 0.2s;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
}

.sidebar.collapsed {
  width: 80px;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo span {
  margin-left: 12px;
}

.collapse-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  color: rgba(255, 255, 255, 0.65);
}

.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.2s;
}

.sidebar.collapsed + .main-content {
  margin-left: 80px;
}

.content-area {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

/* 菜单项样式 */
.ant-menu-item.active {
  background: #1890ff;
}

.ant-menu-item.active .anticon {
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    z-index: 1000;
    transform: translateX(-100%);
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .main-content {
    margin-left: 0;
  }

  .sidebar.collapsed + .main-content {
    margin-left: 0;
  }
}
```

## API 接口

### GET /api/v1/user/menus
获取用户菜单配置

**响应示例**:
```json
{
  "code": 0,
  "data": [
    {
      "id": "stock_quote",
      "title": "关注的股票",
      "icon": "stock",
      "path": "/stock/quote"
    },
    {
      "id": "fundamental",
      "title": "基本面分析",
      "icon": "chart",
      "path": "/analysis/fundamental"
    },
    {
      "id": "trend",
      "title": "趋势分析",
      "icon": "trend",
      "path": "/analysis/trend"
    },
    {
      "id": "fund_flow",
      "title": "资金趋势",
      "icon": "fund",
      "path": "/analysis/fund-flow"
    }
  ]
}
```

## 测试用例

### 正常流程测试
1. 用户登录分析端
2. 验证左侧显示菜单
3. 验证只显示有权限的菜单项
4. 点击菜单项
5. 验证跳转到对应页面
6. 验证菜单项高亮显示

### 权限过滤测试
1. 创建不同权限的用户
2. 登录不同用户
3. 验证菜单根据权限变化
4. 验证无权限的菜单不显示

### 响应式测试
1. 在移动端访问
2. 验证菜单折叠显示
3. 验证菜单展开/收起功能
4. 验证抽屉菜单在移动端正常工作

### 退出登录测试
1. 点击用户下拉菜单
2. 点击退出登录
3. 验证确认对话框显示
4. 确认退出
5. 验证跳转到登录页面
6. 验证本地状态已清除

### 用户信息展示测试
1. 登录分析端
2. 验证顶部导航栏显示用户信息
3. 验证显示用户名或真实姓名
4. 点击用户下拉菜单
5. 验证显示个人中心和设置选项

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: um-002-user-login.md
- 上一个 Story: um-003-user-management.md
