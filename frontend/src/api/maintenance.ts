/**
 * Maintenance API service.
 * Issue #9: Minimal Printer Maintenance Details
 */

import { apiClient } from './client'
import type { Maintenance, MaintenanceCreate, MaintenanceUpdate } from '@/types/maintenance'
import type { PaginatedResponse } from '@/types/api'

export interface MaintenanceFilters {
  printer_id?: number
  done?: boolean
  limit?: number
  offset?: number
}

export const maintenanceApi = {
  getAll: async (filters: MaintenanceFilters = {}): Promise<PaginatedResponse<Maintenance>> => {
    const params: Record<string, string | number | boolean> = {}
    if (filters.printer_id !== undefined) params.printer_id = filters.printer_id
    if (filters.done !== undefined) params.done = filters.done
    if (filters.limit !== undefined) params.limit = filters.limit
    if (filters.offset !== undefined) params.offset = filters.offset

    const response = await apiClient.get<PaginatedResponse<Maintenance>>('/maintenance', { params })
    return response.data
  },

  getById: async (id: number): Promise<Maintenance> => {
    const response = await apiClient.get<Maintenance>(`/maintenance/${id}`)
    return response.data
  },

  create: async (data: MaintenanceCreate): Promise<Maintenance> => {
    const response = await apiClient.post<Maintenance>('/maintenance', data)
    return response.data
  },

  update: async (id: number, data: MaintenanceUpdate): Promise<Maintenance> => {
    const response = await apiClient.put<Maintenance>(`/maintenance/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/maintenance/${id}`)
  },
}
