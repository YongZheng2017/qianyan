import request from '../utils/request'

// 基本面概览
export function getOverview(ts_code) {
  return request({ url: '/analysis/fundamental/overview', method: 'get', params: { ts_code } })
}

// 三大报表
export function getStatements(ts_code, type = 'income', periods = 8) {
  return request({ url: '/analysis/fundamental/statements', method: 'get', params: { ts_code, type, periods } })
}

// 能力指标
export function getIndicators(ts_code, periods = 12) {
  return request({ url: '/analysis/fundamental/indicators', method: 'get', params: { ts_code, periods } })
}

// 估值
export function getValuation(ts_code) {
  return request({ url: '/analysis/fundamental/valuation', method: 'get', params: { ts_code } })
}