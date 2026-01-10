/**
 * TypeScript types for maintenance records.
 * Issue #9: Minimal Printer Maintenance Details
 */

export interface Maintenance {
  id: number
  printer_id: number
  date: string
  done: boolean
  category: string
  description: string
  cost: number | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface MaintenanceCreate {
  printer_id: number
  date: string
  category: string
  description: string
  done?: boolean
  cost?: number
  notes?: string
}

export interface MaintenanceUpdate {
  date?: string
  category?: string
  description?: string
  done?: boolean
  cost?: number
  notes?: string
}
