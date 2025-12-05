<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning, StarFilled, ArrowLeft, ArrowRight, MoreFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { useMediaStore } from '../stores/media'
import LoadingDots from './LoadingDots.vue'
import http from '../utils/http'

const props = defineProps<{
  title: string
  endpoint: string
  params?: any
}>()

const router = useRouter()
const mediaStore = useMediaStore()

interface MediaItem {
  id: number
  title?: string
  name?: string
  poster_path: string | null
  media_type?: string
  release_date?: string
  first_air_date?: string
  overview?: string
  status: string
  emby_id?: string
  vote_average?: number
}

const items = ref<MediaItem[]>([])
const loading = ref(true)
const error = ref('')
const scrollContainer = ref<HTMLElement | null>(null)
const showLeftArrow = ref(false)
const showRightArrow = ref(true)
const pagesLoaded = ref<number[]>([1])

const tmdbImageBase = '/api/v1/media/tmdb-image/w300'

const updateScrollArrows = () => {
  if (!scrollContainer.value) return
  const { scrollLeft, scrollWidth, clientWidth } = scrollContainer.value
  showLeftArrow.value = scrollLeft > 0
  showRightArrow.value = scrollLeft < scrollWidth - clientWidth - 10
}

const loadData = async () => {
  pagesLoaded.value = [1] // Reset pages
  loading.value = true
  error.value = ''
  
  // Ensure we call fetchMedia for reactivity
  await mediaStore.fetchMedia(props.endpoint, { ...props.params, page: 1 })
  
  loading.value = false
  setTimeout(updateScrollArrows, 100)
}

const handleLoadMore = () => {
  let category = ''
  if (props.endpoint.includes('anime')) {
    category = 'anime'
  } else if (props.params?.media_type === 'movie') {
    category = 'movie'
  } else if (props.params?.media_type === 'tv') {
    category = 'tv'
  }
  
  if (category) {
    router.push({ name: 'more-media', params: { category } })
  }
}

// Use computed for items to be reactive to store updates across ALL loaded pages
const displayItems = computed(() => {
  const allItems: MediaItem[] = []
  for (const page of pagesLoaded.value) {
     const { items } = mediaStore.getMedia(props.endpoint, { ...props.params, page })
     allItems.push(...items)
  }
  return allItems
})

// Watch displayItems to update local `items` ref
watch(displayItems, (newItems) => {
  items.value = newItems
  setTimeout(updateScrollArrows, 100)
})

onMounted(() => {
  loadData()
})

watch(
  () => props.params,
  () => {
    loadData()
  },
  { deep: true }
)

watch(scrollContainer, (el, oldEl) => {
  oldEl?.removeEventListener('scroll', updateScrollArrows)
  el?.addEventListener('scroll', updateScrollArrows)
})

const getPosterUrl = (item: MediaItem) => {
  if (item.poster_path && item.poster_path.startsWith('/')) {
    return `${tmdbImageBase}${item.poster_path}`
  }
  return ''
}

const goToDetails = (item: MediaItem) => {
  let type = item.media_type || (props.params?.is_movie ? 'movie' : 'series') || 'movie'
  if (type === 'series') type = 'tv'
  router.push({ name: 'details', params: { type, id: item.id } })
}

const handleSubscribe = async (item: MediaItem, event: Event) => {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(
      `确定要订阅 "${item.title || item.name}" 吗?`,
      '确认订阅',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    const payload = {
      tmdb_id: String(item.id),
      media_type: item.media_type || (props.params?.is_movie ? 'movie' : 'series') || 'movie',
      title: item.title || item.name,
      poster_path: item.poster_path,
      overview: item.overview,
      release_date: item.release_date || item.first_air_date,
    }

    await http.post('/requests/', payload)
    ElMessage.success('订阅申请提交成功')
    item.status = 'PENDING'
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('提交失败')
      console.error(e)
    }
  }
}

const getYear = (item: MediaItem) => {
  const date = item.release_date || item.first_air_date
  return date ? new Date(date).getFullYear() : ''
}

const scrollLeft = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: -600, behavior: 'smooth' })
}

const scrollRight = () => {
  if (!scrollContainer.value) return
  scrollContainer.value.scrollBy({ left: 600, behavior: 'smooth' })
}
</script>

<template>
  <div class="media-slider">
    <div class="header-row">
      <h2>{{ props.title }}</h2>
      <div class="more-btn" v-if="!endpoint.includes('latest')" @click="handleLoadMore">
        <span>更多</span>
        <el-icon><MoreFilled /></el-icon>
      </div>
    </div>

    <div v-if="error" class="error-state">
      <el-icon :size="24"><Warning /></el-icon>
      <span>{{ error }}</span>
      <el-button size="small" @click="loadData">重试</el-button>
    </div>

    <div v-else-if="!loading && items.length === 0" class="empty-state">
      暂无数据
    </div>

    <div v-else-if="loading" class="slider-container loading-container">
      <LoadingDots />
    </div>

    <div v-else class="slider-wrapper">
      <div
        v-if="showLeftArrow"
        class="scroll-arrow left-arrow"
        @click="scrollLeft"
      >
        <el-icon><ArrowLeft /></el-icon>
      </div>

      <div
        class="slider-container"
        ref="scrollContainer"
        @scroll="updateScrollArrows"
      >
        <div
          v-for="item in items"
          :key="item.id"
          class="media-card"
          @click="goToDetails(item)"
        >
          <div class="poster-wrapper">
            <img v-if="getPosterUrl(item)" :src="getPosterUrl(item)" loading="lazy" />
            <div v-else class="no-poster">
              <div class="no-poster-content">
                <div class="no-poster-title">{{ item.title || item.name }}</div>
                <div class="no-poster-year">{{ getYear(item) }}</div>
              </div>
            </div>

            <div class="type-tag" v-if="item.media_type || props.params?.is_movie !== undefined">
              {{ (item.media_type === 'movie' || props.params?.is_movie) ? '电影' : '剧集' }}
            </div>

            <div class="rating-tag" v-if="item.vote_average">
              {{ item.vote_average.toFixed(1) }}
            </div>

            <div
              class="status-badge"
              :class="{
                'status-approved': item.status === 'APPROVED',
                'status-pending-text': item.status === 'PENDING',
                'status-icon': item.status === 'AVAILABLE' || item.status === 'COMPLETED',
                'status-available': item.status === 'AVAILABLE' || item.status === 'COMPLETED',
                'status-rejected': item.status === 'REJECTED'
              }"
              v-if="item.status !== 'UNKNOWN'"
            >
              <template v-if="item.status === 'APPROVED'">已审批</template>
              <template v-else-if="item.status === 'PENDING'">待审批</template>
              <template v-else-if="item.status === 'REJECTED'">已拒绝</template>
              <template v-else-if="item.status === 'AVAILABLE' || item.status === 'COMPLETED'">已入库</template>
            </div>

            <div class="source-tag" v-if="item.emby_id">Emby</div>
            <div class="source-tag tmdb" v-else>TMDB</div>

            <div class="status-badge-circle" v-if="item.status === 'PENDING'">
              <el-icon><Timer /></el-icon>
            </div>

            <div class="hover-overlay">
              <div class="hover-content">
                <div class="hover-year">{{ getYear(item) }}</div>
                <h3 class="hover-title">{{ item.title || item.name }}</h3>
                <p class="hover-overview">{{ item.overview }}</p>
              </div>

              <div class="hover-actions">
                <div
                  v-if="item.status === 'UNKNOWN'"
                  class="action-btn subscribe-btn"
                  @click="handleSubscribe(item, $event)"
                >
                  <el-icon><StarFilled /></el-icon>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="showRightArrow"
        class="scroll-arrow right-arrow"
        @click="scrollRight"
      >
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<style scoped>
.media-slider {
  margin: 10px 0;
}
.header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-right: 10px;
}
h2 {
  font-size: 1.2rem;
  padding-left: 10px;
  border-left: 4px solid #a855f7;
  color: #433F4B;
  margin: 0;
}
.more-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #a855f7; /* Purple color as requested */
  font-size: 0.9rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
  font-weight: 600;
}
.more-btn:hover {
  background-color: rgba(168, 85, 247, 0.1);
}
.slider-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}
.slider-container {
  display: flex;
  overflow-x: auto;
  gap: 15px;
  padding-top: 15px;
  padding-bottom: 15px;
  scroll-behavior: smooth;
  scrollbar-width: none;
}
.slider-container::-webkit-scrollbar {
  display: none;
}
.media-card {
  min-width: 150px;
  width: 150px;
  position: relative;
}
.poster-wrapper {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  aspect-ratio: 2 / 3;
  background: #e5e7eb;
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.3s ease;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  z-index: 1;
}
.poster-wrapper:hover {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  cursor: pointer;
  z-index: 10;
}
.poster-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.no-poster {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #374151;
  color: #9ca3af;
  padding: 10px;
  text-align: center;
}
.type-tag,
.rating-tag,
.status-badge,
.source-tag {
  position: absolute;
  z-index: 2;
  color: white;
  font-size: 11px;
  font-weight: bold;
  border-radius: 6px;
  padding: 2px 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.type-tag {
  top: 8px;
  left: 8px;
  background-color: #3b82f6;
}
.rating-tag {
  top: 8px;
  right: 8px;
  background-color: #8b5cf6;
}
.status-badge {
  top: 32px;
  right: 8px;
  background-color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
}
.status-badge.status-approved,
.status-badge.status-pending-text,
.status-badge.status-rejected,
.status-badge.status-available {
  border-radius: 999px;
  min-height: 20px;
}
.status-badge.status-approved {
  background-color: #10b981;
}
.status-badge.status-available {
  background-color: #10b981;
}
.status-badge.status-pending-text {
  background-color: #fb923c;
}
.status-badge.status-rejected {
  background-color: #b91c1c;
}
.source-tag {
  bottom: 8px;
  left: 8px;
  background-color: rgba(0,0,0,0.6);
  padding: 2px 4px;
  font-size: 10px;
}
.source-tag.tmdb {
  color: #90cea1;
}
.status-badge-circle {
  position: absolute;
  top: 32px;
  right: 8px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #10b981;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
.scroll-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(255,255,255,0.8);
  backdrop-filter: blur(4px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #333;
  transition: all 0.3s ease;
  opacity: 0;
  z-index: 20; /* Ensure arrows are above hovered posters (z-index: 10) */
}
.slider-wrapper:hover .scroll-arrow {
  opacity: 1;
}
.left-arrow { left: 10px; }
.right-arrow { right: 10px; }
.hover-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.6) 60%, rgba(0,0,0,0.2) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 12px;
  color: white;
}
.poster-wrapper:hover .hover-overlay {
  opacity: 1;
}
.hover-title {
  font-size: 14px;
  font-weight: bold;
  margin: 0 0 4px 0;
}
.hover-overview {
  font-size: 10px;
  color: #d1d5db;
  margin: 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.hover-actions {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  gap: 8px;
}
.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background-color: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.action-btn:hover {
  background-color: white;
  color: #111827;
  transform: scale(1.1);
}
.subscribe-btn:hover {
  color: #f59e0b;
}
.error-state,
.empty-state {
  padding: 20px;
  text-align: center;
  color: #6b7280;
}
</style>

