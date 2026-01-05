<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'

defineProps<{
  collapsed: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

const route = useRoute()
const router = useRouter()

interface NavItem {
  label: string
  icon: string
  to: string
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: 'pi-home', to: '/' },
  { label: 'Printers', icon: 'pi-server', to: '/printers' },
  { label: 'Jobs', icon: 'pi-list', to: '/jobs' },
  { label: 'Analytics', icon: 'pi-chart-bar', to: '/analytics' },
  { label: 'Settings', icon: 'pi-cog', to: '/settings' },
]

function isActive(path: string): boolean {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

function navigate(to: string) {
  router.push(to)
}
</script>

<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div v-if="!collapsed" class="logo">
        <i class="pi pi-box logo-icon"></i>
        <span class="logo-text">3D Print Logger</span>
      </div>
      <Button
        :icon="collapsed ? 'pi pi-angle-right' : 'pi pi-angle-left'"
        text
        rounded
        severity="secondary"
        @click="emit('toggle')"
        class="toggle-btn"
      />
    </div>

    <nav class="sidebar-nav">
      <ul class="nav-list">
        <li v-for="item in navItems" :key="item.to" class="nav-item">
          <button
            class="nav-link"
            :class="{ active: isActive(item.to) }"
            @click="navigate(item.to)"
            :title="collapsed ? item.label : undefined"
          >
            <i :class="['pi', item.icon, 'nav-icon']"></i>
            <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
          </button>
        </li>
      </ul>
    </nav>

    <div class="sidebar-footer">
      <div v-if="!collapsed" class="version-info">v1.0.0</div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  height: 100vh;
  width: 250px;
  background-color: var(--p-surface-card);
  border-right: 1px solid var(--p-surface-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--p-surface-border);
  min-height: 60px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--p-primary-color);
}

.logo-text {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--p-text-color);
  white-space: nowrap;
}

.collapsed .sidebar-header {
  justify-content: center;
  padding: 1rem 0.5rem;
}

.toggle-btn {
  flex-shrink: 0;
}

.sidebar-nav {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.nav-item {
  margin: 0.25rem 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: calc(100% - 1rem);
  margin: 0 0.5rem;
  padding: 0.75rem 1rem;
  border: none;
  background: transparent;
  color: var(--p-text-color);
  font-size: 0.95rem;
  border-radius: var(--p-border-radius);
  cursor: pointer;
  transition:
    background-color 0.2s,
    color 0.2s;
}

.collapsed .nav-link {
  width: calc(100% - 0.5rem);
  margin: 0 0.25rem;
  padding: 0.75rem;
  justify-content: center;
}

.nav-link:hover {
  background-color: var(--p-surface-hover);
}

.nav-link.active {
  background-color: var(--p-primary-color);
  color: var(--p-primary-contrast-color);
}

.nav-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
}

.sidebar-footer {
  padding: 1rem;
  border-top: 1px solid var(--p-surface-border);
  text-align: center;
}

.version-info {
  font-size: 0.75rem;
  color: var(--p-text-muted-color);
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }

  .sidebar-header {
    justify-content: center;
    padding: 1rem 0.5rem;
  }

  .logo {
    display: none;
  }

  .nav-link {
    width: calc(100% - 0.5rem);
    margin: 0 0.25rem;
    padding: 0.75rem;
    justify-content: center;
  }

  .nav-label,
  .version-info {
    display: none;
  }
}
</style>
