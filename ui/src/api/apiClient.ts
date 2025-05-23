import axios from 'axios';

// Determine the base URL for the Management API
// Use environment variable if available, otherwise default to localhost:8000/api/v1
// Vite uses import.meta.env.VITE_* for environment variables
const API_BASE_URL = import.meta.env.VITE_MANAGEMENT_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add interceptors for request/response handling (e.g., logging, error handling)

// apiClient.interceptors.request.use(config => {
//   console.log('Starting Request', config);
//   return config;
// });

// apiClient.interceptors.response.use(response => {
//   console.log('Response:', response);
//   return response;
// }, error => {
//   console.error('Response Error:', error.response || error.message);
//   return Promise.reject(error);
// });

export default apiClient; 