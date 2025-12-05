<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import http from '../utils/http'
import { ElMessage } from 'element-plus'
import { Link } from '@element-plus/icons-vue'
import AppLayout from '../layout/AppLayout.vue'
import LoadingDots from '../components/LoadingDots.vue'
import MediaCard from '../components/MediaCard.vue'

const route = useRoute()
const id = route.params.id as string

const details = ref<any>(null)
const loading = ref(true)
const tmdbImageBase = '/api/v1/media/tmdb-image/original'
const tmdbProfileBase = '/api/v1/media/tmdb-image/h632'

const fetchDetails = async () => {
  loading.value = true
  try {
    const res = await http.get(`/media/person/${id}`)
    details.value = res.data
  } catch (e) {
    ElMessage.error('加载人物详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDetails()
})

const profileUrl = computed(() => {
  if (details.value?.profile_path) {
    return `${tmdbProfileBase}${details.value.profile_path}`
  }
  return ''
})

const sortedCredits = computed(() => {
  if (!details.value?.combined_credits?.cast) return []
  
  // Filter only movies and tv
  let credits = details.value.combined_credits.cast.filter((item: any) => 
    item.media_type === 'movie' || item.media_type === 'tv'
  )
  
  // Remove duplicates (sometimes same ID appears for different roles? usually combined_credits is okay)
  const seen = new Set()
  credits = credits.filter((item: any) => {
    const duplicate = seen.has(item.id)
    seen.add(item.id)
    return !duplicate
  })

  // Sort by popularity descending
  credits.sort((a: any, b: any) => (b.popularity || 0) - (a.popularity || 0))
  
  return credits
})

const knownForBackdrop = computed(() => {
  // Use the most popular credit's backdrop as background
  const best = sortedCredits.value[0]
  if (best?.backdrop_path) {
    return `${tmdbImageBase}${best.backdrop_path}`
  }
  return ''
})

const genderText = computed(() => {
  if (details.value?.gender === 1) return '女性'
  if (details.value?.gender === 2) return '男性'
  return '未知'
})

const openLink = (type: 'tmdb' | 'imdb') => {
  if (type === 'tmdb') {
    window.open(`https://www.themoviedb.org/person/${details.value.id}`, '_blank')
  } else if (type === 'imdb' && details.value.external_ids?.imdb_id) {
    window.open(`https://www.imdb.com/name/${details.value.external_ids.imdb_id}`, '_blank')
  }
}
</script>

<template>
  <AppLayout>
    <div class="person-view" v-if="details && !loading">
      <!-- Header Section with Backdrop from best known work -->
      <div class="header-section">
        <div class="backdrop-container" :style="{ backgroundImage: `url(${knownForBackdrop})` }">
          <div class="gradient-overlay"></div>
        </div>
        
        <div class="header-content container">
          <!-- Left: Profile Image -->
          <div class="poster-column">
            <div class="poster-wrapper">
              <img v-if="profileUrl" :src="profileUrl" alt="Profile" class="main-poster" />
              <div v-else class="no-poster">暂无照片</div>
            </div>
          </div>

          <!-- Info Column -->
          <div class="info-column">
            <h1 class="title">
              {{ details.name }}
            </h1>
            
            <div class="personal-info">
              <div class="info-item" v-if="details.birthday">
                <div class="label">出生日期</div>
                <div class="value">{{ details.birthday }}</div>
              </div>
              <div class="info-item" v-if="details.place_of_birth">
                <div class="label">出生地</div>
                <div class="value">{{ details.place_of_birth }}</div>
              </div>
               <div class="info-item" v-if="details.known_for_department">
                <div class="label">职业</div>
                <div class="value">{{ details.known_for_department }}</div>
              </div>
              <div class="info-item">
                <div class="label">性别</div>
                <div class="value">{{ genderText }}</div>
              </div>
            </div>

            <div class="overview-section" v-if="details.biography">
              <h3>简介</h3>
              <p class="biography">{{ details.biography || '暂无简介' }}</p>
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
        </div>
      </div>

      <!-- Known For Section -->
      <div class="container content-section">
        <div class="section" v-if="sortedCredits.length">
          <h2>参演作品</h2>
          <div class="media-grid">
            <MediaCard
              v-for="item in sortedCredits"
              :key="item.id"
              :item="item"
            />
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
.person-view {
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
  height: 500px;
  background-size: cover;
  background-position: center;
  z-index: 0;
}

/* The Gradient Mask */
.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(to bottom, 
    rgba(243, 244, 246, 0.4) 0%, 
    rgba(243, 244, 246, 0.8) 60%, 
    rgba(243, 244, 246, 1) 100%
  );
  backdrop-filter: blur(2px);
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
  grid-template-columns: 300px 1fr; 
  gap: 40px;
  padding-top: 150px;
}

/* Poster */
.poster-wrapper {
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background: #fff;
  display: flex;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  aspect-ratio: 2/3;
}
.main-poster {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.no-poster {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #e5e7eb;
  color: #9ca3af;
  font-size: 1.2rem;
}

/* Info Column */
.info-column {
  padding-top: 20px;
}
.title {
  font-size: 2.5rem;
  margin: 0 0 20px 0;
  color: #111827;
}

.personal-info {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
  flex-wrap: wrap;
}
.info-item .label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 4px;
}
.info-item .value {
  font-size: 1rem;
  color: #111827;
}

.overview-section h3 {
  font-size: 1.2rem;
  margin-bottom: 10px;
  color: #111827;
}
.biography {
  line-height: 1.6;
  color: #374151;
  margin-bottom: 30px;
  white-space: pre-wrap;
}

.external-links {
  display: flex;
  gap: 10px;
}

.section h2 {
  border-left: 4px solid #a855f7;
  padding-left: 10px;
  margin-bottom: 20px;
  color: #111827;
}

.media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 24px;
  justify-items: center;
  padding-bottom: 40px;
}
</style>

