<script setup lang="ts">
import AppNavbar from '@/components/common/AppNavbar.vue'
import AppFooter from '@/components/common/AppFooter.vue'
</script>

<template>
  <div class="dashboard-layout">
    <AppNavbar />
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
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--p-surface-ground);
}

.main-content {
  flex: 1;
  margin-top: 60px;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  flex: 1;
  padding: 1.5rem;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
}

@media (max-width: 900px) {
  .main-content {
    margin-top: 60px;
  }
}
</style>
