import request from '../utils/request'

// 获取支持的数据源类型
export function getSourceTypes() {
  return request({ url: '/admin/data-sources/types', method: 'get' })
}

// 获取指定数据源类型支持的接口列表
export function getInterfaces(sourceType) {
  return request({ url: `/admin/data-sources/types/${sourceType}/interfaces`, method: 'get' })
}

// 获取数据源类型的凭证字段定义（前端据此动态渲染配置表单）
export function getCredentialsSchema(sourceType) {
  return request({ url: `/admin/data-sources/types/${sourceType}/credentials-schema`, method: 'get' })
}

// 获取接口的参数定义
export function getInterfaceParams(sourceType, interfaceName) {
  return request({ url: `/admin/data-sources/types/${sourceType}/interfaces/${interfaceName}/params`, method: 'get' })
}

// 数据源列表
export function getDataSourceList(params) {
  return request({ url: '/admin/data-sources', method: 'get', params })
}

// 创建数据源
export function createDataSource(data) {
  return request({ url: '/admin/data-sources', method: 'post', data })
}

// 数据源详情
export function getDataSource(id) {
  return request({ url: `/admin/data-sources/${id}`, method: 'get' })
}

// 更新数据源
export function updateDataSource(id, data) {
  return request({ url: `/admin/data-sources/${id}`, method: 'put', data })
}

// 删除数据源
export function deleteDataSource(id) {
  return request({ url: `/admin/data-sources/${id}`, method: 'delete' })
}

// 测试数据源连接
export function testDataSource(id) {
  return request({ url: `/admin/data-sources/${id}/test`, method: 'post' })
}