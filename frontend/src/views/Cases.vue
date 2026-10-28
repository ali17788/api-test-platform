<template>
  <div class="page-content">
    <h2 class="page-title">用例管理 & 文档整理</h2>

    <el-alert v-if="!pid" type="warning" show-icon :closable="false" style="margin-bottom:16px"
              title="请先在「项目管理」中进入一个项目。" />

    <div class="card">
      <!-- 第一行：筛选 -->
      <div class="toolbar">
        <el-select v-model="filters.api_id" placeholder="所属接口" clearable filterable style="width:220px" @change="load">
          <el-option v-for="a in apis" :key="a.id" :label="a.name" :value="a.id" />
        </el-select>
        <el-select v-model="filters.case_type" placeholder="用例类型" clearable style="width:140px" @change="load">
          <el-option v-for="t in ['正向', '反向', '边界', '异常']" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="filters.priority" placeholder="优先级" clearable style="width:120px" @change="load">
          <el-option v-for="p in ['P0', 'P1', 'P2']" :key="p" :label="p" :value="p" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索用例名称" clearable style="width:220px"
                  :prefix-icon="Search" @clear="load" @keyup.enter="load" />
        <div class="toolbar-right">
          <el-select v-model="envId" placeholder="执行环境" style="width:280px">
            <el-option v-for="e in envs" :key="e.id" :value="e.id">
              <span>{{ e.name }}{{ e.is_default ? '（默认）' : '' }}</span>
              <span style="float:right;color:#86909C;font-size:12px;margin-left:12px">{{ e.base_url }}</span>
            </el-option>
          </el-select>
          <el-button type="primary" :disabled="!selected.length" @click="runSelected">批量执行</el-button>
          <el-button type="danger" plain :disabled="!selected.length" @click="delSelected">批量删除</el-button>
          <el-button :icon="MagicStick" @click="organize" :loading="organizing">AI整理用例文档</el-button>
          <el-button type="primary" :icon="Download" @click="exportVisible = true">导出文档</el-button>
        </div>
      </div>
    </div>

    <div class="card">
      <el-table :data="cases" style="width:100%" v-loading="loading" border @selection-change="onSelect">
        <el-table-column type="selection" width="50" align="center" />
        <el-table-column prop="id" label="用例ID" width="80" align="center" />
        <el-table-column prop="name" label="用例名称" min-width="240" show-overflow-tooltip />
        <el-table-column prop="api_name" label="所属接口" min-width="160" show-overflow-tooltip />
        <el-table-column label="用例类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="typeColor(row.case_type)" effect="light">{{ row.case_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="90" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.priority === 'P0' ? 'var(--danger)' : (row.priority === 'P1' ? 'var(--warning)' : 'var(--text-3)'), fontWeight: 600 }">
              {{ row.priority }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="请求参数" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="mono">{{ short(JSON.stringify(row.request_data)) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="预期结果" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">HTTP {{ row.expected?.status_code }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <span :class="'status-' + (row.last_status || 'pending')">{{ statusText(row.last_status) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="200" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
            <el-button link type="primary" @click="runOne(row)">执行</el-button>
            <el-button link type="primary" @click="viewDoc(row)">查看文档</el-button>
          </template>
        </el-table-column>
        <template #empty><div class="empty-text">暂无数据</div></template>
      </el-table>
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="10"
                       v-model:current-page="page" @current-change="load" />
      </div>
    </div>

    <!-- 用例编辑 -->
    <el-dialog v-model="editVisible" title="编辑用例" width="800px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="所属接口">
          <el-select v-model="form.api_id" filterable style="width:100%">
            <el-option v-for="a in apis" :key="a.id" :label="`${a.method} ${a.path} - ${a.name}`" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用例名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="用例类型">
          <el-radio-group v-model="form.case_type">
            <el-radio v-for="t in ['正向', '反向', '边界', '异常']" :key="t" :value="t">{{ t }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="优先级">
          <el-radio-group v-model="form.priority">
            <el-radio v-for="p in ['P0', 'P1', 'P2']" :key="p" :value="p">{{ p }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="测试步骤"><el-input v-model="form.steps" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="请求参数"><el-input v-model="reqText" type="textarea" :rows="4" /></el-form-item>
        <el-form-item label="预期结果(JSON)"><el-input v-model="expText" type="textarea" :rows="4" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 用例文档预览 -->
    <el-dialog v-model="docVisible" title="用例文档预览" width="900px">
      <div class="doc-preview">
        <div class="doc-h">{{ form.name }}</div>
        <table class="doc-tbl">
          <tr><td class="dk">用例ID</td><td>{{ form.id }}</td><td class="dk">优先级</td><td>{{ form.priority }}</td></tr>
          <tr><td class="dk">所属接口</td><td>{{ docApiName }}</td><td class="dk">用例类型</td><td>{{ form.case_type }}</td></tr>
          <tr><td class="dk">请求方式</td><td>{{ docApiMethod }}</td><td class="dk">接口地址</td><td>{{ docApiPath }}</td></tr>
        </table>
        <div class="doc-sec">测试步骤</div>
        <div class="doc-body">{{ form.steps || '—' }}</div>
        <div class="doc-sec">请求参数</div>
        <pre class="json-view">{{ reqText }}</pre>
        <div class="doc-sec">预期结果</div>
        <pre class="json-view">{{ expText }}</pre>
      </div>
      <template #footer><el-button type="primary" @click="docVisible = false">关闭</el-button></template>
    </el-dialog>

    <!-- 导出文档 -->
    <el-dialog v-model="exportVisible" title="导出测试用例文档" width="520px">
      <el-form label-width="100px">
        <el-form-item label="导出格式">
          <el-checkbox-group v-model="exportFormats">
            <el-checkbox value="word" label="Word 文档" />
            <el-checkbox value="excel" label="Excel 表格" />
            <el-checkbox value="pdf" label="PDF 文档" />
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="exportVisible = false">取消</el-button>
        <el-button type="primary" @click="doExport" :loading="exporting">确定导出</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Download, MagicStick } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const cases = ref([])
const apis = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const selected = ref([])
const filters = ref({ api_id: null, case_type: '', priority: '', keyword: '' })
const editVisible = ref(false)
const docVisible = ref(false)
const exportVisible = ref(false)
const exporting = ref(false)
const organizing = ref(false)
const submitting = ref(false)
const exportFormats = ref(['word', 'excel', 'pdf'])
const form = ref({ id: null, api_id: null, name: '', case_type: '正向', priority: 'P1', steps: '' })
const reqText = ref('{}')
const expText = ref('{}')
const docApiName = ref('')
const docApiMethod = ref('')
const docApiPath = ref('')
const envs = ref([])
const envId = ref(null)

const statusText = (s) => ({ passed: '通过', failed: '失败', skipped: '跳过', '': '待执行' }[s] || '待执行')
const typeColor = (t) => ({ '正向': 'success', '反向': 'warning', '边界': 'primary', '异常': 'danger' }[t] || 'info')
const short = (s) => (s && s.length > 60 ? s.slice(0, 60) + '...' : (s || '—'))

async function load() {
  if (!pid.value) return
  loading.value = true
  try {
    const res = await api.listCases(pid.value, { ...filters.value, page: page.value, size: 10 })
    cases.value = res.list
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function loadApis() {
  if (!pid.value) return
  try { apis.value = await api.listAllApis(pid.value) } catch (e) { /* ignore */ }
}

async function loadEnvs() {
  if (!pid.value) return
  try {
    envs.value = await api.listEnvs(pid.value)
    const def = envs.value.find((e) => e.is_default)
    envId.value = def ? def.id : (envs.value[0] ? envs.value[0].id : null)
  } catch (e) { /* ignore */ }
}

function onSelect(rows) { selected.value = rows }

function parseJSON(t, d = {}) { try { return JSON.parse(t || '{}') } catch (e) { return d } }

function openEdit(row) {
  form.value = { id: row.id, api_id: row.api_id, name: row.name, case_type: row.case_type, priority: row.priority, steps: row.steps }
  reqText.value = JSON.stringify(row.request_data || {}, null, 2)
  expText.value = JSON.stringify(row.expected || {}, null, 2)
  editVisible.value = true
}

function viewDoc(row) {
  openEdit(row)
  editVisible.value = false
  const a = apis.value.find((x) => x.id === row.api_id)
  docApiName.value = a ? a.name : ''
  docApiMethod.value = a ? a.method : ''
  docApiPath.value = a ? a.path : ''
  docVisible.value = true
}

async function submitEdit() {
  submitting.value = true
  try {
    await api.updateCase(form.value.id, { ...form.value, request_data: parseJSON(reqText.value), expected: parseJSON(expText.value) })
    ElMessage.success('用例更新成功')
    editVisible.value = false
    load()
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除用例「${row.name}」？`, '删除确认', { type: 'warning' }).catch(() => { throw new Error('cancel') })
  try { await api.deleteCase(row.id); ElMessage.success('用例已删除'); load() } catch (e) { /* ignore */ }
}

async function delSelected() {
  const ids = selected.value.map((r) => r.id)
  await ElMessageBox.confirm(`确认删除选中的 ${ids.length} 条用例？`, '批量删除', { type: 'warning' }).catch(() => { throw new Error('cancel') })
  try { await api.batchDeleteCases(ids); ElMessage.success(`已删除 ${ids.length} 条用例`); load() } catch (e) { /* ignore */ }
}

async function runSelected() {
  const ids = selected.value.map((r) => r.id)
  if (!envId.value && envs.value.length) { ElMessage.warning('请选择执行环境'); return }
  try {
    const res = await api.runCases(ids, envId.value)
    ElMessage.success('执行任务已启动')
    router.push({ path: '/execution', query: { task_id: res.task_id } })
  } catch (e) { /* ignore */ }
}

async function runOne(row) {
  if (!envId.value && envs.value.length) { ElMessage.warning('请先配置执行环境'); return }
  try {
    const res = await api.runCases([row.id], envId.value)
    ElMessage.success('执行任务已启动')
    router.push({ path: '/execution', query: { task_id: res.task_id } })
  } catch (e) { /* ignore */ }
}

async function organize() {
  organizing.value = true
  try {
    const res = await api.organizeDocs(pid.value)
    ElMessage.success(res.order_rule)
    load()
  } catch (e) { /* ignore */ } finally { organizing.value = false }
}

async function doExport() {
  if (!exportFormats.value.length) { ElMessage.warning('请选择导出格式'); return }
  exporting.value = true
  try {
    for (const f of exportFormats.value) {
      const res = await api.exportCases(pid.value, f)
      api.downloadBlob(res, `测试用例文档.${f === 'excel' ? 'xlsx' : f}`)
    }
    ElMessage.success('文档导出成功')
    exportVisible.value = false
  } catch (e) { /* ignore */ } finally { exporting.value = false }
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  load()
  loadApis()
  loadEnvs()
})
</script>

<style scoped>
.mono { font-family: Consolas, Monaco, monospace; font-size: 12px; color: var(--text-3); }
.doc-preview { font-size: 13px; }
.doc-h { font-size: 16px; font-weight: 700; color: var(--text-1); margin-bottom: 14px; }
.doc-tbl { width: 100%; border-collapse: collapse; margin-bottom: 14px; }
.doc-tbl td { border: 1px solid var(--border); padding: 8px 10px; }
.dk { background: #F5F7FA; color: var(--text-3); width: 15%; }
.doc-sec { font-weight: 600; color: var(--text-1); margin: 10px 0 6px; }
.doc-body { color: var(--text-2); }
</style>
