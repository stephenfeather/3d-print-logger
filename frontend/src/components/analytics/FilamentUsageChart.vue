<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { FilamentUsage } from '@/types/analytics'
import { formatFilament } from '@/utils/formatters'

use([BarChart, TitleComponent, TooltipComponent, GridComponent, CanvasRenderer])

const props = defineProps<{
  filamentUsage: FilamentUsage[] | undefined
  loading?: boolean
}>()

const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

const chartOptions = computed(() => {
  if (!props.filamentUsage?.length) return {}

  const types = props.filamentUsage.map((f) => f.filament_type || 'Unknown')
  const usage = props.filamentUsage.map((f) => Math.round(f.total_used * 100) / 100)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: (params: Array<{ name: string; value: number }>) => {
        const p = params[0]
        if (!p) return ''
        return `${p.name}<br/>Usage: ${formatFilament(p.value)}`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '5%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: types,
      axisLabel: {
        interval: 0,
        rotate: types.length > 3 ? 30 : 0,
        fontSize: 12,
      },
    },
    yAxis: {
      type: 'value',
      name: 'Grams',
      nameLocation: 'middle',
      nameGap: 45,
    },
    series: [
      {
        name: 'Filament Used',
        type: 'bar',
        data: usage.map((val, idx) => ({
          value: val,
          itemStyle: { color: colors[idx % colors.length] },
        })),
        barWidth: '60%',
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
    <h3 class="chart-title">Filament Usage by Type</h3>
    <div v-if="loading" class="chart-loading">
      <i class="pi pi-spin pi-spinner"></i>
    </div>
    <div v-else-if="!filamentUsage?.length" class="chart-empty">
      <i class="pi pi-chart-bar"></i>
      <p>No filament data available</p>
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
