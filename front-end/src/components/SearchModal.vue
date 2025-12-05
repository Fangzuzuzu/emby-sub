<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Clock, Close } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits(['update:visible'])

const router = useRouter()
const searchQuery = ref('')
const recentSearches = ref<string[]>([])

// Load recent searches from localStorage
onMounted(() => {
  const stored = localStorage.getItem('recent_searches')
  if (stored) {
    recentSearches.value = JSON.parse(stored)
  }
})

const close = () => {
  emit('update:visible', false)
}

const handleSearch = (query: string) => {
  if (!query.trim()) return
  
  // Add to history
  const history = new Set([query, ...recentSearches.value])
  recentSearches.value = Array.from(history).slice(0, 5) // Keep top 5
  localStorage.setItem('recent_searches', JSON.stringify(recentSearches.value))
  
  close()
  router.push({ name: 'search', query: { q: query } })
}

// const clearHistory = () => {
//   recentSearches.value = []
//   localStorage.removeItem('recent_searches')
// }
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    :show-close="false"
    width="600px"
    class="search-modal"
    align-center
    destroy-on-close
  >
    <div class="search-container">
      <div class="input-wrapper">
        <el-icon class="search-icon"><Search /></el-icon>
        <input 
          ref="searchInput"
          v-model="searchQuery" 
          placeholder="搜索电影、电视剧..." 
          class="search-input"
          @keyup.enter="handleSearch(searchQuery)"
          autofocus
        />
        <el-icon class="close-icon" v-if="searchQuery" @click="searchQuery = ''"><Close /></el-icon>
      </div>
      
      <div class="recent-section" v-if="recentSearches.length">
        <div class="section-header">
          <span>最近搜索</span>
          <!-- <span class="clear-btn" @click="clearHistory">清除</span> -->
        </div>
        <div class="tags">
          <div 
            v-for="tag in recentSearches" 
            :key="tag" 
            class="search-tag"
            @click="handleSearch(tag)"
          >
            <el-icon><Clock /></el-icon>
            {{ tag }}
          </div>
        </div>
      </div>
    </div>
  </el-dialog>
</template>

<style>
/* Global override for dialog to match design */
.search-modal .el-dialog__header {
  display: none;
}
.search-modal .el-dialog__body {
  padding: 0;
}
.search-modal {
  border-radius: 12px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
</style>

<style scoped>
.search-container {
  padding: 20px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #f3f4f6;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 20px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.input-wrapper:focus-within {
  border-color: #a855f7;
  background: #fff;
}

.search-icon {
  font-size: 1.2rem;
  color: #9ca3af;
  margin-right: 12px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  color: #1f2937;
  outline: none;
}

.close-icon {
  cursor: pointer;
  color: #9ca3af;
}

.section-header {
  font-size: 0.9rem;
  color: #6b7280;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.search-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #a855f7;
  color: #fff;
  border-radius: 20px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.search-tag:hover {
  opacity: 0.9;
}
</style>

