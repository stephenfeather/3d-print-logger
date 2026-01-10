<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const mobileMenuOpen = ref(false)

interface NavItem {
  label: string
  icon: string
  to: string
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: 'pi-home', to: '/' },
  { label: 'Prints', icon: 'pi-list', to: '/prints' },
  { label: 'Printers', icon: 'pi-server', to: '/printers' },
  { label: 'Maintenance', icon: 'pi-wrench', to: '/maintenance' },
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
  mobileMenuOpen.value = false
}

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}

function toggleMobileMenu() {
  mobileMenuOpen.value = !mobileMenuOpen.value
}
</script>

<template>
  <nav class="app-navbar">
    <div class="navbar-brand">
      <i class="pi pi-box brand-icon"></i>
      <span class="brand-text">3D Print Logger</span>
    </div>

    <button class="mobile-toggle" @click="toggleMobileMenu" aria-label="Toggle navigation">
      <i :class="['pi', mobileMenuOpen ? 'pi-times' : 'pi-bars']"></i>
    </button>

    <ul class="navbar-nav" :class="{ open: mobileMenuOpen }">
      <li v-for="item in navItems" :key="item.to" class="nav-item">
        <button
          class="nav-link"
          :class="{ active: isActive(item.to) }"
          @click="navigate(item.to)"
        >
          <i :class="['pi', item.icon, 'nav-icon']"></i>
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </li>
    </ul>

    <div class="navbar-actions" :class="{ open: mobileMenuOpen }">
      <Button
        icon="pi pi-sign-out"
        label="Logout"
        severity="secondary"
        text
        class="logout-btn"
        @click="handleLogout"
      />
    </div>
  </nav>
</template>

<style scoped>
.app-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: var(--p-surface-card);
  border-bottom: 1px solid var(--p-surface-border);
  display: flex;
  align-items: center;
  padding: 0 1.5rem;
  z-index: 1000;
  gap: 1rem;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-shrink: 0;
}

.brand-icon {
  font-size: 1.5rem;
  color: var(--p-primary-color);
}

.brand-text {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--p-text-color);
  white-space: nowrap;
}

.mobile-toggle {
  display: none;
  background: transparent;
  border: none;
  color: var(--p-text-color);
  font-size: 1.25rem;
  padding: 0.5rem;
  cursor: pointer;
  margin-left: auto;
}

.navbar-nav {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  list-style: none;
  margin: 0;
  padding: 0;
  flex: 1;
  justify-content: center;
}

.nav-item {
  margin: 0;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  color: var(--p-text-color);
  font-size: 0.9rem;
  border-radius: var(--p-border-radius);
  cursor: pointer;
  transition:
    background-color 0.2s,
    color 0.2s;
  white-space: nowrap;
}

.nav-link:hover {
  background-color: var(--p-surface-hover);
}

.nav-link.active {
  background-color: var(--p-primary-color);
  color: var(--p-primary-contrast-color);
}

.nav-icon {
  font-size: 1rem;
}

.navbar-actions {
  flex-shrink: 0;
}

.logout-btn {
  white-space: nowrap;
}

/* Mobile styles */
@media (max-width: 900px) {
  .app-navbar {
    flex-wrap: wrap;
    height: auto;
    min-height: 60px;
    padding: 0.75rem 1rem;
  }

  .mobile-toggle {
    display: block;
  }

  .navbar-nav {
    display: none;
    flex-direction: column;
    align-items: stretch;
    width: 100%;
    order: 3;
    padding: 0.5rem 0;
    gap: 0;
  }

  .navbar-nav.open {
    display: flex;
  }

  .nav-link {
    justify-content: flex-start;
    padding: 0.75rem 1rem;
    width: 100%;
  }

  .navbar-actions {
    display: none;
    width: 100%;
    order: 4;
    padding: 0.5rem 0;
    border-top: 1px solid var(--p-surface-border);
  }

  .navbar-actions.open {
    display: block;
  }

  .logout-btn {
    width: 100%;
    justify-content: flex-start;
  }
}

/* Tablet - show icons only */
@media (min-width: 901px) and (max-width: 1100px) {
  .nav-label {
    display: none;
  }

  .nav-link {
    padding: 0.5rem 0.75rem;
  }
}
</style>
