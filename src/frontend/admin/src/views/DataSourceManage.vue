<template>
  <div class="page">
    <div class="page-header">
      <h2>数据源管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon> 新增数据源
      </el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="searchText" placeholder="搜索名称/描述" style="width: 260px" @keyup.enter="fetchList">
        <template #append><el-button icon="Search" @click="fetchList" /></template>
      </el-input>
      <el-select v-model="typeFilter" placeholder="类型" clearable style="width: 140px; margin-left: 12px" @change="fetchList">
        <el-option label="Tushare" value="tushare" />
        <el-option label="AKShare" value="akshare" />
        <el-option label="自定义" value="custom" />
      </el-select>
    </div>

    <el-table v-loading="loading" :data="list" border style="margin-top: 16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="source_type" label="类型" width="100">
        <template #default="{ row }">{{ typeLabel(row.source_type) }}</template>
      </el-table-column>
      <el-table-column prop="api_url" label="API地址" min-width="200" show-overflow-tooltip />
      <el-table-column label="凭证" width="170">
        <template #default="{ row }">
          <span v-if="row.has_credentials">{{ firstMasked(row.credentials_masked) }}</span>
          <span v-else style="color:#999">未配置</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="最后测试" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.last_test_result === 1" type="success" size="small">成功</el-tag>
          <el-tag v-else-if="row.last_test_result === 0" type="danger" size="small">失败</el-tag>
          <span v-else style="color:#999">未测试</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :loading="testingId === row.id" @click="handleTest(row)">测试</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page.page" v-model:page-size="page.pageSize"
        :page-sizes="[10, 20, 50]" :total="page.total"
        layout="total, sizes, prev, pager, next" @size-change="fetchList" @current-change="fetchList"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogType === 'create' ? '新增数据源' : '编辑数据源'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="如：Tushare主数据源" />
        </el-form-item>
        <el-form-item label="类型" prop="source_type">
          <el-select v-model="form.source_type" style="width: 100%" :disabled="dialogType === 'edit'" @change="onTypeChange">
            <el-option label="Tushare" value="tushare" />
            <el-option label="AKShare" value="akshare" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="API地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="http://api.tushare.pro" />
        </el-form-item>

        <!-- 动态凭证表单（按数据源类型渲染） -->
        <el-form-item v-if="credSchema.length" label="凭证配置">
          <div style="width:100%">
            <el-row v-for="c in credSchema" :key="c.key" :gutter="10" style="margin-bottom:8px">
              <el-col :span="8" class="cred-label">
                {{ c.name }}<span v-if="c.required" style="color:#f56c6c">*</span>
                <span v-if="c.hint" class="hint">{{ c.hint }}</span>
              </el-col>
              <el-col :span="16">
                <el-input v-model="credForm[c.key]" type="password" show-password
                  :placeholder="dialogType === 'edit' ? '为空表示不修改' : `请输入${c.name}`" />
              </el-col>
            </el-row>
            <div v-if="dialogType === 'edit'" class="hint">凭证已加密存储，不回显；留空表示保持不变</div>
          </div>
        </el-form-item>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDataSourceList, createDataSource, updateDataSource, deleteDataSource, testDataSource,
  getCredentialsSchema
} from '../api/dataSource'

const TYPE_LABELS = { tushare: 'Tushare', akshare: 'AKShare', custom: '自定义' }
const typeLabel = (t) => TYPE_LABELS[t] || t
// 列表凭证列：取脱敏值的第一个字段展示
const firstMasked = (m) => { const v = Object.values(m || {})[0]; return v || '已配置' }

const loading = ref(false)
const submitting = ref(false)
const testingId = ref(null)
const list = ref([])
const searchText = ref('')
const typeFilter = ref('')
const page = reactive({ page: 1, pageSize: 10, total: 0 })

const dialogVisible = ref(false)
const dialogType = ref('create')
const formRef = ref(null)
const currentId = ref(null)
const form = reactive({ name: '', source_type: 'tushare', api_url: 'http://api.tushare.pro', description: '', status: 1 })
// 动态凭证
const credSchema = ref([])
const credForm = reactive({})
const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }, { min: 2, max: 50, message: '2-50字符', trigger: 'blur' }],
  source_type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  api_url: [{ required: true, message: '请输入API地址', trigger: 'blur' }]
}

onMounted(fetchList)

async function fetchList() {
  loading.value = true
  try {
    const res = await getDataSourceList({ page: page.page, page_size: page.pageSize, search: searchText.value || undefined, source_type: typeFilter.value || undefined })
    list.value = res.data.list
    page.total = res.data.total
  } finally { loading.value = false }
}

async function loadCredSchema(type) {
  // 清空旧凭证值
  Object.keys(credForm).forEach(k => delete credForm[k])
  if (!type) { credSchema.value = []; return }
  try {
    const res = await getCredentialsSchema(type)
    credSchema.value = res.data || []
    credSchema.value.forEach(c => { credForm[c.key] = '' })
  } catch {
    credSchema.value = []
  }
}

function onTypeChange() { loadCredSchema(form.source_type) }

function handleCreate() {
  dialogType.value = 'create'; currentId.value = null
  Object.assign(form, { name: '', source_type: 'tushare', api_url: 'http://api.tushare.pro', description: '', status: 1 })
  loadCredSchema('tushare')
  dialogVisible.value = true
}

function handleEdit(row) {
  dialogType.value = 'edit'; currentId.value = row.id
  Object.assign(form, { name: row.name, source_type: row.source_type, api_url: row.api_url, description: row.description || '', status: row.status })
  loadCredSchema(row.source_type)
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      // 收集非空凭证字段
      const cred = {}
      Object.entries(credForm).forEach(([k, v]) => { if (v) cred[k] = v })
      const payload = {
        name: form.name, source_type: form.source_type, api_url: form.api_url,
        description: form.description, status: form.status
      }
      if (Object.keys(cred).length) payload.credentials = cred

      if (dialogType.value === 'create') {
        await createDataSource(payload); ElMessage.success('创建成功')
      } else {
        await updateDataSource(currentId.value, payload); ElMessage.success('更新成功')
      }
      dialogVisible.value = false; fetchList()
    } finally { submitting.value = false }
  })
}

function handleDelete(row) {
  ElMessageBox.confirm(`确定删除数据源 "${row.name}" 吗？`, '提示', { type: 'warning' })
    .then(async () => { await deleteDataSource(row.id); ElMessage.success('删除成功'); fetchList() })
    .catch(() => {})
}

async function handleTest(row) {
  testingId.value = row.id
  try {
    const res = await testDataSource(row.id)
    const d = res.data
    if (d.success) ElMessage.success(`${d.message}（${d.response_time_ms}ms）`)
    else ElMessage.error(d.message)
    fetchList()
  } finally { testingId.value = null }
}
</script>

<style scoped>
.page { background: #fff; padding: 20px; border-radius: 4px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; }
.filter-bar { display: flex; align-items: center; }
.pagination { margin-top: 16px; display: flex; justify-content: flex-end; }
.cred-label { line-height: 32px; font-size: 13px; }
.hint { color: #999; font-size: 12px; display: block; }
</style>