import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/market' },
      {
        path: 'market',
        name: 'MarketQuote',
        component: () => import('../views/MarketQuote.vue'),
        meta: { title: '行情' }
      },
      {
        path: 'fundamental',
        name: 'Fundamental',
        component: () => import('../views/Fundamental.vue'),
        meta: { title: '基本面分析' }
      },
      {
        path: 'fund-flow',
        name: 'FundFlow',
        component: () => import('../views/FundFlow.vue'),
        meta: { title: '资金趋势分析' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.path === '/login' && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router