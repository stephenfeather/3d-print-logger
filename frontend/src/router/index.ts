import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '@/layouts/DashboardLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: DashboardLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/pages/DashboardPage.vue'),
        },
        {
          path: 'printers',
          name: 'printers',
          component: () => import('@/pages/PrintersPage.vue'),
        },
        {
          path: 'jobs',
          name: 'jobs',
          component: () => import('@/pages/JobsPage.vue'),
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

export default router
