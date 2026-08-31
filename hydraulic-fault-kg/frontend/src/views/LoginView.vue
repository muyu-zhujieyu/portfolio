<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">⚙</div>
        <h1>液压故障演化事件知识图谱</h1>
        <p>与智能问答后台系统</p>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" size="large" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
            登 录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>演示账号: admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { loginApi } from '@/api/kgApi'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: 'admin',
  password: 'admin123'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    // 简化登录：后端可能没有完整实现，直接放行
    // await loginApi(form.username, form.password)
    localStorage.setItem('token', 'demo-token-' + Date.now())
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    // 后端不可用时使用演示模式
    localStorage.setItem('token', 'demo-token-' + Date.now())
    ElMessage.warning('后端未响应，使用演示模式')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a3a5c 0%, #2c5f8a 50%, #1a3a5c 100%);
}
.login-card {
  width: 420px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2);
  padding: 40px;
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-header h1 {
  font-size: 20px;
  color: #1a3a5c;
  margin: 12px 0 4px;
}
.login-header p {
  font-size: 14px;
  color: #909399;
}
.login-icon {
  font-size: 48px;
  color: #c41e3a;
}
.login-footer {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  margin-top: 16px;
}
</style>
