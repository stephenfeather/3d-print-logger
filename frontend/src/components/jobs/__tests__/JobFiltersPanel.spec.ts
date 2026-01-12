import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import JobFiltersPanel from '../JobFiltersPanel.vue'

// Mock the composable
vi.mock('@/composables/usePrinters', () => ({
  usePrinters: () => ({
    data: { value: [] },
  }),
}))

describe('JobFiltersPanel', () => {
  it('associates printer label with select control', () => {
    const wrapper = mount(JobFiltersPanel)

    const printerLabel = wrapper.find('label')
    const printerSelect = wrapper.findComponent({ name: 'Select' })

    // Label should have an 'id' attribute
    expect(printerLabel.attributes('id')).toBeDefined()

    // Select should have matching 'aria-labelledby' attribute
    expect(printerSelect.attributes('aria-labelledby')).toBe(printerLabel.attributes('id'))
  })

  it('associates status label with select control', () => {
    const wrapper = mount(JobFiltersPanel)

    const labels = wrapper.findAll('label')
    const statusLabel = labels[1] // Second label
    const selects = wrapper.findAllComponents({ name: 'Select' })
    const statusSelect = selects[1] // Second select

    // Label should have an 'id' attribute
    expect(statusLabel.attributes('id')).toBeDefined()

    // Select should have matching 'aria-labelledby' attribute
    expect(statusSelect.attributes('aria-labelledby')).toBe(statusLabel.attributes('id'))
  })

  it('associates date range label with datepicker control', () => {
    const wrapper = mount(JobFiltersPanel)

    const labels = wrapper.findAll('label')
    const dateLabel = labels[2] // Third label
    const datePicker = wrapper.findComponent({ name: 'DatePicker' })

    // Label should have an 'id' attribute
    expect(dateLabel.attributes('id')).toBeDefined()

    // DatePicker should have matching 'aria-labelledby' attribute
    expect(datePicker.attributes('aria-labelledby')).toBe(dateLabel.attributes('id'))
  })
})
