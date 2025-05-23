import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AgentList } from '../components/AgentList';
import { AgentProvider } from '../contexts/AgentContext';
import { AuthProvider } from '../contexts/AuthContext';

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
  deleteAgent: jest.fn().mockResolvedValue({}),
  updateAgentStatus: jest.fn().mockResolvedValue({})
}));

describe('AgentList Component', () => {
  const renderComponent = () => {
    return render(
      <AuthProvider>
        <AgentProvider>
          <AgentList />
        </AgentProvider>
      </AuthProvider>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the agent list', async () => {
    renderComponent();
    
    // Wait for agents to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
      expect(screen.getByText('test-agent-2')).toBeInTheDocument();
    });
    
    // Check if agent details are displayed correctly
    expect(screen.getByText('system')).toBeInTheDocument();
    expect(screen.getByText('network')).toBeInTheDocument();
    expect(screen.getByText('active')).toBeInTheDocument();
    expect(screen.getByText('inactive')).toBeInTheDocument();
  });

  it('handles agent deletion', async () => {
    renderComponent();
    
    // Wait for agents to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    });
    
    // Click delete button for first agent
    const deleteButton = screen.getAllByRole('button', { name: /delete/i })[0];
    fireEvent.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    // Verify agent was removed from the list
    await waitFor(() => {
      expect(screen.queryByText('test-agent-1')).not.toBeInTheDocument();
    });
  });

  it('handles agent status toggle', async () => {
    renderComponent();
    
    // Wait for agents to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    });
    
    // Click status toggle for first agent
    const statusToggle = screen.getAllByRole('switch')[0];
    fireEvent.click(statusToggle);
    
    // Verify status was updated
    await waitFor(() => {
      expect(screen.getByText('inactive')).toBeInTheDocument();
    });
  });

  it('handles agent selection', async () => {
    renderComponent();
    
    // Wait for agents to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    });
    
    // Click on first agent
    const agentRow = screen.getByText('test-agent-1').closest('tr');
    fireEvent.click(agentRow);
    
    // Verify agent details are displayed
    expect(screen.getByText('Agent Details')).toBeInTheDocument();
    expect(screen.getByText('localhost')).toBeInTheDocument();
    expect(screen.getByText('8080')).toBeInTheDocument();
  });

  it('handles search functionality', async () => {
    renderComponent();
    
    // Wait for agents to load
    await waitFor(() => {
      expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    });
    
    // Enter search term
    const searchInput = screen.getByPlaceholderText(/search agents/i);
    fireEvent.change(searchInput, { target: { value: 'test-agent-1' } });
    
    // Verify filtering
    expect(screen.getByText('test-agent-1')).toBeInTheDocument();
    expect(screen.queryByText('test-agent-2')).not.toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getAgents } = require('../api/agents');
    getAgents.mockRejectedValueOnce(new Error('Failed to fetch agents'));
    
    renderComponent();
    
    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load agents/i)).toBeInTheDocument();
    });
  });

  it('handles empty state', async () => {
    // Mock empty response
    const { getAgents } = require('../api/agents');
    getAgents.mockResolvedValueOnce([]);
    
    renderComponent();
    
    // Verify empty state message
    await waitFor(() => {
      expect(screen.getByText(/no agents found/i)).toBeInTheDocument();
    });
  });
}); 