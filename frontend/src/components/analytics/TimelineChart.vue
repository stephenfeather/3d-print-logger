<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { TimelineEntry, TimelinePeriod } from '@/types/analytics'
import SelectButton from 'primevue/selectbutton'

use([LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const props = defineProps<{
  timeline: TimelineEntry[] | undefined
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:period': [value: TimelinePeriod]
}>()

const periodOptions = [
  { label: 'Daily', value: 'day' },
  { label: 'Weekly', value: 'week' },
  { label: 'Monthly', value: 'month' },
]

const selectedPeriod = ref<TimelinePeriod>('day')

watch(selectedPeriod, (val) => emit('update:period', val))

const chartOptions = computed(() => {
  if (!props.timeline?.length) return {}

  const periods = props.timeline.map((t) => t.period)
  const successful = props.timeline.map((t) => t.successful_jobs)
  const failed = props.timeline.map((t) => t.failed_jobs)
  const total = props.timeline.map((t) => t.job_count)

  return {
    tooltip: {
      trigger: 'axis',
    },
    legend: {
      data: ['Total', 'Successful', 'Failed'],
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
      data: periods,
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      name: 'Jobs',
      nameLocation: 'middle',
      nameGap: 40,
    },
    series: [
      {
        name: 'Total',
        type: 'line',
        data: total,
        itemStyle: { color: '#3b82f6' },
        lineStyle: { width: 3 },
        areaStyle: { color: 'rgba(59, 130, 246, 0.1)' },
        smooth: true,
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
        },
      },
      {
        name: 'Successful',
        type: 'line',
        data: successful,
        itemStyle: { color: '#22c55e' },
        lineStyle: { width: 2 },
        smooth: true,
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
        },
      },
      {
        name: 'Failed',
        type: 'line',
        data: failed,
        itemStyle: { color: '#ef4444' },
        lineStyle: { width: 2 },
        smooth: true,
        emphasis: {
          itemStyle: {
            borderWidth: 2,
            borderColor: '#fff',
          },
        },
      },
    ],
  }
})
</script>

<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3 class="chart-title">Print Timeline</h3>
      <SelectButton
        v-model="selectedPeriod"
        :options="periodOptions"
        optionLabel="label"
        optionValue="value"
        :allowEmpty="false"
        size="small"
      />
    </div>
    <div v-if="loading" class="chart-loading">
      <i class="pi pi-spin pi-spinner"></i>
    </div>
    <div v-else-if="!timeline?.length" class="chart-empty">
      <i class="pi pi-chart-line"></i>
      <p>No timeline data available</p>
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

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.chart-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.chart {
  flex: 1;
  min-height: 350px;
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
