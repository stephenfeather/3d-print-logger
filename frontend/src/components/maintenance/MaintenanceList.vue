<script setup lang="ts">
/**
 * List component for maintenance records.
 * Issue #9: Minimal Printer Maintenance Details
 */

import { ref, computed } from 'vue'
import { useMaintenance, useDeleteMaintenance } from '@/composables/useMaintenance'
import { usePrinters } from '@/composables/usePrinters'
import { formatDateTime, formatCurrency } from '@/utils/formatters'
import type { Maintenance } from '@/types/maintenance'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Select from 'primevue/select'
import Skeleton from 'primevue/skeleton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import MaintenanceFormDialog from './MaintenanceFormDialog.vue'

const confirm = useConfirm()
const toast = useToast()

// Filters
const selectedPrinter = ref<number | undefined>(undefined)
const selectedDone = ref<boolean | undefined>(undefined)

const filters = computed(() => ({
  printer_id: selectedPrinter.value,
  done: selectedDone.value,
}))

const { data: maintenanceData, isLoading, isError, refetch } = useMaintenance(filters.value)
const { data: printers } = usePrinters()
const deleteMutation = useDeleteMaintenance()

const showDialog = ref(false)
const editingRecord = ref<Maintenance | null>(null)

const printerOptions = computed(() => [
  { label: 'All Printers', value: undefined },
  ...(printers.value || []).map((p) => ({ label: p.name, value: p.id })),
])

const statusOptions = [
  { label: 'All', value: undefined },
  { label: 'Completed', value: true },
  { label: 'Pending', value: false },
]

// Get printer name by ID
const printerMap = computed(() => {
  const map: Record<number, string> = {}
  for (const p of printers.value || []) {
    map[p.id] = p.name
  }
  return map
})

function getPrinterName(printerId: number): string {
  return printerMap.value[printerId] || `Printer ${printerId}`
}

function openAddDialog() {
  editingRecord.value = null
  showDialog.value = true
}

function openEditDialog(record: Maintenance) {
  editingRecord.value = record
  showDialog.value = true
}

function confirmDelete(record: Maintenance) {
  confirm.require({
    message: `Are you sure you want to delete this maintenance record?`,
    header: 'Delete Maintenance Record',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    rejectClass: 'p-button-secondary p-button-text',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteMutation.mutateAsync(record.id)
        toast.add({
          severity: 'success',
          summary: 'Record Deleted',
          detail: 'Maintenance record has been deleted',
          life: 3000,
        })
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete record',
          life: 5000,
        })
      }
    },
  })
}

function handleSaved() {
  refetch()
}

function getCategorySeverity(category: string): "secondary" | "success" | "info" | "warn" | "danger" | "contrast" | undefined {
  switch (category) {
    case 'cleaning':
      return 'info'
    case 'calibration':
      return 'secondary'
    case 'parts_replacement':
      return 'warn'
    case 'repair':
      return 'danger'
    case 'inspection':
      return 'success'
    case 'upgrade':
      return 'contrast'
    default:
      return 'secondary'
  }
}

function formatCategory(category: string): string {
  return category
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<template>
  <div class="maintenance-list">
    <div class="list-header">
      <div>
        <h2>Maintenance Records</h2>
        <p class="text-muted">Track printer maintenance and repairs</p>
      </div>
      <Button label="Add Record" icon="pi pi-plus" @click="openAddDialog" />
    </div>

    <div class="filter-row">
      <Select
        v-model="selectedPrinter"
        :options="printerOptions"
        option-label="label"
        option-value="value"
        placeholder="Filter by Printer"
        class="filter-select"
        @change="refetch()"
      />
      <Select
        v-model="selectedDone"
        :options="statusOptions"
        option-label="label"
        option-value="value"
        placeholder="Filter by Status"
        class="filter-select"
        @change="refetch()"
      />
    </div>

    <div v-if="isLoading" class="loading-state">
      <Skeleton v-for="i in 3" :key="i" height="4rem" class="mb-3" />
    </div>

    <div v-else-if="isError" class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <p>Failed to load maintenance records</p>
      <Button label="Retry" severity="secondary" @click="() => refetch()" />
    </div>

    <div v-else-if="!maintenanceData?.items?.length" class="empty-state">
      <i class="pi pi-wrench"></i>
      <h3>No maintenance records yet</h3>
      <p>Start tracking your printer maintenance</p>
      <Button label="Add Record" icon="pi pi-plus" @click="openAddDialog" />
    </div>

    <DataTable v-else :value="maintenanceData.items" class="maintenance-table" dataKey="id">
      <Column field="date" header="Date" :sortable="true">
        <template #body="{ data }">
          {{ formatDateTime(data.date) }}
        </template>
      </Column>
      <Column header="Printer" :sortable="true">
        <template #body="{ data }">
          {{ getPrinterName(data.printer_id) }}
        </template>
      </Column>
      <Column field="category" header="Category" :sortable="true">
        <template #body="{ data }">
          <Tag :value="formatCategory(data.category)" :severity="getCategorySeverity(data.category)" />
        </template>
      </Column>
      <Column field="description" header="Description" :sortable="false">
        <template #body="{ data }">
          <span class="description-cell">{{ data.description }}</span>
        </template>
      </Column>
      <Column field="done" header="Status" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          <Tag
            :value="data.done ? 'Completed' : 'Pending'"
            :severity="data.done ? 'success' : 'warn'"
          />
        </template>
      </Column>
      <Column field="cost" header="Cost" :sortable="true" style="width: 100px">
        <template #body="{ data }">
          <span v-if="data.cost !== null">{{ formatCurrency(data.cost) }}</span>
          <span v-else class="text-muted">-</span>
        </template>
      </Column>
      <Column header="Actions" :exportable="false" style="width: 120px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button
              icon="pi pi-pencil"
              severity="secondary"
              text
              rounded
              v-tooltip.top="'Edit'"
              @click="openEditDialog(data)"
            />
            <Button
              icon="pi pi-trash"
              severity="danger"
              text
              rounded
              v-tooltip.top="'Delete'"
              @click="confirmDelete(data)"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <MaintenanceFormDialog
      v-model:visible="showDialog"
      :record="editingRecord"
      @saved="handleSaved"
    />
  </div>
</template>

<style scoped>
.maintenance-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.list-header h2 {
  margin: 0 0 0.25rem 0;
  color: var(--p-text-color);
}

.text-muted {
  color: var(--p-text-muted-color);
  margin: 0;
}

.filter-row {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-select {
  min-width: 180px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
  text-align: center;
}

.loading-state {
  align-items: stretch;
  padding: 1rem;
}

.error-state i,
.empty-state i {
  font-size: 3rem;
  color: var(--p-text-muted-color);
  opacity: 0.5;
  margin-bottom: 1rem;
}

.error-state p,
.empty-state p {
  color: var(--p-text-muted-color);
  margin: 0.5rem 0 1rem;
}

.empty-state h3 {
  margin: 0;
  color: var(--p-text-color);
}

.maintenance-table {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
}

.description-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}

.mb-3 {
  margin-bottom: 0.75rem;
}
</style>
