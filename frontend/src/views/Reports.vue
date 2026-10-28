<template>
  <div class="page-content">
    <h2 class="page-title">测试报告</h2>

    <el-alert v-if="!pid" type="info" show-icon :closable="false" style="margin-bottom:16px"
              title="进入项目后可查看该项目下的历史报告；未选择项目时展示全部历史任务。" />

    <div class="card">
      <el-table :data="reports" style="width:100%" v-loading="loading" border>
        <el-table-column prop="name" label="任务名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="created_at" label="执行时间" width="180" />
        <el-table-column label="执行环境" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.env_name">
              <el-tag size="small" type="primary" effect="light">{{ row.env_name }}</el-tag>
              <span class="env-url">{{ row.env_base_url || '未配置域名' }}</span>
            </span>
            <span v-else class="env-url">未指定</span>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="执行时长" width="110" align="center">
          <template #default="{ row }">{{ row.duration }}s</template>
        </el-table-column>
        <el-table-column prop="total" label="总用例数" width="100" align="center" />
        <el-table-column label="通过率" width="180" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.pass_rate" :stroke-width="10"
                         :color="row.pass_rate >= 80 ? '#00B42A' : (row.pass_rate >= 50 ? '#FF7D00' : '#F53F3F')" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <span :class="'status-' + row.status">{{ statusText(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/reports/${row.id}`)">查看详情</el-button>
            <el-button link type="primary" @click="exportOne(row)">导出报告</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty><div class="empty-text">暂无数据</div></template>
      </el-table>
      <div style="margin-top:16px;display:flex;justify-content:flex-end">
        <el-pagination background layout="total, prev, pager, next" :total="total" :page-size="10"
                       v-model:current-page="page" @current-change="load" />
      </div>
    </div>

    <el-dialog v-model="exportVisible" title="导出测试报告" width="480px">
      <el-form label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportFmt">
            <el-radio value="html">HTML</el-radio>
            <el-radio value="excel">Excel</el-radio>
            <el-radio value="pdf">PDF</el-radio>
          </el-radio-group>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../api'

const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const reports = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const exportVisible = ref(false)
const exporting = ref(false)
const exportFmt = ref('html')
const curRow = ref(null)

const statusText = (s) => ({ running: '执行中', finished: '已完成', stopped: '已终止', pending: '等待中' }[s] || s)

async function load() {
  if (!pid.value) return
  loading.value = true
  try {
    const res = await api.listReports(pid.value, { page: page.value, size: 10 })
    reports.value = res.list
    total.value = res.total
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function exportOne(row) { curRow.value = row; exportVisible.value = true }

async function doExport() {
  exporting.value = true
  try {
    const res = await api.exportReport(curRow.value.id, exportFmt.value)
    api.downloadBlob(res, `测试报告_${curRow.value.name}.${exportFmt.value === 'excel' ? 'xlsx' : exportFmt.value}`)
    ElMessage.success('报告导出成功')
    exportVisible.value = false
  } catch (e) { /* ignore */ } finally { exporting.value = false }
}

async function onDelete(row) {
  await ElMessageBox.confirm(`确认删除报告「${row.name}」？`, '删除确认', { type: 'warning' }).catch(() => { throw new Error('cancel') })
  try { await api.deleteReport(row.id); ElMessage.success('报告已删除'); load() } catch (e) { /* ignore */ }
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  load()
})
</script>

<style scoped>
.env-url {
  font-family: Consolas, Monaco, monospace; font-size: 12px;
  color: var(--text-3); margin-left: 8px;
}
</style>
