<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useCreatePrinter, useUpdatePrinter } from '@/composables/usePrinters'
import type { Printer, PrinterCreate, PrinterUpdate, PrinterType, FilamentDiameter } from '@/types/printer'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Textarea from 'primevue/textarea'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const PRINTER_TYPES: PrinterType[] = ['FDM', 'Resin', 'SLS']
const FILAMENT_DIAMETERS: FilamentDiameter[] = [1.75, 2.85, 3.0]

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
  // Hardware details
  printer_type: undefined,
  make: '',
  model: '',
  description: '',
  // Specifications
  filament_diameter: 1.75,
  nozzle_diameter: undefined,
  bed_x: undefined,
  bed_y: undefined,
  bed_z: undefined,
  has_heated_bed: false,
  has_heated_chamber: false,
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
          // Hardware details
          printer_type: props.printer.printer_type || undefined,
          make: props.printer.make || '',
          model: props.printer.model || '',
          description: props.printer.description || '',
          // Specifications
          filament_diameter: (props.printer.filament_diameter as FilamentDiameter) || 1.75,
          nozzle_diameter: props.printer.nozzle_diameter || undefined,
          bed_x: props.printer.bed_x || undefined,
          bed_y: props.printer.bed_y || undefined,
          bed_z: props.printer.bed_z || undefined,
          has_heated_bed: props.printer.has_heated_bed || false,
          has_heated_chamber: props.printer.has_heated_chamber || false,
        }
      } else {
        form.value = {
          name: '',
          moonraker_url: '',
          location: '',
          moonraker_api_key: '',
          // Hardware details
          printer_type: undefined,
          make: '',
          model: '',
          description: '',
          // Specifications
          filament_diameter: 1.75,
          nozzle_diameter: undefined,
          bed_x: undefined,
          bed_y: undefined,
          bed_z: undefined,
          has_heated_bed: false,
          has_heated_chamber: false,
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

  // Validate bed dimensions (must be > 0 if provided)
  if (form.value.nozzle_diameter !== undefined && form.value.nozzle_diameter <= 0) {
    errors.value.nozzle_diameter = 'Nozzle diameter must be greater than 0'
  }
  if (form.value.bed_x !== undefined && form.value.bed_x <= 0) {
    errors.value.bed_x = 'Bed width must be greater than 0'
  }
  if (form.value.bed_y !== undefined && form.value.bed_y <= 0) {
    errors.value.bed_y = 'Bed depth must be greater than 0'
  }
  if (form.value.bed_z !== undefined && form.value.bed_z <= 0) {
    errors.value.bed_z = 'Bed height must be greater than 0'
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
        // Hardware details
        printer_type: form.value.printer_type,
        make: form.value.make || undefined,
        model: form.value.model || undefined,
        description: form.value.description || undefined,
        // Specifications
        filament_diameter: form.value.filament_diameter,
        nozzle_diameter: form.value.nozzle_diameter,
        bed_x: form.value.bed_x,
        bed_y: form.value.bed_y,
        bed_z: form.value.bed_z,
        has_heated_bed: form.value.has_heated_bed,
        has_heated_chamber: form.value.has_heated_chamber,
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
    :style="{ width: '600px', maxHeight: '90vh' }"
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

      <!-- Hardware Details Section -->
      <div class="section-divider">Hardware Details</div>

      <div class="form-row">
        <div class="form-field">
          <label for="printer_type">Printer Type</label>
          <Select
            id="printer_type"
            v-model="form.printer_type"
            :options="PRINTER_TYPES"
            placeholder="Select type"
            :disabled="isLoading"
          />
        </div>

        <div class="form-field">
          <label for="make">Make</label>
          <InputText
            id="make"
            v-model="form.make"
            placeholder="e.g., Prusa, Bambu Lab"
            :disabled="isLoading"
          />
        </div>
      </div>

      <div class="form-row">
        <div class="form-field">
          <label for="model">Model</label>
          <InputText
            id="model"
            v-model="form.model"
            placeholder="e.g., MK4, X1 Carbon"
            :disabled="isLoading"
          />
        </div>

        <div class="form-field">
          <label for="filament_diameter">Filament Diameter (mm)</label>
          <Select
            id="filament_diameter"
            v-model="form.filament_diameter"
            :options="FILAMENT_DIAMETERS"
            :disabled="isLoading"
          />
        </div>
      </div>

      <div class="form-field">
        <label for="description">Description</label>
        <Textarea
          id="description"
          v-model="form.description"
          placeholder="Optional notes about this printer"
          :disabled="isLoading"
          rows="3"
        />
      </div>

      <!-- Specifications Section -->
      <div class="section-divider">Specifications</div>

      <div class="form-row">
        <div class="form-field">
          <label for="nozzle_diameter">Nozzle Diameter (mm)</label>
          <InputNumber
            id="nozzle_diameter"
            v-model="form.nozzle_diameter"
            :invalid="!!errors.nozzle_diameter"
            placeholder="0.4"
            :min="0"
            :max-fraction-digits="2"
            :disabled="isLoading"
          />
          <small v-if="errors.nozzle_diameter" class="p-error">{{ errors.nozzle_diameter }}</small>
        </div>

        <div class="form-field">
          <label for="bed_x">Bed Width (mm)</label>
          <InputNumber
            id="bed_x"
            v-model="form.bed_x"
            :invalid="!!errors.bed_x"
            placeholder="220"
            :min="0"
            :max-fraction-digits="1"
            :disabled="isLoading"
          />
          <small v-if="errors.bed_x" class="p-error">{{ errors.bed_x }}</small>
        </div>
      </div>

      <div class="form-row">
        <div class="form-field">
          <label for="bed_y">Bed Depth (mm)</label>
          <InputNumber
            id="bed_y"
            v-model="form.bed_y"
            :invalid="!!errors.bed_y"
            placeholder="220"
            :min="0"
            :max-fraction-digits="1"
            :disabled="isLoading"
          />
          <small v-if="errors.bed_y" class="p-error">{{ errors.bed_y }}</small>
        </div>

        <div class="form-field">
          <label for="bed_z">Bed Height (mm)</label>
          <InputNumber
            id="bed_z"
            v-model="form.bed_z"
            :invalid="!!errors.bed_z"
            placeholder="250"
            :min="0"
            :max-fraction-digits="1"
            :disabled="isLoading"
          />
          <small v-if="errors.bed_z" class="p-error">{{ errors.bed_z }}</small>
        </div>
      </div>

      <div class="form-row">
        <div class="form-field checkbox-field">
          <Checkbox
            id="has_heated_bed"
            v-model="form.has_heated_bed"
            :binary="true"
            :disabled="isLoading"
          />
          <label for="has_heated_bed">Heated Bed</label>
        </div>

        <div class="form-field checkbox-field">
          <Checkbox
            id="has_heated_chamber"
            v-model="form.has_heated_chamber"
            :binary="true"
            :disabled="isLoading"
          />
          <label for="has_heated_chamber">Heated Chamber</label>
        </div>
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
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.form-field label {
  font-weight: 500;
  color: var(--p-text-color);
}

.form-field :deep(input),
.form-field :deep(.p-inputnumber-input),
.form-field :deep(.p-select),
.form-field :deep(.p-textarea) {
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-field {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-field label {
  order: 2;
  margin: 0;
}

.section-divider {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--p-primary-color);
  border-bottom: 2px solid var(--p-surface-border);
  padding-bottom: 0.5rem;
  margin-top: 0.5rem;
}

.help-text {
  color: var(--p-text-muted-color);
  font-size: 0.875rem;
}

.p-error {
  color: var(--p-red-500);
}
</style>
