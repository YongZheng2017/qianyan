import httpx, time, sys
sys.stdout.reconfigure(encoding="utf-8")
TOKEN = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
                   json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {TOKEN}"}

# 触发任务 2（已存在的同步股票列表任务）
r = httpx.post("http://localhost:8000/api/v1/admin/sync-tasks/2/execute", headers=h, json={}, timeout=10)
exec_id = r.json()["data"]["execution_id"]
print(f"触发成功，execution_id: {exec_id}")

# 轮询直到完成
for i in range(15):
    time.sleep(2)
    p = httpx.get(f"http://localhost:8000/api/v1/admin/sync-logs/{exec_id}/progress", headers=h, timeout=10).json()["data"]
    print(f"  [{i*2}s] status={p['status']} records={p['total_records']} calls={p['api_calls']}")
    if p["status"] != "running":
        break

# 最终详情
d = httpx.get(f"http://localhost:8000/api/v1/admin/sync-logs/{exec_id}", headers=h, timeout=10).json()["data"]
print(f"\n最终: status={d['status']} duration={d['duration_seconds']}s error={(d['error_message'] or '无')[:100]}")
print(f"调用明细 {len(d['call_logs'])} 条:")
for c in d["call_logs"]:
    print(f"  #{c['call_seq']} {c['status']} retry:{c['retry_count']} {c['duration_ms']}ms | {(c['error_message'] or 'OK')[:70]}")