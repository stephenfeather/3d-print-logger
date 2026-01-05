<script setup lang="ts">
import JobsTable from '@/components/jobs/JobsTable.vue'
</script>

<template>
  <div class="jobs-page">
    <div class="page-header">
      <h1>Print Jobs</h1>
      <p class="text-muted">View and manage your print history</p>
    </div>

    <JobsTable />
  </div>
</template>

<style scoped>
.jobs-page {
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
</style>
