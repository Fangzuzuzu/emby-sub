<script setup lang="ts">
import { useAuthStore } from '../stores/auth'
import { useRouter, useRoute } from 'vue-router'
import { 
  HomeFilled, 
  List, 
  User, 
  Setting,
  Expand,
  Fold
} from '@element-plus/icons-vue'

defineProps<{
  isCollapse: boolean
}>()

const emit = defineEmits(['toggle'])

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const menuItems = [
  { index: '/', icon: HomeFilled, label: '发现' },
  { index: '/requests', icon: List, label: '我的订阅' },
]

if (authStore.user?.role === 'admin') {
  menuItems.push({ index: '/admin', icon: Setting, label: '管理后台' })
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="sidebar" :class="{ 'is-collapsed': isCollapse }">
    <div class="logo-container">
      <div class="brand" :class="{ 'hidden': isCollapse }">
        <img src="/vite.svg" alt="Logo" class="logo-icon" />
        <span class="logo-text">EmbySub</span>
      </div>
      <el-icon class="toggle-btn" @click="emit('toggle')">
        <component :is="isCollapse ? Expand : Fold" />
      </el-icon>
    </div>
    
    <div class="menu-container">
      <router-link 
        v-for="item in menuItems" 
        :key="item.index" 
        :to="item.index" 
        class="menu-item"
        :class="{ active: route.path === item.index }"
        :title="isCollapse ? item.label : ''"
      >
        <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
        <span class="menu-label" :class="{ 'hidden': isCollapse }">{{ item.label }}</span>
      </router-link>
    </div>

    <div class="user-section">
      <div class="user-info">
        <el-avatar :size="32" :icon="User" class="user-avatar" />
        <span class="user-name" :class="{ 'hidden': isCollapse }">{{ authStore.user?.name }}</span>
      </div>
      <div class="logout-btn" @click="handleLogout" :class="{ 'hidden': isCollapse }">
        退出
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background-color: #ffffff; /* White background */
  border-right: 1px solid #e5e7eb; /* Light border */
  display: flex;
  flex-direction: column;
  color: #374151; /* Dark text */
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;
  box-shadow: 2px 0 8px rgba(0,0,0,0.02);
  transition: width 0.3s ease;
  overflow: hidden; /* Critical: Prevent content from bleeding out */
  white-space: nowrap; /* Critical: Prevent text wrapping during resize */
  will-change: width; /* Optimize for animation */
}

.sidebar.is-collapsed {
  width: 64px;
}

.logo-container {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
  font-weight: bold;
  font-size: 1.5rem;
  color: #111827;
  border-bottom: 1px solid #f3f4f6;
  justify-content: space-between;
  overflow: hidden; /* Prevent text bleed */
}

.sidebar.is-collapsed .logo-container {
  justify-content: center;
  padding: 0;
}

.brand {
  display: flex;
  align-items: center;
  transition: opacity 0.2s ease, width 0.2s ease;
  opacity: 1;
  overflow: hidden;
}

.brand.hidden {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.logo-icon {
  width: 32px;
  height: 32px;
  margin-right: 12px;
  flex-shrink: 0;
}

.logo-text {
  background: linear-gradient(to right, #a855f7, #ec4899);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.toggle-btn {
  cursor: pointer;
  color: #9ca3af;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 4px;
  flex-shrink: 0;
}
.toggle-btn:hover {
  color: #a855f7;
  background-color: #f3f4f6;
}

.menu-container {
  flex: 1;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

.sidebar.is-collapsed .menu-container {
  padding: 24px 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  color: #6b7280; /* Light gray text */
  text-decoration: none;
  transition: all 0.2s;
  overflow: hidden;
}

.sidebar.is-collapsed .menu-item {
  justify-content: center;
  padding: 12px 0;
}

.menu-item:hover {
  background-color: #f3f4f6;
  color: #111827;
}

.menu-item.active {
  background-color: #f3f4f6;
  color: #a855f7; /* Purple text */
  background: linear-gradient(90deg, rgba(168, 85, 247, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%);
  border-left: 4px solid #a855f7;
}

.menu-icon {
  font-size: 1.2rem;
  margin-right: 12px;
  flex-shrink: 0;
}

.sidebar.is-collapsed .menu-icon {
  margin-right: 0;
}

.menu-label {
  font-weight: 500;
  transition: opacity 0.2s ease;
  opacity: 1;
}
.menu-label.hidden {
  opacity: 0;
  width: 0;
}

.user-section {
  padding: 16px;
  border-top: 1px solid #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  overflow: hidden;
}

.sidebar.is-collapsed .user-section {
  justify-content: center;
  padding: 16px 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.sidebar.is-collapsed .user-info {
  gap: 0;
}

.user-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
  transition: opacity 0.2s ease;
  opacity: 1;
}
.user-name.hidden {
  opacity: 0;
  width: 0;
}

.logout-btn {
  font-size: 0.8rem;
  color: #9ca3af;
  cursor: pointer;
  transition: opacity 0.2s ease;
  opacity: 1;
  flex-shrink: 0;
}
.logout-btn.hidden {
  opacity: 0;
  width: 0;
  pointer-events: none;
}
.logout-btn:hover {
  color: #ef4444;
}
</style>
