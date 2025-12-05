<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import http from '../utils/http'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: ''
})
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('username', form.value.username)
    formData.append('password', form.value.password)
    
    const res = await http.post('/auth/login', formData)
    authStore.setToken(res.data.access_token)
    authStore.setUser(res.data.user)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error('登录失败：凭证无效或 Emby 连接错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <span>Emby 媒体订阅管理</span>
        </div>
      </template>
      <el-form :model="form" label-width="0">
        <el-form-item>
          <el-input v-model="form.username" placeholder="Emby 用户名" :prefix-icon="'User'" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="'Lock'" @keyup.enter="handleLogin" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            使用 Emby 账号登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 360px;
}
.card-header {
  text-align: center;
  font-weight: bold;
  font-size: 1.2rem;
}
</style>

