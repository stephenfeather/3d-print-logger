import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { jobsApi } from '@/api/jobs'
import type { JobFilters, JobStatus, JobUpdatePayload } from '@/types/job'

export function useJobs(initialFilters?: Partial<JobFilters>) {
  const filters = ref<JobFilters>({
    limit: 20,
    offset: 0,
    ...initialFilters,
  })

  const queryKey = computed(() => ['jobs', filters.value])

  const query = useQuery({
    queryKey,
    queryFn: () => jobsApi.getAll(filters.value),
    staleTime: 30000,
  })

  function updateFilters(newFilters: Partial<JobFilters>) {
    filters.value = { ...filters.value, ...newFilters, offset: 0 }
  }

  function setPage(page: number) {
    filters.value = {
      ...filters.value,
      offset: (page - 1) * filters.value.limit,
    }
  }

  function setPageSize(size: number) {
    filters.value = { ...filters.value, limit: size, offset: 0 }
  }

  function setStatus(status: JobStatus | undefined) {
    filters.value = { ...filters.value, status, offset: 0 }
  }

  function setPrinter(printerId: number | undefined) {
    filters.value = { ...filters.value, printer_id: printerId, offset: 0 }
  }

  function setDateRange(startAfter?: string, startBefore?: string) {
    filters.value = {
      ...filters.value,
      start_after: startAfter,
      start_before: startBefore,
      offset: 0,
    }
  }

  const currentPage = computed(() => Math.floor(filters.value.offset / filters.value.limit) + 1)

  const totalPages = computed(() => {
    if (!query.data.value) return 1
    return Math.ceil(query.data.value.total / filters.value.limit)
  })

  return {
    ...query,
    filters,
    currentPage,
    totalPages,
    updateFilters,
    setPage,
    setPageSize,
    setStatus,
    setPrinter,
    setDateRange,
  }
}

export function useJob(id: number) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => jobsApi.getById(id),
    enabled: id > 0,
  })
}

export function useDeleteJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => jobsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}

export function useUpdateJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: JobUpdatePayload }) =>
      jobsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
    },
  })
}

// Convenience hook for recent jobs on dashboard
export function useRecentJobs(limit = 5) {
  return useQuery({
    queryKey: ['jobs', 'recent', limit],
    queryFn: () => jobsApi.getAll({ limit, offset: 0 }),
    staleTime: 30000,
  })
}
