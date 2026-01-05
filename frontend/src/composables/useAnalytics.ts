import { useQuery } from '@tanstack/vue-query'
import { analyticsApi } from '@/api/analytics'
import type { TimelinePeriod } from '@/types/analytics'

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: () => analyticsApi.getSummary(),
    staleTime: 60000, // 1 minute - dashboard stats don't need frequent updates
  })
}

export function usePrinterStats() {
  return useQuery({
    queryKey: ['analytics', 'printers'],
    queryFn: () => analyticsApi.getPrinterStats(),
    staleTime: 60000,
  })
}

export function useFilamentUsage() {
  return useQuery({
    queryKey: ['analytics', 'filament'],
    queryFn: () => analyticsApi.getFilamentUsage(),
    staleTime: 60000,
  })
}

export function useTimeline(period: TimelinePeriod = 'day') {
  return useQuery({
    queryKey: ['analytics', 'timeline', period],
    queryFn: () => analyticsApi.getTimeline(period),
    staleTime: 60000,
  })
}
