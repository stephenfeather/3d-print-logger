export interface DashboardSummary {
  total_jobs: number
  total_print_time: number
  total_filament_used: number
  successful_jobs: number
  failed_jobs: number
  active_printers: number
}

export interface PrinterStats {
  printer_id: number
  printer_name: string
  total_jobs: number
  total_print_time: number
  total_filament_used: number
  successful_jobs: number
  failed_jobs: number
  last_job_at: string | null
}

export interface FilamentUsage {
  filament_type: string
  total_used: number
  job_count: number
}

export type TimelinePeriod = 'day' | 'week' | 'month'

export interface TimelineEntry {
  period: string
  job_count: number
  total_print_time: number
  successful_jobs: number
  failed_jobs: number
}
