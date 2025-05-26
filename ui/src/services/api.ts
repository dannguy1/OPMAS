import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';
import { User, Finding, Action, DashboardStats, RecentActivity } from '../types';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
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
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      if (error.response.status === 401) {
        // Handle unauthorized access
        localStorage.removeItem('token');
        window.location.href = '/login';
      } else {
        // Show error message
        const message = error.response.data && typeof error.response.data === 'object' && 'message' in error.response.data
          ? String(error.response.data.message)
          : 'An error occurred';
        toast.error(message);
      }
    } else if (error.request) {
      // The request was made but no response was received
      toast.error('No response from server');
    } else {
      // Something happened in setting up the request that triggered an Error
      toast.error('Error setting up request');
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await apiClient.post<{ access_token: string; token_type: string }>(
      '/api/v1/auth/login',
      formData,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
    return response.data;
  },
  getCurrentUser: async () => {
    const response = await apiClient.get<User>('/api/v1/auth/me');
    return response.data;
  },
  logout: async () => {
    const response = await apiClient.post('/api/v1/auth/logout');
    return response.data;
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async () => {
    const response = await apiClient.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
  },
  getRecentActivity: async () => {
    const response = await apiClient.get<RecentActivity[]>('/api/v1/dashboard/activity/recent');
    return response.data;
  },
};

// Findings API
export const findingsApi = {
  getFindings: async () => {
    const response = await apiClient.get<Finding[]>('/api/v1/findings');
    return response.data;
  },
  getFinding: async (id: string) => {
    const response = await apiClient.get<Finding>(`/api/v1/findings/${id}`);
    return response.data;
  },
  createFinding: async (finding: Omit<Finding, 'id' | 'createdAt' | 'updatedAt'>) => {
    const response = await apiClient.post<Finding>('/api/v1/findings', finding);
    return response.data;
  },
  updateFinding: async (id: string, finding: Partial<Finding>) => {
    const response = await apiClient.put<Finding>(`/api/v1/findings/${id}`, finding);
    return response.data;
  },
  deleteFinding: async (id: string) => {
    await apiClient.delete(`/api/v1/findings/${id}`);
  },
};

// Actions API
export const actionsApi = {
  getActions: async () => {
    const response = await apiClient.get<Action[]>('/api/v1/actions');
    return response.data;
  },
  getAction: async (id: string) => {
    const response = await apiClient.get<Action>(`/api/v1/actions/${id}`);
    return response.data;
  },
  createAction: async (action: Omit<Action, 'id' | 'createdAt' | 'updatedAt'>) => {
    const response = await apiClient.post<Action>('/api/v1/actions', action);
    return response.data;
  },
  updateAction: async (id: string, action: Partial<Action>) => {
    const response = await apiClient.put<Action>(`/api/v1/actions/${id}`, action);
    return response.data;
  },
  deleteAction: async (id: string) => {
    await apiClient.delete(`/api/v1/actions/${id}`);
  },
};
