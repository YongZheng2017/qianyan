<template>
  <div class="dashboard">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="sidebarWidth" class="sidebar">
        <div class="logo">
          <span v-if="!collapsed">股票分析系统</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          :collapse="collapsed"
          router
          class="menu"
        >
          <el-menu-item
            v-for="menu in userStore.menus"
            :key="menu.id"
            :index="menu.path"
          >
            <el-icon>
              <component :is="getIcon(menu.icon)" />
            </el-icon>
            <template #title>{{ menu.title }}</template>
          </el-menu-item>
        </el-menu>

        <div class="collapse-btn" @click="toggleCollapse">
          <el-icon>
            <component :is="collapsed ? Expand : Fold" />
          </el-icon>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentMenu">
                {{ currentMenu.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32" :icon="UserFilled" />
                <span class="username">
                  {{ userStore.userInfo?.real_name || userStore.userInfo?.username }}
                </span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item disabled>
                    {{ userStore.userInfo?.real_name || userStore.userInfo?.username }}
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 内容区 -->
        <el-main class="main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  UserFilled, ArrowDown, SwitchButton,
  TrendCharts, DataLine, Money, Document,
  Expand, Fold
} from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import { getUserMenus } from '../api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)
const sidebarWidth = computed(() => collapsed.value ? '64px' : '200px')

const activeMenu = computed(() => route.path)
const currentMenu = computed(() => {
  return userStore.menus.find(m => m.path === route.path)
})

// 菜单图标映射（返回已导入的组件，而非字符串名）
const ICON_MAP = {
  stock: TrendCharts,
  chart: DataLine,
  trend: TrendCharts,
  fund: Money,
  document: Document
}
const getIcon = (iconName) => ICON_MAP[iconName] || Document

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

const handleCommand = async (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    }).catch(() => {
      // 取消退出
    })
  }
}

onMounted(async () => {
  // 未登录跳转登录页
  if (!userStore.token) {
    router.push('/login')
    return
  }
  // 每次进入刷新菜单（覆盖 localStorage 旧缓存，避免菜单变更后路由不匹配）
  try {
    const res = await getUserMenus()
    if (res.data && res.data.length > 0) {
      userStore.setMenus(res.data)
    }
  } catch {
    // 静默失败，继续使用本地缓存的菜单
  }
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: #bfcbd9;
  position: relative;
  transition: width 0.3s;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border-bottom: 1px solid #3a4a5d;
  font-weight: bold;
  font-size: 16px;
}

.menu {
  border: none;
  background-color: #304156;
}

.menu .el-menu-item {
  color: #bfcbd9;
}

.menu .el-menu-item:hover,
.menu .el-menu-item.is-active {
  background-color: #263445;
  color: #409eff;
}

.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  color: #bfcbd9;
  font-size: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #333;
}

.username {
  font-size: 14px;
}

.main {
  background-color: #f0f2f5;
}

/* 让所有 el-container 撑满父级高度，避免下半部分露灰 */
.dashboard :deep(.el-container) {
  height: 100%;
}

/* 内容区撑满剩余高度，超出可滚动 */
.dashboard :deep(.el-main) {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

/* 页面卡片撑满内容区高度 */
.dashboard :deep(.el-main > *) {
  min-height: 100%;
  box-sizing: border-box;
}

/* 欢迎页面 */
.welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 120px);
}

.welcome-content {
  text-align: center;
}

.welcome-content h1 {
  color: #409eff;
  margin-bottom: 20px;
}

.welcome-content p {
  color: #999;
  margin-bottom: 30px;
}
</style>