<script setup lang="ts">
import { useRecentJobs } from '@/composables/useJobs'
import { formatDuration, formatRelativeTime } from '@/utils/formatters'
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS } from '@/utils/constants'
import type { JobStatus } from '@/types/job'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'

const { data: recentJobs, isLoading, isError } = useRecentJobs(5)

function getStatusColor(status: string): string {
  return JOB_STATUS_COLORS[status as JobStatus] || 'secondary'
}

function getStatusLabel(status: string): string {
  return JOB_STATUS_LABELS[status as JobStatus] || status
}
</script>

<template>
  <div class="recent-jobs-card">
    <div class="card-header">
      <h3>Recent Print Jobs</h3>
      <router-link to="/prints" class="view-all-link">View all</router-link>
    </div>

    <div v-if="isLoading" class="loading-state">
      <Skeleton v-for="i in 5" :key="i" height="3rem" class="mb-2" />
    </div>

    <div v-else-if="isError" class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <span>Failed to load recent jobs</span>
    </div>

    <div v-else-if="!recentJobs?.items.length" class="empty-state">
      <i class="pi pi-inbox"></i>
      <span>No print jobs yet</span>
    </div>

    <DataTable v-else :value="recentJobs.items" :rows="5" class="recent-jobs-table">
      <Column header="" style="width: 50px">
        <template #body="{ data }">
          <div v-if="data.details?.thumbnail_base64" class="thumbnail-mini">
            <img
              :src="`data:image/png;base64,${data.details.thumbnail_base64}`"
              :alt="data.filename"
            />
          </div>
          <div v-else class="thumbnail-placeholder-mini">
            <i class="pi pi-box"></i>
          </div>
        </template>
      </Column>
      <Column field="filename" header="File">
        <template #body="{ data }">
          <span class="filename" :title="data.filename">{{ data.filename }}</span>
        </template>
      </Column>
      <Column field="status" header="Status">
        <template #body="{ data }">
          <Tag :severity="getStatusColor(data.status)">
            {{ getStatusLabel(data.status) }}
          </Tag>
        </template>
      </Column>
      <Column field="print_duration" header="Duration">
        <template #body="{ data }">
          {{ formatDuration(data.print_duration) }}
        </template>
      </Column>
      <Column field="start_time" header="Started">
        <template #body="{ data }">
          {{ formatRelativeTime(data.start_time) }}
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.recent-jobs-card {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
  padding: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.view-all-link {
  font-size: 0.875rem;
  color: var(--p-primary-color);
  text-decoration: none;
}

.view-all-link:hover {
  text-decoration: underline;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
  gap: 0.5rem;
}

.loading-state {
  align-items: stretch;
}

.error-state i,
.empty-state i {
  font-size: 2rem;
  opacity: 0.5;
}

.filename {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.thumbnail-mini img {
  width: 32px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  background-color: var(--p-surface-ground);
}

.thumbnail-placeholder-mini {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--p-surface-ground);
  border-radius: 4px;
  color: var(--p-text-muted-color);
  opacity: 0.5;
  font-size: 0.75rem;
}

:deep(.recent-jobs-table) {
  font-size: 0.875rem;
}

:deep(.recent-jobs-table .p-datatable-header) {
  display: none;
}
</style>
