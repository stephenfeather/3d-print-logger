export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface ApiKey {
  id: number
  key_prefix: string
  name: string
  is_active: boolean
  expires_at: string | null
  last_used: string | null
  created_at: string
}

export interface ApiKeyCreate {
  name: string
  expires_at?: string
}

export interface ApiKeyCreated extends ApiKey {
  key: string
}

export interface SystemInfo {
  version: string
  database_type: string
  active_printers: number
  total_jobs: number
  uptime_seconds: number | null
}

export interface ErrorResponse {
  detail: string
  code?: string
}

export interface HealthResponse {
  status: string
}
