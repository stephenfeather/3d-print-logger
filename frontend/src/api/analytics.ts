import { apiClient } from './client'
import type {
  DashboardSummary,
  PrinterStats,
  FilamentUsage,
  TimelineEntry,
  TimelinePeriod,
} from '@/types/analytics'

export const analyticsApi = {
  getSummary: async (): Promise<DashboardSummary> => {
    const response = await apiClient.get<DashboardSummary>('/analytics/summary')
    return response.data
  },

  getPrinterStats: async (): Promise<PrinterStats[]> => {
    const response = await apiClient.get<PrinterStats[]>('/analytics/printers')
    return response.data
  },

  getFilamentUsage: async (): Promise<FilamentUsage[]> => {
    const response = await apiClient.get<FilamentUsage[]>('/analytics/filament')
    return response.data
  },

  getTimeline: async (period: TimelinePeriod = 'day'): Promise<TimelineEntry[]> => {
    const response = await apiClient.get<TimelineEntry[]>('/analytics/timeline', {
      params: { period },
    })
    return response.data
  },
}
