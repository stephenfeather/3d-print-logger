export interface JobDetails {
  id: number
  print_job_id: number
  layer_height: number | null
  first_layer_height: number | null
  nozzle_temp: number | null
  bed_temp: number | null
  print_speed: number | null
  infill_percentage: number | null
  infill_pattern: string | null
  support_enabled: boolean | null
  support_type: string | null
  filament_type: string | null
  filament_brand: string | null
  filament_color: string | null
  estimated_time: number | null
  estimated_filament: number | null
  layer_count: number | null
  object_height: number | null
  thumbnail_base64: string | null
}

export type JobStatus = 'completed' | 'error' | 'cancelled' | 'printing' | 'paused'

export interface PrintJob {
  id: number
  printer_id: number
  job_id: string
  user: string | null
  filename: string
  status: JobStatus
  start_time: string | null
  end_time: string | null
  print_duration: number | null
  total_duration: number | null
  filament_used: number | null
  job_metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
  details: JobDetails | null
}

export interface JobFilters {
  printer_id?: number
  status?: JobStatus
  start_after?: string
  start_before?: string
  limit: number
  offset: number
}
