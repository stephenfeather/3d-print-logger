<script setup lang="ts">
/**
 * Dialog for creating/editing maintenance records.
 * Issue #9: Minimal Printer Maintenance Details
 */

import { ref, watch, computed } from 'vue'
import { useCreateMaintenance, useUpdateMaintenance } from '@/composables/useMaintenance'
import { usePrinters } from '@/composables/usePrinters'
import type { Maintenance, MaintenanceCreate, MaintenanceUpdate } from '@/types/maintenance'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import Checkbox from 'primevue/checkbox'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import Button from 'primevue/button'
import { useToast } from 'primevue/usetoast'

const CATEGORIES = [
  { label: 'Cleaning', value: 'cleaning' },
  { label: 'Calibration', value: 'calibration' },
  { label: 'Parts Replacement', value: 'parts_replacement' },
  { label: 'Repair', value: 'repair' },
  { label: 'Inspection', value: 'inspection' },
  { label: 'Upgrade', value: 'upgrade' },
  { label: 'Other', value: 'other' },
]

const props = defineProps<{
  visible: boolean
  record?: Maintenance | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  saved: []
}>()

const toast = useToast()
const createMutation = useCreateMaintenance()
const updateMutation = useUpdateMaintenance()
const { data: printers } = usePrinters()

const isEdit = computed(() => !!props.record)
const dialogTitle = computed(() => (isEdit.value ? 'Edit Maintenance Record' : 'Add Maintenance Record'))

const printerOptions = computed(() =>
  (printers.value || []).map((p) => ({
    label: p.name,
    value: p.id,
  })),
)

interface FormState {
  printer_id: number | undefined
  date: Date
  category: string
  description: string
  done: boolean
  cost: number | undefined
  notes: string
}

const form = ref<FormState>({
  printer_id: undefined,
  date: new Date(),
  category: '',
  description: '',
  done: false,
  cost: undefined,
  notes: '',
})

const errors = ref<Record<string, string>>({})

// Reset form when dialog opens/closes or record changes
watch(
  () => [props.visible, props.record],
  () => {
    if (props.visible) {
      if (props.record) {
        form.value = {
          printer_id: props.record.printer_id,
          date: new Date(props.record.date),
          category: props.record.category,
          description: props.record.description,
          done: props.record.done,
          cost: props.record.cost ?? undefined,
          notes: props.record.notes || '',
        }
      } else {
        form.value = {
          printer_id: undefined,
          date: new Date(),
          category: '',
          description: '',
          done: false,
          cost: undefined,
          notes: '',
        }
      }
      errors.value = {}
    }
  },
  { immediate: true },
)

function validate(): boolean {
  errors.value = {}

  if (!form.value.printer_id) {
    errors.value.printer_id = 'Printer is required'
  }

  if (!form.value.category) {
    errors.value.category = 'Category is required'
  }

  if (!form.value.description.trim()) {
    errors.value.description = 'Description is required'
  }

  if (form.value.cost !== undefined && form.value.cost < 0) {
    errors.value.cost = 'Cost cannot be negative'
  }

  return Object.keys(errors.value).length === 0
}

async function handleSubmit() {
  if (!validate()) return

  try {
    if (isEdit.value && props.record) {
      const updateData: MaintenanceUpdate = {
        date: form.value.date.toISOString(),
        category: form.value.category,
        description: form.value.description,
        done: form.value.done,
        cost: form.value.cost,
        notes: form.value.notes || undefined,
      }
      await updateMutation.mutateAsync({ id: props.record.id, data: updateData })
      toast.add({
        severity: 'success',
        summary: 'Record Updated',
        detail: 'Maintenance record has been updated',
        life: 3000,
      })
    } else {
      const createData: MaintenanceCreate = {
        printer_id: form.value.printer_id!,
        date: form.value.date.toISOString(),
        category: form.value.category,
        description: form.value.description,
        done: form.value.done,
        cost: form.value.cost,
        notes: form.value.notes || undefined,
      }
      await createMutation.mutateAsync(createData)
      toast.add({
        severity: 'success',
        summary: 'Record Added',
        detail: 'Maintenance record has been created',
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
    :style="{ width: '500px', maxHeight: '90vh' }"
    @update:visible="(val) => emit('update:visible', val)"
  >
    <form class="maintenance-form" @submit.prevent="handleSubmit">
      <div class="form-field">
        <label for="printer">Printer *</label>
        <Select
          id="printer"
          v-model="form.printer_id"
          :options="printerOptions"
          option-label="label"
          option-value="value"
          placeholder="Select a printer"
          :invalid="!!errors.printer_id"
          :disabled="isLoading || isEdit"
          class="w-full"
        />
        <small v-if="errors.printer_id" class="p-error">{{ errors.printer_id }}</small>
      </div>

      <div class="form-field">
        <label for="date">Date *</label>
        <DatePicker
          id="date"
          v-model="form.date"
          :show-time="true"
          :disabled="isLoading"
          class="w-full"
        />
      </div>

      <div class="form-field">
        <label for="category">Category *</label>
        <Select
          id="category"
          v-model="form.category"
          :options="CATEGORIES"
          option-label="label"
          option-value="value"
          placeholder="Select a category"
          :invalid="!!errors.category"
          :disabled="isLoading"
          class="w-full"
        />
        <small v-if="errors.category" class="p-error">{{ errors.category }}</small>
      </div>

      <div class="form-field">
        <label for="description">Description *</label>
        <InputText
          id="description"
          v-model="form.description"
          :invalid="!!errors.description"
          :disabled="isLoading"
          class="w-full"
        />
        <small v-if="errors.description" class="p-error">{{ errors.description }}</small>
      </div>

      <div class="form-field">
        <label for="cost">Cost</label>
        <InputNumber
          id="cost"
          v-model="form.cost"
          mode="currency"
          currency="USD"
          :min="0"
          :invalid="!!errors.cost"
          :disabled="isLoading"
          class="w-full"
        />
        <small v-if="errors.cost" class="p-error">{{ errors.cost }}</small>
      </div>

      <div class="form-field">
        <label for="notes">Notes</label>
        <Textarea
          id="notes"
          v-model="form.notes"
          rows="3"
          :disabled="isLoading"
          class="w-full"
        />
      </div>

      <div class="form-field checkbox-field">
        <Checkbox
          id="done"
          v-model="form.done"
          :binary="true"
          :disabled="isLoading"
        />
        <label for="done">Completed</label>
      </div>
    </form>

    <template #footer>
      <Button
        label="Cancel"
        severity="secondary"
        text
        :disabled="isLoading"
        @click="emit('update:visible', false)"
      />
      <Button
        :label="isEdit ? 'Save Changes' : 'Add Record'"
        :loading="isLoading"
        @click="handleSubmit"
      />
    </template>
  </Dialog>
</template>

<style scoped>
.maintenance-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
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

.checkbox-field {
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
}

.checkbox-field label {
  order: 2;
}

.w-full {
  width: 100%;
}

.p-error {
  color: var(--p-red-500);
}
</style>
