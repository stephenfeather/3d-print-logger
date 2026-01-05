<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCreatePrinter, useUpdatePrinter } from '@/composables/usePrinters'
import type { Printer, PrinterCreate, PrinterUpdate } from '@/types/printer'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const props = defineProps<{
  visible: boolean
  printer?: Printer | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const toast = useToast()
const createMutation = useCreatePrinter()
const updateMutation = useUpdatePrinter()

const isEdit = computed(() => !!props.printer)
const dialogTitle = computed(() => (isEdit.value ? 'Edit Printer' : 'Add Printer'))

const form = ref<PrinterCreate>({
  name: '',
  moonraker_url: '',
  location: '',
  moonraker_api_key: '',
})

const errors = ref<Record<string, string>>({})

// Reset form when dialog opens/closes or printer changes
watch(
  () => [props.visible, props.printer],
  () => {
    if (props.visible) {
      if (props.printer) {
        form.value = {
          name: props.printer.name,
          moonraker_url: props.printer.moonraker_url,
          location: props.printer.location || '',
          moonraker_api_key: '',
        }
      } else {
        form.value = {
          name: '',
          moonraker_url: '',
          location: '',
          moonraker_api_key: '',
        }
      }
      errors.value = {}
    }
  },
  { immediate: true },
)

function validate(): boolean {
  errors.value = {}

  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required'
  }

  if (!form.value.moonraker_url.trim()) {
    errors.value.moonraker_url = 'Moonraker URL is required'
  } else {
    try {
      new URL(form.value.moonraker_url)
    } catch {
      errors.value.moonraker_url = 'Invalid URL format'
    }
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  try {
    if (isEdit.value && props.printer) {
      const updateData: PrinterUpdate = {
        name: form.value.name,
        moonraker_url: form.value.moonraker_url,
        location: form.value.location || undefined,
      }
      if (form.value.moonraker_api_key) {
        updateData.moonraker_api_key = form.value.moonraker_api_key
      }
      await updateMutation.mutateAsync({ id: props.printer.id, data: updateData })
      toast.add({
        severity: 'success',
        summary: 'Printer Updated',
        detail: `${form.value.name} has been updated`,
        life: 3000,
      })
    } else {
      await createMutation.mutateAsync(form.value)
      toast.add({
        severity: 'success',
        summary: 'Printer Added',
        detail: `${form.value.name} has been added`,
        life: 3000,
      })
    }

    emit('saved')
    emit('update:visible', false)
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'An error occurred'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: errorMessage,
      life: 5000,
    })
  }
}

function handleClose() {
  emit('update:visible', false)
}

const isLoading = computed(
  () => createMutation.isPending.value || updateMutation.isPending.value,
)
</script>

<template>
  <Dialog
    :visible="visible"
    :header="dialogTitle"
    :modal="true"
    :closable="!isLoading"
    :style="{ width: '500px' }"
    @update:visible="handleClose"
  >
    <form @submit.prevent="handleSubmit" class="printer-form">
      <div class="form-field">
        <label for="name">Name *</label>
        <InputText
          id="name"
          v-model="form.name"
          :invalid="!!errors.name"
          placeholder="My Printer"
          :disabled="isLoading"
        />
        <small v-if="errors.name" class="p-error">{{ errors.name }}</small>
      </div>

      <div class="form-field">
        <label for="moonraker_url">Moonraker URL *</label>
        <InputText
          id="moonraker_url"
          v-model="form.moonraker_url"
          :invalid="!!errors.moonraker_url"
          placeholder="http://printer.local:7125"
          :disabled="isLoading"
        />
        <small v-if="errors.moonraker_url" class="p-error">{{ errors.moonraker_url }}</small>
        <small v-else class="help-text">The URL of your Moonraker instance</small>
      </div>

      <div class="form-field">
        <label for="location">Location</label>
        <InputText
          id="location"
          v-model="form.location"
          placeholder="Office, Workshop, etc."
          :disabled="isLoading"
        />
      </div>

      <div class="form-field">
        <label for="moonraker_api_key">API Key</label>
        <InputText
          id="moonraker_api_key"
          v-model="form.moonraker_api_key"
          :placeholder="isEdit ? 'Leave empty to keep existing' : 'Optional'"
          :disabled="isLoading"
        />
        <small class="help-text">Required if Moonraker authentication is enabled</small>
      </div>
    </form>

    <template #footer>
      <Button label="Cancel" severity="secondary" text @click="handleClose" :disabled="isLoading" />
      <Button
        :label="isEdit ? 'Save Changes' : 'Add Printer'"
        :loading="isLoading"
        @click="handleSubmit"
      />
    </template>
  </Dialog>
</template>

<style scoped>
.printer-form {
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

.form-field :deep(input) {
  width: 100%;
}

.help-text {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.p-error {
  color: var(--p-red-500);
}
</style>
