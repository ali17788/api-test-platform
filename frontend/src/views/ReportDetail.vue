<template>
  <div class="page-content" v-loading="loading">
    <div class="back-row">
      <el-button link type="primary" @click="$router.push('/reports')">
        <el-icon><ArrowLeft /></el-icon>返回报告列表
      </el-button>
      <h2 class="page-title" style="margin:0">报告详情</h2>
      <div class="toolbar-right">
        <el-button @click="rerunFailed" v-if="detail && detail.task.failed > 0">
          <el-icon style="margin-right:4px"><RefreshRight /></el-icon>重跑失败用例
        </el-button>
        <el-button type="primary" @click="exportVisible = true">
          <el-icon style="margin-right:4px"><Download /></el-icon>全域导出
        </el-button>
      </div>
    </div>

    <template v-if="detail">
      <!-- 概览卡片 -->
      <div class="overview-grid">
        <div class="ov"><div class="ok">总用例</div><div class="ov-v">{{ detail.task.total }}</div></div>
        <div class="ov"><div class="ok">成功</div><div class="ov-v" style="color:var(--success)">{{ detail.task.passed }}</div></div>
        <div class="ov"><div class="ok">失败</div><div class="ov-v" style="color:var(--danger)">{{ detail.task.failed }}</div></div>
        <div class="ov"><div class="ok">跳过</div><div class="ov-v" style="color:var(--skip)">{{ detail.task.skipped }}</div></div>
        <div class="ov"><div class="ok">通过率</div><div class="ov-v" :style="{color: detail.pass_rate >= 80 ? 'var(--success)' : 'var(--warning)'}">{{ detail.pass_rate }}%</div></div>
        <div class="ov"><div class="ok">执行时长</div><div class="ov-v">{{ detail.task.duration }}s</div></div>
      </div>
      <div class="meta-row">
        任务名称：{{ detail.task.name }}　|　执行时间：{{ detail.task.created_at }}
      </div>
      <div class="env-row">
        <el-icon class="er-icon"><Connection /></el-icon>
        <span class="er-label">执行环境</span>
        <el-tag type="primary" effect="light">{{ detail.task.env_name || '未指定' }}</el-tag>
        <code class="er-url">{{ detail.task.env_base_url || '未配置域名' }}</code>
        <el-tag v-if="detail.task.env_deleted" type="warning" effect="light" size="small">该环境已删除</el-tag>
        <span class="er-tip">下列「请求地址」即为该环境域名与接口路径拼接后的真实请求目标</span>
      </div>

      <!-- 图表区 -->
      <div class="chart-row">
        <div class="card">
          <div class="card-title">通过率分布</div>
          <div ref="pieRef" class="chart-box"></div>
        </div>
        <div class="card">
          <div class="card-title">模块成功率</div>
          <div ref="barRef" class="chart-box"></div>
        </div>
      </div>

      <!-- 用例详情列表 -->
      <div class="card">
        <div class="card-title">用例执行明细</div>
        <el-table :data="detail.results" style="width:100%" border row-key="id">
          <el-table-column type="expand">
            <template #default="{ row }">
              <div class="detail-box">
                <div class="ds">请求信息</div>
                <pre class="json-view">{{ formatJson(row.request_info) }}</pre>
                <div class="ds">响应数据</div>
                <pre class="json-view">{{ formatJson(row.response_info) }}</pre>
                <div class="ds">断言日志</div>
                <el-table :data="row.assertions || []" size="small" border style="width:100%">
                  <el-table-column prop="type" label="断言项" width="200" />
                  <el-table-column prop="expected" label="期望" min-width="180" />
                  <el-table-column prop="actual" label="实际" min-width="200" show-overflow-tooltip />
                  <el-table-column label="结果" width="90" align="center">
                    <template #default="{ row: a }">
                      <span :style="{ color: a.passed ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }">
                        {{ a.passed ? '通过' : '失败' }}
                      </span>
                    </template>
                  </el-table-column>
                  <template #empty><div class="empty-text">无断言记录</div></template>
                </el-table>
                <div class="ds" v-if="row.fail_reason">失败原因</div>
                <div v-if="row.fail_reason" class="fail-reason">{{ row.fail_reason }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="case_id" label="用例ID" width="80" align="center" />
          <el-table-column prop="case_name" label="用例名称" min-width="230" show-overflow-tooltip />
          <el-table-column prop="api_name" label="所属接口" min-width="150" show-overflow-tooltip />
          <el-table-column prop="case_type" label="类型" width="90" align="center" />
          <el-table-column label="请求地址" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="url-cell">{{ (row.request_info || {}).url || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <span :class="'status-' + row.status">{{ statusText(row.status) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时(s)" width="100" align="center" />
          <el-table-column prop="fail_reason" label="失败原因" min-width="220" show-overflow-tooltip>
            <template #default="{ row }"><span class="fail-cell">{{ row.fail_reason || '-' }}</span></template>
          </el-table-column>
          <template #empty><div class="empty-text">暂无数据</div></template>
        </el-table>
      </div>
    </template>

    <el-dialog v-model="exportVisible" title="全域导出" width="480px">
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
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { ArrowLeft, Download, RefreshRight, Connection } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const router = useRouter()
const id = ref(Number(route.params.id))
const detail = ref(null)
const loading = ref(false)
const exportVisible = ref(false)
const exporting = ref(false)
const exportFmt = ref('html')
const pieRef = ref(null)
const barRef = ref(null)
let pieChart = null
let barChart = null

const statusText = (s) => ({ passed: '通过', failed: '失败', skipped: '跳过' }[s] || s)
const formatJson = (o) => JSON.stringify(o, null, 2)

async function load() {
  loading.value = true
  try {
    detail.value = await api.reportDetail(id.value)
    await nextTick()
    renderCharts()
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

function renderCharts() {
  if (pieChart) pieChart.dispose()
  if (barChart) barChart.dispose()
  if (!pieRef.value || !barRef.value || !detail.value) return
  const t = detail.value.task
  pieChart = echarts.init(pieRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '62%'], center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data: [
        { name: '成功', value: t.passed, itemStyle: { color: '#00B42A' } },
        { name: '失败', value: t.failed, itemStyle: { color: '#F53F3F' } },
        { name: '跳过', value: t.skipped, itemStyle: { color: '#86909C' } }
      ]
    }]
  })
  const ms = detail.value.module_stats || []
  barChart = echarts.init(barRef.value)
  barChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: ms.map((m) => m.module) },
    yAxis: { type: 'value', max: 100, splitLine: { lineStyle: { color: '#E5E6EB' } } },
    series: [{ type: 'bar', barWidth: 36, data: ms.map((m) => m.rate), itemStyle: { color: '#1677FF', borderRadius: [4, 4, 0, 0] },
              label: { show: true, position: 'top', formatter: '{c}%', color: '#4E5969' } }]
  })
}

async function doExport() {
  exporting.value = true
  try {
    const res = await api.exportReport(id.value, exportFmt.value)
    api.downloadBlob(res, `测试报告.${exportFmt.value === 'excel' ? 'xlsx' : exportFmt.value}`)
    ElMessage.success('报告导出成功')
    exportVisible.value = false
  } catch (e) { /* ignore */ } finally { exporting.value = false }
}

async function rerunFailed() {
  try {
    const res = await api.rerunFailed(id.value)
    ElMessage.success(`已创建重跑任务，共 ${res.total} 条失败用例`)
    router.push({ path: '/execution', query: { task_id: res.task_id } })
  } catch (e) { /* ignore */ }
}

onMounted(load)
onBeforeUnmount(() => { if (pieChart) pieChart.dispose(); if (barChart) barChart.dispose() })
</script>

<style scoped>
.back-row { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.overview-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 12px; }
.ov { background: #fff; border-radius: 8px; box-shadow: var(--shadow); padding: 18px 20px; }
.ok { font-size: 13px; color: var(--text-3); margin-bottom: 6px; }
.ov-v { font-size: 24px; font-weight: 700; color: var(--text-1); }
.meta-row { font-size: 12px; color: var(--text-3); margin-bottom: 20px; }
.env-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 14px; margin-bottom: 20px; border-radius: 6px;
  background: #F0F7FF; border: 1px solid #C9E2FF; font-size: 13px;
}
.er-icon { color: var(--primary); font-size: 15px; }
.er-label { color: var(--text-2); }
.er-url {
  font-family: Consolas, Monaco, monospace; font-size: 12px; color: var(--primary);
  background: #fff; padding: 3px 10px; border-radius: 4px; border: 1px solid #C9E2FF;
  word-break: break-all;
}
.er-tip { color: var(--text-3); font-size: 12px; }
.url-cell {
  font-family: Consolas, Monaco, monospace; font-size: 12px; color: var(--text-2);
}
.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.chart-box { height: 280px; width: 100%; }
.detail-box { padding: 12px 16px; background: #FAFBFC; }
.ds { font-size: 13px; font-weight: 600; color: var(--text-1); margin: 10px 0 6px; }
.fail-reason { color: var(--danger); font-size: 13px; }
.fail-cell { color: var(--danger); }
@media (max-width: 1400px) { .chart-row { grid-template-columns: 1fr; } .overview-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
