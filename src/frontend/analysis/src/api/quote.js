import request from '../utils/request'

// 搜索标的
export function searchSymbols(q, type = 'stock') {
  return request({ url: '/analysis/symbols/search', method: 'get', params: { q, type } })
}

// 查询行情（K线）
export function getQuotes(params) {
  return request({ url: '/analysis/quotes', method: 'get', params })
}