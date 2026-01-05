import type { JobStatus } from '@/types/job'

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  completed: 'success',
  error: 'danger',
  cancelled: 'warn',
  printing: 'info',
  paused: 'secondary',
}

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  completed: 'Completed',
  error: 'Failed',
  cancelled: 'Cancelled',
  printing: 'Printing',
  paused: 'Paused',
}

export const DEFAULT_PAGE_SIZE = 20
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

export const POLLING_INTERVALS = {
  printerStatus: 30000, // 30 seconds
  dashboardSummary: 60000, // 1 minute
  jobsList: 30000, // 30 seconds
} as const
