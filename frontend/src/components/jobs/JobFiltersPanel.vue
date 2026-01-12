<script setup lang="ts">
import { ref, watch } from 'vue'
import { usePrinters } from '@/composables/usePrinters'
import type { JobStatus } from '@/types/job'
import Select from 'primevue/select'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'

const props = defineProps<{
  printerId?: number
  status?: JobStatus
  startAfter?: string
  startBefore?: string
}>()

const emit = defineEmits<{
  'update:printerId': [value: number | undefined]
  'update:status': [value: JobStatus | undefined]
  'update:startAfter': [value: string | undefined]
  'update:startBefore': [value: string | undefined]
  reset: []
}>()

const { data: printers } = usePrinters()

const statusOptions = [
  { label: 'All Statuses', value: undefined },
  { label: 'Completed', value: 'completed' },
  { label: 'Failed', value: 'error' },
  { label: 'Cancelled', value: 'cancelled' },
  { label: 'Printing', value: 'printing' },
  { label: 'Paused', value: 'paused' },
]

const selectedPrinter = ref<number | undefined>(props.printerId)
const selectedStatus = ref<JobStatus | undefined>(props.status)
const dateRange = ref<Date[] | undefined>(
  props.startAfter && props.startBefore
    ? [new Date(props.startAfter), new Date(props.startBefore)]
    : undefined,
)

watch(selectedPrinter, (val) => emit('update:printerId', val))
watch(selectedStatus, (val) => emit('update:status', val))
watch(dateRange, (val) => {
  if (val && val.length === 2 && val[0] && val[1]) {
    emit('update:startAfter', val[0].toISOString())
    emit('update:startBefore', val[1].toISOString())
  } else {
    emit('update:startAfter', undefined)
    emit('update:startBefore', undefined)
  }
})

function handleReset() {
  selectedPrinter.value = undefined
  selectedStatus.value = undefined
  dateRange.value = undefined
  emit('reset')
}

const printerOptions = ref<Array<{ label: string; value: number | undefined }>>([])

watch(
  printers,
  (val) => {
    printerOptions.value = [
      { label: 'All Printers', value: undefined },
      ...(val?.map((p) => ({ label: p.name, value: p.id })) || []),
    ]
  },
  { immediate: true },
)
</script>

<template>
  <div class="filters-panel">
    <div class="filter-group">
      <label id="printer-label">Printer</label>
      <Select
        aria-labelledby="printer-label"
        v-model="selectedPrinter"
        :options="printerOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="All Printers"
        class="filter-select"
      />
    </div>

    <div class="filter-group">
      <label id="status-label">Status</label>
      <Select
        aria-labelledby="status-label"
        v-model="selectedStatus"
        :options="statusOptions"
        optionLabel="label"
        optionValue="value"
        placeholder="All Statuses"
        class="filter-select"
      />
    </div>

    <div class="filter-group">
      <label id="date-range-label">Date Range</label>
      <DatePicker
        aria-labelledby="date-range-label"
        v-model="dateRange"
        selectionMode="range"
        :manualInput="false"
        placeholder="Select date range"
        dateFormat="M d, yy"
        class="filter-date"
        showIcon
      />
    </div>

    <div class="filter-actions">
      <Button
        label="Reset"
        severity="secondary"
        text
        size="small"
        @click="handleReset"
        icon="pi pi-refresh"
      />
    </div>
  </div>
</template>

<style scoped>
.filters-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  padding: 1rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
  margin-bottom: 1rem;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 180px;
}

.filter-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.filter-select,
.filter-date {
  width: 100%;
}

.filter-actions {
  margin-left: auto;
  display: flex;
  align-items: flex-end;
}

@media (max-width: 768px) {
  .filters-panel {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    width: 100%;
  }

  .filter-actions {
    margin-left: 0;
    margin-top: 0.5rem;
  }
}
</style>
