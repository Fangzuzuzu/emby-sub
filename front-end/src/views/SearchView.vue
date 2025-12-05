<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import MediaCard from '../components/MediaCard.vue'
import AppLayout from '../layout/AppLayout.vue'
import LoadingDots from '../components/LoadingDots.vue'
import { useMediaStore } from '../stores/media'
import { Warning } from '@element-plus/icons-vue'

const route = useRoute()
const mediaStore = useMediaStore()

const items = ref<any[]>([])
const loading = ref(true)
const error = ref('')

const loadData = async () => {
  const query = route.query.q as string
  if (!query) return

  loading.value = true
  error.value = ''
  items.value = []

  try {
    const data = await mediaStore.fetchMedia('/media/search', { query })
    items.value = data
  } catch (e) {
    error.value = '搜索失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
watch(() => route.query.q, loadData)
</script>

<template>
  <AppLayout>
    <div class="content-container">
      <h2 v-if="route.query.q">"{{ route.query.q }}" 的搜索结果</h2>
      
      <div v-if="loading" class="loading-container">
         <LoadingDots />
      </div>

      <div v-else-if="error" class="error-state">
        <el-icon :size="24"><Warning /></el-icon>
        <span>{{ error }}</span>
        <el-button size="small" @click="loadData">重试</el-button>
      </div>

      <div v-else-if="items.length === 0" class="empty-search">
        <span v-if="route.query.q">未找到相关结果</span>
        <span v-else>请输入关键词进行搜索</span>
      </div>

      <div v-else class="grid-container">
        <MediaCard 
          v-for="item in items" 
          :key="item.id" 
          :item="item" 
        />
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.content-container {
  padding: 80px 40px 40px;
}
h2 {
  font-size: 1.5rem;
  margin-bottom: 24px;
  color: #374151;
}
.grid-container {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: flex-start;
}
.loading-container {
  display: flex;
  justify-content: center;
  padding: 40px;
}
.empty-search, .error-state {
  text-align: center;
  margin-top: 40px;
  color: #6b7280;
  font-size: 1.1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
</style>

