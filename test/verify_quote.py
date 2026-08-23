"""验证分析端行情 API"""
import httpx, sys, time
sys.stdout.reconfigure(encoding="utf-8")
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

print("=== 1. 搜索股票 ===")
r = httpx.get("http://localhost:8000/api/v1/analysis/symbols/search", params={"q":"平安"}, headers=h).json()
for s in r["data"][:3]:
    print(f"  {s['code']} {s['name']} ({s['extra']})")

print("\n=== 2. 查询日线（000001.SZ 近5根）===")
r = httpx.get("http://localhost:8000/api/v1/analysis/quotes",
              params={"symbol":"000001.SZ","type":"stock","period":"daily","limit":5}, headers=h).json()
d = r["data"]
print(f"  {d['name']} {d['symbol']} | 周期:{d['period']} | {len(d['items'])}根")
for it in d["items"][-3:]:
    print(f"  {it['trade_date']} 开{it['open']} 高{it['high']} 低{it['low']} 收{it['close']} 涨幅{it['pct_chg']}%")