# UM-003: 用户管理

## 用户故事

作为系统管理员，我希望能够管理系统中的用户，包括查看用户列表、新增用户、编辑用户信息和修改用户密码，以便进行用户管理工作。

。

## 验收标准

### 功能需求

#### AC1: 显示用户列表
**Given**: 管理员登录管理端
**When**: 进入用户管理页面
**Then**: 显示系统中所有用户的列表
**And**: 包含用户名、真实姓名、邮箱、状态、创建时间等信息

#### AC2: 用户列表分页
**Given**: 用户数据超过 10 条
**When**: 查看用户列表
**Then**: 显示分页控件
**And**: 默认每页显示 10 条数据

#### AC3: 用户列表搜索
**Given**: 在用户管理页面
**When**: 在搜索框输入用户名
**Then**: 显示匹配的用户

#### AC4: 用户列表筛选
**Given**: 在用户管理页面
**When**: 选择用户状态筛选条件
**Then**: 显示符合状态的用户

#### AC5: 新增用户
**Given**: 在用户管理页面
**When**: 点击新增用户按钮
**Then**: 显示新增用户表单
**And**: 包含用户名、密码、真实姓名、邮箱、角色、状态字段

#### AC6: 新增用户验证
**Given**: 在新增用户表单
**When**: 用户名为空或已存在
**Then**: 提示相应的错误信息

#### AC7: 编辑用户
**Given**: 在用户列表
**When**: 点击某个用户的编辑按钮
**Then**: 显示编辑用户表单
**And**: 用户名字段为只读状态
**And**: 不显示密码字段

#### AC8: 修改用户密码
**Given**: 在用户列表
**When**: 点击某个用户的修改密码按钮
**Then**: 显示修改密码弹窗
**And**: 包含新密码和确认密码字段

#### AC9: 删除用户
**Given**: 在用户列表
**When**: 点击某个用户的删除按钮
**Then**: 显示确认对话框
**And**: 确认后删除用户

## 表单字段要求

### 新增用户表单

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| 用户名 | 文本 | 是 | 4-20字符，字母数字下划线，唯一 |
| 密码 | 密码 | 是 | 6-20字符，包含字母和数字 |
| 确认密码 | 密码 | 是 | 与密码一致 |
| 真实姓名 | 文本 | 否 | 最多50字符 |
| 邮箱 | 邮箱 | 否 | 邮箱格式 |
| 角色 | 选择 | 是 | 至少选择一个 |
| 状态 | 选择 | 是 | 启用/禁用，默认启用 |

### 编辑用户表单

| 字段 | 类型 | 必填 | 是否可编辑 |
|------|------|------|------------|
| 用户名 | 文本 | 是 | 否 |
| 真实姓名 | 文本 | 否 | 是 |
| 邮箱 | 邮箱 | 否 | 是 |
| 角色 | 选择 | 是 | 是 |
| 状态 | 选择 | 是 | 是 |

### 修改密码表单

| 字段 | 类型 | 必填 | 验证规则 |
|------|------|------|----------|
| 新密码 | 密码 | 是 | 6-20字符，包含字母和数字 |
| 确认密码 | 密码 | 是 | 与新密码一致 |

## 技术实现

### 前端页面实现

```jsx
// UserListPage.jsx
function UserListPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 });
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [modalVisible, setModalVisible] = useState(false);
  const [modalType, setModalType] = useState('create'); // 'create', 'edit', 'password'
  const [currentUser, setCurrentUser] = useState(null);
  const [form] = Form.useForm();

  const fetchUsers = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await fetch(
        `/api/v1/admin/users?page=${page}&page_size=${pageSize}&search=${searchText}&status=${statusFilter}`,
        { headers: { 'Authorization': `Bearer ${localStorage.getItem('admin_token')}` } }
      );

      const data = await response.json();
      if (data.code === 0) {
        setUsers(data.data.list);
        setPagination({ current: data.data.page, pageSize: data.data.page_size, total: data.data.total });
      }
    } catch (err) {
      message.error('获取用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [searchText, statusFilter]);

  const handleCreate = () => {
    setModalType('create');
    setCurrentUser(null);
    form.resetFields();
    form.setFieldsValue({ status: 1 });
    setModalVisible(true);
  };

  const handleEdit = (user) => {
    setModalType('edit');
    setCurrentUser(user);
    form.setFieldsValue({
      username: user.username,
      real_name: user.real_name,
      email: user.email,
      role_ids: user.role_ids,
      status: user.status
    });
    setModalVisible(true);
  };

  const handleChangePassword = (user) => {
    setModalType('password');
    setCurrentUser(user);
    form.resetFields();
    setModalVisible(true);
  };

  const handleDelete = (user) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除用户 ${user.username} 吗？`,
      onOk: async () => {
        try {
          await fetch(`/api/v1/admin/users/${user.id}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('admin_token')}` }
          });
          message.success('删除成功');
          fetchUsers();
        } catch (err) {
          message.error('删除失败');
        }
      }
    });
  };

  const handleModalSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      let response;
      if (modalType === 'create') {
        response = await fetch('/api/v1/admin/users', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(values)
        });
      } else if (modalType === 'edit') {
        response = await fetch(`/api/v1/admin/users/${currentUser.id}`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(values)
        });
      } else if (modalType === 'password') {
        response = await fetch(`/api/v1/admin/users/${currentUser.id}/password`, {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('admin_token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(values)
        });
      }

      const data = await response.json();
      if (data.code === 0) {
        message.success('操作成功');
        setModalVisible(false);
        fetchUsers();
      } else {
        message.error(data.message);
      }
    } catch (err) {
      message.error('操作失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '用户 ID', dataIndex: 'id', key: 'id' },
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '真实姓名', dataIndex: 'real_name', key: 'real_name' },
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <span className={status === 1 ? 'status-active' : 'status-inactive'}>{status === 1 ? '启用' : '禁用'}</span>
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => handleEdit(record)}>编辑</Button>
          <Button size="small" onClick={() => handleChangePassword(record)}>修改密码</Button>
          <Button size="small" danger onClick={() => handleDelete(record)}>删除</Button>
        </Space>
      )
    }
  ];

  return (
    <div className="user-list-page">
      <div className="page-header">
        <h2>用户管理</h2>
        <Button type="primary" onClick={handleCreate}>新增用户</Button>
      </div>

      <div className="filter-bar">
        <Input.Search
          placeholder="搜索用户名"
          onSearch={setSearchText}
          style={{ width: 200, marginRight: 16 }}
        />
        <Select value={statusFilter} onChange={setStatusFilter} style={{ width: 120 }}>
          <Option value="all">全部状态</Option>
          <Option value="1">启用</Option>
          <Option value="0">禁用</Option>
        </Select>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        loading={loading}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          onChange: (page, pageSize) => fetchUsers(page, pageSize)
        }}
        rowKey="id"
      />

      <Modal
        title={modalType === 'create' ? '新增用户' : modalType === 'edit' ? '编辑用户' : '修改密码'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={handleModalSubmit}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          {modalType === 'create' && (
            <>
              <Form.Item name="username" label="用户名" rules={[{ required: true, message: '请输入用户名' }]}>
                <Input placeholder="请输入用户名" />
              </Form.Item>
              <Form.Item name="password" label="密码" rules={[{ required: true, message: '请输入密码' }]}>
                <Input.Password placeholder="请输入密码" />
              </Form.Item>
              <Form.Item name="confirm_password" label="确认密码" rules={[{ required: true, message: '请确认密码' }]}>
                <Input.Password placeholder="请再次输入密码" />
              </Form.Item>
            </>
          )}

          {(modalType === 'create' || modalType === 'edit') && (
            <>
              {modalType === 'edit' && (
                <Form.Item name="username" label="用户名">
                  <Input disabled />
                </Form.Item>
              )}
              <Form.Item name="real_name" label="真实姓名">
                <Input placeholder="请输入真实姓名" />
              </Form.Item>
              <Form.Item name="email" label="邮箱" rules={[{ type: 'email', message: '请输入有效的邮箱地址' }]}>
                <Input placeholder="请输入邮箱" />
              </Form.Item>
              <Form.Item name="role_ids" label="角色" rules={[{ required: true, message: '请选择角色' }]}>
                <Select mode="multiple" placeholder="请选择角色">
                  {/* 角色选项 */}
                </Select>
              </Form.Item>
              <Form.Item name="status" label="状态" rules={[{ required: true, message: '请选择状态' }]}>
                <Select>
                  <Option value={1}>启用</Option>
                  <Option value={0}>禁用</Option>
                </Select>
              </Form.Item>
            </>
          )}

          {modalType === 'password' && (
            <>
              <Form.Item name="new_password" label="新密码" rules={[{ required: true, message: '请输入新密码' }]}>
                <Input.Password placeholder="请输入新密码" />
              </Form.Item>
              <Form.Item name="confirm_password" label="确认密码" rules={[{ required: true, message: '请确认密码' }]}>
                <Input.Password placeholder="请再次输入密码" />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
}
```

### 后端 API 实现

```python
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class UserListResponse(BaseModel):
    list: list
    page: int
    page_size: int
    total: int

class UserCreateRequest(BaseModel):
    username: str
    password: str
    confirm_password: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    role_ids: list[int]
    status: int

class UserUpdateRequest(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    role_ids: list[int]
    status: int

class ChangePasswordRequest(BaseModel):
    new_password: str
    confirm_password: str

# 获取用户列表
@router.get("/admin/users", response_model=UserListResponse)
async def get_user_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user)
):
    where_clauses = []
    params = []

    if search:
        where_clauses.append("(username LIKE ? OR real_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if status == "1":
        where_clauses.append("status = 1")
    elif status == "0":
        where_clauses.append("status = 0")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) FROM users WHERE {where_sql}"
    total = await db.fetch_one(count_sql, params)

    offset = (page - 1) * page_size
    list_sql = f"""
        SELECT id, username, real_name, email, status, created_at, last_login_at
        FROM users WHERE {where_sql}
        ORDER BY created_at DESC LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    users = await db.fetch_all(list_sql, params)

    result = []
    for user in users:
        role_ids = await get_user_role_ids(user.id)
        result.append({
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "email": user.email,
            "role_ids": role_ids,
            "status": user.status,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at
        })

    return {"list": result, "page": page, "page_size": page_size, "total": total}

# 创建用户
@router.post("/admin/users")
async def create_user(request: UserCreateRequest, current_user: User = Depends(get_current_admin_user)):
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    existing = await get_user_by_username(request.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    password_hash = pwd_context.hash(request.password)

    user_id = await db.execute(
        """INSERT INTO users (username, password_hash, real_name, email, status)
           VALUES (?, ?, ?, ?, ?)""",
        [request.username, password_hash, request.real_name, request.email, request.status]
    )

    for role_id in request.role_ids:
        await db.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", [user_id, role_id])

    await log_operation(user_id=current_user.id, action="create_user", detail=f"创建用户: {request.username}")

    return {"code": 0, "message": "创建成功", "data": {"id": user_id}}

# 更新用户
@router.put("/admin/users/{user_id}")
async def update_user(user_id: int, request: UserUpdateRequest, current_user: User = Depends(get_current_admin_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.username == "admin" and not request.role_ids:
        raise HTTPException(status_code=400, detail="管理员账号至少需要保留一个角色")

    await db.execute(
        """UPDATE users SET real_name = ?, email = ?, status = ? WHERE id = ?""",
        [request.real_name, request.email, request.status, user_id]
    )

    await db.execute("DELETE FROM user_roles WHERE user_id = ?", [user_id])
    for role_id in request.role_ids:
        await db.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", [user_id, role_id])

    await log_operation(user_id=current_user.id, action="update_user", detail=f"更新用户: {user.username}")

    return {"code": 0, "message": "更新成功"}

# 修改密码
@router.put("/admin/users/{user_id}/password")
async def change_user_password(user_id: int, request: ChangePasswordRequest, current_user: User = Depends(get_current_admin_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")

    password_hash = pwd_context.hash(request.new_password)
    await db.execute("UPDATE users SET password_hash = ? WHERE id = ?", [password_hash, user_id])

    await log_operation(user_id=current_user.id, action="change_password", detail=f"修改用户 {user.username} 的密码")

    return {"code": 0, "message": "密码修改成功"}

# 删除用户
@router.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_admin_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.username == "admin":
        raise HTTPException(status_code=403, detail="不能删除管理员账号")

    await db.execute("DELETE FROM users WHERE id = ?", [user_id])

    await log_operation(user_id=current_user.id, action="delete_user", detail=f"删除用户: {user.username}")

    return {"code": 0, "message": "删除成功"}
```

## API 接口

### GET /api/v1/admin/users
获取用户列表

**请求参数**:
- `page`: 页码，默认 1
- `page_size`: 每页数量，默认 10
- `search`: 搜索关键词
- `status`: 状态筛选（1=启用，0=禁用）

**响应示例**:
```{ "code": 0, "message": "success", "data": { "list": [ { "id": 1, "username": "admin", "real_name": "系统管理员", "email": "", "role_ids": [1], "status": 1, "created_at": "2024-01-01T00:00:00", "last_login_at": "2024-04-19T10:00:00" } ], "page": 1, "page_size": 10, "total": 1 } }
```

### POST /api/v1/admin/users
创建用户

**请求参数**:
```json
{
  "username": "user002",
  "password": "password123",
  "confirm_password": "password123",
  "real_name": "李四",
  "email": "lisi@example.com",
  "role_ids": [2],
  "status": 1
}
```

### PUT /api/v1/admin/users/{user_id}
更新用户

**请求参数**:
```json
{
  "real_name": "李四丰",
  "email": "lisi@example.com",
  "role_ids": [2, 3],
  "status": 1
}
```

### PUT /api/v1/admin/users/{user_id}/password
修改用户密码

**请求参数**:
```json
{
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
```

### DELETE /api/v1/admin/users/{user_id}
删除用户

## 测试用例

### 用户列表测试
1. 进入用户管理页面，验证显示列表
2. 测试分页功能
3. 测试搜索功能
4. 测试状态筛选功能

### 新增用户测试
1. 点击新增用户按钮
2. 输入有效信息，验证创建成功
3. 测试必填项验证
4. 测试用户名唯一性验证

### 编辑用户测试
1. 点击编辑按钮
2. 修改用户信息，验证更新成功
3. 测试 admin 账号保护

### 修改密码测试
1. 点击修改密码按钮
2. 输入新密码，验证修改成功
3. 测试密码验证

### 删除用户测试
1. 点击删除按钮
2. 确认删除，验证删除成功
3. 测试 admin 账号不能删除

## 相关文档

- Feature Map: feature-map.md
- 依赖 Story: um-002-user-login.md
- 下一个 Story: um-004-user-menu.md
