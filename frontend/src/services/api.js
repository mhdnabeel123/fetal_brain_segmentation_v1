import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    config.metadata = { startTime: Date.now() };
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    const duration = Date.now() - response.config.metadata.startTime;
    console.log(`[API] ${response.config.method?.toUpperCase()} ${response.config.url} - ${duration}ms`);
    return response;
  },
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An unexpected error occurred';
    console.error(`[API Error] ${message}`);
    return Promise.reject({ message, status: error.response?.status });
  }
);

export const predictImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/predict/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export const getModelInfo = async () => {
  const response = await api.get('/model-info');
  return response.data;
};

export default api;

export const chatWithCopilot = async (messages, context) => {
  try {
    const response = await api.post('/chat/', {
      messages,
      context
    });
    return response.data;
  } catch (error) {
    console.error("Chat Error:", error);
    throw error;
  }
};
