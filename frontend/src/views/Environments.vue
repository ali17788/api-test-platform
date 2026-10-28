<template>
  <div class="page-content">
    <h2 class="page-title">测试环境配置</h2>

    <el-alert v-if="!pid" type="warning" show-icon :closable="false" style="margin-bottom:16px"
              title="请先在「项目管理」中选择一个项目进入，再配置该项目下的测试环境。" />

    <div class="toolbar" style="margin-bottom:16px">
      <el-button type="primary" @click="openDialog()" :disabled="!pid">
        <el-icon style="margin-right:4px"><Plus /></el-icon>新增测试环境
      </el-button>
      <span v-if="pid" class="cur-tip">当前项目：{{ projectName }}</span>
    </div>

    <div v-for="env in envs" :key="env.id" class="env-card">
      <div class="env-head">
        <div class="env-name">
          <span class="name-text">{{ env.name }}</span>
          <el-tag v-if="env.is_default" type="primary" size="small" effect="light" style="margin-left:10px">默认环境</el-tag>
        </div>
        <div class="env-ops">
          <el-button link type="primary" @click="openDialog(env)">编辑</el-button>
          <el-button link type="danger" @click="onDelete(env)">删除</el-button>
        </div>
      </div>
      <div class="env-body">
        <div class="kv"><span class="k">接口域名</span><span class="v">{{ env.base_url }}</span></div>
        <div class="kv"><span class="k">请求超时</span><span class="v">{{ env.timeout }} 秒</span></div>
        <div class="kv"><span class="k">失败重试</span><span class="v">{{ env.retry }} 次</span></div>
        <div class="kv kv-full">
          <span class="k">全局请求头</span>
          <span class="v" v-if="env.headers && env.headers.length">
            <el-tag v-for="(h, i) in env.headers" :key="i" size="small" style="margin:0 8px 6px 0">
              {{ h.key }}: {{ h.value }}
            </el-tag>
          </span>
          <span class="v" v-else style="color:var(--text-3)">未配置</span>
        </div>
      </div>
    </div>

    <div v-if="pid && !envs.length" class="card">
      <div class="empty-text">暂无数据</div>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑测试环境' : '新增测试环境'" width="700px">
      <el-form :model="form" label-width="100px">
        <div class="form-section-title">基础信息</div>
        <el-form-item label="环境名称" required>
          <el-input v-model="form.name" placeholder="如：测试环境 / 预发环境 / 生产环境" />
        </el-form-item>
        <el-form-item label="接口域名" required>
          <el-input v-model="form.base_url" placeholder="如：https://api.example.com" />
        </el-form-item>
        <div class="form-section-title">全局请求头</div>
        <div v-for="(h, i) in form.headers" :key="i" class="header-row">
          <el-input v-model="h.key" placeholder="Key（如 Authorization）" style="width:38%" />
          <el-input v-model="h.value" placeholder="Value" style="width:52%" />
          <el-button link type="danger" @click="removeHeader(i)">删除</el-button>
        </div>
        <el-button link type="primary" :icon="Plus" @click="addHeader" style="margin:6px 0 12px">新增请求头</el-button>
        <div class="form-section-title">参数配置</div>
        <el-form-item label="请求超时(s)">
          <el-input-number v-model="form.timeout" :min="1" :max="300" />
        </el-form-item>
        <el-form-item label="失败重试次数">
          <el-input-number v-model="form.retry" :min="0" :max="5" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { api } from '../api'

const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const projectName = ref('')
const envs = ref([])
const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({ id: null, name: '', base_url: '', headers: [], timeout: 10, retry: 0, is_default: false })

async function load() {
  if (!pid.value) return
  try {
    const proj = await api.listProjects()
    const p = (proj || []).find((x) => x.id === pid.value)
    projectName.value = p ? p.name : ''
    envs.value = await api.listEnvs(pid.value)
  } catch (e) { /* ignore */ }
}

function openDialog(env) {
  form.value = env
    ? { id: env.id, name: env.name, base_url: env.base_url, headers: JSON.parse(JSON.stringify(env.headers || [])), timeout: env.timeout, retry: env.retry, is_default: !!env.is_default }
    : { id: null, name: '', base_url: '', headers: [], timeout: 10, retry: 0, is_default: false }
  dialogVisible.value = true
}

function addHeader() { form.value.headers.push({ key: '', value: '' }) }
function removeHeader(i) { form.value.headers.splice(i, 1) }

async function onSubmit() {
  if (!form.value.name.trim()) { ElMessage.warning('请输入环境名称'); return }
  if (!form.value.base_url.trim()) { ElMessage.warning('请输入接口域名'); return }
  submitting.value = true
  try {
    const payload = { ...form.value, headers: form.value.headers.filter((h) => h.key) }
    if (form.value.id) { await api.updateEnv(form.value.id, payload); ElMessage.success('环境更新成功') }
    else { await api.createEnv(pid.value, payload); ElMessage.success('环境创建成功') }
    dialogVisible.value = false
    load()
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function onDelete(env) {
  await ElMessageBox.confirm(`确认删除环境「${env.name}」？`, '删除确认', { type: 'warning' }).catch(() => { throw new Error('cancel') })
  try { await api.deleteEnv(env.id); ElMessage.success('环境已删除'); load() } catch (e) { /* ignore */ }
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  load()
})
</script>

<style scoped>
.env-card {
  background: #fff; border-radius: 8px; box-shadow: var(--shadow);
  padding: 20px; margin-bottom: 20px;
}
.env-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.name-text { font-size: 16px; font-weight: 700; color: var(--text-1); }
.env-body { display: flex; flex-wrap: wrap; gap: 12px 40px; }
.kv { display: flex; gap: 10px; font-size: 14px; }
.kv-full { width: 100%; align-items: flex-start; }
.kv .k { color: var(--text-3); min-width: 70px; }
.kv .v { color: var(--text-2); word-break: break-all; }
.header-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.form-section-title {
  font-size: 13px; font-weight: 600; color: var(--text-1);
  border-left: 3px solid var(--primary); padding-left: 8px; margin: 4px 0 12px;
}
.cur-tip { color: var(--text-3); font-size: 13px; }
</style>
