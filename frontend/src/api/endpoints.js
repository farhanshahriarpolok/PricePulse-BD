import apiClient from './client';

export const getHealth = () => apiClient.get('/health');

export const getDailyPulse = () => apiClient.get('/pulse/today');

export const searchRealtime = (query, date = null) => {
  const params = { query };
  if (date) params.date = date;
  return apiClient.get('/search/realtime', { params });
};

export const getCommodities = (category = null) => {
  const params = category ? { category } : {};
  return apiClient.get('/commodities', { params });
};

export const getCommodityDetail = (id) => apiClient.get(`/commodities/${id}`);

export const getCommodityStores = (id) => apiClient.get(`/commodities/${id}/stores`);


export const getCommodityHistory = (id, startDate = null, endDate = null, marketId = null) => {
  const params = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  if (marketId) params.market_id = marketId;
  return apiClient.get(`/commodities/${id}/history`, { params });
};

export const getActiveAnomalies = (date = null) => {
  const params = date ? { date } : {};
  return apiClient.get('/anomalies/active', { params });
};

export const explainAnomaly = (commodityId, date = null) => {
  const params = date ? { date } : {};
  return apiClient.get(`/anomalies/${commodityId}/explain`, { params });
};

export const getLocationSpread = (commodityId, date = null) => {
  const params = { commodity_id: commodityId };
  if (date) params.date = date;
  return apiClient.get('/locations/spread', { params });
};

export const getLocationHierarchy = () => apiClient.get('/locations/hierarchy');

export const submitManualObservation = (payload) => apiClient.post('/observations/manual', payload);

export const getComparisonData = (params) => {
  // params: { ids: '1,2,3', district_id: null }
  return apiClient.get('/commodities/compare', { params });
};

export const getSourceHealth = () => apiClient.get('/system/sources');

export const triggerManualSync = () => apiClient.post('/system/sync');

export const getSyncTaskStatus = (taskId) => apiClient.get(`/system/sync/${taskId}`);

export const injectShock = (payload) => apiClient.post('/simulation/inject-shock', payload);

export const getSpatialArbitrage = (commodityId) =>
  apiClient.get('/locations/arbitrage', { params: { commodity_id: commodityId } });

export const getConsumerOpportunity = (commodityId) =>
  apiClient.get('/locations/consumer-opportunity', { params: { commodity_id: commodityId } });

// ── Bazaar Basket endpoints ───────────────────────────────────────────────────

/**
 * POST /basket/calculate
 * Calculate optimized channel cost breakdown for a custom market basket.
 * @param {Object} payload - { items: [{commodity_id, quantity, raw_unit}], custom_name? }
 */
export const calculateBasket = (payload) => apiClient.post('/basket/calculate', payload);

/**
 * GET /basket/presets
 * Returns 3 pre-defined Bangladeshi family basket presets.
 */
export const getBasketPresets = () => apiClient.get('/basket/presets');

/**
 * POST /basket/saved
 * Save customized household basket to SQLite.
 */
export const saveBasket = (payload) => apiClient.post('/basket/saved', payload);

/**
 * GET /basket/saved
 * List all saved household baskets.
 */
export const getSavedBaskets = () => apiClient.get('/basket/saved');

/**
 * GET /basket/saved/:id
 * Retrieve single saved basket with calculation and item details.
 */
export const getSavedBasketDetail = (basketId) => apiClient.get(`/basket/saved/${basketId}`);

/**
 * DELETE /basket/saved/:id
 * Remove a saved basket.
 */
export const deleteSavedBasket = (basketId) => apiClient.delete(`/basket/saved/${basketId}`);

/**
 * GET /basket/saved/:id/trend
 * 30-day personal CPI trend, volatility metrics, and market analysis narrative.
 */
export const getSavedBasketTrend = (basketId, days = 30) =>
  apiClient.get(`/basket/saved/${basketId}/trend`, { params: { days } });

export const getCommodityForecast = (commodityId, channel = 'wholesale', marketId = null) => {
  const params = { channel };
  if (marketId) params.market_id = marketId;
  return apiClient.get(`/commodities/${commodityId}/forecast`, { params });
};

/**
 * GET /commodities/:id/supply-chain
 * Supply chain price gap deconstruction into freight, arath commission,
 * porterage handling, transit shrinkage, and residual spread (unobserved/unallocated portion).
 */
export const getSupplyChainDeconstruction = (commodityId, params = {}) => {
  return apiClient.get(`/commodities/${commodityId}/supply-chain`, { params });
};
