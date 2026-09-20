import request from '../utils/request'

// 个股资金流向
export function getStockFlow(ts_code, limit = 60) {
  return request({ url: '/analysis/fund-flow/stock', method: 'get', params: { ts_code, limit } })
}

// 市场资金总览
export function getMarketFlow(limit = 30) {
  return request({ url: '/analysis/fund-flow/market', method: 'get', params: { limit } })
}

// 净流入/流出排行
export function getFlowRank(top = 10) {
  return request({ url: '/analysis/fund-flow/rank', method: 'get', params: { top } })
}

// 宏观指标列表
export function getMacroIndicators() {
  return request({ url: '/analysis/fund-flow/macro/indicators', method: 'get' })
}

// 宏观指标时序
export function getMacroSeries(indicator, field, limit = 120) {
  return request({ url: '/analysis/fund-flow/macro/series', method: 'get', params: { indicator, field, limit } })
}