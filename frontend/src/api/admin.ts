import { apiClient } from './client'
import type { ApiKey, ApiKeyCreate, ApiKeyCreated, SystemInfo, HealthResponse } from '@/types/api'

export const adminApi = {
  getApiKeys: async (): Promise<ApiKey[]> => {
    const response = await apiClient.get<ApiKey[]>('/admin/api-keys')
    return response.data
  },

  createApiKey: async (data: ApiKeyCreate): Promise<ApiKeyCreated> => {
    const response = await apiClient.post<ApiKeyCreated>('/admin/api-keys', data)
    return response.data
  },

  revokeApiKey: async (id: number): Promise<void> => {
    await apiClient.delete(`/admin/api-keys/${id}`)
  },

  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await apiClient.get<SystemInfo>('/admin/system')
    return response.data
  },
}

export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/health')
    return response.data
  },
}
