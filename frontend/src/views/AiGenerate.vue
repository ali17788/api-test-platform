<template>
  <div class="page-content">
    <h2 class="page-title">AI 用例自动生成</h2>

    <el-alert v-if="!pid" type="warning" show-icon :closable="false" style="margin-bottom:16px"
              title="请先在「项目管理」中进入一个项目。" />

    <div class="card">
      <div class="card-title">AI 生成配置</div>
      <el-form label-width="120px" class="gen-form">
        <el-form-item label="生成范围">
          <el-radio-group v-model="scope">
            <el-radio value="single">单接口生成</el-radio>
            <el-radio value="all">全项目批量生成</el-radio>
          </el-radio-group>
          <el-select v-if="scope === 'single'" v-model="apiId" placeholder="请选择接口" filterable
                     style="width:340px;margin-left:16px">
            <el-option v-for="a in apis" :key="a.id" :label="`${a.method} ${a.path} - ${a.name}`" :value="a.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="用例生成类型">
          <el-radio-group v-model="genType">
            <el-radio value="positive">仅正向用例</el-radio>
            <el-radio value="full">全量用例（正向+反向+边界+异常）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="生成引擎">
          <el-tag :type="aiReady ? 'success' : 'warning'" effect="light">
            {{ aiReady ? 'AI 大模型（' + aiModel + '）' : '内置规则引擎（未配置 AI Key）' }}
          </el-tag>
          <span class="tip-text">在「系统AI配置」中配置大模型密钥后，将自动切换为 AI 大模型智能生成</span>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="large" :loading="generating" @click="onGenerate">
            <el-icon style="margin-right:6px"><MagicStick /></el-icon>开始AI生成用例
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" v-if="generating || result">
      <div class="card-title">生成进度</div>
      <div v-if="generating" class="progress-text">当前正在生成：{{ currentApi }}</div>
      <el-progress :percentage="progress" :stroke-width="14" style="margin:12px 0" />
      <div class="progress-sub">
        已生成 {{ generatedCount }} 条用例<template v-if="targetApis.length"> / 目标接口 {{ targetApis.length }} 个</template>
        <template v-if="!generating && generatingDone"> · 生成完成</template>
      </div>

      <div v-if="result" class="result-box">
        <div class="result-title">本次生成结果</div>
        <div class="result-stats">
          <div class="rs"><span class="rs-k">接口数</span><span class="rs-v">{{ result.api_count }}</span></div>
          <div class="rs"><span class="rs-k">生成用例数</span><span class="rs-v success">{{ result.case_count }}</span></div>
          <div class="rs"><span class="rs-k">生成引擎</span><span class="rs-v">{{ result.engine }}</span></div>
        </div>
        <el-button type="primary" @click="$router.push('/cases')">前往用例管理查看</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { MagicStick } from '@element-plus/icons-vue'
import { api } from '../api'

const route = useRoute()
const pid = ref(Number(localStorage.getItem('currentProjectId') || 0))
const apis = ref([])
const scope = ref('all')
const apiId = ref(null)
const genType = ref('full')
const generating = ref(false)
const generatingDone = ref(false)
const progress = ref(0)
const currentApi = ref('—')
const generatedCount = ref(0)
const result = ref(null)
const aiReady = ref(false)
const aiModel = ref('')

const targetApis = computed(() => {
  if (scope.value === 'single') {
    const a = apis.value.find((x) => x.id === apiId.value)
    return a ? [a] : []
  }
  return apis.value
})

async function load() {
  if (!pid.value) return
  try {
    apis.value = await api.listAllApis(pid.value)
    if (apis.value.length && !apiId.value) apiId.value = apis.value[0].id
  } catch (e) { /* ignore */ }
  try {
    const cfg = await api.getAiConfig()
    aiReady.value = !!cfg.configured
    aiModel.value = cfg.model
  } catch (e) { /* ignore */ }
}

async function onGenerate() {
  if (!pid.value) { ElMessage.warning('请先进入项目'); return }
  if (!targetApis.value.length) { ElMessage.warning('当前没有可生成用例的接口'); return }
  generating.value = true
  generatingDone.value = false
  result.value = null
  progress.value = 0
  generatedCount.value = 0
  let total = 0
  try {
    // 逐接口生成，实现真实进度反馈
    for (let i = 0; i < targetApis.value.length; i++) {
      const a = targetApis.value[i]
      currentApi.value = `${a.method} ${a.path} · ${a.name}`
      const res = await api.generateCases({ project_id: pid.value, scope: 'single', api_id: a.id, gen_type: genType.value })
      total += res.case_count
      generatedCount.value = total
      progress.value = Math.round(((i + 1) / targetApis.value.length) * 100)
    }
    result.value = { api_count: targetApis.value.length, case_count: total, engine: aiReady.value ? 'AI 大模型' : '内置规则引擎（降级）' }
    ElMessage.success(`成功生成 ${total} 条用例`)
  } catch (e) { /* ignore */ } finally {
    generating.value = false
    generatingDone.value = true
  }
}

onMounted(() => {
  pid.value = Number(localStorage.getItem('currentProjectId') || 0)
  const qid = route.query.api_id
  if (qid) { scope.value = 'single'; apiId.value = Number(qid) }
  load()
})
</script>

<style scoped>
.gen-form { max-width: 900px; }
.tip-text { margin-left: 12px; font-size: 12px; color: var(--text-3); }
.progress-text { font-size: 14px; color: var(--text-2); }
.progress-sub { font-size: 12px; color: var(--text-3); }
.result-box { margin-top: 20px; border-top: 1px solid var(--border); padding-top: 16px; }
.result-title { font-size: 14px; font-weight: 600; color: var(--text-1); margin-bottom: 12px; }
.result-stats { display: flex; gap: 40px; margin-bottom: 16px; }
.rs { display: flex; flex-direction: column; gap: 4px; }
.rs-k { font-size: 12px; color: var(--text-3); }
.rs-v { font-size: 20px; font-weight: 700; color: var(--text-1); }
.rs-v.success { color: var(--success); }
</style>
