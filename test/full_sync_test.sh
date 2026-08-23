#!/bin/bash
# 数据同步全流程测试

BASE="http://localhost:8000"
TOKEN=$(curl -s -X POST $BASE/api/v1/admin/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"123456\"}" | python -c "import sys,json; print(json.load(sys.stdin)['data']['token'])")
AUTH="Authorization: Bearer $TOKEN"

echo "=== 1. 创建数据源 ==="
curl -s -X POST $BASE/api/v1/admin/data-sources -H "$AUTH" -H "Content-Type: application/json" -d @test/ds_create.json | python -c "import sys,json; d=json.load(sys.stdin)['data']; print('数据源ID:', d['id'], '| 名称:', d['name'])"

echo ""
echo "=== 2. 创建同步任务(stock_basic) ==="
cat > /tmp/st.json <<'EOF'
{"name":"同步股票列表","source_id":1,"data_interface":"stock_basic","sync_mode":"full","target_table":"stocks","params":[{"param_key":"list_status","param_value":"L"}],"interval_ms":1200,"timeout_seconds":30,"retry_count":2,"status":1}
EOF
curl -s -X POST $BASE/api/v1/admin/sync-tasks -H "$AUTH" -H "Content-Type: application/json" -d @/tmp/st.json | python -c "import sys,json; d=json.load(sys.stdin)['data']; print('任务ID:', d['id'], '| 接口:', d['data_interface'], '| 目标表:', d['target_table'])"

echo ""
echo "=== 3. 手动触发同步 ==="
EXEC_ID=$(curl -s -X POST $BASE/api/v1/admin/sync-tasks/1/execute -H "$AUTH" -H "Content-Type: application/json" -d '{}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['execution_id'])")
echo "执行ID: $EXEC_ID"

echo "等待后台执行..."
sleep 4

echo ""
echo "=== 4. 查询执行详情(含调用明细) ==="
curl -s $BASE/api/v1/admin/sync-logs/$EXEC_ID -H "$AUTH" | python -c "
import sys,json
d=json.load(sys.stdin)['data']
print('状态:', d['status'], '| 记录数:', d['total_records'], '| API调用:', d['api_calls'], '| 耗时:', d['duration_seconds'],'s')
print('错误:', (d['error_message'] or '无')[:80])
for c in d.get('call_logs',[]):
    print(f\"  调用#{c['call_seq']}: {c['status']} | 重试:{c['retry_count']} | {c['duration_ms']}ms | {c['error_message'] or 'OK'}\"[:80])
"

echo ""
echo "=== 5. 同步统计 ==="
curl -s $BASE/api/v1/admin/sync-logs/stats -H "$AUTH" | python -c "
import sys,json
d=json.load(sys.stdin)['data']
print(f\"今日同步:{d['today_count']} | 成功:{d['success_count']} | 失败:{d['failed_count']} | 成功率:{d['success_rate']}% | 总记录:{d['total_records']}\")
"