<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '../utils/http'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, UserFilled, Check, Picture, ArrowDown, ArrowUp, Link } from '@element-plus/icons-vue'
import AppLayout from '../layout/AppLayout.vue'
import LoadingDots from '../components/LoadingDots.vue'
import HeartIcon from '../components/HeartIcon.vue'
import { useMediaStore } from '../stores/media'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const mediaType = route.params.type as string
const id = route.params.id as string

const mediaStore = useMediaStore()
const authStore = useAuthStore()
const details = ref<any>(null)
const loading = ref(true)
const actionLoading = ref(false)
const tmdbImageBase = '/api/v1/media/tmdb-image/original'
const tmdbPosterBase = '/api/v1/media/tmdb-image/w500'
const tmdbStillBase = '/api/v1/media/tmdb-image/w300'
const posterRef = ref<HTMLElement | null>(null)
const posterHeight = ref(0)
const castTrackRef = ref<HTMLElement | null>(null)

// Season accordion state
const expandedSeasons = ref<Set<number>>(new Set())
const seasonsData = ref<Record<number, any>>({})
const seasonsLoading = ref<Record<number, boolean>>({})

const updatePosterHeight = () => {
  if (posterRef.value) {
    posterHeight.value = posterRef.value.offsetHeight
  }
}

const fetchDetails = async () => {
  loading.value = true
  try {
    const res = await http.get(`/media/${mediaType}/${id}`)
    details.value = res.data
    await nextTick()
    updatePosterHeight()
  } catch (e) {
    ElMessage.error('加载详情失败')
  } finally {
    loading.value = false
  }
}

const toggleSeason = async (seasonNumber: number) => {
  if (expandedSeasons.value.has(seasonNumber)) {
    expandedSeasons.value.delete(seasonNumber)
  } else {
    expandedSeasons.value.add(seasonNumber)
    if (!seasonsData.value[seasonNumber]) {
      await fetchSeasonDetails(seasonNumber)
    }
  }
}

const fetchSeasonDetails = async (seasonNumber: number) => {
  if (mediaType !== 'tv') return
  
  seasonsLoading.value = { ...seasonsLoading.value, [seasonNumber]: true }
  try {
    const res = await http.get(`/media/tv/${id}/season/${seasonNumber}`)
    seasonsData.value = { ...seasonsData.value, [seasonNumber]: res.data }
  } catch (e) {
    console.error('Failed to fetch season details', e)
  } finally {
    seasonsLoading.value = { ...seasonsLoading.value, [seasonNumber]: false }
  }
}

onMounted(() => {
  fetchDetails()
  window.addEventListener('resize', updatePosterHeight)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updatePosterHeight)
})

const backdropUrl = computed(() => {
  if (details.value?.backdrop_path) {
    return `${tmdbImageBase}${details.value.backdrop_path}`
  }
  return ''
})

const posterUrl = computed(() => {
  if (details.value?.poster_path) {
    return `${tmdbPosterBase}${details.value.poster_path}`
  }
  return ''
})

const year = computed(() => {
  const date = details.value?.release_date || details.value?.first_air_date
  return date ? new Date(date).getFullYear() : ''
})

const statusText = computed(() => {
  return details.value?.status || 'Released'
})

const videoInfo = computed(() => details.value?.media_info?.video)

const formatBitrate = (bitrate?: number | null) => {
  if (!bitrate) return '--'
  return `${(bitrate / 1000000).toFixed(1)} Mbps`
}

const formatFrameRate = (rate?: number | string | null) => {
  if (!rate) return '--'
  const num = typeof rate === 'string' ? parseFloat(rate) : rate
  return num ? `${Number(num).toFixed(3).replace(/\.?0+$/, '')} fps` : '--'
}

const formatResolution = (info: any) => {
  if (!info?.width || !info?.height) return '--'
  return `${info.width} x ${info.height}`
}

const isAvailable = computed(() => details.value?.status === 'AVAILABLE' || details.value?.status === 'COMPLETED')

const isPendingRequestForCurrentUser = computed(() => {
  return details.value?.status === 'PENDING' && details.value?.request_user_id === authStore.user?.id
})

const isPendingRequestForOtherUser = computed(() => {
  return details.value?.status === 'PENDING' && details.value?.request_user_id !== authStore.user?.id
})

// Main subscription (whole show) logic
const handleSubscribe = async () => {
  if (!details.value) return
  try {
    await ElMessageBox.confirm(
      `确定要订阅 "${details.value.title || details.value.name}" 吗?`,
      '确认订阅',
      { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info' }
    )
    actionLoading.value = true

    const payload = {
      tmdb_id: String(details.value.id),
      media_type: mediaType,
      title: details.value.title || details.value.name,
      poster_path: details.value.poster_path,
      overview: details.value.overview,
      release_date: details.value.release_date || details.value.first_air_date
    }

    await http.post('/requests/', payload)
    ElMessage.success('订阅申请提交成功')
    details.value.status = 'PENDING'
    details.value.media_info = null
    mediaStore.updateMediaStatus(details.value.id, 'PENDING')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('提交失败')
  } finally {
    actionLoading.value = false
  }
}

const handleCancelSubscribe = async () => {
  if (!details.value) return
  try {
    await ElMessageBox.confirm(
      `确定要取消 "${details.value.title || details.value.name}" 的订阅申请吗?`,
      '取消订阅',
      { confirmButtonText: '确认', cancelButtonText: '保留', type: 'warning' }
    )
    actionLoading.value = true
    await http.delete(`/requests/${details.value.id}`)
    ElMessage.success('已取消订阅申请')
    details.value.status = 'UNKNOWN'
    details.value.media_info = null
    mediaStore.updateMediaStatus(details.value.id, 'UNKNOWN')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('取消订阅失败')
  } finally {
    actionLoading.value = false
  }
}

// Season Subscription Logic
const isSeasonSubscribed = (season: any) => {
  return ['PENDING', 'APPROVED', 'AVAILABLE', 'COMPLETED'].includes(season.subscription_status)
}

const toggleSeasonSubscription = async (season: any) => {
  if (isSeasonSubscribed(season)) {
    // Cancel
    try {
      await ElMessageBox.confirm(
        `确定要取消订阅 ${season.name} 吗?`,
        '取消订阅',
        { confirmButtonText: '确认', cancelButtonText: '保留', type: 'warning' }
      )
      // Assuming DELETE supports query param for season
      await http.delete(`/requests/${details.value.id}`, { params: { season_number: season.season_number } })
      season.subscription_status = null
      ElMessage.success('已取消该季订阅')
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('取消失败')
    }
  } else {
    // Subscribe
    try {
      await ElMessageBox.confirm(
        `确定要订阅 ${season.name} 吗?`,
        '确认订阅',
        { confirmButtonText: '确认', cancelButtonText: '取消', type: 'info' }
      )
      
      const payload = {
        tmdb_id: String(details.value.id),
        media_type: mediaType,
        title: details.value.title || details.value.name,
        poster_path: details.value.poster_path,
        overview: details.value.overview,
        release_date: details.value.release_date || details.value.first_air_date,
        specific_season: season.season_number
      }
      
      await http.post('/requests/', payload)
      season.subscription_status = 'PENDING'
      ElMessage.success('该季订阅申请提交成功')
    } catch (e) {
        if (e !== 'cancel') ElMessage.error('提交失败')
    }
  }
}

const openLink = (type: 'tmdb' | 'imdb') => {
  if (type === 'tmdb') {
    window.open(`https://www.themoviedb.org/${mediaType}/${details.value.id}`, '_blank')
  } else if (type === 'imdb' && details.value.external_ids?.imdb_id) {
    window.open(`https://www.imdb.com/title/${details.value.external_ids.imdb_id}`, '_blank')
  }
}

const scrollCast = (offset: number) => {
  if (!castTrackRef.value) return
  castTrackRef.value.scrollBy({ left: offset, behavior: 'smooth' })
}

const router = useRouter()
const goToPerson = (personId: number) => {
  router.push({ name: 'person', params: { id: personId } })
}

// Helper to determine season status
const getSeasonStatus = (season: any) => {
  const total = season.episode_count || 0
  const existing = season.existing_episode_count || 0
  
  if (existing === 0) return 'MISSING'
  if (existing >= total) return 'FULL'
  return 'PARTIAL'
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'FULL': return '已入库'
    case 'PARTIAL': return '部分缺失'
    case 'MISSING': return '缺失'
    default: return ''
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'FULL': return 'status-full'
    case 'PARTIAL': return 'status-partial'
    case 'MISSING': return 'status-missing'
    default: return ''
  }
}
</script>

<template>
  <AppLayout>
    <div class="details-view" v-if="details && !loading">
      <!-- Header Section -->
      <div class="header-section">
        <div class="backdrop-container" :style="{ backgroundImage: `url(${backdropUrl})` }">
          <div class="gradient-overlay"></div>
        </div>
        
        <div class="header-content container">
          <div class="poster-column">
            <div class="poster-wrapper" ref="posterRef">
              <img :src="posterUrl" alt="Poster" class="main-poster" @load="updatePosterHeight" />
            </div>
          </div>

          <div class="info-column">
            <h1 class="title">
              {{ details.title || details.name }}
              <span class="year">({{ year }})</span>
            </h1>
            <div class="tagline" v-if="details.tagline">{{ details.tagline }}</div>
            <div class="overview-section">
              <h3>简介</h3>
              <p>{{ details.overview }}</p>
            </div>
            <div class="crew-grid">
               <div class="crew-item" v-for="crew in details.credits?.crew?.slice(0, 6)" :key="crew.id">
                  <div class="role">{{ crew.job }}</div>
                  <div class="name">{{ crew.name }}</div>
               </div>
            </div>
            <div class="external-links">
              <el-button round size="small" @click="openLink('tmdb')">
                <el-icon class="el-icon--left"><Link /></el-icon> TheMovieDb
              </el-button>
              <el-button round size="small" @click="openLink('imdb')" v-if="details.external_ids?.imdb_id">
                <el-icon class="el-icon--left"><Link /></el-icon> IMDb
              </el-button>
            </div>
          </div>

          <div class="sidebar-column">
            <el-card class="info-card" :style="{ height: posterHeight ? posterHeight + 'px' : 'auto' }">
              <div class="action-area">
                <template v-if="isAvailable">
                  <el-tooltip v-if="videoInfo" placement="top" effect="dark" popper-class="media-info-tooltip">
                    <template #content>
                      <div class="media-info-tooltip-content">
                        <div class="tooltip-title">本地媒体信息</div>
                        <ul>
                          <li><span>标题</span><span>{{ videoInfo.title || '--' }}</span></li>
                          <li><span>编解码器</span><span>{{ videoInfo.codec || '--' }}</span></li>
                          <li><span>分辨率</span><span>{{ formatResolution(videoInfo) }}</span></li>
                          <li><span>帧率</span><span>{{ formatFrameRate(videoInfo.frame_rate) }}</span></li>
                          <li><span>码率</span><span>{{ formatBitrate(videoInfo.bitrate) }}</span></li>
                          <li><span>视频范围</span><span>{{ videoInfo.video_range || '--' }}</span></li>
                        </ul>
                      </div>
                    </template>
                    <span class="tooltip-trigger">
                      <el-button type="warning" size="large" style="width: 100%" icon="Star" disabled>已入库</el-button>
                    </span>
                  </el-tooltip>
                  <!-- If available but no media info (e.g. just approved/completed but Emby scan pending), just show button -->
                  <el-button v-else type="warning" size="large" style="width: 100%" icon="Star" disabled>已入库</el-button>
                </template>
                <template v-else-if="isPendingRequestForCurrentUser">
                  <el-button 
                    type="warning" 
                    size="large" 
                    style="width: 100%" 
                    icon="Star" 
                    :loading="actionLoading" 
                    @click="handleCancelSubscribe"
                  >
                    取消订阅
                  </el-button>
                </template>
                <template v-else-if="isPendingRequestForOtherUser">
                  <el-button 
                    type="info" 
                    size="large" 
                    style="width: 100%" 
                    icon="Timer" 
                    disabled
                  >
                    待审批
                  </el-button>
                </template>
                <template v-else>
                  <el-button 
                    type="warning" 
                    size="large" 
                    style="width: 100%" 
                    icon="Star" 
                    :loading="actionLoading" 
                    @click="handleSubscribe"
                  >
                    订阅
                  </el-button>
                </template>
              </div>
              
              <div class="info-list">
                <div class="info-item rating-item" v-if="details.vote_average">
                   <div class="stars">
                     <el-rate v-model="details.vote_average" disabled show-score text-color="#ff9900" score-template="{value}" :max="10" />
                   </div>
                </div>
                <div class="info-item">
                  <div class="label">ID</div>
                  <div class="value">{{ details.id }}</div>
                </div>
                <div class="info-item">
                  <div class="label">原始标题</div>
                  <div class="value">{{ details.original_title || details.original_name }}</div>
                </div>
                <div class="info-item">
                  <div class="label">状态</div>
                  <div class="value">{{ statusText }}</div>
                </div>
                <div class="info-item">
                  <div class="label">上映日期</div>
                  <div class="value">{{ details.release_date || details.first_air_date }}</div>
                </div>
                <div class="info-item">
                  <div class="label">原始语言</div>
                  <div class="value">{{ details.original_language?.toUpperCase() }}</div>
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>

      <!-- TV Seasons Accordion -->
      <div class="container content-section" v-if="mediaType === 'tv' && details.seasons?.length > 0">
        <div class="section seasons-section">
          <h2>季</h2>
          <div class="seasons-list">
            <div 
              v-for="season in details.seasons" 
              :key="season.id"
              class="season-accordion-item"
              :class="{ expanded: expandedSeasons.has(season.season_number) }"
            >
              <!-- Accordion Header -->
              <div class="season-header" @click="toggleSeason(season.season_number)">
                <div class="season-info-left">
                  <span class="season-name">{{ season.name }}</span>
                  <span class="season-count">{{ season.episode_count }}集</span>
                </div>
                <div class="season-info-right">
                  <span class="season-status" :class="getStatusClass(getSeasonStatus(season))">
                    {{ getStatusLabel(getSeasonStatus(season)) }}
                  </span>
                  
                  <!-- Subscription Heart -->
                  <div 
                    class="heart-wrapper" 
                    @click.stop="toggleSeasonSubscription(season)"
                    title="订阅此季"
                  >
                    <component 
                      :is="HeartIcon" 
                      class="season-heart" 
                      :class="{ active: isSeasonSubscribed(season) }" 
                    />
                  </div>

                  <el-icon class="expand-icon">
                    <ArrowUp v-if="expandedSeasons.has(season.season_number)" />
                    <ArrowDown v-else />
                  </el-icon>
                </div>
              </div>

              <!-- Accordion Content (Episodes) -->
              <div v-if="expandedSeasons.has(season.season_number)" class="season-content">
                <div v-if="seasonsLoading[season.season_number]" class="season-loading">
                  <LoadingDots />
                </div>
                <div v-else-if="seasonsData[season.season_number]?.episodes" class="episodes-list">
                  <div 
                    v-for="episode in seasonsData[season.season_number].episodes" 
                    :key="episode.id" 
                    class="episode-card"
                  >
                    <div class="episode-content">
                      <div class="episode-header">
                        <span class="episode-number">{{ episode.episode_number }} - {{ episode.name }}</span>
                        <span class="episode-date" v-if="episode.air_date">{{ episode.air_date }}</span>
                        <el-icon v-if="episode.is_in_library" class="aired-icon"><Check /></el-icon>
                      </div>
                      <p class="episode-overview" v-if="episode.overview">{{ episode.overview }}</p>
                      <p class="episode-overview empty" v-else>暂无简介</p>
                    </div>
                    
                    <div class="episode-still" v-if="episode.still_path">
                      <img :src="`${tmdbStillBase}${episode.still_path}`" loading="lazy" />
                    </div>
                    <div class="episode-still no-image" v-else>
                      <el-icon><Picture /></el-icon>
                    </div>
                  </div>
                </div>
                <div v-else class="empty-season">
                  暂无本季详情
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cast Section -->
      <div class="container content-section">
        <div class="section cast-section" v-if="details.credits?.cast?.length">
          <h2>演员阵容</h2>
          <div class="cast-slider">
            <button class="cast-arrow left" @click="scrollCast(-400)">
              <el-icon><ArrowLeft /></el-icon>
            </button>
            <div class="cast-track" ref="castTrackRef">
              <div class="cast-card" v-for="person in details.credits.cast" :key="person.id" @click="goToPerson(person.id)">
                <div class="avatar">
                  <img v-if="person.profile_path" :src="`/api/v1/media/tmdb-image/w185${person.profile_path}`" loading="lazy" />
                  <div v-else class="no-avatar">
                    <el-icon><UserFilled /></el-icon>
                  </div>
                </div>
                <div class="cast-info">
                  <div class="name">{{ person.name }}</div>
                  <div class="character">{{ person.character }}</div>
                </div>
              </div>
            </div>
            <button class="cast-arrow right" @click="scrollCast(400)">
              <el-icon><ArrowRight /></el-icon>
            </button>
          </div>
        </div>
      </div>

    </div>
    <div v-else-if="loading" class="loading-container">
      <LoadingDots />
    </div>
  </AppLayout>
</template>

<style scoped>
.details-view {
  color: #374151;
  position: relative;
  margin-top: -64px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 600px;
}

.header-section {
  position: relative;
  margin-bottom: 40px;
}

.backdrop-container {
  position: absolute;
  top: 0;
  left: -32px;
  right: -32px;
  height: 600px;
  background-size: cover;
  background-position: top center;
  z-index: 0;
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, 
    rgba(243, 244, 246, 0) 0%, 
    rgba(243, 244, 246, 0.2) 50%, 
    rgba(243, 244, 246, 0.9) 85%,
    rgba(243, 244, 246, 1) 100%
  );
}

.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  position: relative;
  z-index: 1; 
}

.header-content {
  display: grid;
  grid-template-columns: 300px 1fr 300px; 
  gap: 40px;
  padding-top: 300px;
}

.poster-wrapper {
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background: #fff;
  display: flex;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.main-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.info-column {
  padding-top: 20px;
}
.title {
  font-size: 2.5rem;
  margin: 0 0 10px 0;
  color: #111827;
  text-shadow: 0 2px 4px rgba(255,255,255,0.5);
}
.year {
  font-weight: 300;
  color: #4b5563;
}
.tagline {
  font-size: 1.1rem;
  font-style: italic;
  color: #4b5563;
  margin-bottom: 20px;
}
.overview-section h3 {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: #111827;
}
.overview-section p {
  line-height: 1.6;
  color: #374151;
  margin-bottom: 30px;
}
.crew-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}
.crew-item .role {
  font-weight: bold;
  font-size: 0.9rem;
  color: #111827;
}
.crew-item .name {
  color: #4b5563;
  font-size: 0.9rem;
}
.external-links {
  display: flex;
  gap: 10px;
}

.poster-column, .sidebar-column {
  display: flex;
  flex-direction: column;
}
.sidebar-column {
  padding-top: 20px;
}
.poster-wrapper, .info-card {
  border-radius: 12px;
}
.poster-wrapper {
  flex: 1;
}
.info-card {
  border: none;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  background: #fff;
}
.tooltip-trigger {
  display: inline-flex;
  width: 100%;
}
.media-info-tooltip { padding: 0; }
.media-info-tooltip-content { min-width: 260px; max-width: 320px; }
.media-info-tooltip-content .tooltip-title { font-weight: 600; margin-bottom: 8px; }
.media-info-tooltip-content ul { list-style: none; margin: 0; padding: 0; }
.media-info-tooltip-content li { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; margin-bottom: 4px; color: #f8fafc; }
.media-info-tooltip-content li span:first-child { color: #cbd5f5; }
.action-area { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #f3f4f6; }
.info-list { display: flex; flex-direction: column; gap: 12px; }
.info-item { font-size: 0.9rem; display: flex; flex-direction: column; }
.rating-item { align-items: center; margin-bottom: 10px; }
.info-item .label { font-weight: 600; color: #111827; margin-bottom: 2px; }
.info-item .value { color: #6b7280; }

/* Cast Grid */
.cast-section h2, .seasons-section h2 {
  border-left: 4px solid #a855f7;
  padding-left: 10px;
  margin-bottom: 20px;
  color: #111827;
}
.cast-slider { position: relative; display: flex; align-items: center; gap: 12px; }
.cast-track { display: flex; overflow-x: auto; gap: 16px; scroll-behavior: smooth; padding-bottom: 10px; scrollbar-width: none; }
.cast-track::-webkit-scrollbar { display: none; }
.cast-card { width: 110px; flex-shrink: 0; background: #fff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s; padding: 10px 8px; text-align: center; cursor: pointer; }
.cast-card:hover { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.12); }
.cast-arrow { border: none; background: #fff; border-radius: 50%; width: 36px; height: 36px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; justify-content: center; align-items: center; cursor: pointer; color: #6b7280; transition: transform 0.2s, opacity 0.2s; position: absolute; z-index: 10; opacity: 0; }
.cast-slider:hover .cast-arrow { opacity: 1; }
.cast-arrow.left { left: -18px; }
.cast-arrow.right { right: -18px; }
.cast-arrow:hover { transform: scale(1.05); }
.avatar { height: 140px; background: #f3f4f6; display: flex; align-items: center; justify-content: center; }
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.no-avatar { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #e5e7eb; color: #9ca3af; font-size: 4rem; }
.cast-info { padding: 10px; text-align: center; }
.cast-info .name { font-weight: bold; font-size: 0.9rem; color: #111827; margin-bottom: 2px; }
.cast-info .character { font-size: 0.8rem; color: #6b7280; }

/* Seasons Accordion Styles */
.seasons-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.season-accordion-item {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  overflow: hidden;
}
.season-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px; /* Slimmer padding as requested */
  cursor: pointer;
  background: #fff;
  transition: background-color 0.2s;
}
.season-header:hover {
  background-color: #f9fafb;
}
.season-info-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.season-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #111827;
}
.season-count {
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.8rem;
  color: #6b7280;
}
.season-info-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.season-status {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 6px;
}
.status-full {
  background-color: #d1fae5;
  color: #059669;
}
.status-partial {
  background-color: #fef3c7;
  color: #d97706;
}
.status-missing {
  background-color: #fee2e2;
  color: #dc2626;
}
.heart-wrapper {
  padding: 4px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}
.heart-wrapper:hover {
  background-color: #fee2e2;
}
.season-heart {
  width: 20px;
  height: 20px;
  color: #d1d5db;
  cursor: pointer;
  transition: color 0.2s, transform 0.2s;
}
.season-heart:hover {
  transform: scale(1.1);
}
.season-heart.active {
  color: #ef4444;
}
.expand-icon {
  color: #6b7280;
  font-size: 1.2rem;
}

.season-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
}
.episodes-list {
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
  padding: 0 20px;
}
.episode-card {
  display: flex;
  gap: 20px;
  padding: 20px 0;
  border-bottom: 1px solid #e5e7eb;
}
.episode-card:last-child {
  border-bottom: none;
}
.episode-content {
  flex: 1;
}
.episode-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.episode-number {
  font-weight: bold;
  font-size: 1rem;
  color: #111827;
}
.episode-date {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #374151;
  color: #fff;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}
.aired-icon {
  color: #10b981;
  background: #d1fae5;
  border-radius: 50%;
  padding: 2px;
  font-size: 1rem;
  margin-left: 8px;
}
.episode-overview {
  color: #4b5563;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
}
.episode-overview.empty {
  color: #9ca3af;
  font-style: italic;
}
.episode-still {
  width: 200px;
  flex-shrink: 0;
  aspect-ratio: 16/9;
  border-radius: 8px;
  overflow: hidden;
  background: #f3f4f6;
}
.episode-still img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.episode-still.no-image {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 2rem;
}
.empty-season {
  text-align: center;
  padding: 40px;
  color: #6b7280;
  font-style: italic;
}
</style>
