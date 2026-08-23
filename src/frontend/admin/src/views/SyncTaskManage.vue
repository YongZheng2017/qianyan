<template>
  <div class="page">
    <div class="page-header">
      <h2>同步任务管理</h2>
      <el-button type="primary" @click="handleCreate"><el-icon><Plus /></el-icon> 新增任务</el-button>
    </div>

    <div class="filter-bar">
      <el-select v-model="sourceFilter" placeholder="按数据源筛选" clearable style="width: 200px" @change="fetchList">
        <el-option v-for="s in sourceOptions" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="list" border style="margin-top: 16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="任务名称" width="150" />
      <el-table-column prop="source_name" label="数据源" width="140" />
      <el-table-column label="接口" width="160">
        <template #default="{ row }">{{ row.interface_name }}（{{ row.data_interface }}）</template>
      </el-table-column>
      <el-table-column prop="target_table" label="目标表" width="120" />
      <el-table-column label="频率配置" width="160">
        <template #default="{ row }">
          <div>间隔:{{ row.interval_ms }}ms 超时:{{ row.timeout_seconds }}s 重试:{{ row.retry_count }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="最后同步" width="200">
        <template #default="{ row }">
          <el-tag v-if="row.last_sync_status === 'success'" type="success" size="small">成功 {{ row.last_sync_records }}条</el-tag>
          <el-tag v-else-if="row.last_sync_status === 'failed'" type="danger" size="small">失败</el-tag>
          <span v-else style="color:#999">未同步</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="360" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" :loading="executingId === row.id" @click="handleExecute(row)">执行</el-button>
          <el-button size="small" @click="handleSchedule(row)">调度</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination v-model:current-page="page.page" v-model:page-size="page.pageSize"
        :page-sizes="[10,20,50]" :total="page.total" layout="total,sizes,prev,pager,next"
        @size-change="fetchList" @current-change="fetchList" />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增同步任务' : '编辑同步任务'" width="640px" @closed="onDialogClosed">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名称" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="数据源" prop="source_id">
          <el-select v-model="form.source_id" style="width:100%" :disabled="dialogType==='edit'" @change="onSourceChange">
            <el-option v-for="s in sourceOptions" :key="s.id" :label="`${s.name}（${s.source_type}）`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据接口" prop="data_interface">
          <el-select v-model="form.data_interface" style="width:100%" :disabled="!form.source_id || dialogType==='edit'" @change="onInterfaceChange">
            <el-option v-for="i in interfaceOptions" :key="i.value" :label="`${i.label}（${i.value}）`" :value="i.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="同步模式" prop="sync_mode">
          <el-radio-group v-model="form.sync_mode">
            <el-radio label="full">全量</el-radio>
            <el-radio label="incremental">增量</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标表" prop="target_table"><el-input v-model="form.target_table" /></el-form-item>

        <!-- 动态参数 -->
        <el-form-item v-if="paramDefs.length" label="同步参数">
          <div style="width:100%">
            <el-row v-for="p in paramDefs" :key="p.key" :gutter="10" style="margin-bottom:8px">
              <el-col :span="8" class="param-label">{{ p.name }}<span v-if="p.hint" class="hint">{{ p.hint }}</span></el-col>
              <el-col :span="16">
                <el-select v-if="p.type==='select'" v-model="paramForm[p.key]" :placeholder="p.name">
                  <el-option v-for="o in (p.options||[])" :key="o[0]" :label="o[1]" :value="o[0]" />
                </el-select>
                <el-date-picker v-else-if="p.type==='date'" v-model="paramForm[p.key]" type="date"
                  value-format="YYYYMMDD" :placeholder="p.name" style="width:100%" />
                <el-input v-else v-model="paramForm[p.key]" :placeholder="p.name" />
              </el-col>
            </el-row>
          </div>
        </el-form-item>

        <el-form-item label="调用间隔(ms)" prop="interval_ms"><el-input-number v-model="form.interval_ms" :min="100" :max="60000" :step="100" /></el-form-item>
        <el-form-item label="超时(秒)" prop="timeout_seconds"><el-input-number v-model="form.timeout_seconds" :min="5" :max="300" /></el-form-item>
        <el-form-item label="重试次数" prop="retry_count"><el-input-number v-model="form.retry_count" :min="0" :max="5" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status"><el-radio :label="1">启用</el-radio><el-radio :label="0">禁用</el-radio></el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 调度配置对话框 -->
    <el-dialog v-model="scheduleDialog" title="调度配置" width="480px">
      <el-form :model="schedule" label-width="100px">
        <el-form-item label="调度类型">
          <el-radio-group v-model="schedule.schedule_type" @change="onScheduleTypeChange">
            <el-radio label="daily">每日</el-radio>
            <el-radio label="weekly">每周</el-radio>
            <el-radio label="cron">Cron</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="schedule.schedule_type !== 'cron'" label="执行时间">
          <el-time-picker v-model="schedule.execute_time" value-format="HH:mm" format="HH:mm" placeholder="如 18:00" />
        </el-form-item>
        <el-form-item v-if="schedule.schedule_type === 'weekly'" label="星期">
          <el-checkbox-group v-model="schedule.weekdaysArr">
            <el-checkbox v-for="(w,i) in ['周一','周二','周三','周四','周五','周六','周日']" :key="i" :label="i">{{ w }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="schedule.schedule_type === 'cron'" label="Cron表达式">
          <el-input v-model="schedule.cron_expr" placeholder="如 0 18 * * 1-5（分 时 日 月 周）" />
          <div class="hint">标准5段式：分 时 日 月 周（0=周日/周一取决于配置）</div>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="schedule.enabled" :active-value="1" :inactive-value="0" />
          <span v-if="schedule.next_run_at" class="hint" style="margin-left:12px">下次执行: {{ formatTime(schedule.next_run_at) }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scheduleDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSaveSchedule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 手动执行对话框 -->
    <el-dialog v-model="execDialog" title="手动执行同步" width="520px">
      <p style="margin-bottom:12px;color:#666">任务：<b>{{ currentTask?.name }}</b>（{{ currentTask?.interface_name }}）</p>
      <p style="margin-bottom:8px;color:#666">临时参数覆盖（可选，留空用任务默认参数）：</p>
      <el-row v-for="p in paramDefs" :key="p.key" :gutter="10" style="margin-bottom:8px">
        <el-col :span="8" class="param-label">{{ p.name }}</el-col>
        <el-col :span="16">
          <el-date-picker v-if="p.type==='date'" v-model="execParams[p.key]" type="date" value-format="YYYYMMDD" style="width:100%" />
          <el-input v-else v-model="execParams[p.key]" />
        </el-col>
      </el-row>
      <template #footer>
        <el-button @click="execDialog = false">取消</el-button>
        <el-button type="success" :loading="submitting" @click="confirmExecute">立即执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { getSyncTaskList, createSyncTask, updateSyncTask, deleteSyncTask, executeSyncTask, setSchedule, getSchedule } from '../api/syncTask'
import { getDataSourceList, getInterfaces, getInterfaceParams } from '../api/dataSource'

const router = useRouter()
const loading = ref(false); const submitting = ref(false); const executingId = ref(null)
const list = ref([]); const sourceOptions = ref([])
const sourceFilter = ref('')
const page = reactive({ page: 1, pageSize: 10, total: 0 })

const dialogVisible = ref(false); const dialogType = ref('create'); const formRef = ref(null); const currentId = ref(null)
const interfaceOptions = ref([]); const paramDefs = ref([])
const form = reactive({ name:'', source_id:null, data_interface:'', sync_mode:'full', target_table:'', interval_ms:500, timeout_seconds:30, retry_count:3, description:'', status:1 })
const paramForm = reactive({})
const rules = {
  name: [{ required:true, message:'请输入任务名称', trigger:'blur' }],
  source_id: [{ required:true, message:'请选择数据源', trigger:'change' }],
  data_interface: [{ required:true, message:'请选择数据接口', trigger:'change' }],
  target_table: [{ required:true, message:'请输入目标表', trigger:'blur' }]
}

// 调度
const scheduleDialog = ref(false)
const schedule = reactive({ schedule_type:'daily', execute_time:'18:00', weekdaysArr:[], cron_expr:'', enabled:0, next_run_at:null })

// 执行
const execDialog = ref(false); const currentTask = ref(null); const execParams = reactive({})

onMounted(async () => {
  await fetchSources()
  fetchList()
})

async function fetchSources() {
  const res = await getDataSourceList({ page:1, page_size:100, status:1 })
  sourceOptions.value = res.data.list.map(s => ({ id:s.id, name:s.name, source_type:s.source_type }))
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getSyncTaskList({ page:page.page, page_size:page.pageSize, source_id:sourceFilter.value || undefined })
    list.value = res.data.list; page.total = res.data.total
  } finally { loading.value = false }
}

function getSourceType(id) { return sourceOptions.value.find(s => s.id === id)?.source_type }

async function onSourceChange() {
  form.data_interface = ''; interfaceOptions.value = []; paramDefs.value = []
  const st = getSourceType(form.source_id); if (!st) return
  const res = await getInterfaces(st)
  interfaceOptions.value = res.data
}

async function onInterfaceChange(val) {
  form.target_table = interfaceOptions.value.find(i => i.value === val)?.target_table || ''
  Object.keys(paramForm).forEach(k => delete paramForm[k])
  const st = getSourceType(form.source_id); if (!st) return
  const res = await getInterfaceParams(st, val)
  paramDefs.value = res.data
  res.data.forEach(p => { paramForm[p.key] = p.default ?? '' })
}

function buildParams(obj) {
  return Object.entries(obj).filter(([,v]) => v !== '' && v != null).map(([k,v]) => ({ param_key:k, param_value:String(v) }))
}

function handleCreate() {
  dialogType.value = 'create'; currentId.value = null
  Object.assign(form, { name:'', source_id:null, data_interface:'', sync_mode:'full', target_table:'', interval_ms:500, timeout_seconds:30, retry_count:3, description:'', status:1 })
  interfaceOptions.value = []; paramDefs.value = []
  Object.keys(paramForm).forEach(k => delete paramForm[k])
  dialogVisible.value = true
}

async function handleEdit(row) {
  dialogType.value = 'edit'; currentId.value = row.id
  Object.assign(form, { name:row.name, source_id:row.source_id, data_interface:row.data_interface, sync_mode:row.sync_mode, target_table:row.target_table, interval_ms:row.interval_ms, timeout_seconds:row.timeout_seconds, retry_count:row.retry_count, description:row.description||'', status:row.status })
  // 加载接口选项和参数定义
  await onSourceChange()
  if (row.source_type) { /* source_type 来自列表 */ }
  const st = row.source_type || getSourceType(row.source_id)
  if (st) {
    const res = await getInterfaceParams(st, row.data_interface)
    paramDefs.value = res.data
    Object.keys(paramForm).forEach(k => delete paramForm[k])
    ;(row.params || []).forEach(p => { paramForm[p.param_key] = p.param_value || '' })
    res.data.forEach(p => { if (!(p.key in paramForm)) paramForm[p.key] = p.default ?? '' })
  }
  dialogVisible.value = true
}

function onDialogClosed() { paramDefs.value = []; Object.keys(paramForm).forEach(k => delete paramForm[k]) }

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const payload = { ...form, params: buildParams(paramForm) }
      if (dialogType.value === 'create') { await createSyncTask(payload); ElMessage.success('创建成功') }
      else { await updateSyncTask(currentId.value, payload); ElMessage.success('更新成功') }
      dialogVisible.value = false; fetchList()
    } finally { submitting.value = false }
  })
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定删除任务 "${row.name}" 吗？`, '提示', { type:'warning' })
    .then(async () => { await deleteSyncTask(row.id); ElMessage.success('删除成功'); fetchList() }).catch(() => {})
}

async function handleExecute(row) {
  currentTask.value = row
  Object.keys(execParams).forEach(k => delete execParams[k])
  const st = row.source_type || getSourceType(row.source_id)
  if (st) {
    try {
      const res = await getInterfaceParams(st, row.data_interface)
      res.data.forEach(p => { execParams[p.key] = '' })
    } catch {}
  }
  execDialog.value = true
}

async function confirmExecute() {
  submitting.value = true
  try {
    const override = {}
    Object.entries(execParams).filter(([,v]) => v !== '' && v != null).forEach(([k,v]) => { override[k] = String(v) })
    const res = await executeSyncTask(currentTask.value.id, { params: Object.keys(override).length ? override : null })
    ElMessage.success('同步已触发')
    execDialog.value = false
    ElMessageBox.confirm(`执行ID: ${res.data.execution_id}\n是否查看执行日志？`, '已触发', { confirmButtonText:'查看日志', cancelButtonText:'关闭' })
      .then(() => router.push('/sync-logs')).catch(() => {})
    fetchList()
  } finally { submitting.value = false }
}

async function handleSchedule(row) {
  currentId.value = row.id
  Object.assign(schedule, { schedule_type:'daily', execute_time:'18:00', weekdaysArr:[], cron_expr:'', enabled:0, next_run_at:null })
  try {
    const res = await getSchedule(row.id)
    if (res.data) {
      const d = res.data
      Object.assign(schedule, { schedule_type:d.schedule_type, execute_time:d.execute_time?.slice(0,5) || '18:00', weekdaysArr:d.weekdays ? d.weekdays.split(',').map(Number) : [], cron_expr:d.cron_expr || '', enabled:d.enabled, next_run_at:d.next_run_at })
    }
  } catch {}
  scheduleDialog.value = true
}

function onScheduleTypeChange() {}

async function handleSaveSchedule() {
  if ((schedule.schedule_type === 'daily' || schedule.schedule_type === 'weekly') && !schedule.execute_time) { ElMessage.warning('请设置执行时间'); return }
  if (schedule.schedule_type === 'weekly' && !schedule.weekdaysArr.length) { ElMessage.warning('请选择星期'); return }
  if (schedule.schedule_type === 'cron' && !schedule.cron_expr) { ElMessage.warning('请输入Cron表达式'); return }
  submitting.value = true
  try {
    const payload = { schedule_type:schedule.schedule_type, enabled:schedule.enabled }
    if (schedule.schedule_type !== 'cron') payload.execute_time = schedule.execute_time
    if (schedule.schedule_type === 'weekly') payload.weekdays = schedule.weekdaysArr.join(',')
    if (schedule.schedule_type === 'cron') payload.cron_expr = schedule.cron_expr
    await setSchedule(currentId.value, payload)
    ElMessage.success('调度已保存')
    scheduleDialog.value = false
  } finally { submitting.value = false }
}

function formatTime(t) { if (!t) return ''; return new Date(t).toLocaleString('zh-CN') }
</script>

<style scoped>
.page { background:#fff; padding:20px; border-radius:4px; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-header h2 { margin:0; font-size:20px; }
.filter-bar { display:flex; align-items:center; }
.pagination { margin-top:16px; display:flex; justify-content:flex-end; }
.param-label { line-height:32px; font-size:13px; }
.hint { color:#999; font-size:12px; margin-left:4px; display:block; }
</style>