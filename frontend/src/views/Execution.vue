<template>
  <div class="page-content">
    <h2 class="page-title">测试执行</h2>

    <el-alert v-if="!pid" type="warning" show-icon :closable="false" style="margin-bottom:16px"
              title="请先在「项目管理」中进入一个项目。" />

    <!-- 执行配置区 -->
    <div class="card">
      <div class="card-title">执行配置</div>
      <div class="toolbar">
        <el-select v-model="envId" placeholder="选择测试环境" style="width:300px">
          <el-option v-for="e in envs" :key="e.id" :value="e.id">
            <span>{{ e.name }}{{ e.is_default ? '（默认）' : '' }}</span>
            <span style="float:right;color:#86909C;font-size:12px;margin-left:12px">{{ e.base_url }}</span>
          </el-option>
        </el-select>
        <el-select v-model="scope" placeholder="执行用例范围" style="width:200px">
          <el-option label="全项目用例" value="all" />
          <el-option label="仅失败用例" value="failed" />
          <el-option label="指定接口用例" value="api" />
        </el-select>
        <el-select v-if="scope === 'api'" v-model="scopeApiId" placeholder="选择接口" filterable style="width:240px">
          <el-option v-for="a in apis" :key="a.id" :label="a.name" :value="a.id" />
        </el-select>
        <el-input-number v-model="timeout" :min="1" :max="300" size="default" />
        <span class="unit">秒超时</span>
        <el-input-number v-model="retry" :min="0" :max="5" size="default" />
        <span class="unit">次重试</span>
        <div class="toolbar-right">
          <el-button type="primary" size="large" :loading="starting" :disabled="running" @click="start">
            <el-icon style="margin-right:6px"><VideoPlay /></el-icon>开始执行
          </el-button>
        </div>
      </div>
      <!-- 环境确认条：执行前明确「打到哪台机器」 -->
      <div v-if="curEnv" class="env-confirm">
        <el-icon class="ec-icon"><Connection /></el-icon>
        <span class="ec-label">本次执行目标环境</span>
        <el-tag type="primary" effect="light">{{ curEnv.name }}</el-tag>
        <code class="ec-url">{{ curEnv.base_url || '未配置域名' }}</code>
        <span class="ec-meta">超时 {{ curEnv.timeout }}s · 重试 {{ curEnv.retry }} 次</span>
      </div>
      <div v-else-if="envs.length === 0 && pid" class="env-confirm env-warn">
        <el-icon class="ec-icon"><WarningFilled /></el-icon>
        <span>当前项目尚未配置测试环境，请先到「环境配置」添加环境（填写接口域名）后再执行</span>
      </div>
    </div>

    <!-- 实时统计区 -->
    <div class="mini-grid">
      <div class="mini-card"><div class="mk">已执行</div><div class="mv">{{ stats.executed }} / {{ stats.total }}</div></div>
      <div class="mini-card"><div class="mk">成功</div><div class="mv" style="color:var(--success)">{{ stats.passed }}</div></div>
      <div class="mini-card"><div class="mk">失败</div><div class="mv" style="color:var(--danger)">{{ stats.failed }}</div></div>
      <div class="mini-card"><div class="mk">跳过</div><div class="mv" style="color:var(--skip)">{{ stats.skipped }}</div></div>
    </div>

    <div class="card" style="margin-top:20px">
      <div class="card-title">
        <span>整体执行进度</span>
        <el-tag v-if="task" :type="task.status === 'running' ? 'primary' : (task.status === 'finished' ? 'success' : 'warning')" effect="light">
          {{ statusText(task.status) }}
        </el-tag>
      </div>
      <el-progress :percentage="percent" :stroke-width="14" :color="percent === 100 ? '#00B42A' : '#1677FF'" />
    </div>

    <!-- 日志面板 -->
    <div class="card">
      <div class="card-title">
        <span>实时执行日志</span>
        <el-button type="danger" size="small" :disabled="!running" @click="stopTask">
          <el-icon style="margin-right:4px"><VideoPause /></el-icon>终止任务
        </el-button>
      </div>
      <div class="log-panel" ref="logRef">
        <div v-for="l in logs" :key="l.id" :class="'log-line log-' + l.level">{{ l.message }}</div>
        <div v-if="!logs.length" class="log-line" style="color:#86909C">暂无日志，点击「开始执行」启动测试任务…</div>
      </div>
    </div>

    <!-- 执行完成弹窗 -->
    <el-dialog v-model="resultVisible" title="执行结果统计" width="520px" :close-on-click-modal="false">
      <div class="result-stats">
        <div class="rs"><div class="rs-k">总用例</div><div class="rs-v">{{ stats.total }}</div></div>
        <div class="rs"><div class="rs-k">成功</div><div class="rs-v" style="color:var(--success)">{{ stats.passed }}</div></div>
        <div class="rs"><div class="rs-k">失败</div><div class="rs-v" style="color:var(--danger)">{{ stats.failed }}</div></div>
        <div class="rs"><div class="rs-k">通过率</div><div class="rs-v">{{ stats.executed ? Math.round(stats.passed / stats.executed * 100) : 0 }}%</div></div>
      </div>
      <template #footer>
        <el-button @click="resultVisible = false">关闭</el-button>
        <el-button v-if="stats.failed > 0" @click="rerun">重跑失败用例</el-button>
        <el-button type="primary" @click="viewReport">查看测试报告</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, VideoPause, Connection, WarningFilled } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const envs = ref([])
const apis = ref([])
const envId = ref(null)
const scope = ref('all')
const scopeApiId = ref(null)
const timeout = ref(10)
const retry = ref(0)
const task = ref(null)
const taskId = ref(null)
const running = ref(false)
const starting = ref(false)
const logs = ref([])
const resultVisible = ref(false)
const logRef = ref(null)
let timer = null
let lastLogId = 0

const stats = computed(() => task.value
  ? { total: task.value.total, executed: task.value.executed, passed: task.value.passed, failed: task.value.failed, skipped: task.value.skipped }
  : { total: 0, executed: 0, passed: 0, failed: 0, skipped: 0 })

const percent = computed(() => {
  if (!task.value || !task.value.total) return 0
  return Math.round(task.value.executed / task.value.total * 100)
})

// 当前选中环境对象：用于执行前明确「请求会打到哪台机器」
const curEnv = computed(() => envs.value.find((e) => e.id === envId.value) || null)

const statusText = (s) => ({ running: '执行中', finished: '已完成', stopped: '已终止', pending: '等待中' }[s] || s)

async function loadEnvs() {
  if (!pid.value) return
  try {
    envs.value = await api.listEnvs(pid.value)
    const def = envs.value.find((e) => e.is_default)
    if (def) envId.value = def.id
    else if (envs.value.length) envId.value = envs.value[0].id
  } catch (e) { /* ignore */ }
  try { apis.value = await api.listAllApis(pid.value) } catch (e) { /* ignore */ }
}

async function start() {
  starting.value = true
  try {
    let caseIds = []
    if (scope.value === 'api') {
      if (!scopeApiId.value) { ElMessage.warning('请选择接口'); starting.value = false; return }
      const res = await api.listCases(pid.value, { api_id: scopeApiId.value, size: 100 })
      caseIds = res.list.map((c) => c.id)
      if (!caseIds.length) { ElMessage.warning('该接口下暂无用例'); starting.value = false; return }
      var payload = { project_id: pid.value, env_id: envId.value, scope: 'selected', case_ids: caseIds }
    } else {
      var payload = { project_id: pid.value, env_id: envId.value, scope: scope.value }
    }
    const res = await api.startTask(payload)
    taskId.value = res.task_id
    logs.value = []
    lastLogId = 0
    running.value = true
    ElMessage.success(`任务已启动，共 ${res.total} 条用例`)
    startPolling()
  } catch (e) { /* ignore */ } finally { starting.value = false }
}

function startPolling() {
  stopPolling()
  timer = setInterval(poll, 1000)
  poll()
}

function stopPolling() { if (timer) { clearInterval(timer); timer = null } }

async function poll() {
  if (!taskId.value) return
  try {
    const res = await api.taskStatus(taskId.value, lastLogId)
    task.value = res.task
    if (res.logs && res.logs.length) {
      logs.value.push(...res.logs)
      lastLogId = res.logs[res.logs.length - 1].id
      await nextTick()
      if (logRef.value) logRef.value.scrollTop = logRef.value.scrollHeight
    }
    if (res.task.status !== 'running' && res.task.status !== 'pending') {
      running.value = false
      stopPolling()
      if (res.task.status === 'finished') resultVisible.value = true
    }
  } catch (e) { running.value = false; stopPolling() }
}

async function stopTask() {
  try { await api.stopTask(taskId.value); ElMessage.info('终止指令已发送') } catch (e) { /* ignore */ }
}

function viewReport() {
  resultVisible.value = false
  router.push(`/reports/${taskId.value}`)
}

async function rerun() {
  try {
    const res = await api.rerunFailed(taskId.value)
    ElMessage.success(`已创建重跑任务，共 ${res.total} 条失败用例`)
    resultVisible.value = false
    taskId.value = res.task_id
    logs.value = []
    lastLogId = 0
    running.value = true
    startPolling()
  } catch (e) { /* ignore */ }
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  loadEnvs()
  const qid = route.query.task_id
  if (qid) { taskId.value = Number(qid); running.value = true; startPolling() }
})
onBeforeUnmount(stopPolling)
</script>

<style scoped>
.unit { font-size: 13px; color: var(--text-3); margin-right: 8px; }
.mini-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
.mini-card { background: #fff; border-radius: 8px; box-shadow: var(--shadow); padding: 16px 20px; }
.mk { font-size: 13px; color: var(--text-3); margin-bottom: 6px; }
.mv { font-size: 22px; font-weight: 700; color: var(--text-1); }
.result-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.rs { text-align: center; background: #F7F8FA; border-radius: 6px; padding: 14px 8px; }
.rs-k { font-size: 12px; color: var(--text-3); margin-bottom: 6px; }
.rs-v { font-size: 24px; font-weight: 700; color: var(--text-1); }
.env-confirm {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-top: 14px; padding: 10px 14px; border-radius: 6px;
  background: #F0F7FF; border: 1px solid #C9E2FF; font-size: 13px;
}
.env-confirm.env-warn { background: #FFF7E8; border-color: #FFD08A; color: #A15C00; }
.ec-icon { color: var(--primary); font-size: 15px; }
.env-warn .ec-icon { color: #FF7D00; }
.ec-label { color: var(--text-2); }
.ec-url {
  font-family: Consolas, Monaco, monospace; font-size: 12px; color: var(--primary);
  background: #fff; padding: 3px 10px; border-radius: 4px; border: 1px solid #C9E2FF;
  word-break: break-all;
}
.ec-meta { color: var(--text-3); font-size: 12px; }
</style>
