<script setup lang="ts">
import Sidebar from './Sidebar.vue'
import Topbar from './Topbar.vue'
import { ref, onMounted, onUnmounted } from 'vue'
import { useUIStore } from '../stores/ui'

const pageContentRef = ref<HTMLElement | null>(null)
const isScrolled = ref(false)
const uiStore = useUIStore()

const handleScroll = () => {
  if (pageContentRef.value) {
    isScrolled.value = pageContentRef.value.scrollTop > 20
  }
}

onMounted(() => {
  pageContentRef.value?.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  pageContentRef.value?.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div class="app-layout">
    <Sidebar :isCollapse="uiStore.isCollapse" @toggle="uiStore.toggleSidebar" />
    <div class="main-content" :class="{ 'is-collapsed': uiStore.isCollapse }">
      <Topbar class="sticky-topbar" :class="{ 'is-scrolled': isScrolled, 'is-collapsed': uiStore.isCollapse }" />
      
      <div class="page-content" ref="pageContentRef">
        <div class="content-wrapper">
          <slot></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  background-color: #F5F5FB;
  overflow: hidden;
}

.main-content {
  flex: 1;
  margin-left: 240px; /* Width of sidebar */
  display: flex;
  flex-direction: column;
  width: calc(100% - 240px);
  position: relative;
  transition: margin-left 0.3s ease, width 0.3s ease;
  will-change: margin-left, width;
}

.main-content.is-collapsed {
  margin-left: 64px;
  width: calc(100% - 64px);
}

.sticky-topbar {
  position: fixed; /* Changed from absolute to fixed */
  top: 0;
  left: 240px; /* Start after sidebar */
  right: 0;
  width: calc(100% - 240px); /* Full width minus sidebar */
  z-index: 100;
  transition: left 0.3s ease, width 0.3s ease, background-color 0.3s ease, box-shadow 0.3s ease;
  will-change: left, width;
}

.sticky-topbar.is-collapsed {
  left: 64px;
  width: calc(100% - 64px);
}

.sticky-topbar.is-scrolled {
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  padding-top: 64px; /* Account for fixed Topbar height */
}

.content-wrapper {
  padding: 0 32px 40px;
}
</style>
