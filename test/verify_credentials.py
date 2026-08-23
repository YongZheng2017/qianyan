"""验证凭证功能：schema、创建、列表、测试连接"""
import httpx, sys, time
sys.stdout.reconfigure(encoding="utf-8")

# 等待后端就绪
for _ in range(15):
    try:
        if httpx.get("http://localhost:8000/health", timeout=3).status_code == 200:
            break
    except Exception:
        time.sleep(2)
else:
    print("后端未就绪"); sys.exit(1)

T = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
               json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {T}"}

print("=== 1. Tushare 凭证 schema ===")
r = httpx.get("http://localhost:8000/api/v1/admin/data-sources/types/tushare/credentials-schema", headers=h).json()
print(r["data"])

print("\n=== 2. 创建数据源（credentials: {token: xxx}）===")
r = httpx.post("http://localhost:8000/api/v1/admin/data-sources", headers=h, json={
    "name": "凭证测试源", "source_type": "tushare", "api_url": "http://api.tushare.pro",
    "credentials": {"token": "my-secret-token-12345"},
    "description": "验证凭证加密", "status": 1
}).json()
print("code:", r["code"], "| has_credentials:", r["data"]["has_credentials"], "| masked:", r["data"]["credentials_masked"])
sid = r["data"]["id"]

print("\n=== 3. 列表（脱敏 + has_credentials）===")
r = httpx.get("http://localhost:8000/api/v1/admin/data-sources", headers=h).json()
for d in r["data"]["list"]:
    print(f"  id={d['id']} {d['name']} | has_cred={d['has_credentials']} | masked={d['credentials_masked']}")

print("\n=== 4. 测试连接（解密凭证调用 Tushare）===")
r = httpx.post(f"http://localhost:8000/api/v1/admin/data-sources/{sid}/test", headers=h).json()
print(r["data"])

print("\n=== 5. 更新（credentials 留空应保持不变）===")
r = httpx.put(f"http://localhost:8000/api/v1/admin/data-sources/{sid}", headers=h,
              json={"description": "已更新描述"}).json()
print("更新后 masked（应保持原脱敏）:", r["data"]["credentials_masked"])

# 清理
httpx.delete(f"http://localhost:8000/api/v1/admin/data-sources/{sid}", headers=h)
print("\n✅ 验证完成（测试数据已清理）")