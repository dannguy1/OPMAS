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
    element: <AuthProvider />,
    children: [
      {
        path: 'login',
        element: <Login />,
      },
      {
        path: '',
        element: (
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        ),
        children: [
          {
            index: true,
            element: <Dashboard />,
          },
          {
            path: 'findings',
            element: <Findings />,
          },
          {
            path: 'actions',
            element: <Actions />,
          },
        ],
      },
    ],
  },
]);

export { router }; 