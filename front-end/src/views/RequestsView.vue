<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '../utils/http'
import AppLayout from '../layout/AppLayout.vue'
import { ElMessage } from 'element-plus'

interface RequestItem {
  id: number
  title: string
  status: string
  poster_path?: string
  request_date: string
  specific_season?: number
}

const requests = ref<RequestItem[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    // Pass own=true to only fetch current user's requests
    const res = await http.get('/requests/', { params: { own: true } })
    requests.value = res.data
  } catch (e) {
    ElMessage.error('加载订阅列表失败')
  } finally {
    loading.value = false
  }
})

const getStatusTag = (status: string) => {
  switch (status) {
    case 'approved': return 'success'
    case 'pending': return 'warning'
    case 'rejected': return 'danger'
    case 'completed': return 'success'
    default: return 'info'
  }
}

const formatStatus = (status: string) => {
  switch (status) {
    case 'approved': return '已批准'
    case 'pending': return '待审批'
    case 'rejected': return '已拒绝'
    case 'completed': return '已完成'
    default: return status.toUpperCase()
  }
}

const tmdbImageBase = '/api/v1/media/tmdb-image/w200'
</script>

<template>
  <AppLayout>
    <div class="container">
      <h1>我的订阅</h1>
      <el-table :data="requests" v-loading="loading" style="width: 100%">
        <el-table-column label="海报" width="80">
          <template #default="scope">
            <img v-if="scope.row.poster_path" :src="`${tmdbImageBase}${scope.row.poster_path}`" style="width: 50px; border-radius: 4px" />
          </template>
        </el-table-column>
        <el-table-column label="标题">
          <template #default="scope">
            <span>{{ scope.row.title }}</span>
            <el-tag v-if="scope.row.specific_season" size="small" type="info" style="margin-left: 8px">第 {{ scope.row.specific_season }} 季</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusTag(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="request_date" label="申请日期">
          <template #default="scope">
             {{ new Date(scope.row.request_date).toLocaleDateString() }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </AppLayout>
</template>

<style scoped>
.container {
  padding: 100px 40px 40px 40px; /* Added top padding */
  color: #374151;
}
h1 {
  margin-bottom: 20px;
  color: #111827;
}
</style>
