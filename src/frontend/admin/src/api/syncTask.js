import request from '../utils/request'

// 同步任务列表
export function getSyncTaskList(params) {
  return request({ url: '/admin/sync-tasks', method: 'get', params })
}

// 创建同步任务
export function createSyncTask(data) {
  return request({ url: '/admin/sync-tasks', method: 'post', data })
}

// 同步任务详情
export function getSyncTask(id) {
  return request({ url: `/admin/sync-tasks/${id}`, method: 'get' })
}

// 更新同步任务
export function updateSyncTask(id, data) {
  return request({ url: `/admin/sync-tasks/${id}`, method: 'put', data })
}

// 删除同步任务
export function deleteSyncTask(id) {
  return request({ url: `/admin/sync-tasks/${id}`, method: 'delete' })
}

// 手动触发同步
export function executeSyncTask(id, params = {}) {
  return request({ url: `/admin/sync-tasks/${id}/execute`, method: 'post', data: params })
}

// 设置/更新调度配置
export function setSchedule(id, data) {
  return request({ url: `/admin/sync-tasks/${id}/schedule`, method: 'post', data })
}

// 启用/停用调度
export function toggleSchedule(id, enabled) {
  return request({ url: `/admin/sync-tasks/${id}/schedule/toggle`, method: 'put', params: { enabled } })
}

// 查询调度配置
export function getSchedule(id) {
  return request({ url: `/admin/sync-tasks/${id}/schedule`, method: 'get' })
}