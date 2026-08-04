"""
测试脚本 - 启动应用并测试 API
"""
import subprocess
import sys
import time
import requests
import json

def install_dependencies():
    """安装依赖"""
    print("📦 安装 Python 依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ 依赖安装完成\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)


def start_application():
    """启动应用"""
    print("🚀 启动应用...")
    print("提示：应用将在后台启动，测试完成后请手动停止\n")

    # 启动应用（后台运行）
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 等待应用启动
    print("⏳ 等待应用启动...")
    time.sleep(5)

    return process


def test_health_check():
    """测试健康检查"""
    print("\n📋 测试 1: 健康检查")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        assert response.status_code == 200
        print("✅ 健康检查通过\n")
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")


def test_admin_login():
    """测试管理员登录"""
    print("📋 测试 2: 管理员登录")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/admin/auth/login",
            json={"username": "admin", "password": "123456"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200
        assert data["code"] == 0
        assert "token" in data["data"]

        print("✅ 管理员登录成功\n")
        return data["data"]["token"]
    except Exception as e:
        print(f"❌ 管理员登录失败: {e}\n")
        return None


def test_get_users(token):
    """测试获取用户列表"""
    print("📋 测试 3: 获取用户列表")
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"}
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200
        assert data["code"] == 0
        assert "list" in data["data"]

        print("✅ 获取用户列表成功\n")
    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}\n")


def test_create_user(token):
    """测试创建用户"""
    print("📋 测试 4: 创建用户")
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "username": "testuser",
                "password": "test123",
                "confirm_password": "test123",
                "real_name": "测试用户",
                "email": "test@example.com",
                "role_ids": [1],
                "status": 1
            }
        )
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

        assert response.status_code == 200
        assert data["code"] == 0

        print("✅ 创建用户成功\n")
        return data["data"]["id"]
    except Exception as e:
        print(f"❌ 创建用户失败: {e}\n")
        return None


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 钱眼投资分析系统 - API 测试")
    print("=" * 60)

    # 1. 安装依赖
    install_dependencies()

    # 2. 启动应用
    process = start_application()

    try:
        # 3. 测试健康检查
        test_health_check()

        # 4. 测试管理员登录
        token = test_admin_login()
        if not token:
            print("❌ 无法获取 token，停止测试")
            return

        # 5. 测试获取用户列表
        test_get_users(token)

        # 6. 测试创建用户
        test_create_user(token)

        print("=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        print("\n🌐 访问 API 文档: http://localhost:8000/docs")
        print("按 Ctrl+C 停止应用...")

        # 保持应用运行
        process.wait()

    except KeyboardInterrupt:
        print("\n\n🛑 停止应用...")
    finally:
        process.terminate()
        process.wait()
        print("✅ 应用已停止")


if __name__ == "__main__":
    main()