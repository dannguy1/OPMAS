import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';
import { User, Finding, Action, DashboardStats, RecentActivity } from '../types';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://192.168.10.8:8000';
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

// Export the apiClient instance
export default apiClient;

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

// System API
export const systemApi = {
  get: async (path: string, config?: any) => {
    const response = await apiClient.get(`/api/v1${path}`, config);
    return response.data;
  },
  post: async (path: string, data: any) => {
    const response = await apiClient.post(`/api/v1${path}`, data);
    return response.data;
  },
};

// Actions API
export const actionsApi = {
  get: async (path: string, config?: any) => {
    const response = await apiClient.get(`/api/v1${path}`, config);
    return response.data;
  },
  post: async (path: string, data: any) => {
    const response = await apiClient.post(`/api/v1${path}`, data);
    return response.data;
  },
  patch: async (path: string, data: any) => {
    const response = await apiClient.patch(`/api/v1${path}`, data);
    return response.data;
  },
  delete: async (path: string) => {
    await apiClient.delete(`/api/v1${path}`);
  },
};

// Playbooks API
export const playbooksApi = {
  getPlaybooks: async () => {
    const response = await apiClient.get('/api/v1/playbooks');
    return response.data;
  },
  getPlaybook: async (id: string) => {
    const response = await apiClient.get(`/api/v1/playbooks/${id}`);
    return response.data;
  },
  createPlaybook: async (playbook: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.post('/api/v1/playbooks', playbook);
    return response.data;
  },
  updatePlaybook: async (id: string, playbook: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.put(`/api/v1/playbooks/${id}`, playbook);
    return response.data;
  },
  deletePlaybook: async (id: string) => {
    await apiClient.delete(`/api/v1/playbooks/${id}`);
  },
  getPlaybookStatus: async (id: string) => {
    const response = await apiClient.get(`/api/v1/playbooks/${id}/status`);
    return response.data;
  },
  executePlaybook: async (id: string, metadata?: any) => {
    const response = await apiClient.post(`/api/v1/playbooks/${id}/execute`, metadata);
    return response.data;
  },
  // Playbook Steps
  getPlaybookSteps: async (playbookId: string) => {
    const response = await apiClient.get(`/api/v1/playbooks/${playbookId}/steps`);
    return response.data;
  },
  createPlaybookStep: async (playbookId: string, step: { action_type: string; description?: string; command_template?: string }) => {
    const response = await apiClient.post(`/api/v1/playbooks/${playbookId}/steps`, step);
    return response.data;
  },
  updatePlaybookStep: async (playbookId: string, stepId: string, step: { action_type: string; description?: string; command_template?: string }) => {
    const response = await apiClient.put(`/api/v1/playbooks/${playbookId}/steps/${stepId}`, step);
    return response.data;
  },
  deletePlaybookStep: async (playbookId: string, stepId: string) => {
    await apiClient.delete(`/api/v1/playbooks/${playbookId}/steps/${stepId}`);
  },
};

// Rules API
export const rulesApi = {
  getRules: async (params?: { search?: string; sort_by?: string; sort_direction?: string }) => {
    const response = await apiClient.get('/api/v1/rules', { params });
    return response.data;
  },
  getRule: async (id: string) => {
    const response = await apiClient.get(`/api/v1/rules/${id}`);
    return response.data;
  },
  createRule: async (rule: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.post('/api/v1/rules', rule);
    return response.data;
  },
  updateRule: async (id: string, rule: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.put(`/api/v1/rules/${id}`, rule);
    return response.data;
  },
  deleteRule: async (id: string) => {
    await apiClient.delete(`/api/v1/rules/${id}`);
  },
  getRuleStatus: async (id: string) => {
    const response = await apiClient.get(`/api/v1/rules/${id}/status`);
    return response.data;
  },
  updateRuleStatus: async (id: string, status: string, error?: string) => {
    const response = await apiClient.post(`/api/v1/rules/${id}/status`, { status, error });
    return response.data;
  },
};
