<template>
  <div class="login-page">
    <div class="login-card">
      <div class="title-area">
        <div class="big-title">AI驱动Web接口自动化测试工具</div>
        <div class="slogan">AI全自动接口测试 · 零代码自动化平台</div>
      </div>

      <div class="form-area">
        <el-form :model="form" @submit.prevent ref="formRef">
          <el-form-item>
            <el-input v-model="form.username" placeholder="请输入用户名" :prefix-icon="User" size="large" @keyup.enter="onLogin" />
            <div v-if="showErr && !form.username" class="err-tip">请输入用户名</div>
          </el-form-item>
          <el-form-item>
            <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" :prefix-icon="Lock" size="large" @keyup.enter="onLogin" />
            <div v-if="showPwdErr" class="err-tip">请输入密码</div>
          </el-form-item>
        </el-form>
      </div>

      <div class="btn-area">
        <el-button type="primary" class="login-btn" :loading="loading" @click="onLogin">
          {{ loading ? '登录中...' : '登录' }}
        </el-button>
      </div>

      <div class="demo-tip">演示账号：admin / admin123</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { api } from '../api'

const router = useRouter()
const form = ref({ username: '', password: '' })
const loading = ref(false)
const showErr = ref(false)
const showPwdErr = ref(false)

async function onLogin() {
  showErr.value = false
  showPwdErr.value = false
  if (!form.value.username) { showErr.value = true; return }
  if (!form.value.password) { showPwdErr.value = true; return }
  loading.value = true
  try {
    const data = await api.login({ username: form.value.username, password: form.value.password })
    localStorage.setItem('token', data.token)
    localStorage.setItem('username', data.username)
    localStorage.setItem('roleName', data.role_name || '')
    localStorage.setItem('menus', JSON.stringify(data.menus || []))
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    /* 错误提示已在 api 层统一处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  background: linear-gradient(135deg, #F5F7FA 0%, #E8F3FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-card {
  width: 420px;
  height: 380px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 40px 32px;
  display: flex;
  flex-direction: column;
}
.title-area { text-align: center; margin-bottom: 28px; }
.big-title { font-size: 18px; font-weight: 700; color: var(--text-1); margin-bottom: 12px; }
.slogan { font-size: 12px; color: var(--text-3); }
.form-area { flex: 1; }
.btn-area { margin-bottom: 8px; }
.login-btn { width: 100%; height: 40px; border-radius: 6px; font-size: 14px; }
.err-tip { color: var(--danger); font-size: 12px; line-height: 20px; }
.demo-tip { text-align: center; font-size: 12px; color: var(--text-3); }
:deep(.el-form-item) { margin-bottom: 20px; }
:deep(.el-form-item__error) { display: none; }
</style>
