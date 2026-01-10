<script setup lang="ts">
</script>

<template>
  <div class="maintenance-page">
    <div class="page-header">
      <h1>Maintenance</h1>
      <p class="text-muted">Track printer maintenance and service history</p>
    </div>

    <div class="placeholder-card">
      <i class="pi pi-wrench placeholder-icon"></i>
      <h2>Coming Soon</h2>
      <p>Maintenance tracking features are under development.</p>
    </div>
  </div>
</template>

<style scoped>
.maintenance-page {
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

.placeholder-card {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  border: 1px solid var(--p-surface-border);
  padding: 3rem;
  text-align: center;
  color: var(--p-text-muted-color);
}

.placeholder-icon {
  font-size: 3rem;
  opacity: 0.5;
  margin-bottom: 1rem;
}

.placeholder-card h2 {
  margin: 0 0 0.5rem 0;
  color: var(--p-text-color);
  font-size: 1.25rem;
}

.placeholder-card p {
  margin: 0;
}
</style>
