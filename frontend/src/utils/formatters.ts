/**
 * Format seconds into human-readable duration string
 * @param seconds - Duration in seconds
 * @returns Formatted string like "2h 30m" or "45m 12s"
 */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) {
    return '-'
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`
  }
  return `${secs}s`
}

/**
 * Format filament usage (in mm) to grams with 1 decimal place
 * Uses average density of 1.24 g/cm^3 for PLA
 * @param mm - Filament length in millimeters
 * @param diameter - Filament diameter in mm (default 1.75)
 * @returns Formatted string like "125.4g"
 */
export function formatFilament(mm: number | null | undefined, diameter = 1.75): string {
  if (mm === null || mm === undefined) {
    return '-'
  }

  // Volume in mm^3 = pi * r^2 * length
  const radius = diameter / 2
  const volumeMm3 = Math.PI * radius * radius * mm

  // Convert mm^3 to cm^3 (1 cm^3 = 1000 mm^3)
  const volumeCm3 = volumeMm3 / 1000

  // PLA density ~1.24 g/cm^3
  const grams = volumeCm3 * 1.24

  return `${grams.toFixed(1)}g`
}

/**
 * Format date string to locale-specific format
 * @param dateString - ISO date string
 * @returns Formatted date string
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) {
    return '-'
  }

  const date = new Date(dateString)
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

/**
 * Format date string with time
 * @param dateString - ISO date string
 * @returns Formatted date-time string
 */
export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) {
    return '-'
  }

  const date = new Date(dateString)
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param dateString - ISO date string
 * @returns Relative time string
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) {
    return '-'
  }

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) {
    return 'Just now'
  }
  if (diffMins < 60) {
    return `${diffMins}m ago`
  }
  if (diffHours < 24) {
    return `${diffHours}h ago`
  }
  if (diffDays < 7) {
    return `${diffDays}d ago`
  }

  return formatDate(dateString)
}

/**
 * Format percentage with 1 decimal place
 * @param value - Percentage value (0-100)
 * @returns Formatted percentage string
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return '-'
  }
  return `${value.toFixed(1)}%`
}

/**
 * Format temperature in Celsius
 * @param temp - Temperature value
 * @returns Formatted temperature string
 */
export function formatTemp(temp: number | null | undefined): string {
  if (temp === null || temp === undefined) {
    return '-'
  }
  return `${temp}°C`
}

/**
 * Capitalize first letter of a string
 * @param str - String to capitalize
 * @returns Capitalized string
 */
export function capitalize(str: string | null | undefined): string {
  if (!str) {
    return ''
  }
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Format number as currency
 * @param value - Numeric value
 * @param currency - Currency code (default USD)
 * @returns Formatted currency string
 */
export function formatCurrency(value: number | null | undefined, currency = 'USD'): string {
  if (value === null || value === undefined) {
    return '-'
  }
  return new Intl.NumberFormat(undefined, {
    style: 'currency',
    currency,
  }).format(value)
}

/**
 * Humanize a filename into a readable title
 * Removes extension, replaces underscores/hyphens with spaces, capitalizes words
 * @param filename - The filename to humanize (e.g., "benchy_v2.gcode")
 * @returns Humanized title (e.g., "Benchy V2")
 */
export function humanizeFilename(filename: string | null | undefined): string {
  if (!filename) {
    return ''
  }
  // Remove extension
  const name = filename.includes('.') ? filename.split('.').slice(0, -1).join('.') : filename
  // Replace underscores/hyphens with spaces and capitalize each word
  return name
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}
