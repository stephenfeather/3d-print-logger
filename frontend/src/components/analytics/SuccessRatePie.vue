<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { DashboardSummary } from '@/types/analytics'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  summary: DashboardSummary | undefined
  loading?: boolean
}>()

const chartOptions = computed(() => {
  if (!props.summary) return {}

  const total = props.summary.total_jobs
  const successful = props.summary.successful_jobs
  const failed = props.summary.failed_jobs
  const other = total - successful - failed

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
    },
    series: [
      {
        name: 'Print Status',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'var(--p-surface-card)',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: [
          { value: successful, name: 'Successful', itemStyle: { color: '#22c55e' } },
          { value: failed, name: 'Failed', itemStyle: { color: '#ef4444' } },
          { value: other, name: 'Other', itemStyle: { color: '#f59e0b' } },
        ].filter((d) => d.value > 0),
      },
    ],
  }
})
</script>

<template>
  <div class="chart-container">
    <h3 class="chart-title">Print Success Rate</h3>
    <div v-if="loading" class="chart-loading">
      <i class="pi pi-spin pi-spinner"></i>
    </div>
    <div v-else-if="!summary || summary.total_jobs === 0" class="chart-empty">
      <i class="pi pi-chart-pie"></i>
      <p>No print data available</p>
    </div>
    <VChart v-else :option="chartOptions" autoresize class="chart" />
  </div>
</template>

<style scoped>
.chart-container {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  padding: 1.5rem;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-title {
  margin: 0 0 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.chart {
  flex: 1;
  min-height: 250px;
}

.chart-loading,
.chart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--p-text-muted-color);
  gap: 0.5rem;
}

.chart-loading i,
.chart-empty i {
  font-size: 2rem;
  opacity: 0.5;
}
</style>
