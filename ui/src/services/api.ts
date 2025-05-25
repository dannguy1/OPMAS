import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { Agent, AgentRule, Finding, FindingFilter, Configuration } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for authentication
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    const response = await this.api.request<T>(config);
    return response.data;
  }

  // Agent endpoints
  async getAgents(enabled?: boolean): Promise<Agent[]> {
    const params = enabled !== undefined ? { enabled } : {};
    return this.request<Agent[]>({ method: 'GET', url: '/agents', params });
  }

  async getAgent(name: string): Promise<Agent> {
    return this.request<Agent>({ method: 'GET', url: `/agents/${name}` });
  }

  async createAgent(agent: Omit<Agent, 'id' | 'status' | 'created_at' | 'updated_at'>): Promise<Agent> {
    return this.request<Agent>({ method: 'POST', url: '/agents', data: agent });
  }

  async updateAgent(name: string, agent: Partial<Agent>): Promise<Agent> {
    return this.request<Agent>({ method: 'PUT', url: `/agents/${name}`, data: agent });
  }

  async deleteAgent(name: string): Promise<void> {
    return this.request<void>({ method: 'DELETE', url: `/agents/${name}` });
  }

  // Agent Rule endpoints
  async getAgentRules(agentName: string, enabled?: boolean): Promise<AgentRule[]> {
    const params = enabled !== undefined ? { enabled } : {};
    return this.request<AgentRule[]>({ method: 'GET', url: `/agents/${agentName}/rules`, params });
  }

  async createAgentRule(agentName: string, rule: Omit<AgentRule, 'id' | 'agent_id' | 'created_at' | 'updated_at'>): Promise<AgentRule> {
    return this.request<AgentRule>({ method: 'POST', url: `/agents/${agentName}/rules`, data: rule });
  }

  async updateAgentRule(agentName: string, ruleName: string, rule: Partial<AgentRule>): Promise<AgentRule> {
    return this.request<AgentRule>({ method: 'PUT', url: `/agents/${agentName}/rules/${ruleName}`, data: rule });
  }

  async deleteAgentRule(agentName: string, ruleName: string): Promise<void> {
    return this.request<void>({ method: 'DELETE', url: `/agents/${agentName}/rules/${ruleName}` });
  }

  // Finding endpoints
  async getFindings(filter: FindingFilter): Promise<Finding[]> {
    return this.request<Finding[]>({ method: 'GET', url: '/findings', params: filter });
  }

  async getFinding(id: number): Promise<Finding> {
    return this.request<Finding>({ method: 'GET', url: `/findings/${id}` });
  }

  async deleteFinding(id: number): Promise<void> {
    return this.request<void>({ method: 'DELETE', url: `/findings/${id}` });
  }

  // Configuration endpoints
  async getConfigurations(): Promise<Configuration[]> {
    return this.request<Configuration[]>({ method: 'GET', url: '/config' });
  }

  async getConfiguration(id: number): Promise<Configuration> {
    return this.request<Configuration>({ method: 'GET', url: `/config/${id}` });
  }

  async createConfiguration(config: Omit<Configuration, 'id' | 'created_at' | 'updated_at'>): Promise<Configuration> {
    return this.request<Configuration>({ method: 'POST', url: '/config', data: config });
  }

  async updateConfiguration(id: number, config: Partial<Configuration>): Promise<Configuration> {
    return this.request<Configuration>({ method: 'PUT', url: `/config/${id}`, data: config });
  }

  async deleteConfiguration(id: number): Promise<void> {
    return this.request<void>({ method: 'DELETE', url: `/config/${id}` });
  }

  // Health check
  async checkHealth(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>({ method: 'GET', url: '/health' });
  }
}

export const apiService = new ApiService();
export default apiService;
