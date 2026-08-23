"""
数据同步全流程测试（使用 httpx，避免 shell 管道问题）
"""
import httpx
import json
import time
import sys

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=30)

# 解决 Windows 控制台编码
sys.stdout.reconfigure(encoding="utf-8")


def pp(title, data):
    print(f"\n=== {title} ===")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])


# 1. 登录
r = client.post("/api/v1/admin/auth/login", json={"username": "admin", "password": "123456"})
token = r.json()["data"]["token"]
headers = {"Authorization": f"Bearer {token}"}
print("登录成功")

# 2. 创建数据源
r = client.post("/api/v1/admin/data-sources", headers=headers, json={
    "name": "Tushare测试源", "source_type": "tushare",
    "api_url": "http://api.tushare.pro",
    "token": "test-invalid-token",
    "description": "测试", "status": 1
})
ds = r.json()
pp("创建数据源", ds)
source_id = ds["data"]["id"]

# 3. 创建同步任务
r = client.post("/api/v1/admin/sync-tasks", headers=headers, json={
    "name": "同步股票列表", "source_id": source_id,
    "data_interface": "stock_basic", "sync_mode": "full",
    "target_table": "stocks",
    "params": [{"param_key": "list_status", "param_value": "L"}],
    "interval_ms": 1200, "timeout_seconds": 30, "retry_count": 2, "status": 1
})
task = r.json()
pp("创建同步任务", task)
task_id = task["data"]["id"]

# 4. 手动触发同步
r = client.post(f"/api/v1/admin/sync-tasks/{task_id}/execute", headers=headers, json={})
exec_resp = r.json()
pp("触发同步", exec_resp)
exec_id = exec_resp["data"]["execution_id"]

# 5. 等待后台执行
print("\n等待后台执行（含2次重试，约6秒）...")
time.sleep(8)

# 6. 查询执行详情
r = client.get(f"/api/v1/admin/sync-logs/{exec_id}", headers=headers)
detail = r.json()
pp("执行详情(含调用明细)", detail)

# 7. 查询进度
r = client.get(f"/api/v1/admin/sync-logs/{exec_id}/progress", headers=headers)
pp("执行进度", r.json())

# 8. 统计
r = client.get("/api/v1/admin/sync-logs/stats", headers=headers)
pp("同步统计", r.json())

# 9. 设置调度
r = client.post(f"/api/v1/admin/sync-tasks/{task_id}/schedule", headers=headers, json={
    "schedule_type": "daily", "execute_time": "18:00", "enabled": 1
})
pp("设置每日18:00调度", r.json())

# 10. 查询调度
r = client.get(f"/api/v1/admin/sync-tasks/{task_id}/schedule", headers=headers)
pp("调度配置", r.json())

# 清理（可选）
# client.delete(f"/api/v1/admin/sync-tasks/{task_id}", headers=headers)
# client.delete(f"/api/v1/admin/data-sources/{source_id}", headers=headers)

print("\n✅ 全流程测试完成")
client.close()