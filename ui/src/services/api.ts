import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { toast } from 'react-hot-toast';
import { Agent, AgentRule, Finding, FindingFilter, Configuration } from '../types';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

// Error types
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: string,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Get token from localStorage
    const token = localStorage.getItem('auth_token');

    // Add token to headers if it exists
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Handle specific error cases
      switch (error.response.status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
          break;
        case 403:
          toast.error('You do not have permission to perform this action');
          break;
        case 429:
          toast.error('Too many requests. Please try again later');
          break;
        default:
          toast.error(error.response.data?.message || 'An error occurred');
      }

      // Create APIError with response data
      return Promise.reject(
        new APIError(
          error.response.data?.message || 'An error occurred',
          error.response.status,
          error.response.data?.code,
          error.response.data
        )
      );
    }

    // Network error or timeout
    if (error.code === 'ECONNABORTED') {
      toast.error('Request timed out. Please try again');
    } else {
      toast.error('Network error. Please check your connection');
    }

    return Promise.reject(
      new APIError(
        error.message || 'Network error',
        undefined,
        error.code
      )
    );
  }
);

// API methods
export const api = {
  // Auth endpoints
  auth: {
    login: async (username: string, password: string) => {
      const response = await apiClient.post('/auth/login', { username, password });
      return response.data;
    },
    logout: async () => {
      const response = await apiClient.post('/auth/logout');
      return response.data;
    },
    refreshToken: async () => {
      const response = await apiClient.post('/auth/refresh');
      return response.data;
    },
  },

  // System status
  status: {
    getSystemStatus: async () => {
      const response = await apiClient.get('/status');
      return response.data;
    },
    startSystem: async () => {
      const response = await apiClient.post('/control/start');
      return response.data;
    },
    stopSystem: async () => {
      const response = await apiClient.post('/control/stop');
      return response.data;
    },
  },

  // Agents
  agents: {
    list: async () => {
      const response = await apiClient.get('/agents');
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/agents/${id}`);
      return response.data;
    },
    create: async (data: any) => {
      const response = await apiClient.post('/agents', data);
      return response.data;
    },
    update: async (id: string, data: any) => {
      const response = await apiClient.put(`/agents/${id}`, data);
      return response.data;
    },
    delete: async (id: string) => {
      const response = await apiClient.delete(`/agents/${id}`);
      return response.data;
    },
  },

  // Findings
  findings: {
    list: async (params?: any) => {
      const response = await apiClient.get('/findings', { params });
      return response.data;
    },
    get: async (id: string) => {
      const response = await apiClient.get(`/findings/${id}`);
      return response.data;
    },
  },
};

export default api;
