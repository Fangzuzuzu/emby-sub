<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMediaStore } from '../stores/media'
import MediaCard from '../components/MediaCard.vue'
import LoadingDots from '../components/LoadingDots.vue'
import AppLayout from '../layout/AppLayout.vue'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const mediaStore = useMediaStore()
const category = route.params.category as string

const items = ref<any[]>([])
const loading = ref(false)
const pagesLoaded = ref<number[]>([1])
const moreLoading = ref(false)
const hasMore = ref(true)

const config = computed(() => {
  switch (category) {
    case 'movie':
      return { title: '热门电影', endpoint: '/media/trending', params: { media_type: 'movie' } }
    case 'tv':
      // Exclude anime (genre 16) from TV shows list
      return { title: '热门剧集', endpoint: '/media/trending', params: { media_type: 'tv', without_genres: '16' } }
    case 'anime':
      return { title: '动漫', endpoint: '/media/anime', params: {} }
    default:
      return { title: '未知分类', endpoint: '', params: {} }
  }
})

const loadData = async () => {
  loading.value = true
  try {
    await mediaStore.fetchMedia(config.value.endpoint, { ...config.value.params, page: 1 })
  } finally {
    loading.value = false
  }
}

const loadMore = async () => {
  if (moreLoading.value || !hasMore.value) return
  moreLoading.value = true
  const nextPage = pagesLoaded.value.length + 1
  
  try {
    // We need to fetch directly here to know if we got results, as fetchMedia returns array
    const newItems = await mediaStore.fetchMedia(config.value.endpoint, { ...config.value.params, page: nextPage })
    if (newItems && newItems.length > 0) {
      pagesLoaded.value.push(nextPage)
    } else {
      hasMore.value = false
    }
  } catch (e) {
    console.error('Load more failed', e)
  } finally {
    moreLoading.value = false
  }
}

// Combine items from all loaded pages reactively
const displayItems = computed(() => {
  const allItems: any[] = []
  for (const page of pagesLoaded.value) {
     const { items } = mediaStore.getMedia(config.value.endpoint, { ...config.value.params, page })
     allItems.push(...items)
  }
  return allItems
})

watch(displayItems, (newItems) => {
  items.value = newItems
})

onMounted(() => {
  if (config.value.endpoint) {
    loadData()
  }
})

const goBack = () => {
  router.back()
}
</script>

<template>
  <AppLayout>
    <div class="more-view">
      <div class="header">
        <div class="back-btn" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          <span>返回</span>
        </div>
        <h1>{{ config.title }}</h1>
      </div>

      <div v-if="loading && items.length === 0" class="loading-container">
        <LoadingDots />
      </div>

      <div v-else class="content-grid">
        <div v-for="item in items" :key="item.id" class="grid-item">
          <MediaCard :item="item" />
        </div>
      </div>

      <div v-if="hasMore && items.length > 0" class="load-more-container">
        <el-button :loading="moreLoading" @click="loadMore" type="primary" plain round>加载更多</el-button>
      </div>
      <div v-if="!hasMore && items.length > 0" class="no-more">
        没有更多数据了
      </div>
    </div>
  </AppLayout>
</template>

<style scoped>
.more-view {
  padding: 20px 0;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  gap: 20px;
  padding-left: 10px; /* Align with sidebar padding/search box */
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #6b7280;
  font-weight: 500;
  padding: 8px 12px;
  margin-left: -12px; /* Negative margin to align text visually with container left edge */
  border-radius: 8px;
  transition: background-color 0.2s;
}

.back-btn:hover {
  background-color: #f3f4f6;
  color: #111827;
}

h1 {
  margin: 0;
  font-size: 1.8rem;
  color: #111827;
  border-left: 5px solid #a855f7;
  padding-left: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.grid-item {
  display: flex;
  justify-content: center;
}

.loading-container {
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.load-more-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
}

.no-more {
  text-align: center;
  color: #9ca3af;
  padding: 20px;
}
</style>

