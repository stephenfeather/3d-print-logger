<script setup lang="ts">
import { ref, computed } from 'vue'
import { useJobs, useDeleteJob } from '@/composables/useJobs'
import { formatDuration, formatDateTime } from '@/utils/formatters'
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS, PAGE_SIZE_OPTIONS } from '@/utils/constants'
import type { JobStatus, PrintJob } from '@/types/job'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import Paginator from 'primevue/paginator'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import JobFiltersPanel from './JobFiltersPanel.vue'
import JobDetailsModal from './JobDetailsModal.vue'

const confirm = useConfirm()
const toast = useToast()

const {
  data: jobs,
  isLoading,
  isError,
  refetch,
  filters,
  setPage,
  setPageSize,
  setStatus,
  setPrinter,
  setDateRange,
  updateFilters,
} = useJobs()

const deleteMutation = useDeleteJob()

const showDetailsModal = ref(false)
const selectedJob = ref<PrintJob | null>(null)

function getStatusColor(status: string): string {
  return JOB_STATUS_COLORS[status as JobStatus] || 'secondary'
}

function getStatusLabel(status: string): string {
  return JOB_STATUS_LABELS[status as JobStatus] || status
}

function openDetails(job: PrintJob) {
  selectedJob.value = job
  showDetailsModal.value = true
}

function confirmDelete(job: PrintJob) {
  confirm.require({
    message: `Are you sure you want to delete the job for "${job.filename}"?`,
    header: 'Delete Job',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Delete',
    rejectClass: 'p-button-secondary p-button-text',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await deleteMutation.mutateAsync(job.id)
        toast.add({
          severity: 'success',
          summary: 'Job Deleted',
          detail: 'Job has been deleted',
          life: 3000,
        })
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete job',
          life: 5000,
        })
      }
    },
  })
}

function handlePageChange(event: { page: number; rows: number }) {
  if (event.rows !== filters.value.limit) {
    setPageSize(event.rows)
  } else {
    setPage(event.page + 1)
  }
}

function handleResetFilters() {
  updateFilters({
    printer_id: undefined,
    status: undefined,
    start_after: undefined,
    start_before: undefined,
  })
}

const first = computed(() => filters.value.offset)
</script>

<template>
  <div class="jobs-table-container">
    <JobFiltersPanel
      :printer-id="filters.printer_id"
      :status="filters.status"
      :start-after="filters.start_after"
      :start-before="filters.start_before"
      @update:printer-id="setPrinter"
      @update:status="setStatus"
      @update:start-after="(v) => setDateRange(v, filters.start_before)"
      @update:start-before="(v) => setDateRange(filters.start_after, v)"
      @reset="handleResetFilters"
    />

    <div v-if="isLoading" class="loading-state">
      <Skeleton v-for="i in 5" :key="i" height="3rem" class="mb-2" />
    </div>

    <div v-else-if="isError" class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <p>Failed to load jobs</p>
      <Button label="Retry" severity="secondary" @click="() => refetch()" />
    </div>

    <div v-else-if="!jobs?.items.length" class="empty-state">
      <i class="pi pi-inbox"></i>
      <h3>No print jobs found</h3>
      <p v-if="filters.printer_id || filters.status || filters.start_after">
        Try adjusting your filters
      </p>
      <p v-else>Print jobs will appear here once you start printing</p>
    </div>

    <template v-else>
      <DataTable :value="jobs.items" class="jobs-table" dataKey="id">
        <Column header="" style="width: 70px">
          <template #body="{ data }">
            <div v-if="data.details?.thumbnail_base64" class="thumbnail-container">
              <img
                :src="`data:image/png;base64,${data.details.thumbnail_base64}`"
                :alt="data.filename"
                class="job-thumbnail"
              />
            </div>
            <div v-else class="thumbnail-placeholder">
              <i class="pi pi-box"></i>
            </div>
          </template>
        </Column>
        <Column field="filename" header="File" :sortable="false">
          <template #body="{ data }">
            <span class="filename" :title="data.filename">{{ data.filename }}</span>
          </template>
        </Column>
        <Column field="status" header="Status" style="width: 120px">
          <template #body="{ data }">
            <Tag :severity="getStatusColor(data.status)">
              {{ getStatusLabel(data.status) }}
            </Tag>
          </template>
        </Column>
        <Column field="print_duration" header="Duration" style="width: 100px">
          <template #body="{ data }">
            {{ formatDuration(data.print_duration) }}
          </template>
        </Column>
        <Column field="start_time" header="Started" style="width: 180px">
          <template #body="{ data }">
            {{ formatDateTime(data.start_time) }}
          </template>
        </Column>
        <Column header="Actions" :exportable="false" style="width: 100px">
          <template #body="{ data }">
            <div class="action-buttons">
              <Button
                icon="pi pi-eye"
                severity="secondary"
                text
                rounded
                @click="openDetails(data)"
                v-tooltip.top="'View Details'"
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

      <Paginator
        :first="first"
        :rows="filters.limit"
        :totalRecords="jobs.total"
        :rowsPerPageOptions="PAGE_SIZE_OPTIONS"
        @page="handlePageChange"
        class="jobs-paginator"
      />
    </template>

    <JobDetailsModal v-model:visible="showDetailsModal" :job="selectedJob" />
  </div>
</template>

<style scoped>
.jobs-table-container {
  display: flex;
  flex-direction: column;
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
  margin: 0;
}

.jobs-table {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  overflow: hidden;
}

.filename {
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

.thumbnail-container {
  width: 50px;
  height: 50px;
}

.job-thumbnail {
  width: 50px;
  height: 50px;
  object-fit: cover;
  border-radius: 4px;
  background-color: var(--p-surface-ground);
}

.thumbnail-placeholder {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--p-surface-ground);
  border-radius: 4px;
  color: var(--p-text-muted-color);
  opacity: 0.5;
}

.jobs-paginator {
  margin-top: 1rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
}
</style>
