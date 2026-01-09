export type PrinterType = 'FDM' | 'Resin' | 'SLS'
export type FilamentDiameter = 1.75 | 2.85 | 3.0

export interface Printer {
  id: number
  name: string
  moonraker_url: string
  location: string | null
  is_active: boolean
  last_seen: string | null

  // Hardware details (Issue #8)
  printer_type: PrinterType | null
  make: string | null
  model: string | null
  description: string | null

  // Specifications
  filament_diameter: number | null
  nozzle_diameter: number | null
  bed_x: number | null
  bed_y: number | null
  bed_z: number | null
  has_heated_bed: boolean
  has_heated_chamber: boolean

  // Material tracking
  loaded_materials: any[] | null

  created_at: string
  updated_at: string
}

export interface PrinterCreate {
  name: string
  moonraker_url: string
  location?: string
  moonraker_api_key?: string

  // Hardware details (Issue #8)
  printer_type?: PrinterType
  make?: string
  model?: string
  description?: string

  // Specifications
  filament_diameter?: FilamentDiameter
  nozzle_diameter?: number
  bed_x?: number
  bed_y?: number
  bed_z?: number
  has_heated_bed?: boolean
  has_heated_chamber?: boolean

  // Material tracking
  loaded_materials?: any[]
}

export interface PrinterUpdate {
  name?: string
  moonraker_url?: string
  location?: string
  moonraker_api_key?: string
  is_active?: boolean

  // Hardware details (Issue #8)
  printer_type?: PrinterType
  make?: string
  model?: string
  description?: string

  // Specifications
  filament_diameter?: FilamentDiameter
  nozzle_diameter?: number
  bed_x?: number
  bed_y?: number
  bed_z?: number
  has_heated_bed?: boolean
  has_heated_chamber?: boolean

  // Material tracking
  loaded_materials?: any[]
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
