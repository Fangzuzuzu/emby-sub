<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import http from '../utils/http'
import { Bell } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const notifications = ref<any[]>([])
const unreadCount = ref(0)

const fetchNotifications = async () => {
  try {
    const res = await http.get('/notifications/')
    notifications.value = res.data
    unreadCount.value = notifications.value.filter(n => !n.is_read).length
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  if (authStore.token) {
      fetchNotifications()
      setInterval(fetchNotifications, 60000) // Poll every minute
  }
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const markRead = async (id: number) => {
    try {
        await http.put(`/notifications/${id}/read`)
        fetchNotifications()
    } catch(e) {}
}
</script>

<template>
  <div class="navbar">
    <div class="logo">Emby订阅</div>
    <div class="menu">
       <router-link to="/">首页</router-link>
       <router-link to="/requests">我的订阅</router-link>
       <router-link v-if="authStore.user?.role === 'admin'" to="/admin">管理后台</router-link>
    </div>
    <div class="user-actions">
       <el-popover placement="bottom" :width="300" trigger="click">
        <template #reference>
          <div class="notification-icon">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0">
              <el-icon :size="20"><Bell /></el-icon>
            </el-badge>
          </div>
        </template>
        <div class="notification-list">
            <div v-if="notifications.length === 0" class="empty-notifications">暂无通知</div>
            <div v-for="note in notifications" :key="note.id" class="notification-item" :class="{ unread: !note.is_read }" @click="markRead(note.id)">
                <div class="title">{{ note.title }}</div>
                <div class="message">{{ note.message }}</div>
                <div class="time">{{ new Date(note.created_at).toLocaleString() }}</div>
            </div>
        </div>
      </el-popover>

       <el-dropdown>
        <span class="el-dropdown-link">
          {{ authStore.user?.name }}
          <el-icon class="el-icon--right"><arrow-down /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<style scoped>
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 40px;
  height: 60px;
  background-color: rgba(0,0,0,0.8);
  position: sticky;
  top: 0;
  z-index: 100;
}
.logo {
  font-weight: bold;
  font-size: 1.5rem;
  color: #e50914;
}
.menu a {
  color: #fff;
  text-decoration: none;
  margin-right: 20px;
  font-weight: 500;
}
.menu a:hover {
  color: #ccc;
}
.user-actions {
    display: flex;
    align-items: center;
    gap: 20px;
}
.notification-icon {
    cursor: pointer;
    color: #fff;
    display: flex;
    align-items: center;
}
.el-dropdown-link {
  cursor: pointer;
  color: #fff;
  display: flex;
  align-items: center;
}
.notification-list {
    max-height: 300px;
    overflow-y: auto;
}
.notification-item {
    padding: 10px;
    border-bottom: 1px solid #eee;
    cursor: pointer;
}
.notification-item:hover {
    background-color: #f5f5f5;
}
.notification-item.unread {
    background-color: #e6f7ff;
}
.title {
    font-weight: bold;
    font-size: 0.9rem;
}
.message {
    font-size: 0.8rem;
    color: #666;
}
.time {
    font-size: 0.7rem;
    color: #999;
    margin-top: 4px;
}
.empty-notifications {
    padding: 20px;
    text-align: center;
    color: #999;
}
</style>
