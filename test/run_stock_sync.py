"""触发同步股票列表任务并验证数据落库"""
import httpx, time, sys
sys.stdout.reconfigure(encoding="utf-8")
T = httpx.post("http://localhost:8000/api/v1/admin/auth/login",
               json={"username":"admin","password":"123456"}).json()["data"]["token"]
h = {"Authorization": f"Bearer {T}"}

# 找 stock_basic 任务
tasks = httpx.get("http://localhost:8000/api/v1/admin/sync-tasks?page_size=100", headers=h).json()["data"]["list"]
task = next((t for t in tasks if t["data_interface"] == "stock_basic"), None)
if not task:
    print("未找到 stock_basic 任务"); sys.exit(1)
print(f"找到任务: id={task['id']} {task['name']} → 目标表 {task['target_table']}")

# 触发执行
r = httpx.post(f"http://localhost:8000/api/v1/admin/sync-tasks/{task['id']}/execute", headers=h, json={}).json()
eid = r["data"]["execution_id"]
print(f"已触发: {eid}")

# 轮询
for i in range(20):
    time.sleep(2)
    p = httpx.get(f"http://localhost:8000/api/v1/admin/sync-logs/{eid}/progress", headers=h).json()["data"]
    print(f"  [{i*2}s] {p['status']} records={p['total_records']} calls={p['api_calls']}")
    if p["status"] != "running":
        break

# 详情
d = httpx.get(f"http://localhost:8000/api/v1/admin/sync-logs/{eid}", headers=h).json()["data"]
print(f"\n最终: {d['status']} | 记录数={d['total_records']} | 耗时={d['duration_seconds']}s")
print(f"错误: {(d['error_message'] or '无')[:150]}")
for c in d["call_logs"]:
    print(f"  调用#{c['call_seq']} {c['status']} {c['duration_ms']}ms {c['record_count']}条")

# 验证 stocks 表数据
if d["status"] == "success":
    import pymysql
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='qianyan')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM stocks")
    print(f"\nstocks 表总记录数: {cur.fetchone()[0]}")
    cur.execute("SELECT ts_code, name, industry, act_ent_type FROM stocks LIMIT 3")
    for row in cur.fetchall():
        print(f"  {row}")
    conn.close()