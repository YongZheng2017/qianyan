<template>
  <div class="quote-page">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-radio-group v-model="symbolType" size="small" @change="onTypeChange">
        <el-radio-button label="stock">股票</el-radio-button>
        <el-radio-button label="sector" disabled>板块</el-radio-button>
        <el-radio-button label="index" disabled>市场</el-radio-button>
      </el-radio-group>

      <el-autocomplete
        v-model="keyword"
        :fetch-suggestions="querySearch"
        placeholder="输入股票代码/名称/拼音"
        value-key="value"
        clearable
        style="width: 280px; margin-left: 12px"
        @select="handleSelect"
      >
        <template #default="{ item }">
          <div class="sug-item">
            <span class="sug-code">{{ item.code }}</span>
            <span class="sug-name">{{ item.name }}</span>
            <span class="sug-extra">{{ item.extra }}</span>
          </div>
        </template>
      </el-autocomplete>

      <el-radio-group v-model="period" size="small" style="margin-left: 12px" @change="loadQuote">
        <el-radio-button label="daily">日线</el-radio-button>
        <el-radio-button label="weekly">周线</el-radio-button>
        <el-radio-button label="monthly">月线</el-radio-button>
      </el-radio-group>

      <el-checkbox-group v-model="maFlags" size="small" style="margin-left: 16px" @change="renderChart">
        <el-checkbox-button label="ma5">MA5</el-checkbox-button>
        <el-checkbox-button label="ma10">MA10</el-checkbox-button>
        <el-checkbox-button label="ma20">MA20</el-checkbox-button>
      </el-checkbox-group>
    </div>

    <!-- 标的标题 -->
    <div class="symbol-title">
      <span class="name">{{ symbolName }}</span>
      <span class="code">{{ symbol }}</span>
      <span v-if="lastItem" class="price" :class="priceClass">
        {{ lastItem.close }}
        <span class="chg">{{ chgText }}</span>
      </span>
    </div>

    <!-- K线图 -->
    <div v-loading="loading" class="chart-wrap">
      <div ref="chartRef" class="chart"></div>
      <el-empty v-if="!loading && quoteData.length === 0" description="暂无行情数据，请先在管理端同步该标的的日线/周线/月线数据" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { searchSymbols, getQuotes } from '../api/quote'

const symbolType = ref('stock')
const keyword = ref('')
const symbol = ref('000001.SZ')
const symbolName = ref('平安银行')
const period = ref('daily')
const maFlags = ref(['ma5', 'ma10', 'ma20'])
const quoteData = ref([])
const loading = ref(false)

const chartRef = ref(null)
let chart = null

const lastItem = ref(null)
const priceClass = ref('')
const chgText = ref('')

// ---- 搜索 ----
async function querySearch(queryString, cb) {
  if (!queryString) { cb([]); return }
  try {
    const res = await searchSymbols(queryString, symbolType.value)
    cb((res.data || []).map(s => ({ ...s, value: `${s.name}(${s.code})` })))
  } catch {
    cb([])
  }
}

function handleSelect(item) {
  symbol.value = item.code
  symbolName.value = item.name
  loadQuote()
}

function onTypeChange() {
  // 当前仅支持股票；板块/市场禁用中
}

// ---- 加载行情 ----
async function loadQuote() {
  if (!symbol.value) return
  loading.value = true
  try {
    const res = await getQuotes({ symbol: symbol.value, type: symbolType.value, period: period.value, limit: 120 })
    const d = res.data
    symbolName.value = d.name
    quoteData.value = d.items || []
    updateLast()
    await nextTick()
    renderChart()
  } finally {
    loading.value = false
  }
}

function updateLast() {
  const items = quoteData.value
  if (!items.length) { lastItem.value = null; return }
  const last = items[items.length - 1]
  lastItem.value = last
  const up = (last.pct_chg ?? 0) >= 0
  priceClass.value = up ? 'up' : 'down'
  chgText.value = `${up ? '+' : ''}${last.pct_chg ?? '-'}%`
}

// ---- 均线计算 ----
function calcMA(closes, n) {
  const r = []
  for (let i = 0; i < closes.length; i++) {
    if (i < n - 1) { r.push('-'); continue }
    let s = 0
    for (let j = 0; j < n; j++) s += closes[i - j]
    r.push(+(s / n).toFixed(2))
  }
  return r
}

// ---- 渲染 K 线 ----
function renderChart() {
  if (!chart) return
  const items = quoteData.value
  if (!items.length) { chart.clear(); return }

  const dates = items.map(d => d.trade_date)
  const ohlc = items.map(d => [d.open, d.close, d.low, d.high])
  const vols = items.map(d => d.vol || 0)
  const closes = items.map(d => d.close)
  const volData = items.map(d => ({
    value: d.vol || 0,
    itemStyle: { color: d.close >= d.open ? '#ec0000' : '#00da3c' }
  }))

  const series = [
    {
      name: 'K线', type: 'candlestick', data: ohlc,
      itemStyle: { color: '#ec0000', color0: '#00da3c', borderColor: '#8a0000', borderColor0: '#008f28' }
    },
  ]
  if (maFlags.value.includes('ma5')) series.push({ name: 'MA5', type: 'line', data: calcMA(closes, 5), smooth: true, showSymbol: false, lineStyle: { width: 1 } })
  if (maFlags.value.includes('ma10')) series.push({ name: 'MA10', type: 'line', data: calcMA(closes, 10), smooth: true, showSymbol: false, lineStyle: { width: 1 } })
  if (maFlags.value.includes('ma20')) series.push({ name: 'MA20', type: 'line', data: calcMA(closes, 20), smooth: true, showSymbol: false, lineStyle: { width: 1 } })
  series.push({ name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volData })

  const option = {
    legend: { data: ['K线', 'MA5', 'MA10', 'MA20', '成交量'], top: 0 },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'cross' },
      valueFormatter: (v) => (v === '-' ? v : v)
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '8%', right: '4%', top: '8%', height: '58%' },
      { left: '8%', right: '4%', top: '74%', height: '16%' }
    ],
    xAxis: [
      { type: 'category', data: dates, scale: true, boundaryGap: false, splitLine: { show: false }, min: 'dataMin', max: 'dataMax' },
      { type: 'category', gridIndex: 1, data: dates, scale: true, boundaryGap: false, axisLabel: { show: false } }
    ],
    yAxis: [
      { scale: true, splitArea: { show: true } },
      { gridIndex: 1, splitNumber: 2, axisLabel: { show: true } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { show: true, type: 'slider', top: '92%', xAxisIndex: [0, 1], start: 50, end: 100 }
    ],
    series
  }
  chart.setOption(option, true)
}

function resize() { chart && chart.resize() }

onMounted(async () => {
  await nextTick()
  chart = echarts.init(chartRef.value)
  window.addEventListener('resize', resize)
  loadQuote()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
  chart = null
})
</script>

<style scoped>
.quote-page { background: #fff; padding: 16px; border-radius: 4px; height: 100%; box-sizing: border-box; display: flex; flex-direction: column; }
.toolbar { display: flex; align-items: center; flex-wrap: wrap; gap: 4px; }
.symbol-title { display: flex; align-items: baseline; gap: 12px; margin: 14px 0 8px; }
.symbol-title .name { font-size: 20px; font-weight: bold; }
.symbol-title .code { color: #909399; font-size: 14px; }
.symbol-title .price { font-size: 18px; font-weight: bold; }
.symbol-title .price.up { color: #ec0000; }
.symbol-title .price.down { color: #00da3c; }
.symbol-title .chg { font-size: 13px; margin-left: 4px; }
.chart-wrap { flex: 1; position: relative; min-height: 420px; }
.chart { width: 100%; height: 100%; min-height: 420px; }
.sug-item { display: flex; gap: 10px; }
.sug-code { color: #409eff; width: 90px; }
.sug-name { flex: 1; }
.sug-extra { color: #909399; font-size: 12px; }
.el-empty { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); }
</style>