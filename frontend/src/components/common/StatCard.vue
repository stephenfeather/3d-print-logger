<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon: string
  iconColor?: string
  loading?: boolean
}>()
</script>

<template>
  <div class="stat-card">
    <div class="stat-icon" :style="{ backgroundColor: iconColor || 'var(--p-primary-color)' }">
      <i :class="['pi', icon]"></i>
    </div>
    <div class="stat-content">
      <span class="stat-title">{{ title }}</span>
      <span v-if="loading" class="stat-value loading">
        <i class="pi pi-spin pi-spinner"></i>
      </span>
      <span v-else class="stat-value">{{ value }}</span>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: var(--p-border-radius);
  flex-shrink: 0;
}

.stat-icon i {
  font-size: 1.25rem;
  color: white;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-title {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.stat-value.loading {
  color: var(--p-text-muted-color);
}
</style>
