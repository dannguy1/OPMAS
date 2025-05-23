import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Settings } from '../components/Settings';
import { AuthProvider } from '../contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API calls
jest.mock('../api/settings', () => ({
  getSettings: jest.fn().mockResolvedValue({
    general: {
      theme: 'light',
      language: 'en',
      timezone: 'UTC',
      refreshInterval: 30
    },
    notifications: {
      email: true,
      slack: false,
      webhook: false,
      emailAddress: 'test@example.com',
      slackWebhook: '',
      webhookUrl: ''
    },
    security: {
      sessionTimeout: 30,
      requireMFA: false,
      allowedIPs: ['192.168.1.1'],
      passwordPolicy: {
        minLength: 8,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: true
      }
    }
  }),
  updateSettings: jest.fn().mockResolvedValue({
    general: {
      theme: 'dark',
      language: 'en',
      timezone: 'UTC',
      refreshInterval: 60
    },
    notifications: {
      email: true,
      slack: true,
      webhook: false,
      emailAddress: 'test@example.com',
      slackWebhook: 'https://hooks.slack.com/test',
      webhookUrl: ''
    },
    security: {
      sessionTimeout: 60,
      requireMFA: true,
      allowedIPs: ['192.168.1.1', '192.168.1.2'],
      passwordPolicy: {
        minLength: 12,
        requireUppercase: true,
        requireLowercase: true,
        requireNumbers: true,
        requireSpecialChars: true
      }
    }
  })
}));

describe('Settings Component', () => {
  const renderSettings = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <Settings />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders settings sections', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByText('General Settings')).toBeInTheDocument();
      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
      expect(screen.getByText('Security Settings')).toBeInTheDocument();
    });
  });

  it('handles general settings update', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByLabelText(/theme/i)).toBeInTheDocument();
    });
    
    // Update theme
    fireEvent.change(screen.getByLabelText(/theme/i), {
      target: { value: 'dark' }
    });
    
    // Update refresh interval
    fireEvent.change(screen.getByLabelText(/refresh interval/i), {
      target: { value: '60' }
    });
    
    // Save changes
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify settings were updated
    await waitFor(() => {
      const { updateSettings } = require('../api/settings');
      expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        general: expect.objectContaining({
          theme: 'dark',
          refreshInterval: 60
        })
      }));
    });
  });

  it('handles notification settings update', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByLabelText(/email notifications/i)).toBeInTheDocument();
    });
    
    // Enable Slack notifications
    fireEvent.click(screen.getByLabelText(/slack notifications/i));
    
    // Enter Slack webhook
    fireEvent.change(screen.getByLabelText(/slack webhook/i), {
      target: { value: 'https://hooks.slack.com/test' }
    });
    
    // Save changes
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify settings were updated
    await waitFor(() => {
      const { updateSettings } = require('../api/settings');
      expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        notifications: expect.objectContaining({
          slack: true,
          slackWebhook: 'https://hooks.slack.com/test'
        })
      }));
    });
  });

  it('handles security settings update', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByLabelText(/session timeout/i)).toBeInTheDocument();
    });
    
    // Update session timeout
    fireEvent.change(screen.getByLabelText(/session timeout/i), {
      target: { value: '60' }
    });
    
    // Enable MFA
    fireEvent.click(screen.getByLabelText(/require mfa/i));
    
    // Add allowed IP
    fireEvent.change(screen.getByLabelText(/allowed ips/i), {
      target: { value: '192.168.1.1,192.168.1.2' }
    });
    
    // Update password policy
    fireEvent.change(screen.getByLabelText(/minimum password length/i), {
      target: { value: '12' }
    });
    
    // Save changes
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify settings were updated
    await waitFor(() => {
      const { updateSettings } = require('../api/settings');
      expect(updateSettings).toHaveBeenCalledWith(expect.objectContaining({
        security: expect.objectContaining({
          sessionTimeout: 60,
          requireMFA: true,
          allowedIPs: ['192.168.1.1', '192.168.1.2'],
          passwordPolicy: expect.objectContaining({
            minLength: 12
          })
        })
      }));
    });
  });

  it('validates settings form', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });
    
    // Try to save with invalid email
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'invalid-email' }
    });
    
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    
    // Verify validation message
    expect(screen.getByText(/invalid email address/i)).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getSettings } = require('../api/settings');
    getSettings.mockRejectedValueOnce(new Error('Failed to fetch settings'));
    
    renderSettings();
    
    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load settings/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    // Mock slow API response
    const { getSettings } = require('../api/settings');
    getSettings.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderSettings();
    
    // Verify loading state is displayed
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it('handles settings reset', async () => {
    renderSettings();
    
    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByLabelText(/theme/i)).toBeInTheDocument();
    });
    
    // Make some changes
    fireEvent.change(screen.getByLabelText(/theme/i), {
      target: { value: 'dark' }
    });
    
    // Click reset button
    fireEvent.click(screen.getByRole('button', { name: /reset/i }));
    
    // Verify settings were reset
    await waitFor(() => {
      expect(screen.getByLabelText(/theme/i)).toHaveValue('light');
    });
  });
}); 