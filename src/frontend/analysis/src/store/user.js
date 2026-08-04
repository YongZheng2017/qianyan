import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('user_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user_info') || 'null'))
  const menus = ref(JSON.parse(localStorage.getItem('user_menus') || '[]'))
  const permissions = ref(JSON.parse(localStorage.getItem('user_permissions') || '[]'))

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('user_token', newToken)
  }

  const setUserInfo = (info) => {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
  }

  const setMenus = (menuList) => {
    menus.value = menuList
    localStorage.setItem('user_menus', JSON.stringify(menuList))
  }

  const setPermissions = (perms) => {
    permissions.value = perms
    localStorage.setItem('user_permissions', JSON.stringify(perms))
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    menus.value = []
    permissions.value = []
    localStorage.removeItem('user_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('user_menus')
    localStorage.removeItem('user_permissions')
    localStorage.removeItem('saved_user')
  }

  const hasPermission = (permission) => {
    return permissions.value.includes(permission)
  }

  return {
    token,
    userInfo,
    menus,
    permissions,
    setToken,
    setUserInfo,
    setMenus,
    setPermissions,
    logout,
    hasPermission
  }
})