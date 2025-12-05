import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  // Initialize from localStorage
  const storedCollapse = localStorage.getItem('sidebar-collapse')
  const isCollapse = ref(storedCollapse === 'true')

  const toggleSidebar = () => {
    isCollapse.value = !isCollapse.value
    localStorage.setItem('sidebar-collapse', String(isCollapse.value))
  }

  const setCollapse = (value: boolean) => {
    isCollapse.value = value
    localStorage.setItem('sidebar-collapse', String(value))
  }

  return {
    isCollapse,
    toggleSidebar,
    setCollapse
  }
})

