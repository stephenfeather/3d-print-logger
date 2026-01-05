import { apiClient } from './client'
import type { Printer, PrinterCreate, PrinterUpdate, PrinterStatus } from '@/types/printer'
import type { PaginatedResponse } from '@/types/api'
import type { PrintJob } from '@/types/job'

export const printersApi = {
  getAll: async (includeInactive = false): Promise<Printer[]> => {
    const params = includeInactive ? { include_inactive: true } : {}
    const response = await apiClient.get<Printer[]>('/printers', { params })
    return response.data
  },

  getById: async (id: number): Promise<Printer> => {
    const response = await apiClient.get<Printer>(`/printers/${id}`)
    return response.data
  },

  create: async (data: PrinterCreate): Promise<Printer> => {
    const response = await apiClient.post<Printer>('/printers', data)
    return response.data
  },

  update: async (id: number, data: PrinterUpdate): Promise<Printer> => {
    const response = await apiClient.put<Printer>(`/printers/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/printers/${id}`)
  },

  getStatus: async (id: number): Promise<PrinterStatus> => {
    const response = await apiClient.get<PrinterStatus>(`/printers/${id}/status`)
    return response.data
  },

  getJobs: async (id: number, limit = 20, offset = 0): Promise<PaginatedResponse<PrintJob>> => {
    const response = await apiClient.get<PaginatedResponse<PrintJob>>(`/printers/${id}/jobs`, {
      params: { limit, offset },
    })
    return response.data
  },
}
