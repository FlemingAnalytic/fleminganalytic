import axios from 'axios';

// This line now pulls the backend URL from the .env file
// When you build for production, it will use your fleminganalytic.net address
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.fleminganalytic.com/api';

/**
 * Generic API client with global error handling
 */
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Response interceptor for global error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

/**
 * Stocks & Trading API
 */
export const stocksApi = {
  getSp500: () => apiClient.get('/stocks/sp500'),
  getYtd: () => apiClient.get('/stocks/ytd'),
  getSwingStatus: (ticker) => apiClient.get(`/stocks/swing/status/${ticker}`),
  getEfToday: () => apiClient.get('/stocks/ef/today/'),
  getEfCalculation: (tickers) => apiClient.get(`/stocks/ef/ytd/${tickers}`),
  getMomentumReport: () => apiClient.get('/stocks/momentum', { responseType: 'blob' }),
};

/**
 * News API
 */
export const newsApi = {
  getDates: () => apiClient.get('/news/dates'),
  getDataByDate: (date) => apiClient.get(`/news/date/${date}`),
};

/**
 * Chat & Analysis API
 */
export const chatApi = {
  query: (prompt, model, system) => apiClient.post('/chat/query', { prompt, model, system }),
  listApps: () => apiClient.get('/chat/apps'),
  explainApp: (appName) => apiClient.get(`/chat/explain/${appName}`),
};

/**
 * Smart Analyst API
 */
export const analystApi = {
  listSaved: () => apiClient.get('/analyst/saved-datasets'),
  loadSaved: (filename) => {
    const formData = new FormData();
    formData.append('filename', filename);
    return apiClient.post('/analyst/load-saved', formData);
  },
  loadPublic: (name) => {
    const formData = new FormData();
    formData.append('name', name);
    return apiClient.post('/analyst/load-public', formData);
  },
  loadUrl: (url) => {
    const formData = new FormData();
    formData.append('url', url);
    return apiClient.post('/analyst/load-url', formData);
  },
  classify: (filename, column, method, newName, params = {}) => 
    apiClient.post('/analyst/classify', { filename, column, method, new_name: newName, params }),
  pivot: (filename, rows, cols, values, aggfunc, filters, weightCol) => 
    apiClient.post('/analyst/pivot', { filename, rows, cols, values, aggfunc, filters, weight_col: weightCol }),
  visualize: (filename, chartType, x, y, color, column) => 
    apiClient.post('/analyst/visualize', { filename, chart_type: chartType, x, y, color, column }),
  analyzeFeatures: (filename, target = '') => {
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('target', target);
    return apiClient.post('/analyst/analyze-features', formData);
  },
  trainModel: (filename, target, features, modelType) => {
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('target', target);
    formData.append('features', features);
    formData.append('model_type', modelType);
    return apiClient.post('/analyst/train-model', formData);
  },
  predict: (filename, inputData) => {
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('input_data', JSON.stringify(inputData));
    return apiClient.post('/analyst/predict', formData);
  },
  modelSummary: (filename) => {
    const formData = new FormData();
    formData.append('filename', filename);
    return apiClient.post('/analyst/model-summary', formData);
  },
  joinCensus: (filename, joinColumn, geography, geographyFormat) => 
    apiClient.post('/analyst/join-census', { filename, join_column: joinColumn, geography, geography_format: geographyFormat }),
  export: (filename, format) => apiClient.get(`/analyst/export/${filename}?format=${format}`),
};

/**
 * Astrology Intelligence API
 */
export const astroApi = {
  generateChart: (data) => apiClient.post('/astro/generate-chart', data),
  generatePdf: (data) => apiClient.post('/astro/generate-pdf', data),
  generateEtsySet: (data) => apiClient.post('/astro/generate-etsy-mug-set', data),
};

/**
 * Restaurant & Menu Management API
 */
export const restaurantApi = {
  list: (skip = 0, limit = 10) => apiClient.get(`/food/restaurants?skip=${skip}&limit=${limit}`),
  get: (id) => apiClient.get(`/food/restaurants/${id}`),
  create: (data) => apiClient.post('/food/restaurants', data),
  update: (id, data) => apiClient.put(`/food/restaurants/${id}`, data),
  delete: (id) => apiClient.delete(`/food/restaurants/${id}`),
};

/**
 * St. John Public API
 */
export const stJohnApi = {
  getServices: () => apiClient.get('/stjohn/services'),
  getEvents: () => apiClient.get('/stjohn/events'),
  getMinistries: () => apiClient.get('/stjohn/ministries'),
  getPage: (slug) => apiClient.get(`/stjohn/page/${slug}`),
};

/**
 * St. John Admin API (CMS)
 */
export const stJohnAdminApi = {
  getStats: () => apiClient.get('/stjohn/admin/api/stats'),
  listEvents: () => apiClient.get('/stjohn/admin/api/events'),
  saveEvent: (id, data) => id ? apiClient.put(`/stjohn/admin/api/events/${id}`, data) : apiClient.post('/stjohn/admin/api/events', data),
  deleteEvent: (id) => apiClient.delete(`/stjohn/admin/api/events/${id}`),
  
  listServices: () => apiClient.get('/stjohn/admin/api/services'),
  saveService: (id, data) => id ? apiClient.put(`/stjohn/admin/api/services/${id}`, data) : apiClient.post('/stjohn/admin/api/services', data),
  
  listMinistries: () => apiClient.get('/stjohn/admin/api/ministries'),
  saveMinistry: (id, data) => id ? apiClient.put(`/stjohn/admin/api/ministries/${id}`, data) : apiClient.post('/stjohn/admin/api/ministries', data),
  
  getAssets: () => apiClient.get('/stjohn/admin/api/assets'),
  uploadAsset: (formData) => apiClient.post('/stjohn/admin/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};

export default apiClient;
