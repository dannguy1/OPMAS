import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { QueryProvider } from './providers/QueryProvider';
import { AuthProvider } from './providers/AuthProvider';
import { WebSocketProvider } from './context/WebSocketContext';
import { MainLayout } from './components/layout/MainLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { Login } from './pages/Login';
import { Unauthorized } from './pages/Unauthorized';
import { Dashboard } from './pages/Dashboard';
import { Findings } from './pages/Findings';
import { Actions } from './pages/Actions';

function App() {
  return (
    <QueryProvider>
      <AuthProvider>
        <WebSocketProvider>
          <Router>
            <Toaster position="top-right" />
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <MainLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="findings" element={<Findings />} />
                <Route path="actions" element={<Actions />} />
                <Route path="agents" element={<div>Agents Page</div>} />
                <Route path="playbooks" element={<div>Playbooks Page</div>} />
                <Route path="config" element={<div>Config Page</div>} />
              </Route>
            </Routes>
          </Router>
        </WebSocketProvider>
      </AuthProvider>
    </QueryProvider>
  );
}

export default App;
