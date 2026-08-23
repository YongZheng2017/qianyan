<template>
  <div class="page">
    <!-- 选股 -->
    <div class="toolbar">
      <el-autocomplete
        v-model="keyword"
        :fetch-suggestions="querySearch"
        clearable
        placeholder="输入股票代码/名称（如 000001 或 平安）"
        value-key="value"
        style="width: 300px"
        @select="handleSelect"
      >
        <template #default="{ item }">
          <span style="color:#409eff">{{ item.code }}</span>
          <span style="margin-left:8px">{{ item.name }}</span>
          <span style="color:#909399;margin-left:8px">{{ item.extra }}</span>
        </template>
      </el-autocomplete>
      <span class="title" v-if="stock.name">
        {{ stock.name }} <small>{{ stock.ts_code }}</small>
        <span v-if="stock.industry" class="ind">{{ stock.industry }}</span>
      </span>
    </div>

    <div v-if="!stock.ts_code" class="empty-hint">
      <el-empty description="请选择一只股票查看基本面分析" />
    </div>

    <el-tabs v-else v-model="activeTab" class="tabs" @tab-change="onTabChange">
      <!-- 概览 -->
      <el-tab-pane label="概览" name="overview">
        <div v-if="overview">
          <el-alert
            v-for="r in overview.risk_alerts" :key="r.message"
            :type="r.level === 'danger' ? 'error' : 'warning'"
            :title="r.message" show-icon :closable="false" style="margin-bottom:12px"
          />
          <el-row :gutter="12" class="cards">
            <el-col :span="3" v-for="c in overview.indicators" :key="c.key">
              <div class="card">
                <div class="card-name">{{ c.name }}</div>
                <div class="card-value">{{ fmtNum(c.value) }}</div>
              </div>
            </el-col>
          </el-row>
          <el-card v-if="overview.latest_statement" header="最新财报摘要" style="margin-top:16px">
            <el-descriptions :column="4" border>
              <el-descriptions-item label="报告期">{{ overview.latest_statement.end_date }}</el-descriptions-item>
              <el-descriptions-item label="营业总收入">{{ fmtBig(overview.latest_statement.total_revenue) }}</el-descriptions-item>
              <el-descriptions-item label="净利润">{{ fmtBig(overview.latest_statement.n_income) }}</el-descriptions-item>
              <el-descriptions-item label="归母净利润">{{ fmtBig(overview.latest_statement.n_income_attr_p) }}</el-descriptions-item>
              <el-descriptions-item label="营业利润">{{ fmtBig(overview.latest_statement.operate_profit) }}</el-descriptions-item>
              <el-descriptions-item label="经营现金流">{{ fmtBig(overview.latest_statement.n_cashflow_act) }}</el-descriptions-item>
              <el-descriptions-item label="总资产">{{ fmtBig(overview.latest_statement.total_assets) }}</el-descriptions-item>
              <el-descriptions-item label="总负债">{{ fmtBig(overview.latest_statement.total_liab) }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </div>
      </el-tab-pane>

      <!-- 三大报表 -->
      <el-tab-pane label="三大报表" name="statements">
        <div class="sub-bar">
          <el-radio-group v-model="stmtType" @change="loadStatements">
            <el-radio-button label="income">利润表</el-radio-button>
            <el-radio-button label="balancesheet">资产负债表</el-radio-button>
            <el-radio-button label="cashflow">现金流量表</el-radio-button>
          </el-radio-group>
          <span class="period-sel">报告期：
            <el-select v-model="stmtPeriods" size="small" style="width:90px" @change="loadStatements">
              <el-option :value="4" label="4期" /><el-option :value="8" label="8期" /><el-option :value="12" label="12期" />
            </el-select>
          </span>
        </div>
        <el-table :data="statementRows" border size="small" v-loading="stmtLoading">
          <el-table-column label="项目" prop="name" fixed width="180" />
          <el-table-column v-for="(h, i) in statementHeaders" :key="i" :label="h" align="right" min-width="120">
            <template #default="{ row }">{{ fmtBig(row.values[i]) }}</template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 能力分析 -->
      <el-tab-pane label="能力分析" name="ability">
        <div class="chart-row">
          <div ref="radarRef" class="radar"></div>
          <div class="ind-list">
            <div v-for="g in indicatorGroups" :key="g.key" class="ind-group">
              <div class="ind-group-title">{{ g.name }}</div>
              <div v-for="it in g.items" :key="it.key" class="ind-item">
                <span>{{ it.name }}</span>
                <b>{{ fmtNum(it.values[it.values.length - 1]) }}</b>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- 估值 -->
      <el-tab-pane label="估值分析" name="valuation">
        <div v-if="valuation">
          <el-row :gutter="12" class="cards" v-if="valuation.pe != null">
            <el-col :span="6"><div class="card"><div class="card-name">PE 市盈率</div><div class="card-value">{{ valuation.pe }}</div></div></el-col>
            <el-col :span="6"><div class="card"><div class="card-name">PB 市净率</div><div class="card-value">{{ valuation.pb }}</div></div></el-col>
            <el-col :span="6"><div class="card"><div class="card-name">PEG</div><div class="card-value">{{ valuation.peg ?? '-' }}</div></div></el-col>
            <el-col :span="6"><div class="card"><div class="card-name">最新股价</div><div class="card-value">{{ valuation.close }} <small>{{ valuation.trade_date }}</small></div></div></el-col>
          </el-row>
          <el-alert :title="valuation.conclusion || valuation.note" type="info" show-icon :closable="false" style="margin-top:16px" />
          <el-descriptions :column="3" border style="margin-top:16px" v-if="valuation.eps != null">
            <el-descriptions-item label="基本每股收益EPS">{{ valuation.eps }}</el-descriptions-item>
            <el-descriptions-item label="每股净资产BPS">{{ valuation.bps }}</el-descriptions-item>
            <el-descriptions-item label="净利润同比增长%">{{ fmtNum(valuation.netprofit_yoy) }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { searchSymbols } from '../api/quote'
import { getOverview, getStatements, getIndicators, getValuation } from '../api/fundamental'

const keyword = ref('')
const stock = reactive({ ts_code: '', name: '', industry: '' })
const activeTab = ref('overview')

const overview = ref(null)
const valuation = ref(null)
const stmtType = ref('income')
const stmtPeriods = ref(8)
const statementHeaders = ref([])
const statementRows = ref([])
const stmtLoading = ref(false)
const indicatorGroups = ref([])

const radarRef = ref(null)
let radarChart = null

// ---- 选股 ----
async function querySearch(qs, cb) {
  if (!qs) { cb([]); return }
  try {
    const res = await searchSymbols(qs)
    cb(res.data.map(s => ({ ...s, value: `${s.name}(${s.code})` })))
  } catch { cb([]) }
}
function handleSelect(item) {
  stock.ts_code = item.code; stock.name = item.name; stock.industry = item.extra || ''
  activeTab.value = 'overview'
  loadOverview()
}

// ---- 格式化 ----
function fmtBig(v) {
  if (v == null || v === '') return '-'
  const n = Number(v); if (isNaN(n)) return '-'
  const abs = Math.abs(n)
  if (abs >= 1e12) return (n / 1e12).toFixed(2) + '万亿'
  if (abs >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return (n / 1e4).toFixed(2) + '万'
  return n.toFixed(2)
}
function fmtNum(v) {
  if (v == null || v === '') return '-'
  return Number(v).toFixed(2)
}

// ---- 加载 ----
async function loadOverview() {
  overview.value = null
  const res = await getOverview(stock.ts_code)
  overview.value = res.data
  if (overview.value) { stock.name = overview.value.stock.name; stock.industry = overview.value.stock.industry || '' }
}

async function loadStatements() {
  stmtLoading.value = true
  try {
    const res = await getStatements(stock.ts_code, stmtType.value, stmtPeriods.value)
    statementHeaders.value = res.data.headers
    statementRows.value = res.data.rows
  } finally { stmtLoading.value = false }
}

async function loadIndicators() {
  const res = await getIndicators(stock.ts_code, 12)
  indicatorGroups.value = res.data.groups
  await nextTick()
  renderRadar()
}

async function loadValuation() {
  const res = await getValuation(stock.ts_code)
  valuation.value = res.data
}

// ---- 雷达图 ----
function renderRadar() {
  if (!radarRef.value) return
  if (!radarChart) radarChart = echarts.init(radarRef.value)
  const latest = (gkey, ikey) => {
    const g = indicatorGroups.value.find(x => x.key === gkey)
    if (!g) return 0
    const it = g.items.find(x => x.key === ikey)
    return (it && it.values[it.values.length - 1] != null) ? Number(it.values[it.values.length - 1]) : 0
  }
  radarChart.setOption({
    title: { text: '四大能力（最新期）', left: 'center' },
    tooltip: {},
    radar: {
      indicator: [
        { name: '盈利(ROE)', max: 30 },
        { name: '成长(营收增长%)', max: 50 },
        { name: '营运(应收周转率)', max: 30 },
        { name: '偿债(流动比率)', max: 3 },
      ]
    },
    series: [{
      type: 'radar', areaStyle: { opacity: 0.2 },
      data: [{ value: [latest('profitability', 'roe'), latest('growth', 'or_yoy'), latest('operation', 'ar_turn'), latest('solvency', 'current_ratio')], name: stock.name }]
    }]
  }, true)
}

function onTabChange(tab) {
  if (tab === 'statements' && !statementRows.value.length) loadStatements()
  if (tab === 'ability' && !indicatorGroups.value.length) loadIndicators()
  if (tab === 'valuation' && !valuation.value) loadValuation()
}

function resize() { radarChart && radarChart.resize() }
onMounted(() => window.addEventListener('resize', resize))
onBeforeUnmount(() => { window.removeEventListener('resize', resize); radarChart && radarChart.dispose() })
</script>

<style scoped>
.page { background: #fff; padding: 16px; border-radius: 4px; height: 100%; box-sizing: border-box; overflow: auto; }
.toolbar { display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }
.title { font-size: 18px; font-weight: 600; }
.title small { color: #909399; font-weight: normal; font-size: 13px; }
.title .ind { color: #409eff; font-size: 13px; margin-left: 8px; }
.empty-hint { display: flex; justify-content: center; padding: 60px 0; }
.tabs { margin-top: 8px; }
.cards { margin-bottom: 12px; }
.card { background: #f5f7fa; border-radius: 4px; padding: 12px; text-align: center; }
.card-name { color: #909399; font-size: 12px; }
.card-value { font-size: 20px; font-weight: 600; color: #303133; margin-top: 4px; }
.sub-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.period-sel { color: #606266; }
.chart-row { display: flex; gap: 16px; }
.radar { flex: 1; min-height: 360px; }
.ind-list { flex: 1; }
.ind-group { margin-bottom: 16px; }
.ind-group-title { font-weight: 600; color: #409eff; border-left: 3px solid #409eff; padding-left: 8px; margin-bottom: 8px; }
.ind-item { display: flex; justify-content: space-between; padding: 4px 8px; border-bottom: 1px dashed #ebeef5; }
.ind-item b { color: #303133; }
</style>