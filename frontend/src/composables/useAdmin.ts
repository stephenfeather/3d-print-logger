import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { adminApi, healthApi } from '@/api/admin'
import type { ApiKeyCreate } from '@/types/api'

export function useApiKeys() {
  return useQuery({
    queryKey: ['admin', 'api-keys'],
    queryFn: () => adminApi.getApiKeys(),
    staleTime: 60000,
  })
}

export function useCreateApiKey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ApiKeyCreate) => adminApi.createApiKey(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] })
    },
  })
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => adminApi.revokeApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] })
    },
  })
}

export function useSystemInfo() {
  return useQuery({
    queryKey: ['admin', 'system'],
    queryFn: () => adminApi.getSystemInfo(),
    staleTime: 30000,
  })
}

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    staleTime: 10000,
    refetchInterval: 30000, // Check every 30 seconds
  })
}
