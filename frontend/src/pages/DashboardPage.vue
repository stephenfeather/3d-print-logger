<script setup lang="ts">
import { computed } from 'vue'
import { useDashboardSummary } from '@/composables/useAnalytics'
import { usePrinters } from '@/composables/usePrinters'
import { formatDuration, formatFilament } from '@/utils/formatters'
import StatCard from '@/components/common/StatCard.vue'
import RecentJobsTable from '@/components/common/RecentJobsTable.vue'
import PrinterStatusCard from '@/components/printers/PrinterStatusCard.vue'

const { data: summary, isLoading: summaryLoading } = useDashboardSummary()
const { data: printers, isLoading: printersLoading } = usePrinters()

const successRate = computed(() => {
  if (!summary.value) return '0%'
  const total = summary.value.successful_jobs + summary.value.failed_jobs
  if (total === 0) return '0%'
  const rate = (summary.value.successful_jobs / total) * 100
  return `${rate.toFixed(1)}%`
})
</script>

<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h1>Dashboard</h1>
      <p class="text-muted">Overview of your 3D printing activity</p>
    </div>

    <!-- Summary Stats -->
    <section class="stats-section">
      <div class="stats-grid">
        <StatCard
          title="Total Jobs"
          :value="summary?.total_jobs ?? 0"
          icon="pi-print"
          iconColor="var(--p-blue-500)"
          :loading="summaryLoading"
        />
        <StatCard
          title="Print Time"
          :value="formatDuration(summary?.total_print_time)"
          icon="pi-clock"
          iconColor="var(--p-green-500)"
          :loading="summaryLoading"
        />
        <StatCard
          title="Filament Used"
          :value="formatFilament(summary?.total_filament_used)"
          icon="pi-box"
          iconColor="var(--p-orange-500)"
          :loading="summaryLoading"
        />
        <StatCard
          title="Success Rate"
          :value="successRate"
          icon="pi-check-circle"
          iconColor="var(--p-teal-500)"
          :loading="summaryLoading"
        />
      </div>
    </section>

    <div class="dashboard-grid">
      <!-- Recent Jobs -->
      <section class="recent-jobs-section">
        <RecentJobsTable />
      </section>

      <!-- Printer Status -->
      <section class="printers-section">
        <div class="section-header">
          <h3>Printers</h3>
          <router-link to="/printers" class="view-all-link">Manage</router-link>
        </div>

        <div v-if="printersLoading" class="printers-loading">
          <div v-for="i in 2" :key="i" class="printer-skeleton">
            <div class="skeleton-card"></div>
          </div>
        </div>

        <div v-else-if="!printers?.length" class="printers-empty">
          <i class="pi pi-server"></i>
          <p>No printers configured</p>
          <router-link to="/printers" class="add-printer-link">Add a printer</router-link>
        </div>

        <div v-else class="printers-grid">
          <PrinterStatusCard v-for="printer in printers" :key="printer.id" :printer="printer" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
  color: var(--p-text-color);
}

.text-muted {
  color: var(--p-text-muted-color);
  margin: 0;
}

.stats-section {
  margin-bottom: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

@media (max-width: 1200px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.view-all-link,
.add-printer-link {
  font-size: 0.875rem;
  color: var(--p-primary-color);
  text-decoration: none;
}

.view-all-link:hover,
.add-printer-link:hover {
  text-decoration: underline;
}

.printers-loading {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.printer-skeleton,
.skeleton-card {
  height: 140px;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.printers-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 2rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px dashed var(--p-surface-border);
  text-align: center;
  color: var(--p-text-muted-color);
}

.printers-empty i {
  font-size: 2.5rem;
  opacity: 0.5;
  margin-bottom: 0.5rem;
}

.printers-empty p {
  margin: 0.5rem 0;
}

.printers-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
