# Phase 5: Vue.js Frontend Dashboard Implementation Plan

## Overview

Build a modern Vue.js dashboard for the 3D Print Logger application, consuming the existing FastAPI REST API (19 endpoints). The frontend will provide printer management, job history with filtering, analytics charts, and real-time status updates.

## Current State Analysis

**Backend Complete:**
- 19 REST API endpoints across 5 route groups (printers, jobs, analytics, admin, health)
- X-API-Key header authentication (SHA-256 hashed)
- Pagination with `limit`/`offset` query params
- CORS configured for `http://localhost:3000`

**Frontend Directory:**
- `frontend/` exists but empty (only `.gitkeep`)

### Key API Endpoints to Consume

| Route Group | Endpoints | Purpose |
|-------------|-----------|---------|
| `/api/printers` | 7 endpoints | Printer CRUD + status |
| `/api/jobs` | 3 endpoints | Job listing with filters |
| `/api/analytics` | 4 endpoints | Dashboard stats + charts |
| `/api/admin` | 4 endpoints | API key management |
| `/health` | 1 endpoint | Health check (no auth) |

## Desired End State

A fully functional Vue.js dashboard with:
- Dashboard overview with summary stats and recent activity
- Printer management (add/edit/delete, status display)
- Job history with server-side pagination and filtering
- Analytics charts (print time trends, success rates, filament usage)
- Admin settings (API key management, system info)
- Responsive design for desktop and tablet

### Verification Criteria
- All API endpoints consumed correctly
- TypeScript strict mode passes
- ESLint/Prettier checks pass
- Manual testing of all CRUD operations
- Charts render with sample data

## What We're NOT Doing

- Mobile-first responsive design (desktop/tablet focus)
- WebSocket real-time updates (polling only for MVP)
- Offline support / PWA features
- Dark mode (single theme for MVP)
- User authentication system (API key only)
- i18n / internationalization

## Tech Stack

| Component | Choice | Version |
|-----------|--------|---------|
| Framework | Vue 3 + Composition API | ^3.5.0 |
| Build | Vite | ^5.4.0 |
| Language | TypeScript (strict) | ^5.5.0 |
| State | Pinia | ^2.2.0 |
| Server State | TanStack Vue Query | ^5.50.0 |
| HTTP | Axios | ^1.7.0 |
| UI Library | PrimeVue | ^4.0.0 |
| Icons | PrimeIcons | ^7.0.0 |
| Charts | Apache ECharts (vue-echarts) | ^7.0.0 |
| Router | Vue Router | ^4.3.0 |

---

## Phase 5.1: Project Setup & Infrastructure

### Overview
Initialize Vue 3 project with all dependencies and configure development environment.

### Changes Required:

#### 1. Initialize Vue Project
```bash
cd frontend
npm create vue@latest . -- --typescript --pinia --router --eslint --prettier
```

#### 2. Install Dependencies
```bash
npm install primevue primeicons @primeuix/themes
npm install @tanstack/vue-query axios
npm install echarts vue-echarts
npm install -D @types/node
```

#### 3. Configure Vite
**File**: `frontend/vite.config.ts`
```typescript
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

#### 4. Configure PrimeVue
**File**: `frontend/src/main.ts`
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import ToastService from 'primevue/toastservice'
import ConfirmationService from 'primevue/confirmationservice'

import App from './App.vue'
import router from './router'

import 'primeicons/primeicons.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(VueQueryPlugin)
app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})
app.use(ToastService)
app.use(ConfirmationService)

app.mount('#app')
```

#### 5. Create TypeScript Interfaces
**File**: `frontend/src/types/printer.ts`
```typescript
export interface Printer {
  id: number
  name: string
  moonraker_url: string
  location: string | null
  is_active: boolean
  last_seen: string | null
  created_at: string
  updated_at: string
}

export interface PrinterCreate {
  name: string
  moonraker_url: string
  location?: string
  moonraker_api_key?: string
}

export interface PrinterUpdate {
  name?: string
  moonraker_url?: string
  location?: string
  moonraker_api_key?: string
  is_active?: boolean
}

export interface PrinterStatus {
  printer_id: number
  name: string
  is_connected: boolean
  state: string | null
  progress: number | null
  current_file: string | null
  error: string | null
}
```

**File**: `frontend/src/types/job.ts`
```typescript
export interface JobDetails {
  id: number
  print_job_id: number
  layer_height: number | null
  first_layer_height: number | null
  nozzle_temp: number | null
  bed_temp: number | null
  print_speed: number | null
  infill_percentage: number | null
  infill_pattern: string | null
  support_enabled: boolean | null
  support_type: string | null
  filament_type: string | null
  filament_brand: string | null
  filament_color: string | null
  estimated_time: number | null
  estimated_filament: number | null
  layer_count: number | null
  object_height: number | null
}

export interface PrintJob {
  id: number
  printer_id: number
  job_id: string
  user: string | null
  filename: string
  status: 'completed' | 'error' | 'cancelled' | 'printing' | 'paused'
  start_time: string | null
  end_time: string | null
  print_duration: number | null
  total_duration: number | null
  filament_used: number | null
  job_metadata: Record<string, unknown> | null
  created_at: string
  updated_at: string
  details: JobDetails | null
}

export interface JobFilters {
  printer_id?: number
  status?: string
  start_after?: string
  start_before?: string
  limit: number
  offset: number
}
```

**File**: `frontend/src/types/analytics.ts`
```typescript
export interface DashboardSummary {
  total_jobs: number
  total_print_time: number
  total_filament_used: number
  successful_jobs: number
  failed_jobs: number
  active_printers: number
}

export interface PrinterStats {
  printer_id: number
  printer_name: string
  total_jobs: number
  total_print_time: number
  total_filament_used: number
  successful_jobs: number
  failed_jobs: number
  last_job_at: string | null
}

export interface FilamentUsage {
  filament_type: string
  total_used: number
  job_count: number
}

export interface TimelineEntry {
  period: string
  job_count: number
  total_print_time: number
  successful_jobs: number
  failed_jobs: number
}
```

**File**: `frontend/src/types/api.ts`
```typescript
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

export interface ApiKey {
  id: number
  key_prefix: string
  name: string
  is_active: boolean
  expires_at: string | null
  last_used: string | null
  created_at: string
}

export interface ApiKeyCreate {
  name: string
  expires_at?: string
}

export interface ApiKeyCreated extends ApiKey {
  key: string
}

export interface SystemInfo {
  version: string
  database_type: string
  active_printers: number
  total_jobs: number
  uptime_seconds: number | null
}

export interface ErrorResponse {
  detail: string
  code?: string
}
```

#### 6. Create API Client
**File**: `frontend/src/api/client.ts`
```typescript
import axios, { type AxiosInstance } from 'axios'

const API_KEY_STORAGE_KEY = '3dp_api_key'

export const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add API key to all requests
apiClient.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem(API_KEY_STORAGE_KEY)
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey
  }
  return config
})

// Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Could redirect to setup/login page
      console.error('API key invalid or missing')
    }
    return Promise.reject(error)
  }
)

export function setApiKey(key: string): void {
  localStorage.setItem(API_KEY_STORAGE_KEY, key)
}

export function getApiKey(): string | null {
  return localStorage.getItem(API_KEY_STORAGE_KEY)
}

export function clearApiKey(): void {
  localStorage.removeItem(API_KEY_STORAGE_KEY)
}
```

### Success Criteria:

#### Automated Verification:
- [ ] `npm run build` completes without errors
- [ ] `npm run type-check` passes (vue-tsc)
- [ ] `npm run lint` passes
- [ ] Dev server starts on port 3000: `npm run dev`

#### Manual Verification:
- [ ] Browser opens to `http://localhost:3000` with Vue app
- [ ] No console errors in browser DevTools

---

## Phase 5.2: Core Layout & Navigation

### Overview
Create the dashboard shell with sidebar navigation and main content area.

### Changes Required:

#### 1. Dashboard Layout
**File**: `frontend/src/layouts/DashboardLayout.vue`

#### 2. Sidebar Navigation
**File**: `frontend/src/components/common/Sidebar.vue`

#### 3. Router Configuration
**File**: `frontend/src/router/index.ts`

#### 4. Page Stubs
- `frontend/src/pages/DashboardPage.vue`
- `frontend/src/pages/PrintersPage.vue`
- `frontend/src/pages/JobsPage.vue`
- `frontend/src/pages/AnalyticsPage.vue`
- `frontend/src/pages/SettingsPage.vue`

### Success Criteria:

#### Automated Verification:
- [ ] Build passes: `npm run build`
- [ ] Type check passes: `npm run type-check`

#### Manual Verification:
- [ ] Sidebar shows all navigation items
- [ ] Clicking nav items changes routes
- [ ] Active route is highlighted
- [ ] Layout is responsive at 1024px+ width

---

## Phase 5.3: Dashboard Overview Page

### Overview
Main dashboard with summary cards, recent jobs, and printer status grid.

### Changes Required:

#### 1. API Composables
**File**: `frontend/src/composables/useAnalytics.ts`
**File**: `frontend/src/composables/useJobs.ts`
**File**: `frontend/src/composables/usePrinters.ts`

#### 2. Dashboard Components
- Summary cards (total jobs, print time, filament, success rate)
- Recent jobs table (last 5 jobs)
- Printer status cards grid

#### 3. API Services
**File**: `frontend/src/api/analytics.ts`
**File**: `frontend/src/api/jobs.ts`
**File**: `frontend/src/api/printers.ts`

### Success Criteria:

#### Automated Verification:
- [ ] Build passes
- [ ] Type check passes

#### Manual Verification:
- [ ] Summary cards display stats from API
- [ ] Recent jobs table shows latest 5 jobs
- [ ] Printer cards show status for each printer
- [ ] Loading states display while fetching

---

## Phase 5.4: Printers Management

### Overview
Full CRUD for printer management with status display.

### Changes Required:

#### 1. Printer List Component
#### 2. Add/Edit Printer Dialog
#### 3. Delete Confirmation
#### 4. Printer Status Cards

### Success Criteria:

#### Automated Verification:
- [ ] Build passes
- [ ] Type check passes

#### Manual Verification:
- [ ] Can create new printer via form
- [ ] Can edit existing printer
- [ ] Can delete printer with confirmation
- [ ] Printer list refreshes after changes
- [ ] Form validation works (required fields)

---

## Phase 5.5: Jobs History

### Overview
Paginated job history with server-side filtering.

### Changes Required:

#### 1. Jobs DataTable with PrimeVue
#### 2. Filter controls (printer, status, date range)
#### 3. Job details modal
#### 4. Pagination controls

### Success Criteria:

#### Automated Verification:
- [ ] Build passes
- [ ] Type check passes

#### Manual Verification:
- [ ] DataTable shows jobs with pagination
- [ ] Filtering by printer works
- [ ] Filtering by status works
- [ ] Date range filter works
- [ ] Clicking job opens details modal
- [ ] Pagination controls work

---

## Phase 5.6: Analytics Page

### Overview
Charts and statistics for print analytics.

### Changes Required:

#### 1. Print Time Trends (Line Chart)
#### 2. Success Rate (Donut Chart)
#### 3. Filament Usage by Type (Bar Chart)
#### 4. Printer Comparison Table

### Success Criteria:

#### Automated Verification:
- [ ] Build passes
- [ ] Type check passes

#### Manual Verification:
- [ ] Line chart shows print time over periods
- [ ] Donut chart shows success/fail/cancelled breakdown
- [ ] Bar chart shows filament by type
- [ ] Period selector (day/week/month) works
- [ ] Charts resize correctly

---

## Phase 5.7: Admin/Settings

### Overview
API key management and system information.

### Changes Required:

#### 1. API Key List
#### 2. Create API Key Dialog
#### 3. Revoke Key Confirmation
#### 4. System Info Display
#### 5. Initial Setup Flow (if no API key)

### Success Criteria:

#### Automated Verification:
- [ ] Build passes
- [ ] Type check passes

#### Manual Verification:
- [ ] Can view existing API keys (prefix only)
- [ ] Can create new API key (full key shown once)
- [ ] Can revoke API key
- [ ] System info displays correctly
- [ ] Setup flow works for new installations

---

## Project Structure

```
frontend/
├── src/
│   ├── api/                    # API layer
│   │   ├── client.ts           # Axios instance + interceptors
│   │   ├── printers.ts
│   │   ├── jobs.ts
│   │   ├── analytics.ts
│   │   └── admin.ts
│   ├── assets/                 # Static assets
│   ├── components/
│   │   ├── common/             # Shared components
│   │   │   ├── Sidebar.vue
│   │   │   ├── LoadingSpinner.vue
│   │   │   └── ErrorMessage.vue
│   │   ├── printers/
│   │   │   ├── PrinterCard.vue
│   │   │   ├── PrinterForm.vue
│   │   │   └── PrinterList.vue
│   │   ├── jobs/
│   │   │   ├── JobsTable.vue
│   │   │   ├── JobFilters.vue
│   │   │   └── JobDetailsModal.vue
│   │   └── charts/
│   │       ├── PrintTimeChart.vue
│   │       ├── SuccessRateChart.vue
│   │       └── FilamentChart.vue
│   ├── composables/            # Vue composables
│   │   ├── usePrinters.ts
│   │   ├── useJobs.ts
│   │   ├── useAnalytics.ts
│   │   └── useApiKeys.ts
│   ├── layouts/
│   │   └── DashboardLayout.vue
│   ├── pages/
│   │   ├── DashboardPage.vue
│   │   ├── PrintersPage.vue
│   │   ├── JobsPage.vue
│   │   ├── AnalyticsPage.vue
│   │   └── SettingsPage.vue
│   ├── router/
│   │   └── index.ts
│   ├── stores/                 # Pinia stores
│   │   └── ui.ts               # UI state (sidebar, theme)
│   ├── types/                  # TypeScript interfaces
│   │   ├── printer.ts
│   │   ├── job.ts
│   │   ├── analytics.ts
│   │   └── api.ts
│   ├── utils/                  # Utility functions
│   │   ├── formatters.ts       # Date, duration, size formatters
│   │   └── constants.ts
│   ├── App.vue
│   └── main.ts
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

---

## References

- API Documentation: `src/api/schemas.py` (Pydantic models)
- API Routes: `src/api/routes/` (FastAPI endpoints)
- Architecture: `thoughts/shared/plans/architecture-design.md`
- Research: `.claude/cache/agents/research-agent/latest-output.md`
