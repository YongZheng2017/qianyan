import request from '../utils/request'

// 同步日志列表
export function getSyncLogList(params) {
  return request({ url: '/admin/sync-logs', method: 'get', params })
}

// 同步执行详情（含调用明细）
export function getSyncLogDetail(executionId) {
  return request({ url: `/admin/sync-logs/${executionId}`, method: 'get' })
}

// 实时执行进度
export function getSyncProgress(executionId) {
  return request({ url: `/admin/sync-logs/${executionId}/progress`, method: 'get' })
}

// 同步统计
export function getSyncStats(date) {
  return request({ url: '/admin/sync-logs/stats', method: 'get', params: { date } })
}

// 清理历史日志
export function cleanSyncLogs(beforeDate) {
  return request({ url: '/admin/sync-logs', method: 'delete', params: { before_date: beforeDate } })
}

// 删除单条日志
export function deleteSyncLog(executionId) {
  return request({ url: `/admin/sync-logs/${executionId}`, method: 'delete' })
}