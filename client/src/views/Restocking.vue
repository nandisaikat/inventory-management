<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        </div>
        <div class="budget-control">
          <input
            type="range"
            min="0"
            max="100000"
            step="1000"
            v-model.number="budget"
            class="budget-slider"
          />
          <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendedItems') }}</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.table.sku') }}</th>
                <th>{{ t('restocking.table.name') }}</th>
                <th>{{ t('restocking.table.trend') }}</th>
                <th>{{ t('restocking.table.currentDemand') }}</th>
                <th>{{ t('restocking.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.table.quantity') }}</th>
                <th>{{ t('restocking.table.unitCost') }}</th>
                <th>{{ t('restocking.table.lineCost') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in recommendations" :key="rec.sku">
                <td><strong>{{ rec.sku }}</strong></td>
                <td>{{ rec.name }}</td>
                <td>
                  <span class="badge" :class="rec.trend">
                    {{ t(`trends.${rec.trend}`) }}
                  </span>
                </td>
                <td>{{ rec.current_demand }}</td>
                <td>{{ rec.forecasted_demand }}</td>
                <td>{{ rec.quantity }}</td>
                <td>{{ currencySymbol }}{{ rec.unit_cost }}</td>
                <td><strong>{{ currencySymbol }}{{ rec.line_cost.toLocaleString() }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="order-summary">
          <div class="summary-line">
            {{ t('restocking.totalCost') }}: <strong>{{ currencySymbol }}{{ totalCost.toLocaleString() }}</strong>
            / {{ currencySymbol }}{{ budget.toLocaleString() }}
          </div>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || submitting"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="orderConfirmation" class="confirmation-message">
          {{ t('restocking.orderSubmitted', { orderNumber: orderConfirmation }) }}
        </div>
        <div v-if="submitError" class="error">{{ submitError }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { computeRestockRecommendations } from '../composables/useRestockRecommendations'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const submitting = ref(false)
    const submitError = ref(null)
    const orderConfirmation = ref(null)

    const budget = ref(10000)
    const demandForecasts = ref([])
    const inventoryItems = ref([])

    const loadData = async () => {
      try {
        loading.value = true
        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({})
        ])
        demandForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load restocking data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const restockResult = computed(() => {
      return computeRestockRecommendations(demandForecasts.value, inventoryItems.value, budget.value)
    })

    const recommendations = computed(() => restockResult.value.recommendations)
    const totalCost = computed(() => restockResult.value.totalCost)

    const placeOrder = async () => {
      submitting.value = true
      submitError.value = null
      orderConfirmation.value = null
      try {
        const order = await api.createRestockOrder({
          budget: budget.value,
          items: recommendations.value.map(r => ({
            sku: r.sku,
            name: r.name,
            quantity: r.quantity,
            unit_cost: r.unit_cost
          }))
        })
        orderConfirmation.value = order.order_number
      } catch (err) {
        submitError.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(() => loadData())

    return {
      t,
      loading,
      error,
      submitting,
      submitError,
      orderConfirmation,
      budget,
      recommendations,
      totalCost,
      currencySymbol,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-control {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.budget-slider {
  flex: 1;
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  outline: none;
}

.budget-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  border: 2px solid white;
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  border: 2px solid white;
}

.budget-slider::-moz-range-track {
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
}

.budget-value {
  min-width: 120px;
  text-align: right;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #64748b;
  font-size: 0.938rem;
}

.order-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.summary-line {
  font-size: 0.938rem;
  color: #334155;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.5rem;
  border-radius: 8px;
  font-size: 0.938rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.confirmation-message {
  margin-top: 1rem;
  background: #d1fae5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.938rem;
}
</style>
