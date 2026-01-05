import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { printersApi } from '@/api/printers'
import type { PrinterCreate, PrinterUpdate } from '@/types/printer'

export function usePrinters(includeInactive = false) {
  return useQuery({
    queryKey: ['printers', { includeInactive }],
    queryFn: () => printersApi.getAll(includeInactive),
    staleTime: 30000, // 30 seconds
  })
}

export function usePrinter(id: number) {
  return useQuery({
    queryKey: ['printers', id],
    queryFn: () => printersApi.getById(id),
    enabled: id > 0,
  })
}

export function usePrinterStatus(id: number) {
  return useQuery({
    queryKey: ['printers', id, 'status'],
    queryFn: () => printersApi.getStatus(id),
    enabled: id > 0,
    staleTime: 10000, // 10 seconds - status updates more frequently
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })
}

export function useCreatePrinter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: PrinterCreate) => printersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['printers'] })
    },
  })
}

export function useUpdatePrinter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: PrinterUpdate }) =>
      printersApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['printers'] })
      queryClient.invalidateQueries({ queryKey: ['printers', id] })
    },
  })
}

export function useDeletePrinter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => printersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['printers'] })
    },
  })
}
