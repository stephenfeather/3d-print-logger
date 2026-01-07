import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setApiKey, getApiKey, clearApiKey, hasApiKey } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const apiKey = ref<string | null>(getApiKey())
  const isAuthenticated = computed(() => !!apiKey.value)

  function login(key: string) {
    setApiKey(key)
    apiKey.value = key
  }

  function logout() {
    clearApiKey()
    apiKey.value = null
  }

  function checkAuth(): boolean {
    const key = getApiKey()
    apiKey.value = key
    return hasApiKey()
  }

  return {
    apiKey,
    isAuthenticated,
    login,
    logout,
    checkAuth
  }
})
