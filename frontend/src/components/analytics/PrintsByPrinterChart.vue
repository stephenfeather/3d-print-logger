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
      bottom: 5,
      itemGap: 20,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '12%',
      top: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: printers,
      axisLabel: {
        interval: 0,
        rotate: printers.length > 3 ? 30 : 0,
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      name: 'Jobs',
      nameLocation: 'middle',
      nameGap: 35,
    },
    series: [
      {
        name: 'Successful',
        type: 'bar',
        stack: 'total',
        data: successful,
        itemStyle: { color: '#22c55e' },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
      },
      {
        name: 'Failed',
        type: 'bar',
        stack: 'total',
        data: failed,
        itemStyle: { color: '#ef4444' },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
      },
      {
        name: 'Other',
        type: 'bar',
        stack: 'total',
        data: other,
        itemStyle: { color: '#f59e0b' },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
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
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.2s;
}

.chart-container:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.chart-title {
  margin: 0 0 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.chart {
  flex: 1;
  min-height: 300px;
}

.chart-loading,
.chart-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--p-text-muted-color);
  gap: 1rem;
}

.chart-loading i,
.chart-empty i {
  font-size: 3rem;
  opacity: 0.4;
}

.chart-empty p {
  margin: 0;
  font-size: 0.95rem;
}
</style>
