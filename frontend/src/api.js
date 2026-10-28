import { ElMessage } from 'element-plus'

const BASE = '/api'

function getToken() {
  return localStorage.getItem('token') || ''
}

async function request(path, options = {}) {
  const { method = 'GET', params, body, raw = false } = options
  let url = BASE + path
  if (params && Object.keys(params).length) {
    const usp = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') usp.append(k, v)
    }
    const qs = usp.toString()
    if (qs) url += (url.includes('?') ? '&' : '?') + qs
  }
  const headers = { Authorization: getToken() }
  if (body && !(body instanceof FormData)) headers['Content-Type'] = 'application/json'
  try {
    const resp = await fetch(url, {
      method,
      headers,
      body: body instanceof FormData ? body : (body ? JSON.stringify(body) : undefined)
    })
    if (raw) return resp
    // 文件下载
    const ct = resp.headers.get('content-type') || ''
    if (ct.includes('application/vnd') || ct.includes('application/pdf') || ct.includes('text/html')) {
      return { blob: await resp.blob(), filename: decodeURIComponent((resp.headers.get('content-disposition') || '').split('filename=')[1] || '') }
    }
    const data = await resp.json()
    if (!resp.ok) {
      if (resp.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('username')
        location.hash = '#/login'
        ElMessage.error('登录已失效，请重新登录')
      } else {
        ElMessage.error(data.detail || data.msg || '请求失败')
      }
      throw new Error(data.detail || data.msg || '请求失败')
    }
    if (data.code !== 0) {
      ElMessage.error(data.msg || '请求失败')
      throw new Error(data.msg || '请求失败')
    }
    return data.data
  } catch (e) {
    throw e
  }
}

function downloadBlob(res, defaultName = 'export') {
  const url = URL.createObjectURL(res.blob)
  const a = document.createElement('a')
  a.href = url
  a.download = res.filename || defaultName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export const api = {
  // 认证
  login: (data) => request('/auth/login', { method: 'POST', body: data }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),

  // 菜单目录（动态侧边栏）
  listMenus: () => request('/menus'),

  // 角色
  listRoles: () => request('/roles'),
  createRole: (data) => request('/roles', { method: 'POST', body: data }),
  updateRole: (id, data) => request(`/roles/${id}`, { method: 'PUT', body: data }),
  deleteRole: (id) => request(`/roles/${id}`, { method: 'DELETE' }),

  // 用户
  listUsers: () => request('/users'),
  createUser: (data) => request('/users', { method: 'POST', body: data }),
  updateUser: (id, data) => request(`/users/${id}`, { method: 'PUT', body: data }),
  deleteUser: (id) => request(`/users/${id}`, { method: 'DELETE' }),

  // 项目
  listProjects: (keyword) => request('/projects', { params: { keyword } }),
  createProject: (data) => request('/projects', { method: 'POST', body: data }),
  updateProject: (id, data) => request(`/projects/${id}`, { method: 'PUT', body: data }),
  deleteProject: (id) => request(`/projects/${id}`, { method: 'DELETE' }),
  projectOverview: (id) => request(`/projects/${id}/overview`),

  // 环境
  listEnvs: (pid) => request(`/projects/${pid}/envs`),
  createEnv: (pid, data) => request(`/projects/${pid}/envs`, { method: 'POST', body: data }),
  updateEnv: (id, data) => request(`/envs/${id}`, { method: 'PUT', body: data }),
  deleteEnv: (id) => request(`/envs/${id}`, { method: 'DELETE' }),

  // 接口
  listApis: (pid, params) => request(`/projects/${pid}/apis`, { params }),
  listAllApis: (pid) => request(`/projects/${pid}/apis/all`),
  getApi: (id) => request(`/apis/${id}`),
  createApi: (pid, data) => request(`/projects/${pid}/apis`, { method: 'POST', body: data }),
  updateApi: (id, data) => request(`/apis/${id}`, { method: 'PUT', body: data }),
  deleteApi: (id) => request(`/apis/${id}`, { method: 'DELETE' }),
  uploadDoc: (pid, formData) => request(`/projects/${pid}/apis/upload`, { method: 'POST', body: formData }),

  // 用例
  listCases: (pid, params) => request(`/projects/${pid}/cases`, { params }),
  createCase: (pid, data) => request(`/projects/${pid}/cases`, { method: 'POST', body: data }),
  updateCase: (id, data) => request(`/cases/${id}`, { method: 'PUT', body: data }),
  deleteCase: (id) => request(`/cases/${id}`, { method: 'DELETE' }),
  batchDeleteCases: (ids) => request('/cases/batch-delete', { method: 'POST', body: ids }),
  runCases: (ids, envId) => request('/cases/run', { method: 'POST', body: { ids, env_id: envId || null } }),

  // AI
  getAiConfig: () => request('/ai/config'),
  saveAiConfig: (data) => request('/ai/config', { method: 'POST', body: data }),
  testAi: (data) => request('/ai/config/test', { method: 'POST', body: data }),
  generateCases: (data) => request('/ai/generate', { method: 'POST', body: data }),
  organizeDocs: (pid) => request(`/ai/organize/${pid}`, { method: 'POST' }),
  listModels: () => request('/ai/models'),

  // 执行
  startTask: (data) => request('/execution/start', { method: 'POST', body: data }),
  taskStatus: (id, logAfter) => request(`/execution/${id}/status`, { params: { log_after: logAfter } }),
  stopTask: (id) => request(`/execution/${id}/stop`, { method: 'POST' }),
  rerunFailed: (id) => request(`/execution/${id}/rerun-failed`, { method: 'POST' }),

  // 报告
  listReports: (pid, params) => request(`/reports/project/${pid}`, { params }),
  reportDetail: (id) => request(`/reports/${id}`),
  exportReport: (id, fmt) => request(`/reports/${id}/export?fmt=${fmt}`),
  deleteReport: (id) => request(`/reports/${id}`, { method: 'DELETE' }),

  // 用例文档导出
  exportCases: (pid, fmt) => request(`/projects/${pid}/cases/export?fmt=${fmt}`),

  // 仪表盘
  dashboard: () => request('/dashboard'),

  downloadBlob
}
