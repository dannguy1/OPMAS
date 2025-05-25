import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import MainLayout from './components/layout/MainLayout';
import DashboardPage from './pages/DashboardPage';
import FindingsPage from './pages/FindingsPage';
import IntendedActionsPage from './pages/IntendedActionsPage';
import CoreConfigPage from './pages/CoreConfigPage';
import AgentsPage from './pages/AgentsPage';
import AgentRulesPage from './pages/AgentRulesPage';
import PlaybooksPage from './pages/PlaybooksPage';
import PlaybookStepsPage from './pages/PlaybookStepsPage';
// Import other pages here as they are created

function App() {
  return (
    <>
      {/* --- Add Toaster component here --- */}
      <Toaster
        position="top-right"
        reverseOrder={false}
        toastOptions={{
          duration: 5000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            style: {
              background: '#4CAF50',
              color: '#fff',
            },
          },
          error: {
            duration: 5000,
            style: {
              background: '#f44336',
              color: '#fff',
            },
          },
        }}
      />
      {/* --------------------------------- */}
      <Routes>
        {/* Route that uses the MainLayout */}
        <Route path="/" element={<MainLayout />}>
          {/* Child routes rendered inside MainLayout's <Outlet /> */}
          <Route index element={<DashboardPage />} /> { /* Default page for "/" */}
          <Route path="findings" element={<FindingsPage />} />
          <Route path="actions" element={<IntendedActionsPage />} /> { /* Route for actions */}
          <Route path="config" element={<CoreConfigPage />} />       { /* Route for core config */}
          <Route path="agents" element={<AgentsPage />} />           { /* Route for agents list */}
          <Route path="agents/:agentId/rules" element={<AgentRulesPage />} /> { /* Route for specific agent rules */}
          <Route path="playbooks" element={<PlaybooksPage />} />        { /* Route for playbooks list */}
          <Route path="playbooks/:playbookId/steps" element={<PlaybookStepsPage />} /> { /* Route for specific playbook steps */}
          {/* Define other routes as children here */}
          {/* Example: <Route path="agents" element={<AgentsPage />} /> */}

          {/* Fallback for unknown paths *within* the layout */}
          <Route path="*" element={<div>Page Not Found Inside Layout</div>} />
        </Route>

        {/* Add other top-level routes here if needed (e.g., for a login page without the main layout) */}
        {/* <Route path="/login" element={<LoginPage />} /> */}

        {/* Fallback for unknown paths *outside* the layout */}
        {/* Optional: You might want a different not-found for routes not matching the layout path */}
        {/* <Route path="*" element={<div>Resource Not Found</div>} /> */}
      </Routes>
    </>
  );
}

export default App;
