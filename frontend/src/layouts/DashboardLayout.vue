<script setup lang="ts">
import { ref } from 'vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppFooter from '@/components/common/AppFooter.vue'

const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="dashboard-layout" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <AppSidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <main class="main-content">
      <div class="content-wrapper">
        <router-view />
      </div>
      <AppFooter />
    </main>
  </div>
</template>

<style scoped>
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--p-surface-ground);
}

.main-content {
  flex: 1;
  margin-left: 250px;
  transition: margin-left 0.3s ease;
  display: flex;
  flex-direction: column;
}

.sidebar-collapsed .main-content {
  margin-left: 60px;
}

.content-wrapper {
  flex: 1;
  padding: 1.5rem;
  max-width: 1600px;
}

@media (max-width: 768px) {
  .main-content {
    margin-left: 60px;
  }
}
</style>
