"""
简单API测试脚本
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("API 测试")
print("=" * 60)

# 1. 健康检查
print("\n1. 健康检查")
response = requests.get(f"{BASE_URL}/health")
print(f"状态码: {response.status_code}")
print(f"响应: {response.json()}\n")

# 2. 管理员登录
print("2. 管理员登录")
response = requests.post(
    f"{BASE_URL}/api/v1/admin/auth/login",
    json={"username": "admin", "password": "123456"}
)
print(f"状态码: {response.status_code}")
data = response.json()
print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

if data.get("code") == 0:
    token = data["data"]["token"]

    # 3. 获取用户列表
    print("3. 获取用户列表")
    response = requests.get(
        f"{BASE_URL}/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

    # 4. 创建新用户
    print("4. 创建新用户")
    response = requests.post(
        f"{BASE_URL}/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "testuser",
            "password": "test123",
            "confirm_password": "test123",
            "real_name": "测试用户",
            "email": "test@example.com",
            "role_ids": [2],
            "status": 1
        }
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}\n")

print("=" * 60)
print("测试完成")
print("=" * 60)