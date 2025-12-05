import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import http from '../utils/http'

type CacheEntry = { items: any[]; timestamp: number }
type CacheShape = Record<string, CacheEntry>

const CACHE_TTL_MS = 15 * 60 * 1000 // 15 minutes

const normalizeCache = (raw: Record<string, any>): CacheShape => {
  const normalized: CacheShape = {}
  Object.keys(raw || {}).forEach((key) => {
    const value = raw[key]
    if (Array.isArray(value)) {
      normalized[key] = { items: value, timestamp: 0 }
    } else if (value && Array.isArray(value.items)) {
      normalized[key] = { items: value.items, timestamp: Number(value.timestamp) || 0 }
    }
  })
  return normalized
}

const shouldRefresh = (entry?: CacheEntry) => {
  if (!entry) return true
  return Date.now() - entry.timestamp > CACHE_TTL_MS
}

export const useMediaStore = defineStore('media', () => {
  const savedCache = localStorage.getItem('media-cache')
  const initialCache = savedCache ? normalizeCache(JSON.parse(savedCache)) : {}
  const cache = ref<CacheShape>(initialCache)
  
  const loadingStates = ref<Record<string, boolean>>({})
  const errors = ref<Record<string, string>>({})

  watch(cache, (newCache) => {
    localStorage.setItem('media-cache', JSON.stringify(newCache))
  }, { deep: true })

  const refreshFromServer = async (key: string, endpoint: string, params: any = {}, silent = false) => {
    if (!silent) {
    loadingStates.value[key] = true
    errors.value[key] = ''
    }

    try {
      const res = await http.get(endpoint, { params })
      const items = res.data.results || res.data
      cache.value[key] = { items, timestamp: Date.now() }
    } catch (e) {
      console.error(e)
      errors.value[key] = '加载失败，请检查网络或 API 配置'
    } finally {
      if (!silent) {
      loadingStates.value[key] = false
    }
    }
    
    return cache.value[key]?.items || []
  }

  const fetchMedia = async (endpoint: string, params: any = {}) => {
    const key = `${endpoint}:${JSON.stringify(params)}`
    const entry = cache.value[key]

    if (shouldRefresh(entry)) {
      return await refreshFromServer(key, endpoint, params)
    }

    // Return cached items immediately, but refresh in background to keep data fresh
    // We must await the background refresh if we want the UI to update via reactivity for the SAME key
    // However, returning entry.items returns the OLD array reference.
    // The component usage `const result = mediaStore.getMedia()` calls this.
    // If getMedia returns `entry.items`, it is reactive if `cache` is reactive.
    // BUT fetchMedia returns `entry.items` (the raw array).
    
    // To fix the "stuck" issue:
    // 1. Trigger refresh.
    refreshFromServer(key, endpoint, params, true)
    // 2. Return the CURRENT items. If refresh finishes later, cache.value[key] updates.
    // Components should use getMedia() computed/reactive properties to see the update.
    // But many components just do `items.value = await fetchMedia()`.
    // This assigns the OLD array. The component doesn't know about the NEW array unless it watches something.
    
    return entry ? entry.items : []
  }

  // Helper to reactively get data
  const getMedia = (endpoint: string, params: any = {}) => {
    const key = `${endpoint}:${JSON.stringify(params)}`
    // We need to return a computed-like structure or just the current state
    // If used in a computed or template, accessing cache.value[key] creates dependency.
    return {
      get items() { return cache.value[key]?.items || [] }, // Getter for reactivity
      get loading() { return loadingStates.value[key] || false },
      get error() { return errors.value[key] || '' }
    }
  }

  const updateMediaStatus = (tmdbId: string | number, status: string) => {
    const targetId = String(tmdbId)
    Object.keys(cache.value).forEach((key) => {
      const entry = cache.value[key]
      if (!entry || entry.items.length === 0) return

      let mutated = false
      const updatedItems = entry.items.map((item) => {
        if (String(item.id) === targetId) {
          mutated = true
          return { ...item, status }
        }
        return item
      })

      if (mutated) {
        cache.value[key] = { items: updatedItems, timestamp: entry.timestamp }
      }
    })
  }

  const clearCache = () => {
    cache.value = {}
    localStorage.removeItem('media-cache')
  }

  return { fetchMedia, getMedia, updateMediaStatus, clearCache }
})
