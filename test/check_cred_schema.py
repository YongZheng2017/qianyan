import httpx, sys
sys.stdout.reconfigure(encoding="utf-8")
T = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
               json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {T}"}
r = httpx.get("http://localhost:8000/api/v1/admin/data-sources/types/tushare/credentials-schema", headers=h)
print("HTTP", r.status_code)
print(r.text[:500])