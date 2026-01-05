<script setup lang="ts">
import { formatDuration, formatDateTime, formatTemp, formatFilament } from '@/utils/formatters'
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS } from '@/utils/constants'
import type { PrintJob, JobStatus } from '@/types/job'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'

defineProps<{
  visible: boolean
  job: PrintJob | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

function getStatusColor(status: string): string {
  return JOB_STATUS_COLORS[status as JobStatus] || 'secondary'
}

function getStatusLabel(status: string): string {
  return JOB_STATUS_LABELS[status as JobStatus] || status
}

function handleClose() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="visible"
    header="Job Details"
    :modal="true"
    :style="{ width: '600px' }"
    @update:visible="handleClose"
  >
    <div v-if="job" class="job-details">
      <div class="detail-header">
        <h3 class="filename">{{ job.filename }}</h3>
        <Tag :severity="getStatusColor(job.status)">{{ getStatusLabel(job.status) }}</Tag>
      </div>

      <div class="details-grid">
        <div class="detail-section">
          <h4>Print Information</h4>
          <dl class="detail-list">
            <div class="detail-item">
              <dt>Job ID</dt>
              <dd><code>{{ job.job_id }}</code></dd>
            </div>
            <div class="detail-item">
              <dt>Printer ID</dt>
              <dd>{{ job.printer_id }}</dd>
            </div>
            <div class="detail-item">
              <dt>Start Time</dt>
              <dd>{{ formatDateTime(job.start_time) }}</dd>
            </div>
            <div class="detail-item">
              <dt>End Time</dt>
              <dd>{{ formatDateTime(job.end_time) }}</dd>
            </div>
            <div class="detail-item">
              <dt>Print Duration</dt>
              <dd>{{ formatDuration(job.print_duration) }}</dd>
            </div>
            <div class="detail-item">
              <dt>Total Duration</dt>
              <dd>{{ formatDuration(job.total_duration) }}</dd>
            </div>
            <div class="detail-item">
              <dt>Filament Used</dt>
              <dd>{{ formatFilament(job.filament_used) }}</dd>
            </div>
          </dl>
        </div>

        <div v-if="job.details" class="detail-section">
          <h4>Slicer Settings</h4>
          <dl class="detail-list">
            <div v-if="job.details.layer_height" class="detail-item">
              <dt>Layer Height</dt>
              <dd>{{ job.details.layer_height }}mm</dd>
            </div>
            <div v-if="job.details.first_layer_height" class="detail-item">
              <dt>First Layer</dt>
              <dd>{{ job.details.first_layer_height }}mm</dd>
            </div>
            <div v-if="job.details.nozzle_temp" class="detail-item">
              <dt>Nozzle Temp</dt>
              <dd>{{ formatTemp(job.details.nozzle_temp) }}</dd>
            </div>
            <div v-if="job.details.bed_temp" class="detail-item">
              <dt>Bed Temp</dt>
              <dd>{{ formatTemp(job.details.bed_temp) }}</dd>
            </div>
            <div v-if="job.details.print_speed" class="detail-item">
              <dt>Print Speed</dt>
              <dd>{{ job.details.print_speed }}mm/s</dd>
            </div>
            <div v-if="job.details.infill_percentage" class="detail-item">
              <dt>Infill</dt>
              <dd>{{ job.details.infill_percentage }}%</dd>
            </div>
            <div v-if="job.details.filament_type" class="detail-item">
              <dt>Filament Type</dt>
              <dd>{{ job.details.filament_type }}</dd>
            </div>
            <div v-if="job.details.filament_brand" class="detail-item">
              <dt>Filament Brand</dt>
              <dd>{{ job.details.filament_brand }}</dd>
            </div>
            <div v-if="job.details.layer_count" class="detail-item">
              <dt>Layer Count</dt>
              <dd>{{ job.details.layer_count }}</dd>
            </div>
            <div v-if="job.details.object_height" class="detail-item">
              <dt>Object Height</dt>
              <dd>{{ job.details.object_height }}mm</dd>
            </div>
            <div v-if="job.details.support_enabled !== null" class="detail-item">
              <dt>Supports</dt>
              <dd>{{ job.details.support_enabled ? 'Yes' : 'No' }}</dd>
            </div>
          </dl>
        </div>

        <div v-else class="detail-section no-details">
          <h4>Slicer Settings</h4>
          <p>No detailed metadata available for this job</p>
        </div>
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.job-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--p-surface-border);
}

.filename {
  margin: 0;
  font-size: 1.1rem;
  word-break: break-all;
}

.details-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 600px) {
  .details-grid {
    grid-template-columns: 1fr;
  }
}

.detail-section h4 {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--p-text-muted-color);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.detail-list {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.detail-item dt {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.detail-item dd {
  margin: 0;
  font-weight: 500;
  text-align: right;
}

.detail-item code {
  font-size: 0.75rem;
  background-color: var(--p-surface-ground);
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
}

.no-details p {
  color: var(--p-text-muted-color);
  font-style: italic;
}
</style>
