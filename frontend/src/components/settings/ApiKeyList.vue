<script setup lang="ts">
import { ref } from 'vue'
import { useApiKeys, useRevokeApiKey } from '@/composables/useAdmin'
import { formatDateTime } from '@/utils/formatters'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Skeleton from 'primevue/skeleton'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import ApiKeyCreateDialog from './ApiKeyCreateDialog.vue'

const confirm = useConfirm()
const toast = useToast()

const { data: apiKeys, isLoading, isError, refetch } = useApiKeys()
const revokeMutation = useRevokeApiKey()

const showCreateDialog = ref(false)

function confirmRevoke(keyId: number, keyName: string) {
  confirm.require({
    message: `Are you sure you want to revoke the API key "${keyName}"? This cannot be undone.`,
    header: 'Revoke API Key',
    icon: 'pi pi-exclamation-triangle',
    rejectLabel: 'Cancel',
    acceptLabel: 'Revoke',
    rejectClass: 'p-button-secondary p-button-text',
    acceptClass: 'p-button-danger',
    accept: async () => {
      try {
        await revokeMutation.mutateAsync(keyId)
        toast.add({
          severity: 'success',
          summary: 'API Key Revoked',
          detail: 'The API key has been revoked',
          life: 3000,
        })
      } catch {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to revoke API key',
          life: 5000,
        })
      }
    },
  })
}

function handleKeyCreated(key: string) {
  toast.add({
    severity: 'success',
    summary: 'API Key Created',
    detail: 'Copy the key now - it will not be shown again',
    life: 10000,
  })
  // Show the key in a separate message so user can copy it
  toast.add({
    severity: 'info',
    summary: 'Your API Key',
    detail: key,
    life: 30000,
  })
}
</script>

<template>
  <div class="api-key-list">
    <div class="card-header">
      <h3>API Keys</h3>
      <Button
        label="Create Key"
        icon="pi pi-plus"
        size="small"
        @click="showCreateDialog = true"
      />
    </div>

    <div v-if="isLoading" class="loading-state">
      <Skeleton v-for="i in 3" :key="i" height="3rem" class="mb-2" />
    </div>

    <div v-else-if="isError" class="error-state">
      <i class="pi pi-exclamation-circle"></i>
      <p>Failed to load API keys</p>
      <Button label="Retry" severity="secondary" size="small" @click="() => refetch()" />
    </div>

    <div v-else-if="!apiKeys?.length" class="empty-state">
      <i class="pi pi-key"></i>
      <p>No API keys created yet</p>
      <Button
        label="Create Your First Key"
        size="small"
        @click="showCreateDialog = true"
      />
    </div>

    <DataTable v-else :value="apiKeys" class="api-keys-table">
      <Column field="name" header="Name" />
      <Column field="key_prefix" header="Key Prefix">
        <template #body="{ data }">
          <code>{{ data.key_prefix }}...</code>
        </template>
      </Column>
      <Column field="is_active" header="Status" style="width: 100px">
        <template #body="{ data }">
          <Tag :severity="data.is_active ? 'success' : 'danger'">
            {{ data.is_active ? 'Active' : 'Revoked' }}
          </Tag>
        </template>
      </Column>
      <Column field="last_used" header="Last Used" style="width: 180px">
        <template #body="{ data }">
          {{ data.last_used ? formatDateTime(data.last_used) : 'Never' }}
        </template>
      </Column>
      <Column field="created_at" header="Created" style="width: 180px">
        <template #body="{ data }">
          {{ formatDateTime(data.created_at) }}
        </template>
      </Column>
      <Column header="Actions" style="width: 80px">
        <template #body="{ data }">
          <Button
            v-if="data.is_active"
            icon="pi pi-ban"
            severity="danger"
            text
            rounded
            size="small"
            @click="confirmRevoke(data.id, data.name)"
            v-tooltip.top="'Revoke'"
          />
        </template>
      </Column>
    </DataTable>

    <ApiKeyCreateDialog
      v-model:visible="showCreateDialog"
      @created="handleKeyCreated"
    />
  </div>
</template>

<style scoped>
.api-key-list {
  background-color: var(--p-surface-card);
  border-radius: var(--p-border-radius);
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--p-text-color);
}

.loading-state {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem;
  color: var(--p-text-muted-color);
  gap: 0.5rem;
  text-align: center;
}

.error-state i,
.empty-state i {
  font-size: 2.5rem;
  opacity: 0.5;
}

.api-keys-table :deep(code) {
  font-size: 0.85rem;
  background-color: var(--p-surface-ground);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}
</style>
