<script setup lang="ts">
import { ref } from 'vue'
import { usePrinters, useDeletePrinter } from '@/composables/usePrinters'
import { formatRelativeTime } from '@/utils/formatters'
import type { Printer } from '@/types/printer'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import PrinterFormDialog from './PrinterFormDialog.vue'

const confirm = useConfirm()
const toast = useToast()

const { data: printers, isLoading, isError, refetch } = usePrinters(true) // include inactive
const deleteMutation = useDeletePrinter()

const showDialog = ref(false)
const editingPrinter = ref<Printer | null>(null)

function openAddDialog() {
  editingPrinter.value = null
  showDialog.value = true
}

function openEditDialog(printer: Printer) {
  editingPrinter.value = printer
  showDialog.value = true
}

function confirmDelete(printer: Printer) {
  confirm.require({
    message: `Are you sure you want to delete "${printer.name}"? This will also delete all associated print jobs.`,
    header: 'Delete Printer',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    rejectClass: 'p-button-secondary p-button-text',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteMutation.mutateAsync(printer.id)
        toast.add({
          severity: 'success',
          summary: 'Printer Deleted',
          detail: `${printer.name} has been deleted`,
          life: 3000,
        })
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete printer',
          life: 5000,
        })
      }
    },
  })
}

function handleSaved() {
  refetch()
}
</script>

<template>
  <div class="printer-list">
    <div class="list-header">
      <div>
        <h2>Printers</h2>
        <p class="text-muted">Manage your connected 3D printers</p>
      </div>
      <Button label="Add Printer" icon="pi pi-plus" @click="openAddDialog" />
    </div>

    <div v-if="isLoading" class="loading-state">
      <Skeleton v-for="i in 3" :key="i" height="4rem" class="mb-3" />
    </div>

    <div v-else-if="isError" class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <p>Failed to load printers</p>
      <Button label="Retry" severity="secondary" @click="() => refetch()" />
    </div>

    <div v-else-if="!printers?.length" class="empty-state">
      <i class="pi pi-server"></i>
      <h3>No printers yet</h3>
      <p>Add your first printer to start logging print jobs</p>
      <Button label="Add Printer" icon="pi pi-plus" @click="openAddDialog" />
    </div>

    <DataTable v-else :value="printers" class="printers-table" dataKey="id">
      <Column field="name" header="Name" :sortable="true">
        <template #body="{ data }">
          <div class="printer-name">
            <span class="name">{{ data.name }}</span>
            <Tag v-if="!data.is_active" severity="secondary" value="Inactive" />
          </div>
        </template>
      </Column>
      <Column field="printer_type" header="Type" :sortable="true">
        <template #body="{ data }">
          <Tag v-if="data.printer_type" :value="data.printer_type" severity="secondary" />
          <span v-else class="text-muted">-</span>
        </template>
      </Column>
      <Column header="Make / Model" :sortable="false">
        <template #body="{ data }">
          <span v-if="data.make || data.model">
            {{ [data.make, data.model].filter(Boolean).join(' ') }}
          </span>
          <span v-else class="text-muted">-</span>
        </template>
      </Column>
      <Column header="Bed Size" :sortable="false">
        <template #body="{ data }">
          <span v-if="data.bed_x && data.bed_y && data.bed_z" class="bed-size">
            {{ data.bed_x }} × {{ data.bed_y }} × {{ data.bed_z }} mm
          </span>
          <span v-else class="text-muted">-</span>
        </template>
      </Column>
      <Column field="location" header="Location" :sortable="true">
        <template #body="{ data }">
          {{ data.location || '-' }}
        </template>
      </Column>
      <Column field="last_seen" header="Last Seen" :sortable="true">
        <template #body="{ data }">
          {{ formatRelativeTime(data.last_seen) }}
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
              @click="openEditDialog(data)"
              v-tooltip.top="'Edit'"
            />
            <Button
              icon="pi pi-trash"
              severity="danger"
              text
              rounded
              @click="confirmDelete(data)"
              v-tooltip.top="'Delete'"
            />
          </div>
        </template>
      </Column>
    </DataTable>

    <PrinterFormDialog
      v-model:visible="showDialog"
      :printer="editingPrinter"
      @saved="handleSaved"
    />
  </div>
</template>

<style scoped>
.printer-list {
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

.bed-size {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.loading-state {
  padding: 1rem 0;
}

.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px dashed var(--p-surface-border);
  text-align: center;
  gap: 0.5rem;
}

.error-state i,
.empty-state i {
  font-size: 3rem;
  color: var(--p-text-muted-color);
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0.5rem 0 0.25rem;
  color: var(--p-text-color);
}

.empty-state p,
.error-state p {
  color: var(--p-text-muted-color);
  margin: 0 0 1rem;
}

.printers-table {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  overflow: hidden;
}

.printer-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.printer-name .name {
  font-weight: 500;
}

.url {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  background-color: var(--p-surface-ground);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.action-buttons {
  display: flex;
  gap: 0.25rem;
}
</style>
