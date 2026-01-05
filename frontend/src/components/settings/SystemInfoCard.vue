<script setup lang="ts">
import { computed } from 'vue'
import { useSystemInfo, useHealthCheck } from '@/composables/useAdmin'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'

const { data: systemInfo, isLoading: systemLoading } = useSystemInfo()
const { data: health, isLoading: healthLoading } = useHealthCheck()

function formatUptime(seconds: number | null | undefined): string {
  if (!seconds) return 'N/A'
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  const parts: string[] = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0) parts.push(`${hours}h`)
  if (minutes > 0) parts.push(`${minutes}m`)

  return parts.join(' ') || '< 1m'
}

const isHealthy = computed(() => health.value?.status === 'healthy')
</script>

<template>
  <div class="system-info-card">
    <div class="card-header">
      <h3>System Information</h3>
      <Tag v-if="!healthLoading" :severity="isHealthy ? 'success' : 'danger'">
        {{ isHealthy ? 'Healthy' : 'Unhealthy' }}
      </Tag>
    </div>

    <div v-if="systemLoading" class="loading-state">
      <Skeleton v-for="i in 5" :key="i" height="2rem" class="mb-2" />
    </div>

    <dl v-else-if="systemInfo" class="info-list">
      <div class="info-item">
        <dt>Version</dt>
        <dd>{{ systemInfo.version }}</dd>
      </div>
      <div class="info-item">
        <dt>Database</dt>
        <dd>{{ systemInfo.database_type }}</dd>
      </div>
      <div class="info-item">
        <dt>Active Printers</dt>
        <dd>{{ systemInfo.active_printers }}</dd>
      </div>
      <div class="info-item">
        <dt>Total Jobs</dt>
        <dd>{{ systemInfo.total_jobs.toLocaleString() }}</dd>
      </div>
      <div class="info-item">
        <dt>Uptime</dt>
        <dd>{{ formatUptime(systemInfo.uptime_seconds) }}</dd>
      </div>
    </dl>

    <div v-else class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <p>Failed to load system info</p>
    </div>
  </div>
</template>

<style scoped>
.system-info-card {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-list {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--p-surface-border);
}

.info-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-item dt {
  color: var(--p-text-muted-color);
}

.info-item dd {
  margin: 0;
  font-weight: 500;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: var(--p-text-muted-color);
  gap: 0.5rem;
}

.error-state i {
  font-size: 2rem;
  opacity: 0.5;
}
</style>
