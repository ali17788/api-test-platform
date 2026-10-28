import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'login', component: () => import('./views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('./layout/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: () => import('./views/Dashboard.vue'), meta: { title: '首页仪表盘' } },
      { path: 'projects', name: 'projects', component: () => import('./views/Projects.vue'), meta: { title: '项目管理' } },
      { path: 'envs', name: 'envs', component: () => import('./views/Environments.vue'), meta: { title: '环境配置' } },
      { path: 'apis', name: 'apis', component: () => import('./views/ApiManage.vue'), meta: { title: '接口管理' } },
      { path: 'ai-generate', name: 'ai-generate', component: () => import('./views/AiGenerate.vue'), meta: { title: 'AI用例生成' } },
      { path: 'cases', name: 'cases', component: () => import('./views/Cases.vue'), meta: { title: '用例管理' } },
      { path: 'execution', name: 'execution', component: () => import('./views/Execution.vue'), meta: { title: '测试执行' } },
      { path: 'reports', name: 'reports', component: () => import('./views/Reports.vue'), meta: { title: '测试报告' } },
      { path: 'reports/:id', name: 'report-detail', component: () => import('./views/ReportDetail.vue'), meta: { title: '报告详情' } },
      { path: 'ai-config', name: 'ai-config', component: () => import('./views/AiConfig.vue'), meta: { title: '系统AI配置' } },
      { path: 'users', name: 'users', component: () => import('./views/Users.vue'), meta: { title: '用户与权限' } }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return { path: '/login' }
  }
  if (to.path === '/login' && token) {
    return { path: '/dashboard' }
  }
  return true
})

export default router
