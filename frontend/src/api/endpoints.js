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

