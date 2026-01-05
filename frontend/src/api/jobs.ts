import { apiClient } from './client'
import type { PrintJob, JobFilters } from '@/types/job'
import type { PaginatedResponse } from '@/types/api'

export const jobsApi = {
  getAll: async (filters: JobFilters): Promise<PaginatedResponse<PrintJob>> => {
    const params: Record<string, string | number> = {
      limit: filters.limit,
      offset: filters.offset,
    }

    if (filters.printer_id !== undefined) {
      params.printer_id = filters.printer_id
    }
    if (filters.status) {
      params.status = filters.status
    }
    if (filters.start_after) {
      params.start_after = filters.start_after
    }
    if (filters.start_before) {
      params.start_before = filters.start_before
    }

    const response = await apiClient.get<PaginatedResponse<PrintJob>>('/jobs', {
      params,
    })
    return response.data
  },

  getById: async (id: number): Promise<PrintJob> => {
    const response = await apiClient.get<PrintJob>(`/jobs/${id}`)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/jobs/${id}`)
  },
}
