<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { StarFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import http from '../utils/http'

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

const props = defineProps<{
  item: MediaItem
  defaultParams?: any
}>()

const router = useRouter()
const tmdbImageBase = '/api/v1/media/tmdb-image/w300'

const getPosterUrl = (item: MediaItem) => {
  if (item.poster_path && item.poster_path.startsWith('/')) {
    return `${tmdbImageBase}${item.poster_path}`
  }
  return ''
}

const goToDetails = (item: MediaItem) => {
  let type = item.media_type || (props.defaultParams?.is_movie ? 'movie' : 'series') || 'movie'
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
      media_type: item.media_type || (props.defaultParams?.is_movie ? 'movie' : 'series') || 'movie', 
      title: item.title || item.name,
      poster_path: item.poster_path,
      overview: item.overview,
      release_date: item.release_date || item.first_air_date
    }
    
    // Simple heuristic if not explicit
    if (!payload.media_type) payload.media_type = 'movie'
    
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
</script>

<template>
  <div class="media-card" @click="goToDetails(item)">
    <div class="poster-wrapper">
      <img v-if="getPosterUrl(item)" :src="getPosterUrl(item)" loading="lazy" />
      <div v-else class="no-poster">
        <div class="no-poster-content">
          <div class="no-poster-title">{{ item.title || item.name }}</div>
          <div class="no-poster-year">{{ getYear(item) }}</div>
          <div class="no-poster-overview">{{ item.overview }}</div>
        </div>
      </div>
      
      <!-- Default Badges (Always Visible) -->
      <div class="type-tag" v-if="item.media_type || props.defaultParams?.is_movie !== undefined">
          {{ (item.media_type === 'movie' || props.defaultParams?.is_movie) ? '电影' : '剧集' }}
      </div>
      
      <div
        :class="[
          'status-tag',
          {
            'status-tag--available': item.status === 'AVAILABLE' || item.status === 'COMPLETED',
            'status-tag--approved': item.status === 'APPROVED',
            'status-tag--rejected': item.status === 'REJECTED',
            'status-tag--pending': item.status === 'PENDING'
          }
        ]"
        v-if="['APPROVED', 'AVAILABLE', 'COMPLETED', 'REJECTED', 'PENDING'].includes(item.status)"
      >
        {{
          item.status === 'REJECTED'
            ? '已拒绝'
            : (item.status === 'AVAILABLE' || item.status === 'COMPLETED' ? '已入库' : (item.status === 'PENDING' ? '待审批' : '已批准'))
        }}
      </div>
      
      <div class="rating-tag" v-if="item.vote_average">
        {{ item.vote_average.toFixed(1) }}
      </div>

      <!-- Emby/TMDB Source Tag (Bottom Left) -->
      <div class="source-tag" v-if="item.emby_id">
          Emby
      </div>
      <div class="source-tag tmdb" v-else>
          TMDB
      </div>
      <!-- Hover Overlay -->
      <div class="hover-overlay">
          <div class="hover-content">
            <div class="hover-year">{{ getYear(item) }}</div>
            <h3 class="hover-title">{{ item.title || item.name }}</h3>
            <p class="hover-overview">{{ item.overview }}</p>
          </div>
          
          <!-- Subscribe Button (Bottom Right) -->
          <div class="hover-actions">
            <div v-if="item.status === 'UNKNOWN'" class="action-btn subscribe-btn" @click="handleSubscribe(item, $event)">
              <el-icon><StarFilled /></el-icon>
            </div>
          </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.media-card {
  min-width: 150px;
  width: 150px;
  position: relative;
}
.poster-wrapper {
  position: relative;
  border-radius: 12px; 
  overflow: hidden;
  aspect-ratio: 2/3;
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
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #9ca3af;
  background: #374151;
  text-align: center;
  padding: 10px;
}
.no-poster-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100%;
  justify-content: center;
}
.no-poster-title {
  font-size: 13px;
  font-weight: bold;
  color: #e5e7eb;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.no-poster-year {
  font-size: 11px;
  color: #9ca3af;
}
.no-poster-overview {
  font-size: 9px;
  color: #9ca3af;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-top: 4px;
  line-height: 1.2;
}

/* Badges */
.type-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  background-color: #3b82f6; 
  color: white;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  z-index: 2;
}
.rating-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  background-color: #8b5cf6; 
  color: white;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  z-index: 2;
}
.status-tag {
  position: absolute;
  top: 32px;
  left: auto;
  right: 8px;
  background-color: #f59e0b; 
  color: white;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 4px;
}
.status-tag--available {
  background-color: #10b981;
}
.status-tag--approved {
  background-color: #f59e0b;
}
.status-tag--rejected {
  background-color: #ef4444;
}
.status-tag--pending {
  background-color: #fb923c;
}
.source-tag {
  position: absolute;
  bottom: 8px;
  left: 8px;
  background-color: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
  color: #fff;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 10px;
  z-index: 2;
}
.source-tag.tmdb {
  color: #90cea1;
}

.status-badge {
  position: absolute;
  top: 32px;
  right: 8px;
  background-color: #10b981; 
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  z-index: 2;
}

/* Hover Overlay */
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
  z-index: 3;
}
.poster-wrapper:hover .hover-overlay {
  opacity: 1;
}

.hover-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  margin-bottom: 30px;
}
.hover-year {
  font-size: 12px;
  color: #e5e7eb;
  margin-bottom: 2px;
}
.hover-title {
  font-size: 14px;
  font-weight: bold;
  margin: 0 0 4px 0;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
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
  backdrop-filter: blur(4px);
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
</style>

