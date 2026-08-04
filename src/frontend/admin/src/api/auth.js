import request from '../utils/request'

// 管理员登录
export function adminLogin(data) {
  return request({
    url: '/admin/auth/login',
    method: 'post',
    data
  })
}

// 管理员退出
export function adminLogout() {
  return request({
    url: '/admin/auth/logout',
    method: 'post'
  })
}