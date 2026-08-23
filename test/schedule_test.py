import httpx, sys
sys.stdout.reconfigure(encoding="utf-8")
TOKEN = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
                   json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {TOKEN}"}

print("=== 1. 设置每日18:00调度（任务2）===")
r = httpx.post("http://localhost:8000/api/v1/admin/sync-tasks/2/schedule",
               headers=h, json={"schedule_type":"daily","execute_time":"18:00","enabled":1}, timeout=10)
print(r.json())

print("\n=== 2. 查询调度配置 ===")
r = httpx.get("http://localhost:8000/api/v1/admin/sync-tasks/2/schedule", headers=h, timeout=10)
d = r.json()["data"]
print(f"type={d['schedule_type']} time={d['execute_time']} enabled={d['enabled']} next_run={d['next_run_at']}")

print("\n=== 3. 暂停调度 ===")
r = httpx.put("http://localhost:8000/api/v1/admin/sync-tasks/2/schedule/toggle?enabled=0", headers=h, timeout=10)
print(r.json())

print("\n=== 4. 同步统计 ===")
r = httpx.get("http://localhost:8000/api/v1/admin/sync-logs/stats", headers=h, timeout=10)
d = r.json()["data"]
print(f"今日:{d['today_count']} 成功:{d['success_count']} 失败:{d['failed_count']} 成功率:{d['success_rate']}% 总记录:{d['total_records']}")

print("\n=== 5. 同步日志列表 ===")
r = httpx.get("http://localhost:8000/api/v1/admin/sync-logs?page=1&page_size=5", headers=h, timeout=10)
d = r.json()["data"]
print(f"total={d['total']}")
for l in d["list"]:
    print(f"  {l['execution_id'][:25]}.. | {l['status']} | {l['task_name']} | {l['trigger_type']}")