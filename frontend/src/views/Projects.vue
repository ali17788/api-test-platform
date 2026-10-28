<template>
  <div class="page-content">
    <h2 class="page-title">项目管理</h2>
    <div class="card">
      <div class="toolbar" style="margin-bottom:16px">
        <el-button type="primary" @click="openDialog()">
          <el-icon style="margin-right:4px"><Plus /></el-icon>新增项目
        </el-button>
        <div class="toolbar-right">
          <el-input v-model="keyword" placeholder="请输入项目名称搜索" clearable style="width:260px"
                    :prefix-icon="Search" @clear="load" @keyup.enter="load" />
          <el-button @click="load" :icon="Refresh">刷新</el-button>
        </div>
      </div>

      <el-table :data="filtered" style="width:100%" border stripe>
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="项目名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="description" label="项目描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="owner" label="所属人" width="110" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column prop="api_count" label="接口数" width="90" align="center" />
        <el-table-column prop="case_count" label="用例数" width="90" align="center" />
        <el-table-column label="操作" width="220" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
            <el-button link type="primary" @click="enterProject(row)">进入项目</el-button>
          </template>
        </el-table-column>
        <template #empty><div class="empty-text">暂无数据</div></template>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑项目' : '新增项目'" width="600px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="项目名称" required>
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const list = ref([])
const keyword = ref('')
const dialogVisible = ref(false)
const submitting = ref(false)
const form = ref({ id: null, name: '', description: '' })

const filtered = computed(() => {
  if (!keyword.value) return list.value
  return list.value.filter((p) => p.name.includes(keyword.value))
})

async function load() {
  try { list.value = await api.listProjects() } catch (e) { /* ignore */ }
}

function openDialog(row) {
  form.value = row ? { id: row.id, name: row.name, description: row.description } : { id: null, name: '', description: '' }
  dialogVisible.value = true
}

async function onSubmit() {
  if (!form.value.name.trim()) { ElMessage.warning('请输入项目名称'); return }
  submitting.value = true
  try {
    if (form.value.id) {
      await api.updateProject(form.value.id, { name: form.value.name, description: form.value.description })
      ElMessage.success('项目更新成功')
    } else {
      await api.createProject({ name: form.value.name, description: form.value.description })
      ElMessage.success('项目创建成功')
    }
    dialogVisible.value = false
    load()
  } catch (e) { /* ignore */ } finally { submitting.value = false }
}

async function onDelete(row) {
  await ElMessageBox.confirm(
    `确认删除项目「${row.name}」？该项目的环境、接口、用例数据将一并删除，且不可恢复！`,
    '删除确认', { type: 'warning', confirmButtonText: '确定删除', cancelButtonText: '取消' }
  ).catch(() => { throw new Error('cancel') })
  try {
    await api.deleteProject(row.id)
    ElMessage.success('项目已删除')
    if (localStorage.getItem('currentProjectId') === String(row.id)) {
      localStorage.removeItem('currentProjectId')
      window.dispatchEvent(new Event('project-changed'))
    }
    load()
  } catch (e) { /* ignore */ }
}

function enterProject(row) {
  localStorage.setItem('currentProjectId', String(row.id))
  window.dispatchEvent(new Event('project-changed'))
  ElMessage.success(`已进入项目：${row.name}`)
  router.push('/apis')
}

onMounted(load)
</script>
