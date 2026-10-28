<template>
  <div class="page-content">
    <h2 class="page-title">接口文档解析 & 接口管理</h2>

    <el-alert v-if="!pid" type="warning" show-icon :closable="false" style="margin-bottom:16px"
              title="请先在「项目管理」中进入一个项目。" />

    <div class="card">
      <div class="toolbar">
        <el-button type="primary" @click="uploadVisible = true" :disabled="!pid">
          <el-icon style="margin-right:4px"><Upload /></el-icon>上传文档
        </el-button>
        <el-button @click="openApiDialog()" :disabled="!pid">
          <el-icon style="margin-right:4px"><Plus /></el-icon>手动新增接口
        </el-button>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <div class="toolbar-right">
          <el-input v-model="keyword" placeholder="搜索接口名称/地址" clearable style="width:260px"
                    :prefix-icon="Search" @clear="load" @keyup.enter="load" />
        </div>
      </div>
    </div>

    <div class="card">
      <el-table :data="apis" style="width:100%" v-loading="loading" border>
        <el-table-column prop="name" label="接口名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="请求方式" width="100" align="center">
          <template #default="{ row }">
            <span :class="'tag-method method-' + row.method">{{ row.method }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="接口地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="module" label="所属模块" width="140" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="260" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewApi(row)">查看</el-button>
            <el-button link type="primary" @click="openApiDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
            <el-button link type="primary" @click="genCases(row)">生成用例</el-button>
          </template>
        </el-table-column>
        <template #empty><div class="empty-text">暂无数据</div></template>
      </el-table>
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="10"
                       v-model:current-page="page" @current-change="load" />
      </div>
    </div>

    <!-- 上传文档弹窗 -->
    <el-dialog v-model="uploadVisible" title="上传接口文档" width="600px">
      <el-upload drag :auto-upload="false" :show-file-list="true" :limit="1"
                 accept=".json,.yaml,.yml,.pdf,.html,.htm,.md,.txt"
                 :on-change="onFileChange" :file-list="fileList">
        <el-icon :size="40" color="#1677FF"><UploadFilled /></el-icon>
        <div class="el-upload__text">拖拽文件至此或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">
            支持 5 类格式：<b>OpenAPI/Swagger</b>（json/yaml）、<b>Postman Collection</b>（json）、
            <b>PDF</b>、<b>HTML</b>、<b>Markdown/文本</b>；单个文件不超过 20MB
          </div>
          <div class="el-upload__tip" style="margin-top:4px">
            PDF / HTML 需为文本版（含「请求方法 + 接口路径」如 POST /api/login，或含参数名表格），扫描件图片版无法识别
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="doUpload" :loading="uploading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 接口详情/编辑弹窗 -->
    <el-dialog v-model="apiVisible" :title="(viewMode ? '接口详情' : (apiForm.id ? '编辑接口' : '新增接口'))" width="800px">
      <el-form :model="apiForm" label-width="100px">
        <el-form-item label="接口名称"><el-input v-model="apiForm.name" :disabled="viewMode" /></el-form-item>
        <el-form-item label="请求方式">
          <el-select v-model="apiForm.method" :disabled="viewMode" style="width:150px">
            <el-option v-for="m in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']" :key="m" :label="m" :value="m" />
          </el-select>
        </el-form-item>
        <el-form-item label="接口地址"><el-input v-model="apiForm.path" :disabled="viewMode" placeholder="/api/v1/xxx" /></el-form-item>
        <el-form-item label="所属模块"><el-input v-model="apiForm.module" :disabled="viewMode" /></el-form-item>
        <el-form-item label="Query参数">
          <el-input v-model="queryText" type="textarea" :rows="3" :disabled="viewMode" placeholder='JSON 格式，如 {"page":1}' />
        </el-form-item>
        <el-form-item label="请求体">
          <el-input v-model="bodyText" type="textarea" :rows="4" :disabled="viewMode" placeholder='JSON 格式请求体' />
        </el-form-item>
        <el-form-item label="请求头">
          <el-input v-model="headerText" type="textarea" :rows="2" :disabled="viewMode" placeholder='JSON 格式' />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiVisible = false">{{ viewMode ? '关闭' : '取消' }}</el-button>
        <el-button v-if="!viewMode" type="primary" @click="submitApi" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled, Plus, Refresh, Search } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const apis = ref([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const loading = ref(false)
const uploadVisible = ref(false)
const apiVisible = ref(false)
const viewMode = ref(false)
const uploading = ref(false)
const submitting = ref(false)
const fileList = ref([])
const rawFile = ref(null)
const apiForm = ref({ id: null, name: '', method: 'GET', path: '/', module: '默认模块', headers: {}, query_params: {}, body: {} })
const queryText = ref('{}')
const bodyText = ref('{}')
const headerText = ref('{}')

async function load() {
  if (!pid.value) return
  loading.value = true
  try {
    const res = await api.listApis(pid.value, { keyword: keyword.value, page: page.value, size: 10 })
    apis.value = res.list
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function onFileChange(file) { rawFile.value = file.raw }

async function doUpload() {
  if (!rawFile.value) { ElMessage.warning('请先选择文件'); return }
  uploading.value = true
  const fd = new FormData()
  fd.append('file', rawFile.value)
  try {
    const res = await api.uploadDoc(pid.value, fd)
    ElMessage.success(`接口文档解析完成，共 ${res.parsed} 个有效接口，新增入库 ${res.inserted} 个`)
    uploadVisible.value = false
    fileList.value = []
    rawFile.value = null
    load()
  } catch (e) { /* ignore */ } finally { uploading.value = false }
}

function parseJSON(text, defaultVal = {}) {
  try { return JSON.parse(text || '{}') } catch (e) { return defaultVal }
}

function openApiDialog(row) {
  viewMode.value = false
  if (row) {
    apiForm.value = { id: row.id, name: row.name, method: row.method, path: row.path, module: row.module,
                      headers: row.headers || {}, query_params: row.query_params || {}, body: row.body || {} }
  } else {
    apiForm.value = { id: null, name: '', method: 'GET', path: '/', module: '默认模块', headers: {}, query_params: {}, body: {} }
  }
  queryText.value = JSON.stringify(apiForm.value.query_params, null, 2)
  bodyText.value = JSON.stringify(apiForm.value.body, null, 2)
  headerText.value = JSON.stringify(apiForm.value.headers, null, 2)
  apiVisible.value = true
}

function viewApi(row) { openApiDialog(row); viewMode.value = true }

async function submitApi() {
  if (!apiForm.value.name.trim()) { ElMessage.warning('请输入接口名称'); return }
  submitting.value = true
  try {
    const payload = { ...apiForm.value, query_params: parseJSON(queryText.value), body: parseJSON(bodyText.value), headers: parseJSON(headerText.value) }
    if (apiForm.value.id) { await api.updateApi(apiForm.value.id, payload); ElMessage.success('接口更新成功') }
    else { await api.createApi(pid.value, payload); ElMessage.success('接口创建成功') }
    apiVisible.value = false
    load()
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除接口「${row.name}」？其下用例将一并删除`, '删除确认', { type: 'warning' }).catch(() => { throw new Error('cancel') })
  try { await api.deleteApi(row.id); ElMessage.success('接口已删除'); load() } catch (e) { /* ignore */ }
}

function genCases(row) {
  router.push({ path: '/ai-generate', query: { api_id: row.id } })
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  load()
})
</script>
