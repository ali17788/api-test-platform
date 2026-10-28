<template>
  <div class="page-content">
    <h2 class="page-title">系统 AI 配置</h2>

    <div class="card config-card">
      <div class="card-title">大模型参数配置（全局生效）</div>
      <el-form :model="form" label-width="140px" v-loading="loading">
        <el-form-item label="模型选择">
          <el-select v-model="form.model" filterable allow-create default-first-option style="width:420px"
                     placeholder="请选择或输入自定义模型">
            <el-option v-for="m in models" :key="m.value" :label="m.label" :value="m.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="请输入大模型 API Key"
                    style="width:420px" />
          <span class="tip">留空则自动使用内置规则引擎生成用例</span>
        </el-form-item>
        <el-form-item label="BaseURL">
          <el-input v-model="form.base_url" placeholder="如：https://api.deepseek.com/v1" style="width:420px" />
        </el-form-item>
        <el-form-item label="AI请求超时(s)">
          <el-input-number v-model="form.timeout" :min="5" :max="600" />
        </el-form-item>
        <el-form-item>
          <el-button @click="testConn" :loading="testing" style="margin-right:12px">测试连通性</el-button>
          <el-button type="primary" @click="save" :loading="saving">保存配置</el-button>
        </el-form-item>
      </el-form>

      <el-divider />
      <div class="status-row">
        <span class="status-label">当前引擎状态：</span>
        <el-tag :type="form.api_key ? 'success' : 'warning'" effect="light">
          {{ form.api_key ? `AI 大模型（${form.model}）已配置` : '内置规则引擎（未配置 API Key）' }}
        </el-tag>
      </div>
      <div class="tip-block">
        说明：配置 API Key 后，AI 用例生成、用例文档整理将调用大模型完成；未配置时，系统使用内置规则引擎自动生成
        正向 / 反向 / 边界 / 异常四类用例，保证产品在任何环境下均可完整使用。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api'

const form = ref({ model: 'deepseek-chat', api_key: '', base_url: 'https://api.deepseek.com/v1', timeout: 60 })
const models = ref([])
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)

async function load() {
  loading.value = true
  try {
    const cfg = await api.getAiConfig()
    form.value = { model: cfg.model, api_key: cfg.api_key, base_url: cfg.base_url, timeout: cfg.timeout }
    models.value = await api.listModels()
  } catch (e) { /* ignore */ } finally { loading.value = false }
}

async function save() {
  saving.value = true
  try {
    await api.saveAiConfig(form.value)
    ElMessage.success('AI 配置保存成功，已全局生效')
  } catch (e) { /* ignore */ } finally { saving.value = false }
}

async function testConn() {
  testing.value = true
  try {
    const res = await api.testAi(form.value)
    if (res.success) ElMessage.success(res.message || '连接成功')
    else ElMessage.error(res.message || '连接失败')
  } catch (e) { /* ignore */ } finally { testing.value = false }
}

onMounted(load)
</script>

<style scoped>
.config-card { max-width: 900px; }
.tip { margin-left: 12px; font-size: 12px; color: var(--text-3); }
.status-row { display: flex; align-items: center; margin-bottom: 12px; }
.status-label { font-size: 14px; color: var(--text-2); margin-right: 10px; }
.tip-block {
  font-size: 12px; color: var(--text-3); line-height: 20px;
  background: var(--primary-light); border-radius: 6px; padding: 10px 12px;
}
</style>
