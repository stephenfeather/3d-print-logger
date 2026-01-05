<script setup lang="ts">
import { ref } from 'vue'
import { useDashboardSummary, usePrinterStats, useFilamentUsage, useTimeline } from '@/composables/useAnalytics'
import type { TimelinePeriod } from '@/types/analytics'
import SuccessRatePie from '@/components/analytics/SuccessRatePie.vue'
import PrintsByPrinterChart from '@/components/analytics/PrintsByPrinterChart.vue'
import FilamentUsageChart from '@/components/analytics/FilamentUsageChart.vue'
import TimelineChart from '@/components/analytics/TimelineChart.vue'

const timelinePeriod = ref<TimelinePeriod>('day')

const { data: summary, isLoading: summaryLoading } = useDashboardSummary()
const { data: printerStats, isLoading: printerLoading } = usePrinterStats()
const { data: filamentUsage, isLoading: filamentLoading } = useFilamentUsage()
const { data: timeline, isLoading: timelineLoading, refetch: refetchTimeline } = useTimeline(timelinePeriod.value)

function handlePeriodChange(period: TimelinePeriod) {
  timelinePeriod.value = period
  refetchTimeline()
}
</script>

<template>
  <div class="analytics-page">
    <div class="page-header">
      <h1>Analytics</h1>
      <p class="text-muted">Insights into your printing statistics</p>
    </div>

    <div class="charts-grid">
      <div class="chart-item timeline-chart">
        <TimelineChart
          :timeline="timeline"
          :loading="timelineLoading"
          @update:period="handlePeriodChange"
        />
      </div>

      <div class="chart-item">
        <SuccessRatePie :summary="summary" :loading="summaryLoading" />
      </div>

      <div class="chart-item">
        <PrintsByPrinterChart :printer-stats="printerStats" :loading="printerLoading" />
      </div>

      <div class="chart-item">
        <FilamentUsageChart :filament-usage="filamentUsage" :loading="filamentLoading" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.analytics-page {
  max-width: 1400px;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
  color: var(--p-text-color);
}

.text-muted {
  color: var(--p-text-muted-color);
  margin: 0;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.chart-item {
  min-height: 350px;
}

.timeline-chart {
  grid-column: span 2;
}

@media (max-width: 1024px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }

  .timeline-chart {
    grid-column: span 1;
  }
}
</style>
