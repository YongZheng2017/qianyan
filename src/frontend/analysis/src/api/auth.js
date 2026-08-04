import request from '../utils/request'

// 用户登录
export function userLogin(data) {
  return request({
    url: '/user/auth/login',
    method: 'post',
    data
  })
}

// 用户退出
export function userLogout() {
  return request({
    url: '/user/auth/logout',
    method: 'post'
  })
}

// 获取用户菜单
export function getUserMenus() {
  return request({
    url: '/user/menus',
    method: 'get'
  })
}