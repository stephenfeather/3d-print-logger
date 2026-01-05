<script setup lang="ts">
import SystemInfoCard from '@/components/settings/SystemInfoCard.vue'
import ApiKeyList from '@/components/settings/ApiKeyList.vue'
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h1>Settings</h1>
      <p class="text-muted">Manage API keys and system configuration</p>
    </div>

    <div class="settings-grid">
      <div class="settings-section system-info">
        <SystemInfoCard />
      </div>

      <div class="settings-section api-keys">
        <ApiKeyList />
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 1200px;
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

.settings-grid {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
