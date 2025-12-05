<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import SearchModal from '../components/SearchModal.vue'

const showSearch = ref(false)
</script>

<template>
  <div class="topbar">
    <div class="search-trigger small" @click="showSearch = true">
      <el-icon class="search-icon"><Search /></el-icon>
      <span class="placeholder">搜索</span>
      <span class="shortcut">⌘K</span>
    </div>
    
    <div class="actions">
      <!-- Place for extra icons like notifications, settings if moved from sidebar -->
    </div>

    <SearchModal v-model:visible="showSearch" />
  </div>
</template>

<style scoped>
.topbar {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 32px;
  /* Position styling is handled by parent layout now to allow overlay */
  z-index: 900;
}

.search-trigger.small {
  width: auto;
  max-width: none;
  height: 32px;
  background-color: rgba(255, 255, 255, 0.5); /* Semi-transparent */
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: 6px;
  display: flex;
  align-items: center;
  padding: 0 10px;
  cursor: pointer;
  transition: all 0.2s;
  color: #4b5563;
  gap: 8px;
}

.search-trigger.small:hover {
  background-color: rgba(255, 255, 255, 0.9);
  color: #111827;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.search-icon {
  font-size: 1rem;
}

.placeholder {
  font-size: 0.85rem;
  font-weight: 500;
}

.shortcut {
  font-size: 0.75rem;
  background: rgba(0,0,0,0.05);
  padding: 1px 5px;
  border-radius: 4px;
  color: #6b7280;
  margin-left: 4px;
}
</style>
