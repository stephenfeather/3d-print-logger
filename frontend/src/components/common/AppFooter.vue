<script setup lang="ts">
import { computed } from 'vue'
import { useSystemInfo } from '@/composables/useAdmin'

// Frontend version (from package.json)
const FRONTEND_VERSION = '0.1.0'

const { data: systemInfo } = useSystemInfo()

const versionText = computed(() => {
  if (systemInfo.value) {
    return `v${systemInfo.value.version}`
  }
  return `v${FRONTEND_VERSION}`
})
</script>

<template>
  <footer class="app-footer">
    <div class="footer-content">
      <span class="app-name">3D Print Logger</span>
      <span class="version">{{ versionText }}</span>
      <span class="copyright">&copy; {{ new Date().getFullYear() }}</span>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  padding: 1rem 1.5rem;
  background-color: var(--p-surface-card);
  border-top: 1px solid var(--p-surface-border);
  margin-top: auto;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
  max-width: 1600px;
}

.app-name {
  font-weight: 500;
}

.version {
  font-family: monospace;
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
}
</style>
