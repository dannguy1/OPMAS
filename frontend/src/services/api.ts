import axios from 'axios';
import { Agent, AgentRule, Finding, FindingFilter } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Agent endpoints
export const getAgents = async (enabled?: boolean): Promise<Agent[]> => {
  const params = enabled !== undefined ? { enabled } : {};
  const response = await api.get('/agents', { params });
  return response.data;
};

export const getAgent = async (name: string): Promise<Agent> => {
  const response = await api.get(`/agents/${name}`);
  return response.data;
};

export const createAgent = async (agent: Omit<Agent, 'id' | 'status' | 'created_at' | 'updated_at'>): Promise<Agent> => {
  const response = await api.post('/agents', agent);
  return response.data;
};

export const updateAgent = async (name: string, agent: Partial<Agent>): Promise<Agent> => {
  const response = await api.put(`/agents/${name}`, agent);
  return response.data;
};

export const deleteAgent = async (name: string): Promise<void> => {
  await api.delete(`/agents/${name}`);
};

// Agent Rule endpoints
export const getAgentRules = async (agentName: string, enabled?: boolean): Promise<AgentRule[]> => {
  const params = enabled !== undefined ? { enabled } : {};
  const response = await api.get(`/agents/${agentName}/rules`, { params });
  return response.data;
};

export const createAgentRule = async (agentName: string, rule: Omit<AgentRule, 'id' | 'agent_id' | 'created_at' | 'updated_at'>): Promise<AgentRule> => {
  const response = await api.post(`/agents/${agentName}/rules`, rule);
  return response.data;
};

export const updateAgentRule = async (agentName: string, ruleName: string, rule: Partial<AgentRule>): Promise<AgentRule> => {
  const response = await api.put(`/agents/${agentName}/rules/${ruleName}`, rule);
  return response.data;
};

export const deleteAgentRule = async (agentName: string, ruleName: string): Promise<void> => {
  await api.delete(`/agents/${agentName}/rules/${ruleName}`);
};

// Finding endpoints
export const getFindings = async (filter: FindingFilter): Promise<Finding[]> => {
  const response = await api.get('/findings', { params: filter });
  return response.data;
};

export const getFinding = async (id: number): Promise<Finding> => {
  const response = await api.get(`/findings/${id}`);
  return response.data;
};

export const deleteFinding = async (id: number): Promise<void> => {
  await api.delete(`/findings/${id}`);
};

// Health check
export const checkHealth = async (): Promise<{ status: string; timestamp: string }> => {
  const response = await api.get('/health');
  return response.data;
}; 