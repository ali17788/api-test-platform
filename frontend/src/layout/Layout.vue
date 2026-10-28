<template>
  <div class="layout">
    <!-- 顶部导航栏 -->
    <header class="topbar">
      <div class="topbar-left">
        <div class="logo-box">
          <el-icon :size="20" color="#fff"><Cpu /></el-icon>
        </div>
        <span class="product-name">AI接口自动化测试平台</span>
        <span class="proj-chip" v-if="currentProject">
          当前项目：{{ currentProject.name }}
        </span>
      </div>
      <div class="topbar-right">
        <el-icon :size="16" style="margin-right:6px"><User /></el-icon>
        <span class="username">{{ username }}</span>
        <el-tag v-if="roleName" size="small" effect="light" type="primary" style="margin-left:8px">{{ roleName }}</el-tag>
        <el-button link type="primary" style="margin-left:16px" @click="onLogout">
          <el-icon><SwitchButton /></el-icon>退出登录
        </el-button>
      </div>
    </header>

    <div class="body">
      <!-- 左侧侧边栏（动态：依据当前用户菜单权限渲染） -->
      <aside class="sidebar">
        <div class="menu-title">功能菜单</div>
        <router-link v-for="m in visibleMenus" :key="m.path" :to="m.path" class="menu-item"
                     :class="{ active: isActive(m.path) }">
          <el-icon :size="16"><component :is="m.icon" /></el-icon>
          <span>{{ m.title }}</span>
        </router-link>
      </aside>

      <!-- 右侧主内容区 -->
      <main class="main">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const username = ref(localStorage.getItem('username') || 'admin')
const roleName = ref(localStorage.getItem('roleName') || '')
const currentProject = ref(null)

// 菜单目录（来自后端） + 当前用户允许访问的菜单 key
const menuCatalog = ref([])
const allowedKeys = ref([])

async function loadMenus() {
  try {
    // 优先使用登录时缓存的权限，避免首次渲染闪烁
    const cached = localStorage.getItem('menus')
    if (cached) allowedKeys.value = JSON.parse(cached)
  } catch (e) { /* ignore */ }
  // 两个请求相互独立，单个失败不影响另一个；用 safeApi 包裹避免 Promise.all 整体 reject
  const catalog = await safeApi(() => api.listMenus())
  if (catalog && catalog.length) menuCatalog.value = catalog
  const me = await safeApi(() => api.me())
  if (me) {
    if (Array.isArray(me.menus) && me.menus.length) {
      allowedKeys.value = me.menus
    } else if (me.menus == null) {
      // 后端未返回菜单权限（旧版/未启用 RBAC）：优雅降级展示全部菜单，保证平台可用
      allowedKeys.value = (menuCatalog.value || []).map((m) => m.key)
    }
    localStorage.setItem('menus', JSON.stringify(allowedKeys.value))
    localStorage.setItem('roleName', me.role_name || '')
    roleName.value = me.role_name || ''
  } else if (menuCatalog.value.length) {
    // 拿不到当前用户权限，但有菜单目录：降级展示全部
    allowedKeys.value = menuCatalog.value.map((m) => m.key)
  }
}

async function safeApi(fn) {
  try { return await fn() } catch (e) { return null }
}

const visibleMenus = computed(() =>
  (menuCatalog.value || []).filter((m) => (allowedKeys.value || []).includes(m.key))
)

const isActive = (p) => route.path === p || (p === '/reports' && route.path.startsWith('/reports'))

async function loadProject() {
  const pid = localStorage.getItem('currentProjectId')
  if (!pid) { currentProject.value = null; return }
  try {
    const res = await api.listProjects()
    currentProject.value = (res || []).find((p) => p.id === Number(pid)) || null
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  loadMenus()
  loadProject()
  window.addEventListener('project-changed', loadProject)
})

async function onLogout() {
  await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
  try { await api.logout() } catch (e) { /* ignore */ }
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
  ElMessage.success('已退出登录')
}
</script>

<style scoped>
.layout { height: 100%; display: flex; flex-direction: column; }

.topbar {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex: 0 0 60px;
  box-shadow: var(--shadow);
}
.topbar-left { display: flex; align-items: center; gap: 12px; }
.logo-box {
  width: 32px; height: 32px; border-radius: 6px;
  background: var(--primary);
  display: flex; align-items: center; justify-content: center;
}
.product-name { font-size: 16px; font-weight: 700; color: var(--text-1); }
.proj-chip {
  margin-left: 12px; font-size: 12px; color: var(--primary);
  background: var(--primary-light); border-radius: 12px; padding: 2px 10px;
}
.topbar-right { display: flex; align-items: center; color: var(--text-2); font-size: 14px; }
.username { color: var(--text-2); }

.body { flex: 1; display: flex; min-height: 0; }
.sidebar {
  width: 200px; flex: 0 0 200px; background: #fff;
  border-right: 1px solid var(--border); padding: 16px 12px; overflow-y: auto;
}
.menu-title { font-size: 12px; color: var(--text-3); padding: 0 12px 8px; }
.menu-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 6px; margin-bottom: 4px;
  color: var(--text-2); font-size: 14px; text-decoration: none; cursor: pointer;
}
.menu-item:hover { background: var(--primary-light); color: var(--primary); }
.menu-item.active { background: var(--primary-light); color: var(--primary); font-weight: 600; }

.main { flex: 1; overflow-y: auto; background: var(--bg); }
</style>
