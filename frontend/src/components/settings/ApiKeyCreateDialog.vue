<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCreateApiKey } from '@/composables/useAdmin'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  created: [key: string]
}>()

const toast = useToast()
const createMutation = useCreateApiKey()

const name = ref('')
const expiresAt = ref<Date | undefined>()
const errors = ref<Record<string, string>>({})
const createdKey = ref<string | null>(null)

// Reset form when dialog opens
watch(
  () => createdKey.value,
  () => {
    if (!createdKey.value) {
      name.value = ''
      expiresAt.value = undefined
      errors.value = {}
    }
  },
)

function validate(): boolean {
  errors.value = {}

  if (!name.value.trim()) {
    errors.value.name = 'Name is required'
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  try {
    const result = await createMutation.mutateAsync({
      name: name.value,
      expires_at: expiresAt.value?.toISOString(),
    })

    createdKey.value = result.key
    emit('created', result.key)
  } catch {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to create API key',
      life: 5000,
    })
  }
}

function handleClose() {
  createdKey.value = null
  emit('update:visible', false)
}

async function copyKey() {
  if (createdKey.value) {
    try {
      await navigator.clipboard.writeText(createdKey.value)
      toast.add({
        severity: 'success',
        summary: 'Copied',
        detail: 'API key copied to clipboard',
        life: 2000,
      })
    } catch {
      toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to copy to clipboard',
        life: 3000,
      })
    }
  }
}

const isLoading = computed(() => createMutation.isPending.value)
const minDate = new Date()
</script>

<template>
  <Dialog
    :visible="visible"
    :header="createdKey ? 'API Key Created' : 'Create API Key'"
    :modal="true"
    :closable="!isLoading"
    :style="{ width: '500px' }"
    @update:visible="handleClose"
  >
    <template v-if="createdKey">
      <div class="key-created">
        <div class="key-warning">
          <i class="pi pi-exclamation-triangle"></i>
          <p>
            Copy this key now. You won't be able to see it again!
          </p>
        </div>

        <div class="key-display">
          <code>{{ createdKey }}</code>
          <Button
            icon="pi pi-copy"
            severity="secondary"
            text
            @click="copyKey"
            v-tooltip.top="'Copy to clipboard'"
          />
        </div>
      </div>
    </template>

    <template v-else>
      <form @submit.prevent="handleSubmit" class="create-form">
        <div class="form-field">
          <label for="key-name">Name *</label>
          <InputText
            id="key-name"
            v-model="name"
            :invalid="!!errors.name"
            placeholder="My API Key"
            :disabled="isLoading"
          />
          <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
          <small v-else class="help-text">A descriptive name for this key</small>
        </div>

        <div class="form-field">
          <label for="expires-at">Expires At</label>
          <DatePicker
            id="expires-at"
            v-model="expiresAt"
            :minDate="minDate"
            placeholder="Never"
            showIcon
            :disabled="isLoading"
          />
          <small class="help-text">Optional - leave empty for no expiration</small>
        </div>
      </form>
    </template>

    <template #footer>
      <template v-if="createdKey">
        <Button label="Done" @click="handleClose" />
      </template>
      <template v-else>
        <Button
          label="Cancel"
          severity="secondary"
          text
          @click="handleClose"
          :disabled="isLoading"
        />
        <Button
          label="Create Key"
          :loading="isLoading"
          @click="handleSubmit"
        />
      </template>
    </template>
  </Dialog>
</template>

<style scoped>
.create-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 500;
  color: var(--p-text-color);
}

.form-field :deep(input),
.form-field :deep(.p-datepicker) {
  width: 100%;
}

.help-text {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.p-error {
  color: var(--p-red-500);
}

.key-created {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.key-warning {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background-color: var(--p-yellow-50);
  border: 1px solid var(--p-yellow-200);
  border-radius: var(--p-border-radius);
  color: var(--p-yellow-700);
}

.key-warning i {
  font-size: 1.5rem;
}

.key-warning p {
  margin: 0;
  font-weight: 500;
}

.key-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: var(--p-surface-ground);
  border-radius: var(--p-border-radius);
}

.key-display code {
  flex: 1;
  font-size: 0.9rem;
  word-break: break-all;
}
</style>
