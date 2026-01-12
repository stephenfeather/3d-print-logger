<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { formatDuration, formatDateTime, formatTemp, formatFilament, humanizeFilename } from '@/utils/formatters'
import { JOB_STATUS_COLORS, JOB_STATUS_LABELS } from '@/utils/constants'
import { useUpdateJob } from '@/composables/useJobs'
import type { PrintJob, JobStatus } from '@/types/job'
import Dialog from 'primevue/dialog'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const props = defineProps<{
  visible: boolean
  job: PrintJob | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const toast = useToast()
const updateMutation = useUpdateJob()

const isEditing = ref(false)
const editTitle = ref('')
const editUrl = ref('')

watch(
  () => props.job,
  (newJob) => {
    if (newJob) {
      editTitle.value = newJob.title || humanizeFilename(newJob.filename)
      editUrl.value = newJob.url || ''
    }
    isEditing.value = false
  },
  { immediate: true }
)

const displayTitle = computed(() => {
  if (!props.job) return ''
  return props.job.title || humanizeFilename(props.job.filename)
})

const estimatedCompletion = computed(() => {
  if (!props.job?.start_time || !props.job?.details?.estimated_time) return null
  const startTime = new Date(props.job.start_time)
  const completionTime = new Date(startTime.getTime() + props.job.details.estimated_time * 1000)
  return completionTime.toISOString()
})

function getStatusColor(status: string): string {
  return JOB_STATUS_COLORS[status as JobStatus] || 'secondary'
}

function getStatusLabel(status: string): string {
  return JOB_STATUS_LABELS[status as JobStatus] || status
}

function handleClose() {
  isEditing.value = false
  emit('update:visible', false)
}

function startEditing() {
  if (props.job) {
    editTitle.value = props.job.title || humanizeFilename(props.job.filename)
    editUrl.value = props.job.url || ''
  }
  isEditing.value = true
}

function cancelEditing() {
  if (props.job) {
    editTitle.value = props.job.title || humanizeFilename(props.job.filename)
    editUrl.value = props.job.url || ''
  }
  isEditing.value = false
}

async function saveChanges() {
  if (!props.job) return

  try {
    await updateMutation.mutateAsync({
      id: props.job.id,
      data: {
        title: editTitle.value || null,
        url: editUrl.value || null,
      },
    })
    isEditing.value = false
    toast.add({
      severity: 'success',
      summary: 'Job Updated',
      detail: 'Job details have been saved',
      life: 3000,
    })
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to update job',
      life: 5000,
    })
  }
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
        <div class="header-content">
          <div v-if="job.details?.thumbnail_base64" class="detail-thumbnail">
            <img
              :src="`data:image/png;base64,${job.details.thumbnail_base64}`"
              :alt="job.filename"
              class="detail-thumbnail-img"
            />
          </div>
          <div class="header-text">
            <div v-if="isEditing" class="edit-title-section">
              <InputText
                v-model="editTitle"
                placeholder="Job title"
                class="title-input"
              />
            </div>
            <h3 v-else class="filename">{{ displayTitle }}</h3>
            <p v-if="job.title && job.filename !== displayTitle" class="original-filename">
              {{ job.filename }}
            </p>
            <Tag :severity="getStatusColor(job.status)">{{ getStatusLabel(job.status) }}</Tag>
          </div>
        </div>
        <div class="header-actions">
          <template v-if="isEditing">
            <Button
              icon="pi pi-check"
              severity="success"
              text
              rounded
              :loading="updateMutation.isPending.value"
              @click="saveChanges"
              v-tooltip.top="'Save'"
            />
            <Button
              icon="pi pi-times"
              severity="secondary"
              text
              rounded
              @click="cancelEditing"
              v-tooltip.top="'Cancel'"
            />
          </template>
          <Button
            v-else
            icon="pi pi-pencil"
            severity="secondary"
            text
            rounded
            @click="startEditing"
            v-tooltip.top="'Edit'"
          />
        </div>
      </div>

      <div v-if="isEditing" class="edit-url-section">
        <label for="edit-url" class="edit-label">Model URL</label>
        <InputText
          id="edit-url"
          v-model="editUrl"
          placeholder="https://www.thingiverse.com/thing:..."
          class="url-input"
        />
      </div>

      <div v-else-if="job.url" class="url-display">
        <span class="url-label">Model:</span>
        <a :href="job.url" target="_blank" rel="noopener noreferrer" class="url-link">
          {{ job.url }}
          <i class="pi pi-external-link"></i>
        </a>
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
            <div v-if="job.status === 'printing' && estimatedCompletion" class="detail-item">
              <dt>Est. Completion</dt>
              <dd>{{ formatDateTime(estimatedCompletion) }}</dd>
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
            <div v-if="job.details.slicer_name" class="detail-item">
              <dt>Slicer</dt>
              <dd>{{ job.details.slicer_name }}</dd>
            </div>
            <div v-if="job.details.slicer_version" class="detail-item">
              <dt>Version</dt>
              <dd>{{ job.details.slicer_version }}</dd>
            </div>
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
            <div v-if="job.details.total_filament_used_g" class="detail-item">
              <dt>Total Filament</dt>
              <dd>{{ job.details.total_filament_used_g.toFixed(2) }}g</dd>
            </div>
            <div v-if="job.details.total_filament_cost" class="detail-item">
              <dt>Total Cost</dt>
              <dd>${{ job.details.total_filament_cost.toFixed(2) }}</dd>
            </div>
          </dl>
        </div>

        <div v-else class="detail-section no-details">
          <h4>Slicer Settings</h4>
          <p>No detailed metadata available for this job</p>
        </div>

        <!-- Multi-extruder filament usage (spans full width if present) -->
        <div
          v-if="job.details && (job.details.filament_used_g || job.details.filament_cost)"
          class="detail-section detail-section-full"
        >
          <h4>Per-Extruder Filament Usage</h4>
          <div v-if="job.details.filament_used_g" class="extruder-grid">
            <div
              v-for="(amount, index) in job.details.filament_used_g"
              :key="`extruder-${index}`"
              class="extruder-card"
            >
              <div class="extruder-label">Extruder {{ index + 1 }}</div>
              <dl class="detail-list">
                <div v-if="job.details.filament_used_g && job.details.filament_used_g[index]" class="detail-item">
                  <dt>Weight</dt>
                  <dd>{{ job.details.filament_used_g[index].toFixed(2) }}g</dd>
                </div>
                <div v-if="job.details.filament_used_mm && job.details.filament_used_mm[index]" class="detail-item">
                  <dt>Length</dt>
                  <dd>{{ (job.details.filament_used_mm[index] / 1000).toFixed(2) }}m</dd>
                </div>
                <div v-if="job.details.filament_used_cm3 && job.details.filament_used_cm3[index]" class="detail-item">
                  <dt>Volume</dt>
                  <dd>{{ job.details.filament_used_cm3[index].toFixed(2) }}cm³</dd>
                </div>
                <div v-if="job.details.filament_cost && job.details.filament_cost[index]" class="detail-item">
                  <dt>Cost</dt>
                  <dd>${{ job.details.filament_cost[index].toFixed(2) }}</dd>
                </div>
              </dl>
            </div>
          </div>
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
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--p-surface-border);
}

.header-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  flex: 1;
}

.header-actions {
  display: flex;
  gap: 0.25rem;
}

.detail-thumbnail {
  flex-shrink: 0;
}

.detail-thumbnail-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  background-color: var(--p-surface-ground);
}

.header-text {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 0;
  flex: 1;
}

.filename {
  margin: 0;
  font-size: 1.1rem;
  word-break: break-all;
}

.original-filename {
  margin: 0;
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

.edit-title-section {
  width: 100%;
}

.title-input {
  width: 100%;
}

.edit-url-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.edit-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--p-text-muted-color);
}

.url-input {
  width: 100%;
}

.url-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: var(--p-surface-ground);
  border-radius: 8px;
}

.url-label {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.url-link {
  color: var(--p-primary-color);
  text-decoration: none;
  word-break: break-all;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.url-link:hover {
  text-decoration: underline;
}

.url-link i {
  font-size: 0.75rem;
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

.detail-section-full {
  grid-column: 1 / -1;
}

.extruder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.extruder-card {
  background-color: var(--p-surface-ground);
  border: 1px solid var(--p-surface-border);
  border-radius: 8px;
  padding: 1rem;
}

.extruder-label {
  font-weight: 600;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: var(--p-primary-color);
}

@media (max-width: 600px) {
  .extruder-grid {
    grid-template-columns: 1fr;
  }
}
</style>
