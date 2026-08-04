import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))
  const permissions = ref(JSON.parse(localStorage.getItem('admin_permissions') || '[]'))

  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('admin_token', newToken)
  }

  const setUserInfo = (info) => {
    userInfo.value = info
    localStorage.setItem('admin_user', JSON.stringify(info))
  }

  const setPermissions = (perms) => {
    permissions.value = perms
    localStorage.setItem('admin_permissions', JSON.stringify(perms))
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    localStorage.removeItem('admin_permissions')
  }

  const hasPermission = (permission) => {
    return permissions.value.includes(permission)
  }

  return {
    token,
    userInfo,
    permissions,
    setToken,
    setUserInfo,
    setPermissions,
    logout,
    hasPermission
  }
})