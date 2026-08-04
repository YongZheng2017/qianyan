# 测试文件目录

本目录包含所有测试相关的文件。

## 文件说明

### API 测试
- `test_api.py` - 完整的API测试脚本，包括安装依赖、启动应用、测试各个端点
- `simple_test.py` - 简单的API测试脚本，测试基本功能

### 测试数据
- `test_user.json` - 用户创建测试数据
- `test_create_user.json` - 用户创建测试数据（邮箱为空）

## 使用方法

### 运行完整测试
```bash
cd F:\github\qianyan
python test/test_api.py
```

### 运行简单测试
```bash
python test/simple_test.py
```

### 使用 curl 测试
```bash
# 健康检查
curl http://localhost:8000/health

# 管理员登录
curl -X POST http://localhost:8000/api/v1/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'

# 创建用户（需要token）
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @test/test_create_user.json
```