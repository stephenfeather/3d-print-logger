import { describe, it, expect } from 'vitest'

/**
 * Normalize filename to title
 * - Remove file extension
 * - Replace underscores and hyphens with spaces
 * - Capitalize first letter of each word
 */
function normalizeTitle(filename: string): string {
  const name = filename.includes('.') ? filename.split('.').slice(0, -1).join('.') : filename
  return name.replaceAll(/[_-]+/, ' ').replaceAll(/\b\w/, (c) => c.toUpperCase())
}

describe('normalizeTitle', () => {
  it('removes file extension', () => {
    expect(normalizeTitle('test_file.gcode')).toBe('Test File')
  })

  it('replaces underscores with spaces', () => {
    expect(normalizeTitle('my_print_name.gcode')).toBe('My Print Name')
  })

  it('replaces hyphens with spaces', () => {
    expect(normalizeTitle('my-print-name.gcode')).toBe('My Print Name')
  })

  it('replaces multiple consecutive underscores/hyphens with single space', () => {
    expect(normalizeTitle('my___print---name.gcode')).toBe('My Print Name')
  })

  it('capitalizes first letter of each word', () => {
    expect(normalizeTitle('test_file.gcode')).toBe('Test File')
  })

  it('handles mixed underscores and hyphens', () => {
    expect(normalizeTitle('test_-_file.gcode')).toBe('Test File')
  })

  it('handles filename without extension', () => {
    expect(normalizeTitle('test_file')).toBe('Test File')
  })

  it('handles filename with multiple dots', () => {
    expect(normalizeTitle('my.backup.gcode')).toBe('My.backup')
  })
})
