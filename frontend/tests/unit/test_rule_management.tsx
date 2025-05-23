import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { RuleManagement } from '../components/RuleManagement';
import { AgentProvider } from '../contexts/AgentContext';
import { AuthProvider } from '../contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API calls
jest.mock('../api/rules', () => ({
  getRules: jest.fn().mockResolvedValue([
    {
      id: '1',
      name: 'high-cpu',
      condition: 'cpu_usage > 80',
      action: 'restart_service',
      severity: 'warning',
      enabled: true
    },
    {
      id: '2',
      name: 'low-memory',
      condition: 'memory_usage < 20',
      action: 'alert',
      severity: 'error',
      enabled: false
    }
  ]),
  createRule: jest.fn().mockResolvedValue({
    id: '3',
    name: 'new-rule',
    condition: 'disk_usage > 90',
    action: 'cleanup',
    severity: 'critical',
    enabled: true
  }),
  updateRule: jest.fn().mockResolvedValue({
    id: '1',
    name: 'updated-rule',
    condition: 'cpu_usage > 90',
    action: 'restart_service',
    severity: 'critical',
    enabled: true
  }),
  deleteRule: jest.fn().mockResolvedValue({}),
  toggleRule: jest.fn().mockResolvedValue({
    id: '1',
    enabled: false
  })
}));

describe('RuleManagement Component', () => {
  const renderRuleManagement = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <AgentProvider>
            <RuleManagement />
          </AgentProvider>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders rule list', async () => {
    renderRuleManagement();
    
    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText('high-cpu')).toBeInTheDocument();
      expect(screen.getByText('low-memory')).toBeInTheDocument();
    });
    
    // Verify rule details are displayed
    expect(screen.getByText('cpu_usage > 80')).toBeInTheDocument();
    expect(screen.getByText('memory_usage < 20')).toBeInTheDocument();
    expect(screen.getByText('warning')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  it('handles rule creation', async () => {
    renderRuleManagement();
    
    // Click create rule button
    fireEvent.click(screen.getByRole('button', { name: /create rule/i }));
    
    // Fill in rule form
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: 'new-rule' }
    });
    fireEvent.change(screen.getByLabelText(/condition/i), {
      target: { value: 'disk_usage > 90' }
    });
    fireEvent.change(screen.getByLabelText(/action/i), {
      target: { value: 'cleanup' }
    });
    fireEvent.change(screen.getByLabelText(/severity/i), {
      target: { value: 'critical' }
    });
    
    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify rule was created
    await waitFor(() => {
      expect(screen.getByText('new-rule')).toBeInTheDocument();
      expect(screen.getByText('disk_usage > 90')).toBeInTheDocument();
    });
  });

  it('handles rule update', async () => {
    renderRuleManagement();
    
    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText('high-cpu')).toBeInTheDocument();
    });
    
    // Click edit button for first rule
    const editButton = screen.getAllByRole('button', { name: /edit/i })[0];
    fireEvent.click(editButton);
    
    // Update rule
    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: 'updated-rule' }
    });
    fireEvent.change(screen.getByLabelText(/condition/i), {
      target: { value: 'cpu_usage > 90' }
    });
    fireEvent.change(screen.getByLabelText(/severity/i), {
      target: { value: 'critical' }
    });
    
    // Save changes
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify rule was updated
    await waitFor(() => {
      expect(screen.getByText('updated-rule')).toBeInTheDocument();
      expect(screen.getByText('cpu_usage > 90')).toBeInTheDocument();
      expect(screen.getByText('critical')).toBeInTheDocument();
    });
  });

  it('handles rule deletion', async () => {
    renderRuleManagement();
    
    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText('high-cpu')).toBeInTheDocument();
    });
    
    // Click delete button for first rule
    const deleteButton = screen.getAllByRole('button', { name: /delete/i })[0];
    fireEvent.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    // Verify rule was deleted
    await waitFor(() => {
      expect(screen.queryByText('high-cpu')).not.toBeInTheDocument();
    });
  });

  it('handles rule toggle', async () => {
    renderRuleManagement();
    
    // Wait for rules to load
    await waitFor(() => {
      expect(screen.getByText('high-cpu')).toBeInTheDocument();
    });
    
    // Toggle first rule
    const toggleSwitch = screen.getAllByRole('switch')[0];
    fireEvent.click(toggleSwitch);
    
    // Verify rule was toggled
    await waitFor(() => {
      expect(toggleSwitch).not.toBeChecked();
    });
  });

  it('validates rule form', async () => {
    renderRuleManagement();
    
    // Click create rule button
    fireEvent.click(screen.getByRole('button', { name: /create rule/i }));
    
    // Try to submit empty form
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify validation messages
    expect(screen.getByText(/name is required/i)).toBeInTheDocument();
    expect(screen.getByText(/condition is required/i)).toBeInTheDocument();
    expect(screen.getByText(/action is required/i)).toBeInTheDocument();
    expect(screen.getByText(/severity is required/i)).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getRules } = require('../api/rules');
    getRules.mockRejectedValueOnce(new Error('Failed to fetch rules'));
    
    renderRuleManagement();
    
    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load rules/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    // Mock slow API response
    const { getRules } = require('../api/rules');
    getRules.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderRuleManagement();
    
    // Verify loading state is displayed
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });
}); 