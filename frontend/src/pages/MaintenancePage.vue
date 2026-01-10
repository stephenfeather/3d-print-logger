<script setup lang="ts">
/**
 * Maintenance page for tracking printer maintenance records.
 * Issue #9: Minimal Printer Maintenance Details
 */

import MaintenanceList from '@/components/maintenance/MaintenanceList.vue'
</script>

<template>
  <div class="maintenance-page">
    <MaintenanceList />
  </div>
</template>

<style scoped>
.maintenance-page {
  max-width: 1400px;
}
</style>
