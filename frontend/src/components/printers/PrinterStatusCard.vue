<script setup lang="ts">
import { computed } from 'vue'
import { usePrinterStatus } from '@/composables/usePrinters'
import { formatRelativeTime, formatPercent, capitalize } from '@/utils/formatters'
import type { Printer } from '@/types/printer'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Skeleton from 'primevue/skeleton'

const props = defineProps<{
  printer: Printer
}>()

const { data: status, isLoading, isError } = usePrinterStatus(props.printer.id)

const statusSeverity = computed(() => {
  if (!status.value?.is_connected) return 'secondary'
  switch (status.value?.state) {
    case 'printing':
      return 'info'
    case 'paused':
      return 'warn'
    case 'error':
      return 'danger'
    case 'complete':
      return 'success'
    default:
      return 'secondary'
  }
})

const statusLabel = computed(() => {
  if (!status.value?.is_connected) return 'Offline'
  return capitalize(status.value?.state) || 'Idle'
})

const isCurrentlyPrinting = computed(
  () => status.value?.state === 'printing' || status.value?.state === 'paused',
)
</script>

<template>
  <Card class="printer-status-card">
    <template #title>
      <div class="card-title">
        <span class="printer-name">{{ printer.name }}</span>
        <Tag v-if="!isLoading" :severity="statusSeverity">{{ statusLabel }}</Tag>
        <Skeleton v-else width="60px" height="1.5rem" />
      </div>
    </template>
    <template #subtitle>
      <span class="printer-location">{{ printer.location || 'No location set' }}</span>
    </template>
    <template #content>
      <div v-if="isLoading" class="loading-content">
        <Skeleton height="2rem" class="mb-2" />
        <Skeleton height="1rem" />
      </div>

      <div v-else-if="isError" class="error-content">
        <i class="pi pi-exclamation-circle"></i>
        <span>Unable to fetch status</span>
      </div>

      <div v-else-if="isCurrentlyPrinting && status" class="printing-content">
        <div class="current-file">
          <i class="pi pi-file"></i>
          <span class="file-name" :title="status.current_file || undefined">
            {{ status.current_file || 'Unknown file' }}
          </span>
        </div>
        <ProgressBar :value="status.progress || 0" :showValue="false" class="print-progress" />
        <div class="progress-info">
          <span>{{ formatPercent(status.progress) }}</span>
        </div>
      </div>

      <div v-else class="idle-content">
        <div class="last-seen">
          <i class="pi pi-clock"></i>
          <span>Last seen: {{ formatRelativeTime(printer.last_seen) }}</span>
        </div>
      </div>
    </template>
  </Card>
</template>

<style scoped>
.printer-status-card {
  height: 100%;
}

.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.printer-name {
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.printer-location {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.loading-content,
.error-content,
.idle-content {
  min-height: 60px;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-red-500);
}

.printing-content {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.current-file {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--p-text-color);
}

.current-file i {
  color: var(--p-text-muted-color);
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.print-progress {
  height: 8px;
}

.progress-info {
  display: flex;
  justify-content: flex-end;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.idle-content {
  display: flex;
  align-items: center;
}

.last-seen {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}
</style>
