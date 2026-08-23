import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'
import router from '../router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data

    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }

    return res
  },
  (error) => {
    if (error.response) {
      const status = error.response.status
      const data = error.response.data
      // 兼容两种错误格式：FastAPI HTTPException 用 detail，业务 Response 用 message
      const msg = data?.detail || data?.message

      if (status === 401) {
        const userStore = useUserStore()
        userStore.logout()
        // 静默跳转登录页（401 通常是 token 失效，跳登录即可，不弹刺眼错误）
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      } else {
        ElMessage.error(msg || `请求失败（${status}）`)
      }
    } else {
      ElMessage.error('网络错误，请稍后重试')
    }

    return Promise.reject(error)
  }
)

export default request