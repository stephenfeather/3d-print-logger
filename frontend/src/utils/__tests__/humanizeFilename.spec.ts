import { describe, it, expect } from 'vitest'
import { humanizeFilename } from '../formatters'

describe('humanizeFilename', () => {
  it('removes file extension', () => {
    expect(humanizeFilename('test_file.gcode')).toBe('Test File')
  })

  it('replaces underscores with spaces', () => {
    expect(humanizeFilename('my_print_name.gcode')).toBe('My Print Name')
  })

  it('replaces hyphens with spaces', () => {
    expect(humanizeFilename('my-print-name.gcode')).toBe('My Print Name')
  })

  it('replaces multiple consecutive underscores/hyphens with single space', () => {
    expect(humanizeFilename('my___print---name.gcode')).toBe('My Print Name')
  })

  it('capitalizes first letter of each word', () => {
    expect(humanizeFilename('test_file.gcode')).toBe('Test File')
  })

  it('handles mixed underscores and hyphens', () => {
    expect(humanizeFilename('test_-_file.gcode')).toBe('Test File')
  })

  it('handles filename without extension', () => {
    expect(humanizeFilename('test_file')).toBe('Test File')
  })

  it('handles filename with multiple dots', () => {
    expect(humanizeFilename('my.backup.gcode')).toBe('My.backup')
  })

  it('handles null input', () => {
    expect(humanizeFilename(null)).toBe('')
  })

  it('handles undefined input', () => {
    expect(humanizeFilename(undefined)).toBe('')
  })

  it('handles empty string', () => {
    expect(humanizeFilename('')).toBe('')
  })
})
