export function computeRestockRecommendations(demandForecasts, inventoryItems, budget) {
  const bySku = new Map(inventoryItems.map(item => [item.sku, item]))

  const candidates = demandForecasts
    .map(forecast => {
      const inventoryItem = bySku.get(forecast.item_sku)
      if (!inventoryItem) return null

      const shortfall = forecast.forecasted_demand - forecast.current_demand
      return {
        sku: forecast.item_sku,
        name: forecast.item_name,
        trend: forecast.trend,
        unit_cost: inventoryItem.unit_cost,
        current_demand: forecast.current_demand,
        forecasted_demand: forecast.forecasted_demand,
        shortfall
      }
    })
    .filter(candidate => candidate && candidate.shortfall > 0)

  candidates.sort((a, b) => {
    if (a.trend === 'increasing' && b.trend !== 'increasing') return -1
    if (b.trend === 'increasing' && a.trend !== 'increasing') return 1
    return b.shortfall - a.shortfall
  })

  const recommendations = []
  let runningTotal = 0

  for (const candidate of candidates) {
    if (runningTotal >= budget) break

    const remainingBudget = budget - runningTotal
    const maxAffordableQty = Math.floor(remainingBudget / candidate.unit_cost)
    if (maxAffordableQty <= 0) continue

    const quantity = Math.min(candidate.shortfall, maxAffordableQty)
    if (quantity <= 0) continue

    const lineCost = quantity * candidate.unit_cost
    recommendations.push({
      sku: candidate.sku,
      name: candidate.name,
      trend: candidate.trend,
      current_demand: candidate.current_demand,
      forecasted_demand: candidate.forecasted_demand,
      unit_cost: candidate.unit_cost,
      quantity,
      line_cost: lineCost
    })
    runningTotal += lineCost
  }

  return { recommendations, totalCost: runningTotal }
}
