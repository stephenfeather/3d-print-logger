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

  // Slicer information (Issue #5)
  slicer_name: string | null
  slicer_version: string | null

  // Print statistics
  estimated_time: number | null
  estimated_filament: number | null
  layer_count: number | null
  object_height: number | null

  // Multi-filament usage and cost (Issue #5)
  filament_used_mm: number[] | null
  filament_used_cm3: number[] | null
  filament_used_g: number[] | null
  filament_cost: number[] | null
  total_filament_used_g: number | null
  total_filament_cost: number | null

  // Config block (Issue #5)
  config_block: Record<string, unknown> | null
  raw_metadata: Record<string, unknown> | null

  // Thumbnail
  thumbnail_base64: string | null
}

export type JobStatus = 'completed' | 'error' | 'cancelled' | 'printing' | 'paused'

export interface PrintJob {
  id: number
  printer_id: number
  job_id: string
  user: string | null
  filename: string
  title: string | null
  url: string | null
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

export interface JobUpdatePayload {
  title?: string | null
  url?: string | null
}
