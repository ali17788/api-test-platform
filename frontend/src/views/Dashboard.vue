<template>
  <div class="page-content">
    <h2 class="page-title">首页仪表盘</h2>

    <!-- 数据卡片 -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-label">项目总数</div>
        <div class="stat-value">{{ data.projects }}</div>
        <div class="stat-desc">当前平台创建的测试项目</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">接口总数</div>
        <div class="stat-value">{{ data.apis }}</div>
        <div class="stat-desc">累计导入的有效接口</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">测试用例总数</div>
        <div class="stat-value">{{ data.cases }}</div>
        <div class="stat-desc">AI生成 + 手动新增用例</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">平台用户</div>
        <div class="stat-value">{{ data.users }}</div>
        <div class="stat-desc">系统账号总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">角色数量</div>
        <div class="stat-value">{{ data.roles }}</div>
        <div class="stat-desc">可分配的权限角色</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">近期测试通过率</div>
        <div class="stat-value" :style="{ color: data.week_rate >= 80 ? 'var(--success)' : 'var(--warning)' }">
          {{ data.week_rate }}%
        </div>
        <div class="stat-desc">近7天平均执行通过率</div>
      </div>
    </div>

    <!-- 双图表区 -->
    <div class="chart-row">
      <div class="card chart-card">
        <div class="card-title">执行趋势（近7日）</div>
        <div ref="trendRef" class="chart-box"></div>
      </div>
      <div class="card chart-card">
        <div class="card-title">用例状态分布</div>
        <div ref="pieRef" class="chart-box"></div>
      </div>
    </div>

    <!-- 最近测试任务 -->
    <div class="card">
      <div class="card-title">最近测试任务记录</div>
      <el-table :data="data.recent" style="width:100%" size="default">
        <el-table-column prop="name" label="任务名称" min-width="200" />
        <el-table-column prop="created_at" label="执行时间" width="180" />
        <el-table-column prop="total" label="用例数" width="100" align="center" />
        <el-table-column label="通过率" width="160">
          <template #default="{ row }">
            <el-progress :percentage="row.pass_rate" :stroke-width="10"
                         :color="row.pass_rate >= 80 ? '#00B42A' : (row.pass_rate >= 50 ? '#FF7D00' : '#F53F3F')" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <span :class="'status-' + row.status">
              {{ statusText(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="right" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewReport(row.id)">查看报告</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-text">暂无数据</div>
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import { api } from '../api'

const router = useRouter()
const trendRef = ref(null)
const pieRef = ref(null)
const data = ref({ projects: 0, apis: 0, cases: 0, users: 0, roles: 0, week_rate: 0, trend: [], pie: {}, recent: [] })
let trendChart = null
let pieChart = null

const statusText = (s) => ({ running: '执行中', finished: '已完成', stopped: '已终止', pending: '等待中' }[s] || s)

async function load() {
  try {
    data.value = await api.dashboard()
    await nextTick()
    renderCharts()
  } catch (e) { /* ignore */ }
}

function renderCharts() {
  if (trendChart) trendChart.dispose()
  if (pieChart) pieChart.dispose()
  if (!trendRef.value || !pieRef.value) return

  const t = data.value.trend || []
  trendChart = echarts.init(trendRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['执行用例数', '通过数'], bottom: 0, textStyle: { color: '#4E5969' } },
    grid: { left: 40, right: 20, top: 30, bottom: 40 },
    xAxis: { type: 'category', data: t.map((x) => x.date), axisLine: { lineStyle: { color: '#E5E6EB' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#E5E6EB' } } },
    series: [
      { name: '执行用例数', type: 'line', smooth: true, data: t.map((x) => x.executed), itemStyle: { color: '#1677FF' }, areaStyle: { color: '#E8F3FF' } },
      { name: '通过数', type: 'line', smooth: true, data: t.map((x) => x.passed), itemStyle: { color: '#00B42A' } }
    ]
  })

  const pie = data.value.pie || {}
  pieChart = echarts.init(pieRef.value)
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { color: '#4E5969' } },
    series: [{
      type: 'pie',
      radius: ['40%', '62%'],
      center: ['50%', '45%'],
      label: { formatter: '{b}\n{c}' },
      data: [
        { name: '成功', value: pie.passed || 0, itemStyle: { color: '#00B42A' } },
        { name: '失败', value: pie.failed || 0, itemStyle: { color: '#F53F3F' } },
        { name: '跳过', value: pie.skipped || 0, itemStyle: { color: '#86909C' } },
        { name: '待执行', value: pie.pending || 0, itemStyle: { color: '#FF7D00' } }
      ]
    }]
  })
}

function viewReport(id) {
  router.push(`/reports/${id}`)
}

let timer = null
onMounted(() => {
  load()
  timer = setInterval(load, 15000)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  if (trendChart) trendChart.dispose()
  if (pieChart) pieChart.dispose()
})
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.chart-card { margin-bottom: 20px; }
.chart-box { height: 300px; width: 100%; }
@media (max-width: 1400px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
}
</style>
