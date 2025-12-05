<script setup lang="ts">
import MediaSlider from '../components/MediaSlider.vue'
import AppLayout from '../layout/AppLayout.vue'
</script>

<template>
  <AppLayout>
    <div class="content-container">
      <MediaSlider title="最近添加" endpoint="/media/latest" />
      <MediaSlider title="电影" endpoint="/media/trending" :params="{ media_type: 'movie' }" />
      <!-- Exclude anime (genre 16) from TV shows -->
      <MediaSlider title="剧集" endpoint="/media/trending" :params="{ media_type: 'tv', without_genres: '16' }" />
      <MediaSlider title="动漫" endpoint="/media/anime" />
    </div>
  </AppLayout>
</template>

<style scoped>
.content-container {
  padding-top: 20px; /* Reduced from 80px since AppLayout handles Topbar offset */
}
</style>
