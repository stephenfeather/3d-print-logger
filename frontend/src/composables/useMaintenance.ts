/**
 * Composables for maintenance data management.
 * Issue #9: Minimal Printer Maintenance Details
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { maintenanceApi, type MaintenanceFilters } from '@/api/maintenance'
import type { MaintenanceCreate, MaintenanceUpdate } from '@/types/maintenance'

export function useMaintenance(filters: MaintenanceFilters = {}) {
  return useQuery({
    queryKey: ['maintenance', filters],
    queryFn: () => maintenanceApi.getAll(filters),
    staleTime: 30000, // 30 seconds
  })
}

export function useMaintenanceRecord(id: number) {
  return useQuery({
    queryKey: ['maintenance', id],
    queryFn: () => maintenanceApi.getById(id),
    enabled: id > 0,
  })
}

export function useCreateMaintenance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: MaintenanceCreate) => maintenanceApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
    },
  })
}

export function useUpdateMaintenance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MaintenanceUpdate }) =>
      maintenanceApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
      queryClient.invalidateQueries({ queryKey: ['maintenance', id] })
    },
  })
}

export function useDeleteMaintenance() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => maintenanceApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] })
    },
  })
}
