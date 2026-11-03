<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="initError" class="error">{{ initError }}</div>
    <div v-else>
      <div v-if="successOrder" class="banner success-banner">
        <span>{{ t('restocking.success', { orderNumber: successOrder.order_number }) }}</span>
        <router-link to="/orders">{{ t('restocking.viewOrders') }}</router-link>
      </div>
      <div v-if="actionError" class="banner error-banner">{{ actionError }}</div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(budget) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.stats.recommended') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(selectedTotal) }}</div>
        </div>
        <div :class="['stat-card', isOverBudget ? 'danger' : 'success']">
          <div class="stat-label">{{ t('restocking.stats.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ formatMoney(remaining) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.stats.itemsSelected') }}</div>
          <div class="stat-value">{{ selectedCount }}</div>
        </div>
      </div>

      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budget') }}</h3>
        </div>
        <div class="budget-controls">
          <div class="slider-wrap">
            <input
              v-model.number="budget"
              type="range"
              min="0"
              :max="fullRestockCost"
              step="1"
              class="budget-slider"
              :aria-label="t('restocking.budget')"
            />
            <div class="slider-labels">
              <span>{{ t('restocking.sliderMin') }}: {{ currencySymbol }}0</span>
              <span>{{ t('restocking.sliderMax') }}: {{ currencySymbol }}{{ formatMoney(fullRestockCost) }}</span>
            </div>
          </div>
          <input
            v-model.number="budget"
            type="number"
            min="0"
            step="0.01"
            class="budget-input"
            :aria-label="t('restocking.budgetInput')"
          />
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ rows.length }})</h3>
          <button
            class="place-order-btn"
            :disabled="!canPlaceOrder"
            @click="placeOrder"
          >
            {{ placing ? t('restocking.placing') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="isOverBudget" class="banner warning-banner">{{ t('restocking.overBudget') }}</div>

        <div v-if="rows.length === 0" class="empty-state">{{ t('restocking.noItems') }}</div>
        <div v-else :class="['table-container', { refreshing }]">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.include') }}</th>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.warehouse') }}</th>
                <th>{{ t('restocking.table.onHand') }}</th>
                <th>{{ t('restocking.table.forecast') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.leadTime') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.lineTotal') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.sku">
                <td>
                  <input
                    type="checkbox"
                    :checked="row.included"
                    :aria-label="t('restocking.table.include')"
                    @change="onIncludeChange(row, $event)"
                  />
                </td>
                <td><strong>{{ row.sku }}</strong></td>
                <td>{{ translateProductName(row.name) }}</td>
                <td>{{ translateWarehouse(row.warehouse) }}</td>
                <td>{{ row.quantity_on_hand }}</td>
                <td>{{ row.forecasted_demand }}</td>
                <td>
                  <span :class="['badge', row.trend]">{{ t(`trends.${row.trend}`) }}</span>
                </td>
                <td>{{ currencySymbol }}{{ formatMoney(row.unit_cost) }}</td>
                <td>{{ row.lead_time_days }}</td>
                <td>
                  <input
                    type="number"
                    min="0"
                    step="1"
                    class="qty-input"
                    :value="row.quantity"
                    :aria-label="t('restocking.table.quantity')"
                    @input="onQuantityInput(row, $event)"
                  />
                </td>
                <td><strong>{{ currencySymbol }}{{ formatMoney(row.quantity * row.unit_cost) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

const DEBOUNCE_MS = 300

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => (currentCurrency.value === 'JPY' ? '¥' : '$'))

    const loading = ref(true)       // first load only
    const refreshing = ref(false)   // subsequent refetches (table stays visible)
    const initError = ref(null)
    const actionError = ref(null)
    const placing = ref(false)
    const successOrder = ref(null)

    const budget = ref(0)
    const fullRestockCost = ref(0)
    const rows = ref([])

    // True once the user edits a checkbox or quantity. Any later budget/slider
    // change refetches and rebuilds the rows from the server recommendation,
    // so manual edits are intentionally discarded at that point.
    const customised = ref(false)

    // Only warehouse/category apply to restocking (no month/status dimension)
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    const toRow = (item) => ({
      ...item,
      included: item.recommended_quantity > 0,
      quantity: item.recommended_quantity || item.suggested_quantity
    })

    // Guards against out-of-order responses: only the latest request may apply
    let requestSeq = 0

    const fetchRecommendations = async (budgetValue = budget.value) => {
      const seq = ++requestSeq
      const filters = getCurrentFilters()
      const data = await api.getRestockRecommendations(budgetValue, {
        warehouse: filters.warehouse,
        category: filters.category
      })
      if (seq !== requestSeq) return null
      fullRestockCost.value = data.full_restock_cost
      rows.value = data.items.map(toRow)
      customised.value = false
      return data
    }

    const refresh = async () => {
      // Backend rejects negative budgets; ignore empty/invalid number input
      if (typeof budget.value !== 'number' || !Number.isFinite(budget.value) || budget.value < 0) return
      try {
        refreshing.value = true
        actionError.value = null
        await fetchRecommendations()
      } catch (err) {
        actionError.value = errorMessage(err, 'Failed to load recommendations')
      } finally {
        refreshing.value = false
      }
    }

    const errorMessage = (err, fallback) => {
      const detail = err?.response?.data?.detail
      if (typeof detail === 'string') return detail
      if (detail) return JSON.stringify(detail)
      return `${fallback}: ${err.message}`
    }

    // Hand-written debounce for slider/number-input changes
    let debounceTimer = null
    // Set when budget is assigned programmatically (initial load) so the
    // watcher does not trigger a duplicate fetch
    let skipNextBudgetWatch = false

    watch(budget, () => {
      if (skipNextBudgetWatch) {
        skipNextBudgetWatch = false
        return
      }
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(refresh, DEBOUNCE_MS)
    })

    watch([selectedLocation, selectedCategory], () => {
      clearTimeout(debounceTimer)
      refresh()
    })

    const loadInitial = async () => {
      try {
        loading.value = true
        // budget=0 call is only used to learn full_restock_cost
        const probe = await fetchRecommendations(0)
        const half = Math.round((probe?.full_restock_cost ?? 0) * 0.5)
        if (half !== budget.value) skipNextBudgetWatch = true
        budget.value = half
        await fetchRecommendations(half)
      } catch (err) {
        initError.value = errorMessage(err, 'Failed to load restocking data')
      } finally {
        loading.value = false
      }
    }

    // Selected = included with quantity > 0 (this is also what gets ordered)
    const selectedRows = computed(() => rows.value.filter(r => r.included && r.quantity > 0))
    const selectedTotal = computed(() =>
      selectedRows.value.reduce((sum, r) => sum + r.quantity * r.unit_cost, 0)
    )
    const remaining = computed(() => (Number(budget.value) || 0) - selectedTotal.value)
    const selectedCount = computed(() => selectedRows.value.length)
    // Half-cent tolerance avoids false positives from float rounding
    const isOverBudget = computed(() => selectedTotal.value > (Number(budget.value) || 0) + 0.005)
    const canPlaceOrder = computed(() =>
      !placing.value && selectedCount.value > 0 && !isOverBudget.value
    )

    const onIncludeChange = (row, event) => {
      row.included = event.target.checked
      customised.value = true
    }

    const onQuantityInput = (row, event) => {
      const n = Math.floor(Number(event.target.value))
      row.quantity = Number.isFinite(n) && n > 0 ? n : 0
      customised.value = true
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        placing.value = true
        actionError.value = null
        successOrder.value = null
        const order = await api.placeRestockOrder({
          budget: budget.value,
          items: selectedRows.value.map(r => ({ sku: r.sku, quantity: r.quantity }))
        })
        successOrder.value = order
        await fetchRecommendations()
      } catch (err) {
        actionError.value = errorMessage(err, t('restocking.failed'))
      } finally {
        placing.value = false
      }
    }

    const formatMoney = (value) =>
      Number(value || 0).toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })

    onMounted(loadInitial)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      currencySymbol,
      loading,
      refreshing,
      initError,
      actionError,
      placing,
      successOrder,
      budget,
      fullRestockCost,
      rows,
      customised,
      selectedTotal,
      remaining,
      selectedCount,
      isOverBudget,
      canPlaceOrder,
      onIncludeChange,
      onQuantityInput,
      placeOrder,
      formatMoney,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
/* Global .card supplies the padding and .card-header/.card-title supply the heading
   look, so only the extra gap for the header's action button is set here. */
.card-header {
  gap: var(--space-6);
}

.card-title {
  margin: 0;
}

.budget-card {
  margin-bottom: var(--space-6);
}

.budget-controls {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.slider-wrap {
  flex: 1;
}

.budget-slider {
  width: 100%;
  accent-color: var(--color-primary);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-xs);
  color: var(--color-text-muted);
  margin-top: var(--space-1);
}

.budget-input,
.qty-input {
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  color: var(--color-text);
  background: var(--color-surface);
}

.budget-input {
  width: 160px;
}

.qty-input {
  width: 90px;
  padding: var(--space-1) var(--space-2);
}

.budget-input:focus,
.qty-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: var(--focus-ring);
}

.place-order-btn {
  padding: var(--space-2) var(--space-4);
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.place-order-btn:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.place-order-btn:disabled {
  background: var(--color-border-strong);
  cursor: not-allowed;
}

.banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  margin-bottom: var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--font-sm);
}

/* Banner tints reuse the shared status tokens (soft background, strong text) */
.success-banner {
  background: var(--color-success-soft);
  border: 1px solid var(--color-success);
  color: var(--color-success-text);
}

.success-banner a {
  color: var(--color-success-text);
  font-weight: 600;
}

.error-banner {
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger);
  color: var(--color-danger-text);
}

.warning-banner {
  background: var(--color-warning-soft);
  border: 1px solid var(--color-warning);
  color: var(--color-warning-text);
  /* inside the padded card now, so no extra horizontal margin */
  margin: 0 0 var(--space-4);
}

.refreshing {
  opacity: 0.6;
  transition: opacity 0.2s;
}

.loading,
.error,
.empty-state {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
}

.error {
  color: var(--color-danger);
}
</style>
