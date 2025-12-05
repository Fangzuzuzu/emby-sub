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
  user_id: string
  user_name?: string
  media_type?: string
  tmdb_id?: string
  specific_season?: number
}

const router = useRouter()
import { useRouter } from 'vue-router'

const requests = ref<RequestItem[]>([])
const loading = ref(true)

const fetchRequests = async () => {
  loading.value = true
  try {
    const res = await http.get('/requests/')
    requests.value = res.data
  } catch (e) {
    ElMessage.error('加载申请列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchRequests)

const handleAction = async (id: number, action: 'approve' | 'reject') => {
  try {
    await http.put(`/requests/${id}/${action}`)
    ElMessage.success(action === 'approve' ? '已批准申请' : '已拒绝申请')
    fetchRequests()
  } catch (e) {
    ElMessage.error('操作失败')
  }
}

const goToDetails = (item: RequestItem) => {
  if (item.media_type && item.tmdb_id) {
    let type = item.media_type
    if (type === 'series') type = 'tv'
    router.push({ name: 'details', params: { type, id: item.tmdb_id } })
  }
}

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
      <h1>申请管理</h1>
      <el-table :data="requests" v-loading="loading" style="width: 100%">
        <el-table-column label="海报" width="80">
          <template #default="scope">
            <div class="poster-cell" @click="goToDetails(scope.row)">
               <img v-if="scope.row.poster_path" :src="`${tmdbImageBase}${scope.row.poster_path}`" />
               <div v-else class="no-poster">无图</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题">
           <template #default="scope">
             <span class="title-link" @click="goToDetails(scope.row)">{{ scope.row.title }}</span>
             <el-tag v-if="scope.row.specific_season" size="small" type="info" style="margin-left: 8px">第 {{ scope.row.specific_season }} 季</el-tag>
           </template>
        </el-table-column>
        <el-table-column prop="user_name" label="申请人">
          <template #default="scope">
            {{ scope.row.user_name || scope.row.user_id }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="scope">
            <el-tag :type="getStatusTag(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
         <el-table-column label="操作">
          <template #default="scope">
            <div v-if="scope.row.status === 'pending'">
              <el-button size="small" type="success" @click="handleAction(scope.row.id, 'approve')">批准</el-button>
              <el-button size="small" type="danger" @click="handleAction(scope.row.id, 'reject')">拒绝</el-button>
            </div>
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
.poster-cell {
  width: 50px;
  height: 75px;
  border-radius: 4px;
  overflow: hidden;
  background: #eee;
  cursor: pointer;
}
.poster-cell img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.no-poster {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #999;
}
.title-link {
  color: #3b82f6;
  cursor: pointer;
  font-weight: 500;
}
.title-link:hover {
  text-decoration: underline;
}
</style>
