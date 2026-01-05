import axios, { type AxiosInstance } from 'axios'

const API_KEY_STORAGE_KEY = '3dp_api_key'

export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add API key to all requests
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem(API_KEY_STORAGE_KEY)
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Could redirect to setup/login page
      console.error('API key invalid or missing')
    }
    return Promise.reject(error)
  },
)

export function setApiKey(key: string): void {
  localStorage.setItem(API_KEY_STORAGE_KEY, key)
}

export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE_KEY)
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}

export function hasApiKey(): boolean {
  return !!localStorage.getItem(API_KEY_STORAGE_KEY)
}
