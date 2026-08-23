import httpx, sys
sys.stdout.reconfigure(encoding="utf-8")
TOKEN = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
                   json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {TOKEN}"}
eid = "exec_20260808043408_96d877"
for path in [f"/api/v1/admin/sync-logs/{eid}/progress", f"/api/v1/admin/sync-logs/{eid}"]:
    r = httpx.get(f"http://localhost:8000{path}", headers=h, timeout=10)
    print(f"\n>>> {path}  HTTP {r.status_code}")
    print(r.text[:800])