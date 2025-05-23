import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Notifications } from '../components/Notifications';
import { AuthProvider } from '../contexts/AuthContext';
import { MemoryRouter } from 'react-router-dom';

// Mock the API calls
jest.mock('../api/notifications', () => ({
  getNotifications: jest.fn().mockResolvedValue([
    {
      id: '1',
      type: 'alert',
      message: 'High CPU usage detected',
      severity: 'warning',
      timestamp: '2024-01-01T00:00:00Z',
      read: false
    },
    {
      id: '2',
      type: 'system',
      message: 'System update available',
      severity: 'info',
      timestamp: '2024-01-01T00:05:00Z',
      read: true
    },
    {
      id: '3',
      type: 'security',
      message: 'Failed login attempt',
      severity: 'error',
      timestamp: '2024-01-01T00:10:00Z',
      read: false
    }
  ]),
  markAsRead: jest.fn().mockResolvedValue({}),
  markAllAsRead: jest.fn().mockResolvedValue({}),
  deleteNotification: jest.fn().mockResolvedValue({}),
  clearAllNotifications: jest.fn().mockResolvedValue({})
}));

describe('Notifications Component', () => {
  const renderNotifications = () => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          <Notifications />
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders notifications list', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
      expect(screen.getByText('System update available')).toBeInTheDocument();
      expect(screen.getByText('Failed login attempt')).toBeInTheDocument();
    });
    
    // Verify notification details are displayed
    expect(screen.getByText('warning')).toBeInTheDocument();
    expect(screen.getByText('info')).toBeInTheDocument();
    expect(screen.getByText('error')).toBeInTheDocument();
  });

  it('handles marking notification as read', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Click mark as read button for first notification
    const markAsReadButton = screen.getAllByRole('button', { name: /mark as read/i })[0];
    fireEvent.click(markAsReadButton);
    
    // Verify notification was marked as read
    await waitFor(() => {
      const { markAsRead } = require('../api/notifications');
      expect(markAsRead).toHaveBeenCalledWith('1');
    });
  });

  it('handles marking all notifications as read', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Click mark all as read button
    const markAllAsReadButton = screen.getByRole('button', { name: /mark all as read/i });
    fireEvent.click(markAllAsReadButton);
    
    // Verify all notifications were marked as read
    await waitFor(() => {
      const { markAllAsRead } = require('../api/notifications');
      expect(markAllAsRead).toHaveBeenCalled();
    });
  });

  it('handles notification deletion', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Click delete button for first notification
    const deleteButton = screen.getAllByRole('button', { name: /delete/i })[0];
    fireEvent.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    // Verify notification was deleted
    await waitFor(() => {
      const { deleteNotification } = require('../api/notifications');
      expect(deleteNotification).toHaveBeenCalledWith('1');
    });
  });

  it('handles clearing all notifications', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Click clear all button
    const clearAllButton = screen.getByRole('button', { name: /clear all/i });
    fireEvent.click(clearAllButton);
    
    // Confirm clearing
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    fireEvent.click(confirmButton);
    
    // Verify all notifications were cleared
    await waitFor(() => {
      const { clearAllNotifications } = require('../api/notifications');
      expect(clearAllNotifications).toHaveBeenCalled();
    });
  });

  it('filters notifications by type', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Select alert type filter
    const typeFilter = screen.getByLabelText(/filter by type/i);
    fireEvent.change(typeFilter, { target: { value: 'alert' } });
    
    // Verify only alert notifications are shown
    expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    expect(screen.queryByText('System update available')).not.toBeInTheDocument();
    expect(screen.queryByText('Failed login attempt')).not.toBeInTheDocument();
  });

  it('filters notifications by severity', async () => {
    renderNotifications();
    
    // Wait for notifications to load
    await waitFor(() => {
      expect(screen.getByText('High CPU usage detected')).toBeInTheDocument();
    });
    
    // Select error severity filter
    const severityFilter = screen.getByLabelText(/filter by severity/i);
    fireEvent.change(severityFilter, { target: { value: 'error' } });
    
    // Verify only error notifications are shown
    expect(screen.queryByText('High CPU usage detected')).not.toBeInTheDocument();
    expect(screen.queryByText('System update available')).not.toBeInTheDocument();
    expect(screen.getByText('Failed login attempt')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});
    const { getNotifications } = require('../api/notifications');
    getNotifications.mockRejectedValueOnce(new Error('Failed to fetch notifications'));
    
    renderNotifications();
    
    // Verify error message is displayed
    await waitFor(() => {
      expect(screen.getByText(/failed to load notifications/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    // Mock slow API response
    const { getNotifications } = require('../api/notifications');
    getNotifications.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderNotifications();
    
    // Verify loading state is displayed
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
  });

  it('handles empty state', async () => {
    // Mock empty response
    const { getNotifications } = require('../api/notifications');
    getNotifications.mockResolvedValueOnce([]);
    
    renderNotifications();
    
    // Verify empty state message
    await waitFor(() => {
      expect(screen.getByText(/no notifications/i)).toBeInTheDocument();
    });
  });
}); 