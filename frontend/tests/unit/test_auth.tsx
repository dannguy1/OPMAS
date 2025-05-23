import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../contexts/AuthContext';
import { LoginForm } from '../components/LoginForm';
import { MemoryRouter } from 'react-router-dom';

// Mock the API calls
jest.mock('../api/auth', () => ({
  login: jest.fn().mockResolvedValue({
    access_token: 'test-token',
    user: {
      id: '1',
      email: 'test@example.com',
      role: 'admin'
    }
  }),
  logout: jest.fn().mockResolvedValue({}),
  getCurrentUser: jest.fn().mockResolvedValue({
    id: '1',
    email: 'test@example.com',
    role: 'admin'
  })
}));

// Test component that uses auth context
const TestComponent = () => {
  const { user, isAuthenticated, logout } = useAuth();
  
  return (
    <div>
      {isAuthenticated ? (
        <>
          <p>Welcome, {user?.email}</p>
          <button onClick={logout}>Logout</button>
        </>
      ) : (
        <p>Not authenticated</p>
      )}
    </div>
  );
};

describe('Authentication', () => {
  const renderWithAuth = (component) => {
    return render(
      <MemoryRouter>
        <AuthProvider>
          {component}
        </AuthProvider>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('LoginForm Component', () => {
    it('handles successful login', async () => {
      renderWithAuth(<LoginForm />);
      
      // Fill in login form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'password123' }
      });
      
      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /login/i }));
      
      // Verify loading state
      expect(screen.getByText(/logging in/i)).toBeInTheDocument();
      
      // Verify successful login
      await waitFor(() => {
        expect(screen.queryByText(/logging in/i)).not.toBeInTheDocument();
      });
      
      // Verify token was stored
      expect(localStorage.getItem('token')).toBe('test-token');
    });

    it('handles login error', async () => {
      // Mock login error
      const { login } = require('../api/auth');
      login.mockRejectedValueOnce(new Error('Invalid credentials'));
      
      renderWithAuth(<LoginForm />);
      
      // Fill in login form
      fireEvent.change(screen.getByLabelText(/email/i), {
        target: { value: 'test@example.com' }
      });
      fireEvent.change(screen.getByLabelText(/password/i), {
        target: { value: 'wrong-password' }
      });
      
      // Submit form
      fireEvent.click(screen.getByRole('button', { name: /login/i }));
      
      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });
    });

    it('validates form inputs', () => {
      renderWithAuth(<LoginForm />);
      
      // Submit empty form
      fireEvent.click(screen.getByRole('button', { name: /login/i }));
      
      // Verify validation messages
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  describe('AuthContext', () => {
    it('provides authentication state', async () => {
      renderWithAuth(<TestComponent />);
      
      // Initially not authenticated
      expect(screen.getByText(/not authenticated/i)).toBeInTheDocument();
      
      // Login
      const { login } = require('../api/auth');
      await login('test@example.com', 'password123');
      
      // Verify authenticated state
      await waitFor(() => {
        expect(screen.getByText(/welcome, test@example.com/i)).toBeInTheDocument();
      });
    });

    it('handles logout', async () => {
      // Set initial auth state
      localStorage.setItem('token', 'test-token');
      
      renderWithAuth(<TestComponent />);
      
      // Verify authenticated state
      await waitFor(() => {
        expect(screen.getByText(/welcome, test@example.com/i)).toBeInTheDocument();
      });
      
      // Logout
      fireEvent.click(screen.getByRole('button', { name: /logout/i }));
      
      // Verify logged out state
      await waitFor(() => {
        expect(screen.getByText(/not authenticated/i)).toBeInTheDocument();
      });
      
      // Verify token was removed
      expect(localStorage.getItem('token')).toBeNull();
    });

    it('handles token expiration', async () => {
      // Set initial auth state
      localStorage.setItem('token', 'expired-token');
      
      // Mock getCurrentUser to fail
      const { getCurrentUser } = require('../api/auth');
      getCurrentUser.mockRejectedValueOnce(new Error('Token expired'));
      
      renderWithAuth(<TestComponent />);
      
      // Verify not authenticated
      await waitFor(() => {
        expect(screen.getByText(/not authenticated/i)).toBeInTheDocument();
      });
      
      // Verify token was removed
      expect(localStorage.getItem('token')).toBeNull();
    });

    it('handles role-based access', async () => {
      // Mock user with specific role
      const { getCurrentUser } = require('../api/auth');
      getCurrentUser.mockResolvedValueOnce({
        id: '1',
        email: 'user@example.com',
        role: 'user'
      });
      
      localStorage.setItem('token', 'test-token');
      
      renderWithAuth(<TestComponent />);
      
      // Verify user role is accessible
      await waitFor(() => {
        expect(screen.getByText(/welcome, user@example.com/i)).toBeInTheDocument();
      });
    });
  });
}); 