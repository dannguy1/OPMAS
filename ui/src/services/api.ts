import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';
import { User, Finding, Action, DashboardStats, RecentActivity } from '../types';

// API configuration
const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://192.168.10.8:8000') + '/api/v1';
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
      '/auth/login',
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
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  },
  logout: async () => {
    const response = await apiClient.post('/auth/logout');
    return response.data;
  },
};

// Dashboard API
export const dashboardApi = {
  getStats: async () => {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
  getRecentActivity: async () => {
    const response = await apiClient.get<RecentActivity[]>('/dashboard/activity/recent');
    return response.data;
  },
};

// Findings API
export const findingsApi = {
  getFindings: async (params?: { search?: string; severity?: string; status?: string; sort_by?: string; sort_direction?: string }) => {
    const response = await apiClient.get<Finding[]>('/findings', { params });
    return response.data;
  },
  getFinding: async (id: string) => {
    const response = await apiClient.get<Finding>(`/findings/${id}`);
    return response.data;
  },
  createFinding: async (finding: Omit<Finding, 'id' | 'createdAt' | 'updatedAt'>) => {
    const response = await apiClient.post<Finding>('/findings', finding);
    return response.data;
  },
  updateFinding: async (id: string, finding: Partial<Finding>) => {
    const response = await apiClient.put<Finding>(`/findings/${id}`, finding);
    return response.data;
  },
  deleteFinding: async (id: string) => {
    await apiClient.delete(`/findings/${id}`);
  },
};

// Agents API
export const agentsApi = {
  getAgents: async (params?: { search?: string; sort_by?: string; sort_direction?: string }) => {
    const response = await apiClient.get('/agents/', { params });
    return response.data;
  },
  getAgent: async (id: string) => {
    const response = await apiClient.get(`/agents/${id}`);
    return response.data;
  },
  discoverAgents: async () => {
    const response = await apiClient.post('/agents/discover');
    return response.data;
  },
};

// System API
export const systemApi = {
  getStatus: async () => {
    const response = await apiClient.get('/system/status');
    return response.data;
  },
  getConfig: async () => {
    const response = await apiClient.get('/system/config');
    return response.data;
  },
  updateConfig: async (config: any) => {
    const response = await apiClient.put('/system/config', config);
    return response.data;
  },
};

// Actions API
export const actionsApi = {
  getActions: async (params?: { search?: string; sort_by?: string; sort_direction?: string }) => {
    const response = await apiClient.get('/actions', { params });
    return response.data;
  },
  getAction: async (id: string) => {
    const response = await apiClient.get(`/actions/${id}`);
    return response.data;
  },
  createAction: async (action: any) => {
    const response = await apiClient.post('/actions', action);
    return response.data;
  },
  updateAction: async (id: string, action: any) => {
    const response = await apiClient.put(`/actions/${id}`, action);
    return response.data;
  },
  deleteAction: async (id: string) => {
    await apiClient.delete(`/actions/${id}`);
  },
};

// Playbooks API
export const playbooksApi = {
  getPlaybooks: async () => {
    const response = await apiClient.get('/playbooks');
    return response.data;
  },
  getPlaybook: async (id: string) => {
    const response = await apiClient.get(`/playbooks/${id}`);
    return response.data;
  },
  createPlaybook: async (playbook: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.post('/playbooks', playbook);
    return response.data;
  },
  updatePlaybook: async (id: string, playbook: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.put(`/playbooks/${id}`, playbook);
    return response.data;
  },
  deletePlaybook: async (id: string) => {
    await apiClient.delete(`/playbooks/${id}`);
  },
  getPlaybookStatus: async (id: string) => {
    const response = await apiClient.get(`/playbooks/${id}/status`);
    return response.data;
  },
  executePlaybook: async (id: string, metadata?: any) => {
    const response = await apiClient.post(`/playbooks/${id}/execute`, metadata);
    return response.data;
  },
  // Playbook Steps
  getPlaybookSteps: async (playbookId: string) => {
    const response = await apiClient.get(`/playbooks/${playbookId}/steps`);
    return response.data;
  },
  createPlaybookStep: async (playbookId: string, step: { action_type: string; description?: string; command_template?: string }) => {
    const response = await apiClient.post(`/playbooks/${playbookId}/steps`, step);
    return response.data;
  },
  updatePlaybookStep: async (playbookId: string, stepId: string, step: { action_type: string; description?: string; command_template?: string }) => {
    const response = await apiClient.put(`/playbooks/${playbookId}/steps/${stepId}`, step);
    return response.data;
  },
  deletePlaybookStep: async (playbookId: string, stepId: string) => {
    await apiClient.delete(`/playbooks/${playbookId}/steps/${stepId}`);
  },
};

// Rules API
export const rulesApi = {
  getRules: async (params?: { search?: string; sort_by?: string; sort_direction?: string }) => {
    const response = await apiClient.get('/rules', { params });
    return response.data;
  },
  getRule: async (id: string) => {
    const response = await apiClient.get(`/rules/${id}`);
    return response.data;
  },
  createRule: async (rule: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.post('/rules', rule);
    return response.data;
  },
  updateRule: async (id: string, rule: { name: string; agent_type: string; description?: string }) => {
    const response = await apiClient.put(`/rules/${id}`, rule);
    return response.data;
  },
  deleteRule: async (id: string) => {
    await apiClient.delete(`/rules/${id}`);
  },
  getRuleStatus: async (id: string) => {
    const response = await apiClient.get(`/rules/${id}/status`);
    return response.data;
  },
  updateRuleStatus: async (id: string, status: string, error?: string) => {
    const response = await apiClient.post(`/rules/${id}/status`, { status, error });
    return response.data;
  },
};
