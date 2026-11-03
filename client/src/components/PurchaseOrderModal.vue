<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen && backlogItem" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">
              {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
            </h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body">
            <!-- Backlog item context -->
            <div class="item-context">
              <h4 class="item-name">{{ translateProductName(backlogItem.item_name) }}</h4>
              <div class="item-meta">
                <span class="item-sku">{{ t('purchaseOrder.sku') }}: {{ backlogItem.item_sku }}</span>
                <span class="item-shortage">{{ t('purchaseOrder.shortage') }}: {{ shortage }} {{ t('purchaseOrder.units') }}</span>
              </div>
            </div>

            <!-- View mode -->
            <template v-if="mode === 'view'">
              <div v-if="loading" class="state-message">{{ t('common.loading') }}</div>
              <div v-else-if="error" class="error-message">{{ error }}</div>
              <div v-else-if="purchaseOrder" class="info-grid">
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.poId') }}</div>
                  <div class="info-value mono">{{ purchaseOrder.id }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.supplierName') }}</div>
                  <div class="info-value">{{ purchaseOrder.supplier_name }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.quantity') }}</div>
                  <div class="info-value">{{ purchaseOrder.quantity }} {{ t('purchaseOrder.units') }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.unitCost') }}</div>
                  <div class="info-value">{{ formatMoney(purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.totalCost') }}</div>
                  <div class="info-value strong">{{ formatMoney(purchaseOrder.quantity * purchaseOrder.unit_cost) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.expectedDelivery') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.expected_delivery_date) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.status') }}</div>
                  <div class="info-value">
                    <span class="badge info">{{ purchaseOrder.status }}</span>
                  </div>
                </div>
                <div class="info-item">
                  <div class="info-label">{{ t('purchaseOrder.createdDate') }}</div>
                  <div class="info-value">{{ formatDate(purchaseOrder.created_date) }}</div>
                </div>
                <div v-if="purchaseOrder.notes" class="info-item full-row">
                  <div class="info-label">{{ t('purchaseOrder.notes') }}</div>
                  <div class="info-value">{{ purchaseOrder.notes }}</div>
                </div>
              </div>
            </template>

            <!-- Create mode -->
            <form v-else id="po-form" class="po-form" novalidate @submit.prevent="submit">
              <div class="form-field">
                <label class="form-label" for="po-supplier">{{ t('purchaseOrder.supplierName') }}</label>
                <input id="po-supplier" v-model="form.supplier_name" type="text" class="form-input" />
              </div>

              <div class="form-row">
                <div class="form-field">
                  <label class="form-label" for="po-quantity">{{ t('purchaseOrder.quantity') }}</label>
                  <input id="po-quantity" v-model="form.quantity" type="number" min="1" step="1" class="form-input" />
                </div>
                <div class="form-field">
                  <label class="form-label" for="po-unit-cost">{{ t('purchaseOrder.unitCost') }}</label>
                  <input id="po-unit-cost" v-model="form.unit_cost" type="number" min="0" step="0.01" class="form-input" />
                </div>
              </div>

              <div class="form-field">
                <label class="form-label" for="po-date">{{ t('purchaseOrder.expectedDelivery') }}</label>
                <input id="po-date" v-model="form.expected_delivery_date" type="date" class="form-input" />
              </div>

              <div class="form-field">
                <label class="form-label" for="po-notes">{{ t('purchaseOrder.notes') }}</label>
                <textarea id="po-notes" v-model="form.notes" rows="3" class="form-input"></textarea>
              </div>

              <div v-if="error" class="error-message">{{ error }}</div>
            </form>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" type="button" @click="close">{{ t('common.close') }}</button>
            <button
              v-if="mode === 'create'"
              class="btn-primary"
              type="submit"
              form="po-form"
              :disabled="submitting"
            >
              {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script>
import { ref, reactive, computed, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    backlogItem: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create',
      validator: (value) => ['create', 'view'].includes(value)
    }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentLocale, translateProductName } = useI18n()

    const form = reactive({
      supplier_name: '',
      quantity: '',
      unit_cost: '',
      expected_delivery_date: '',
      notes: ''
    })
    const purchaseOrder = ref(null)
    const loading = ref(false)
    const submitting = ref(false)
    const error = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(0, props.backlogItem.quantity_needed - props.backlogItem.quantity_available)
    })

    const resetState = () => {
      form.supplier_name = ''
      form.quantity = shortage.value > 0 ? shortage.value : ''
      form.unit_cost = ''
      form.expected_delivery_date = ''
      form.notes = ''
      purchaseOrder.value = null
      error.value = null
      loading.value = false
      submitting.value = false
    }

    const loadPurchaseOrder = async () => {
      loading.value = true
      error.value = null
      try {
        purchaseOrder.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        console.error('Failed to load purchase order:', err)
        error.value = err.response?.status === 404
          ? t('purchaseOrder.errors.notFound')
          : t('purchaseOrder.errors.loadFailed')
      } finally {
        loading.value = false
      }
    }

    // Reset the form (and fetch the PO in view mode) every time the modal opens.
    // Also watch backlogItem so a swap while open doesn't show stale data.
    watch(
      () => [props.isOpen, props.backlogItem],
      ([open, item]) => {
        if (!open || !item) return
        resetState()
        if (props.mode === 'view') loadPurchaseOrder()
      },
      { immediate: true }
    )

    // Returns an error message, or null if the form is valid.
    // Values bound to number inputs may be strings, so coerce before checking.
    const validate = () => {
      if (!form.supplier_name.trim()) return t('purchaseOrder.errors.supplierRequired')
      const qty = Number(form.quantity)
      if (form.quantity === '' || !Number.isInteger(qty) || qty <= 0) {
        return t('purchaseOrder.errors.quantityInvalid')
      }
      const cost = Number(form.unit_cost)
      if (form.unit_cost === '' || !Number.isFinite(cost) || cost <= 0) {
        return t('purchaseOrder.errors.unitCostInvalid')
      }
      if (!form.expected_delivery_date) return t('purchaseOrder.errors.dateRequired')
      return null
    }

    const submit = async () => {
      if (submitting.value) return
      const validationError = validate()
      if (validationError) {
        error.value = validationError
        return
      }

      submitting.value = true
      error.value = null
      try {
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier_name.trim(),
          quantity: Number(form.quantity),
          unit_cost: Number(form.unit_cost),
          expected_delivery_date: form.expected_delivery_date,
          notes: form.notes.trim() || null
        })
        emit('po-created', created)
      } catch (err) {
        console.error('Failed to create purchase order:', err)
        // 409 means a PO already exists for this item
        error.value = err.response?.status === 409
          ? t('purchaseOrder.errors.alreadyExists')
          : err.response?.status === 404
            ? t('purchaseOrder.errors.notFound')
            : t('purchaseOrder.errors.createFailed')
      } finally {
        submitting.value = false
      }
    }

    const close = () => {
      emit('close')
    }

    const formatMoney = (value) => {
      const num = Number(value)
      if (!Number.isFinite(num)) return '-'
      // PO unit costs are entered in USD regardless of display currency
      return num.toLocaleString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        style: 'currency',
        currency: 'USD'
      })
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return '-'
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    return {
      t,
      translateProductName,
      form,
      purchaseOrder,
      loading,
      submitting,
      error,
      shortage,
      submit,
      close,
      formatMoney,
      formatDate
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: var(--space-4);
}

.modal-container {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: var(--space-2);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.close-button:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.item-context {
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--color-border);
  margin-bottom: var(--space-6);
}

.item-name {
  font-size: var(--font-xl);
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--space-2) 0;
}

.item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  font-size: var(--font-sm);
  color: var(--color-text-muted);
}

.item-sku {
  font-family: 'Monaco', 'Courier New', monospace;
}

.item-shortage {
  color: var(--color-danger);
  font-weight: 600;
}

.state-message {
  text-align: center;
  padding: var(--space-6);
  color: var(--color-text-muted);
  font-size: var(--font-sm);
}

.error-message {
  padding: var(--space-3) var(--space-4);
  background: var(--color-danger-soft);
  color: var(--color-danger-text);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-6);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-item.full-row {
  grid-column: 1 / -1;
}

.info-label,
.form-label {
  font-size: var(--font-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.info-value {
  font-size: var(--font-sm);
  color: var(--color-text);
  font-weight: 500;
}

.info-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  color: var(--color-primary);
}

.info-value.strong {
  font-weight: 700;
}

.badge.info {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-sm);
  background: var(--color-info-soft);
  color: var(--color-info-text);
  font-size: var(--font-sm);
  font-weight: 600;
  text-transform: capitalize;
}

.po-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-input {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  font-family: inherit;
  color: var(--color-text);
  background: var(--color-surface);
  transition: border-color 0.15s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

textarea.form-input {
  resize: vertical;
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.btn-secondary {
  padding: var(--space-3) var(--space-5);
  background: var(--color-surface-hover);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--font-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: var(--color-border);
  border-color: var(--color-border-strong);
}

.btn-primary {
  padding: var(--space-3) var(--space-5);
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-size: var(--font-sm);
  color: var(--color-surface);
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
