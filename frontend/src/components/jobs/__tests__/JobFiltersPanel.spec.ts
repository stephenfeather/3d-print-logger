import { describe, it, expect, vi, beforeEach } from 'vitest'
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

    // Label should have a 'for' attribute
    expect(printerLabel.attributes('for')).toBeDefined()

    // Select should have matching 'id' attribute
    expect(printerSelect.attributes('id')).toBe(printerLabel.attributes('for'))
  })

  it('associates status label with select control', () => {
    const wrapper = mount(JobFiltersPanel)

    const labels = wrapper.findAll('label')
    const statusLabel = labels[1] // Second label
    const selects = wrapper.findAllComponents({ name: 'Select' })
    const statusSelect = selects[1] // Second select

    // Label should have a 'for' attribute
    expect(statusLabel.attributes('for')).toBeDefined()

    // Select should have matching 'id' attribute
    expect(statusSelect.attributes('id')).toBe(statusLabel.attributes('for'))
  })

  it('associates date range label with datepicker control', () => {
    const wrapper = mount(JobFiltersPanel)

    const labels = wrapper.findAll('label')
    const dateLabel = labels[2] // Third label
    const datePicker = wrapper.findComponent({ name: 'DatePicker' })

    // Label should have a 'for' attribute
    expect(dateLabel.attributes('for')).toBeDefined()

    // DatePicker should have matching 'id' attribute
    expect(datePicker.attributes('id')).toBe(dateLabel.attributes('for'))
  })
})
