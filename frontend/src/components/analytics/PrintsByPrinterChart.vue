<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { PrinterStats } from '@/types/analytics'

use([BarChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  printerStats: PrinterStats[] | undefined
  loading?: boolean
}>()

const chartOptions = computed(() => {
  if (!props.printerStats?.length) return {}

  const printers = props.printerStats.map((p) => p.printer_name)
  const successful = props.printerStats.map((p) => p.successful_jobs)
  const failed = props.printerStats.map((p) => p.failed_jobs)
  const other = props.printerStats.map((p) => p.total_jobs - p.successful_jobs - p.failed_jobs)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: ['Successful', 'Failed', 'Other'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '5%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: printers,
      axisLabel: {
        interval: 0,
        rotate: printers.length > 4 ? 45 : 0,
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        name: 'Successful',
        type: 'bar',
        stack: 'total',
        data: successful,
        itemStyle: { color: '#22c55e' },
      },
      {
        name: 'Failed',
        type: 'bar',
        stack: 'total',
        data: failed,
        itemStyle: { color: '#ef4444' },
      },
      {
        name: 'Other',
        type: 'bar',
        stack: 'total',
        data: other,
        itemStyle: { color: '#f59e0b' },
      },
    ],
  }
})
</script>

<template>
  <div class="chart-container">
    <h3 class="chart-title">Prints by Printer</h3>
    <div v-if="loading" class="chart-loading">
      <i class="pi pi-spin pi-spinner"></i>
    </div>
    <div v-else-if="!printerStats?.length" class="chart-empty">
      <i class="pi pi-chart-bar"></i>
      <p>No printer data available</p>
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
