<template>
  <div class="page">
    <div class="page-header">
      <h2>同步日志</h2>
      <el-button type="warning" @click="handleClean">清理历史日志</el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="12" class="stats">
      <el-col :span="4"><div class="stat-card"><div class="stat-num">{{ stats.today_count }}</div><div class="stat-label">今日同步</div></div></el-col>
      <el-col :span="4"><div class="stat-card success"><div class="stat-num">{{ stats.success_count }}</div><div class="stat-label">成功</div></div></el-col>
      <el-col :span="4"><div class="stat-card danger"><div class="stat-num">{{ stats.failed_count }}</div><div class="stat-label">失败</div></div></el-col>
      <el-col :span="4"><div class="stat-card"><div class="stat-num">{{ stats.success_rate }}%</div><div class="stat-label">成功率</div></div></el-col>
      <el-col :span="4"><div class="stat-card"><div class="stat-num">{{ stats.avg_duration }}s</div><div class="stat-label">平均耗时</div></div></el-col>
      <el-col :span="4"><div class="stat-card"><div class="stat-num">{{ stats.total_records }}</div><div class="stat-label">总记录数</div></div></el-col>
    </el-row>

    <!-- 筛选 -->
    <div class="filter-bar">
      <el-select v-model="filters.task_id" placeholder="按任务筛选" clearable style="width:200px" @change="fetchList">
        <el-option v-for="t in taskOptions" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-select v-model="filters.status" placeholder="按状态筛选" clearable style="width:140px;margin-left:12px" @change="fetchList">
        <el-option label="运行中" value="running" />
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
        <el-option label="超时" value="timeout" />
      </el-select>
      <el-date-picker v-model="dateRange" type="daterange" range-separator="至" start-placeholder="开始" end-placeholder="结束"
        value-format="YYYY-MM-DD" style="margin-left:12px" @change="onDateChange" />
    </div>

    <el-table v-loading="loading" :data="list" border style="margin-top:16px">
      <el-table-column prop="execution_id" label="执行ID" width="220" show-overflow-tooltip />
      <el-table-column prop="task_name" label="任务" width="140" />
      <el-table-column prop="source_name" label="数据源" width="130" />
      <el-table-column label="触发" width="80">
        <template #default="{ row }">{{ row.trigger_type === 'manual' ? '手动' : '定时' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="total_records" label="记录数" width="90" />
      <el-table-column prop="api_calls" label="调用次数" width="90" />
      <el-table-column prop="duration_seconds" label="耗时(秒)" width="90" />
      <el-table-column label="开始时间" width="170">
        <template #default="{ row }">{{ formatTime(row.start_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="showDetail(row)">详情</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination v-model:current-page="page.page" v-model:page-size="page.pageSize"
        :page-sizes="[10,20,50]" :total="page.total" layout="total,sizes,prev,pager,next"
        @size-change="fetchList" @current-change="fetchList" />
    </div>

    <!-- 详情抽屉 -->
    <el-drawer v-model="detailVisible" title="执行详情" size="640px">
      <div v-if="detail" class="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="执行ID">{{ detail.execution_id }}</el-descriptions-item>
          <el-descriptions-item label="状态"><el-tag :type="statusType(detail.status)" size="small">{{ statusText(detail.status) }}</el-tag></el-descriptions-item>
          <el-descriptions-item label="任务">{{ detail.task_name }}</el-descriptions-item>
          <el-descriptions-item label="数据源">{{ detail.source_name }}</el-descriptions-item>
          <el-descriptions-item label="触发方式">{{ detail.trigger_type === 'manual' ? '手动' : '定时' }}</el-descriptions-item>
          <el-descriptions-item label="耗时">{{ detail.duration_seconds ?? '-' }}秒</el-descriptions-item>
          <el-descriptions-item label="记录数">{{ detail.total_records }}</el-descriptions-item>
          <el-descriptions-item label="调用次数">{{ detail.api_calls }}</el-descriptions-item>
          <el-descriptions-item label="开始">{{ formatTime(detail.start_at) }}</el-descriptions-item>
          <el-descriptions-item label="结束">{{ formatTime(detail.end_at) }}</el-descriptions-item>
          <el-descriptions-item label="参数" :span="2"><code>{{ JSON.stringify(detail.params_snapshot) }}</code></el-descriptions-item>
          <el-descriptions-item v-if="detail.error_message" label="错误" :span="2"><span class="err">{{ detail.error_message }}</span></el-descriptions-item>
        </el-descriptions>

        <h4 style="margin:20px 0 12px">接口调用明细（{{ detail.call_logs.length }}次）</h4>
        <el-timeline>
          <el-timeline-item v-for="c in detail.call_logs" :key="c.id" :type="statusType(c.status)" :timestamp="formatTime(c.request_at)" placement="top">
            <el-card shadow="never">
              <div><b>调用#{{ c.call_seq }}</b> <el-tag :type="statusType(c.status)" size="small">{{ statusText(c.status) }}</el-tag>
                <span class="ml">{{ c.duration_ms }}ms · {{ c.record_count }}条 · 重试{{ c.retry_count }}次</span></div>
              <div class="sub">参数: <code>{{ c.request_params ? JSON.stringify(c.request_params) : '-' }}</code></div>
              <div v-if="c.error_message" class="err">{{ c.error_message }}</div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSyncLogList, getSyncLogDetail, getSyncStats, cleanSyncLogs, deleteSyncLog } from '../api/syncLog'
import { getSyncTaskList } from '../api/syncTask'

const loading = ref(false)
const list = ref([])
const page = reactive({ page: 1, pageSize: 10, total: 0 })
const stats = reactive({ today_count:0, success_count:0, failed_count:0, success_rate:0, avg_duration:0, total_records:0 })
const filters = reactive({ task_id:'', status:'' })
const dateRange = ref([])
const taskOptions = ref([])

const detailVisible = ref(false); const detail = ref(null)

const STATUS = { running:{ t:'运行中', c:'primary' }, success:{ t:'成功', c:'success' }, failed:{ t:'失败', c:'danger' }, timeout:{ t:'超时', c:'warning' } }
const statusText = s => STATUS[s]?.t || s
const statusType = s => STATUS[s]?.c || 'info'
const formatTime = t => t ? new Date(t).toLocaleString('zh-CN') : ''

onMounted(async () => {
  try { const res = await getSyncTaskList({ page:1, page_size:100 }); taskOptions.value = res.data.list } catch {}
  fetchStats(); fetchList()
})

function onDateChange() { fetchList() }

async function fetchStats() {
  const res = await getSyncStats(); Object.assign(stats, res.data)
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page:page.page, page_size:page.pageSize, task_id:filters.task_id || undefined, status:filters.status || undefined }
    if (dateRange.value?.length === 2) { params.start_date = dateRange.value[0]; params.end_date = dateRange.value[1] }
    const res = await getSyncLogList(params)
    list.value = res.data.list; page.total = res.data.total
  } finally { loading.value = false }
}

async function showDetail(row) {
  const res = await getSyncLogDetail(row.execution_id)
  detail.value = res.data
  detailVisible.value = true
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定删除日志 ${row.execution_id} 吗？（含调用明细）`, '提示', { type: 'warning' })
    .then(async () => {
      await deleteSyncLog(row.execution_id)
      ElMessage.success('删除成功')
      fetchStats(); fetchList()
    }).catch(() => {})
}

function handleClean() {
  ElMessageBox.prompt('清理此日期之前的日志（YYYY-MM-DD）', '清理历史日志', { inputPlaceholder:'如 2026-07-01' })
    .then(async ({ value }) => {
      const res = await cleanSyncLogs(value)
      ElMessage.success(`已清理 ${res.data.deleted_count} 条`)
      fetchStats(); fetchList()
    }).catch(() => {})
}
</script>

<style scoped>
.page { background:#fff; padding:20px; border-radius:4px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-header h2 { margin:0; font-size:20px; }
.stats { margin-bottom:16px; }
.stat-card { background:#f5f7fa; border-radius:6px; padding:16px; text-align:center; border-left:3px solid #409eff; }
.stat-card.success { border-left-color:#67c23a; }
.stat-card.danger { border-left-color:#f56c6c; }
.stat-num { font-size:24px; font-weight:bold; color:#303133; }
.stat-label { font-size:12px; color:#909399; margin-top:4px; }
.filter-bar { display:flex; align-items:center; }
.pagination { margin-top:16px; display:flex; justify-content:flex-end; }
.detail .err { color:#f56c6c; word-break:break-all; }
.detail .ml { margin-left:8px; color:#909399; font-size:13px; }
.detail .sub { color:#909399; font-size:13px; margin-top:4px; word-break:break-all; }
.detail code { background:#f5f7fa; padding:2px 6px; border-radius:3px; font-size:12px; word-break:break-all; }
</style>