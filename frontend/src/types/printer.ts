export interface Printer {
  id: number
  name: string
  moonraker_url: string
  location: string | null
  is_active: boolean
  last_seen: string | null
  created_at: string
  updated_at: string
}

export interface PrinterCreate {
  name: string
  moonraker_url: string
  location?: string
  moonraker_api_key?: string
}

export interface PrinterUpdate {
  name?: string
  moonraker_url?: string
  location?: string
  moonraker_api_key?: string
  is_active?: boolean
}

export interface PrinterStatus {
  printer_id: number
  name: string
  is_connected: boolean
  state: string | null
  progress: number | null
  current_file: string | null
  error: string | null
}
