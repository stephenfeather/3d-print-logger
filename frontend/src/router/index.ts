import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/ApiKeyLoginPage.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      component: DashboardLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/pages/DashboardPage.vue'),
        },
        {
          path: 'prints',
          name: 'prints',
          component: () => import('@/pages/PrintsPage.vue'),
        },
        {
          path: 'printers',
          name: 'printers',
          component: () => import('@/pages/PrintersPage.vue'),
        },
        {
          path: 'maintenance',
          name: 'maintenance',
          component: () => import('@/pages/MaintenancePage.vue'),
        },
        {
          path: 'analytics',
          name: 'analytics',
          component: () => import('@/pages/AnalyticsPage.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/pages/SettingsPage.vue'),
        },
      ],
    },
  ],
})

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  if (requiresAuth && !authStore.checkAuth()) {
    // Redirect to login if trying to access protected route without auth
    next({ name: 'login' })
  } else if (to.name === 'login' && authStore.checkAuth()) {
    // Redirect to dashboard if already logged in and trying to access login
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
