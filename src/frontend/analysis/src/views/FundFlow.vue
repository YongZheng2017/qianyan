<template>
  <div class="page">
    <el-tabs v-model="activeTab" @tab-change="onTabChange">
      <!-- Tab1: 个股资金 -->
      <el-tab-pane label="个股资金" name="stock">
        <div class="toolbar">
          <el-autocomplete
            v-model="keyword" :fetch-suggestions="querySearch" clearable
            placeholder="输入股票代码/名称" value-key="value" style="width:280px" @select="onSelect"
          >
            <template #default="{ item }">
              <span style="color:#409eff">{{ item.code }}</span>
              <span style="margin-left:8px">{{ item.name }}</span>
            </template>
          </el-autocomplete>
          <span v-if="stockFlow" class="title">
            {{ stockFlow.name }} <small>{{ stockFlow.ts_code }}</small>
            <span v-if="stockFlow.latest" :class="netClass(stockFlow.latest.net_mf_amount)">
              最新净流入 {{ fmtYi(stockFlow.latest.net_mf_amount) }}
            </span>
          </span>
        </div>
        <div v-if="stockFlow && stockFlow.items.length" ref="stockChartRef" class="chart"></div>
        <el-empty v-else-if="!stockLoading" description="暂无资金流向数据，请先在管理端同步「个股资金流向」" />
      </el-tab-pane>

      <!-- Tab2: 市场总览 -->
      <el-tab-pane label="市场总览" name="market">
        <div v-if="marketFlow && marketFlow.items.length" ref="marketChartRef" class="chart"></div>
        <el-empty v-else-if="!marketLoading" description="暂无市场资金数据，请同步某交易日的资金流向（trade_date）" />
      </el-tab-pane>

      <!-- Tab3: 排行榜 -->
      <el-tab-pane label="净流入排行" name="rank">
        <template v-if="rank && rank.inflow.length">
          <div class="rank-head">交易日：{{ rank.trade_date }}</div>
          <el-row :gutter="16">
            <el-col :span="12">
              <h4 style="color:#ec0000">净流入 TOP10（万元）</h4>
              <el-table :data="rank.inflow" size="small" border>
                <el-table-column type="index" width="40" />
                <el-table-column prop="ts_code" label="代码" width="100" />
                <el-table-column prop="name" label="名称" width="90" />
                <el-table-column prop="industry" label="行业" width="90" show-overflow-tooltip />
                <el-table-column prop="net_mf_amount" label="净流入" align="right">
                  <template #default="{ row }"><span class="up">{{ fmtWan(row.net_mf_amount) }}</span></template>
                </el-table-column>
                <el-table-column prop="pct_chg" label="涨跌%" align="right" width="70">
                  <template #default="{ row }"><span :class="row.pct_chg >= 0 ? 'up' : 'down'">{{ row.pct_chg ?? '-' }}</span></template>
                </el-table-column>
              </el-table>
            </el-col>
            <el-col :span="12">
              <h4 style="color:#00a854">净流出 TOP10（万元）</h4>
              <el-table :data="rank.outflow" size="small" border>
                <el-table-column type="index" width="40" />
                <el-table-column prop="ts_code" label="代码" width="100" />
                <el-table-column prop="name" label="名称" width="90" />
                <el-table-column prop="industry" label="行业" width="90" show-overflow-tooltip />
                <el-table-column prop="net_mf_amount" label="净流出" align="right">
                  <template #default="{ row }"><span class="down">{{ fmtWan(row.net_mf_amount) }}</span></template>
                </el-table-column>
                <el-table-column prop="pct_chg" label="涨跌%" align="right" width="70">
                  <template #default="{ row }"><span :class="row.pct_chg >= 0 ? 'up' : 'down'">{{ row.pct_chg ?? '-' }}</span></template>
                </el-table-column>
              </el-table>
            </el-col>
          </el-row>
        </template>
        <el-empty v-else-if="!rankLoading" description="暂无排行数据，请同步资金流向后查看" />
      </el-tab-pane>

      <!-- Tab4: 宏观指标 -->
      <el-tab-pane label="宏观指标" name="macro">
        <div class="toolbar">
          <el-select v-model="macroIndicator" style="width:220px" @change="onMacroChange">
            <el-option v-for="m in macroList" :key="m.key" :label="m.name" :value="m.key" />
          </el-select>
          <el-select v-model="macroField" style="width:140px" @change="loadMacroSeries">
            <el-option v-for="f in macroFields" :key="f" :label="f" :value="f" />
          </el-select>
        </div>
        <div v-if="macroSeries && macroSeries.dates.length" ref="macroChartRef" class="chart"></div>
        <el-empty v-else-if="!macroLoading" description="该指标暂无数据，请先在管理端同步对应宏观数据" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { searchSymbols } from '../api/quote'
import { getStockFlow, getMarketFlow, getFlowRank, getMacroIndicators, getMacroSeries } from '../api/fundflow'

const activeTab = ref('stock')
const keyword = ref('')

// 个股
const stockFlow = ref(null)
const stockLoading = ref(false)
const stockChartRef = ref(null)
let stockChart = null
// 市场
const marketFlow = ref(null)
const marketLoading = ref(false)
const marketChartRef = ref(null)
let marketChart = null
// 排行
const rank = ref(null)
const rankLoading = ref(false)
// 宏观
const macroList = ref([])
const macroIndicator = ref('shibor')
const macroField = ref('y1')
const macroFields = ref([])
const macroSeries = ref(null)
const macroLoading = ref(false)
const macroChartRef = ref(null)
let macroChart = null

// ---- 选股 ----
async function querySearch(qs, cb) {
  if (!qs) { cb([]); return }
  try {
    const res = await searchSymbols(qs)
    cb(res.data.map(s => ({ ...s, value: `${s.name}(${s.code})` })))
  } catch { cb([]) }
}
function onSelect(item) {
  loadStockFlow(item.code)
}

// ---- 格式化 ----
const fmtYi = v => v == null ? '-' : (v / 10000).toFixed(2) + '亿'
const fmtWan = v => v == null ? '-' : Number(v).toFixed(0)
const netClass = v => v >= 0 ? 'up' : 'down'

// ---- Tab1: 个股资金图（净流入柱状 + 收盘价折线 双轴）----
async function loadStockFlow(code) {
  stockLoading.value = true
  try {
    const res = await getStockFlow(code, 60)
    stockFlow.value = res.data
    await nextTick()
    renderStockChart()
  } finally { stockLoading.value = false }
}
function renderStockChart() {
  if (!stockChartRef.value) return
  if (!stockChart) stockChart = echarts.init(stockChartRef.value)
  const items = stockFlow.value.items
  stockChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    legend: { data: ['净流入(万元)', '收盘价'] },
    grid: { left: '8%', right: '6%', top: '10%', bottom: '12%' },
    xAxis: { type: 'category', data: items.map(d => d.trade_date) },
    yAxis: [
      { type: 'value', name: '净流入(万)' },
      { type: 'value', name: '收盘价', scale: true },
    ],
    dataZoom: [{ type: 'inside' }, { show: true, type: 'slider', top: '90%' }],
    series: [
      {
        name: '净流入(万元)', type: 'bar',
        data: items.map(d => ({
          value: d.net_mf_amount,
          itemStyle: { color: d.net_mf_amount >= 0 ? '#ec0000' : '#00a854' },
        })),
      },
      { name: '收盘价', type: 'line', yAxisIndex: 1, data: items.map(d => d.close), smooth: true, showSymbol: false },
    ],
  }, true)
}

// ---- Tab2: 市场总览 ----
async function loadMarket() {
  marketLoading.value = true
  try {
    const res = await getMarketFlow(30)
    marketFlow.value = res.data
    await nextTick()
    if (marketFlow.value.items.length) {
      if (!marketChart) marketChart = echarts.init(marketChartRef.value)
      const items = marketFlow.value.items
      marketChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['全市场净流入(亿元)', '净流入上涨家数', '净流出家数'] },
        grid: { left: '8%', right: '6%', top: '10%', bottom: '12%' },
        xAxis: { type: 'category', data: items.map(d => d.trade_date) },
        yAxis: [{ type: 'value', name: '亿元' }, { type: 'value', name: '家数' }],
        dataZoom: [{ type: 'inside' }],
        series: [
          {
            name: '全市场净流入(亿元)', type: 'bar',
            data: items.map(d => ({ value: +(d.net_mf_amount / 10000).toFixed(2), itemStyle: { color: d.net_mf_amount >= 0 ? '#ec0000' : '#00a854' } })),
          },
          { name: '净流入上涨家数', type: 'line', yAxisIndex: 1, data: items.map(d => d.up_count), smooth: true },
          { name: '净流出家数', type: 'line', yAxisIndex: 1, data: items.map(d => d.down_count), smooth: true },
        ],
      }, true)
    }
  } finally { marketLoading.value = false }
}

// ---- Tab3: 排行 ----
async function loadRank() {
  rankLoading.value = true
  try { rank.value = (await getFlowRank(10)).data } finally { rankLoading.value = false }
}

// ---- Tab4: 宏观 ----
async function loadMacroList() {
  macroList.value = (await getMacroIndicators()).data
  onMacroChange()
}
function onMacroChange() {
  const cfg = macroList.value.find(m => m.key === macroIndicator.value)
  macroFields.value = cfg ? cfg.fields : []
  macroField.value = macroFields.value[0] || ''
  loadMacroSeries()
}
async function loadMacroSeries() {
  if (!macroIndicator.value || !macroField.value) return
  macroLoading.value = true
  try {
    macroSeries.value = (await getMacroSeries(macroIndicator.value, macroField.value, 120)).data
    await nextTick()
    if (macroSeries.value.dates.length) {
      if (!macroChart) macroChart = echarts.init(macroChartRef.value)
      macroChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: '8%', right: '5%', top: '10%', bottom: '12%' },
        xAxis: { type: 'category', data: macroSeries.value.dates },
        yAxis: { type: 'value', scale: true },
        dataZoom: [{ type: 'inside' }, { show: true, type: 'slider', top: '90%' }],
        series: [{
          name: `${macroIndicator.value}.${macroField.value}`, type: 'line',
          data: macroSeries.value.values, smooth: true, showSymbol: false,
          lineStyle: { color: '#409eff' }, areaStyle: { opacity: 0.1 },
        }],
      }, true)
    }
  } finally { macroLoading.value = false }
}

function onTabChange(tab) {
  if (tab === 'market' && !marketFlow.value) loadMarket()
  if (tab === 'rank' && !rank.value) loadRank()
  if (tab === 'macro' && !macroList.value.length) loadMacroList()
}

function resize() { stockChart?.resize(); marketChart?.resize(); macroChart?.resize() }
onMounted(() => window.addEventListener('resize', resize))
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  stockChart?.dispose(); marketChart?.dispose(); macroChart?.dispose()
})
</script>

<style scoped>
.page { background:#fff; padding:16px; border-radius:4px; height:100%; box-sizing:border-box; overflow:auto; }
.toolbar { display:flex; align-items:center; gap:16px; margin-bottom:12px; flex-wrap:wrap; }
.title { font-size:16px; font-weight:600; }
.title small { color:#909399; font-weight:normal; font-size:12px; }
.chart { width:100%; height:440px; }
.rank-head { color:#606266; margin-bottom:8px; }
.up { color:#ec0000; }
.down { color:#00a854; }
</style>