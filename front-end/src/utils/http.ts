import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import router from '../router'

const http = axios.create({
  baseURL: '/api/v1', // We will need to proxy this in vite.config.ts
  timeout: 10000,
})

http.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

http.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response && error.response.status === 403) {
       const authStore = useAuthStore()
       authStore.logout()
       router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default http
