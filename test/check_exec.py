import httpx, sys
sys.stdout.reconfigure(encoding="utf-8")
TOKEN = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
                   json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {TOKEN}"}
r = httpx.get("http://localhost:8000/api/v1/admin/sync-logs/exec_20260808043210_d2ea4c", headers=h, timeout=10)
d = r.json()["data"]
print(f"status: {d['status']} | api_calls: {d['api_calls']} | duration: {d['duration_seconds']}s")
print(f"error: {(d['error_message'] or '无')[:120]}")
print(f"call_logs: {len(d['call_logs'])} 条")
for c in d["call_logs"]:
    print(f"  #{c['call_seq']} {c['status']} retry:{c['retry_count']} {(c['error_message'] or 'OK')[:80]}")