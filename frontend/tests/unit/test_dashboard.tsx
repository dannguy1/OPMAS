import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Dashboard } from '../components/Dashboard';
import { AgentProvider } from '../contexts/AgentContext';
import { AuthProvider } from '../contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API calls
jest.mock('../api/agents', () => ({
  getAgents: jest.fn().mockResolvedValue([
    {
      id: '1',
      name: 'test-agent-1',
      type: 'system',
      status: 'active',
      config: {
        host: 'localhost',
        port: 8080
      }
    },
    {
      id: '2',
      name: 'test-agent-2',
      type: 'network',
      status: 'inactive',
      config: {
        host: 'localhost',
        port: 8081
      }
    }
  ]),
  getAgentStats: jest.fn().mockResolvedValue({
    total: 2,
    active: 1,
    inactive: 1,
    byType: {
      system: 1,
      network: 1
    }
  }),
  getAgentMetrics: jest.fn().mockResolvedValue({
    cpu: [30, 40, 50, 60, 70],
    memory: [40, 45, 50, 55, 60],
    network: [20, 25, 30, 35, 40],
    timestamps: ['2024-01-01T00:00:00Z', '2024-01-01T00:05:00Z', '2024-01-01T00:10:00Z', '2024-01-01T00:15:00Z', '2024-01-01T00:20:00Z']
  })
}));

describe('Dashboard Component', () => {
  const renderDashboard = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <AgentProvider>
            <Dashboard />
          </AgentProvider>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders dashboard overview', async () => {
    renderDashboard();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    });
    
    // Verify stats are displayed
    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.getByText('Active Agents')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    expect(screen.getByText('Inactive Agents')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders agent type distribution', async () => {
    renderDashboard();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Agent Distribution')).toBeInTheDocument();
    });
    
    // Verify agent types are displayed
    expect(screen.getByText('System')).toBeInTheDocument();
    expect(screen.getByText('Network')).toBeInTheDocument();
  });

  it('renders performance metrics', async () => {
    renderDashboard();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });
    
    // Verify metrics are displayed
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    expect(screen.getByText('Network Traffic')).toBeInTheDocument();
  });

  it('handles time range selection', async () => {
    renderDashboard();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });
    
    // Select different time range
    const timeRangeSelect = screen.getByLabelText(/time range/i);
    fireEvent.change(timeRangeSelect, { target: { value: '1h' } });
    
    // Verify metrics were updated
    await waitFor(() => {
      const { getAgentMetrics } = require('../api/agents');
      expect(getAgentMetrics).toHaveBeenCalledWith('1h');
    });
  });

  it('handles agent selection', async () => {
    renderDashboard();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    });
    
    // Select an agent
    const agentSelect = screen.getByLabelText(/select agent/i);
    fireEvent.change(agentSelect, { target: { value: '1' } });
    
    // Verify metrics were updated for selected agent
    await waitFor(() => {
      const { getAgentMetrics } = require('../api/agents');
      expect(getAgentMetrics).toHaveBeenCalledWith('1h', '1');
    });
  });

  it('handles refresh', async () => {
    renderDashboard();
    
    // Wait for initial data to load
    await waitFor(() => {
      expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    });
    
    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: /refresh/i });
    fireEvent.click(refreshButton);
    
    // Verify data was refreshed
    await waitFor(() => {
      const { getAgents, getAgentStats, getAgentMetrics } = require('../api/agents');
      expect(getAgents).toHaveBeenCalledTimes(2);
      expect(getAgentStats).toHaveBeenCalledTimes(2);
      expect(getAgentMetrics).toHaveBeenCalledTimes(2);
    });
  });

  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getAgents } = require('../api/agents');
    getAgents.mockRejectedValueOnce(new Error('Failed to fetch agents'));
    
    renderDashboard();
    
    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    // Mock slow API response
    const { getAgents } = require('../api/agents');
    getAgents.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderDashboard();
    
    // Verify loading state is displayed
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });
}); 