import { createBrowserRouter } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { Findings } from './pages/Findings';
import { Actions } from './pages/Actions';
import { Login } from './pages/Login';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <AuthProvider>
        <MainLayout />
      </AuthProvider>
    ),
    children: [
      {
        path: 'login',
        element: <Login />,
      },
      {
        index: true,
        element: (
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        ),
      },
      {
        path: 'findings',
        element: (
          <ProtectedRoute>
            <Findings />
          </ProtectedRoute>
        ),
      },
      {
        path: 'actions',
        element: (
          <ProtectedRoute>
            <Actions />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);

export { router }; 