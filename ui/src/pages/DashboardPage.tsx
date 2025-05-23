import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient'; // Import the configured axios instance
import toast from 'react-hot-toast'; // Import toast

// Define an interface for the expected status data structure (adjust as needed)
interface SystemStatus {
  // Example structure - this needs to match what the Management API actually returns
  core_components?: {
    [key: string]: string; // e.g., orchestrator: 'running' | 'stopped' | 'error'
  };
  agents?: {
    [key: string]: string; // e.g., WiFiAgent: 'running' | 'stopped' | 'disabled'
  };
  nats_status?: string;
  db_status?: string;
}

const DashboardPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<'start' | 'stop' | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<SystemStatus>('/status');
      setStatus(response.data);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load system status. Is the Management API running?';
      console.error("Failed to fetch system status:", err);
      setError(errorMsg);
      toast.error(errorMsg);
      setStatus(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleStart = async () => {
    setActionLoading('start');
    try {
      const response = await apiClient.post('/control/start');
      toast.success(response.data?.message || 'Start request accepted. System starting...');
      setTimeout(fetchStatus, 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to send start command.';
      console.error("Failed to start system:", err);
      toast.error(errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStop = async () => {
    setActionLoading('stop');
    try {
      const response = await apiClient.post('/control/stop');
      toast.success(response.data?.message || 'Stop request accepted. System stopping...');
      setTimeout(fetchStatus, 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to send stop command.';
      console.error("Failed to stop system:", err);
      toast.error(errorMsg);
    } finally {
      setActionLoading(null);
    }
  };

  return (
    // Apply card style to the main container for this page
    <div className="bg-white p-6 rounded-lg shadow-md">
      {/* Page Header Section (inside card) - Mimic card-header */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        {/* Title style like reference card-header */}
        <h1 className="text-xl font-semibold text-gray-800">Dashboard</h1>
        <div className="space-x-2">
          {/* Style buttons like btn-outline-secondary btn-sm but with color hints */}
          <button 
            onClick={handleStart}
            disabled={actionLoading === 'start'}
            title="Start OPMAS System"
            className="px-3 py-1 text-sm border border-green-300 bg-white text-green-700 rounded hover:bg-green-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-green-400 transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'start' ? 'Starting...' : 'Start System'}
          </button>
          <button 
            onClick={handleStop}
            disabled={actionLoading === 'stop'}
            title="Stop OPMAS System"
            className="px-3 py-1 text-sm border border-red-300 bg-white text-red-700 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading === 'stop' ? 'Stopping...' : 'Stop System'}
          </button>
        </div>
      </div>

      {/* Loading/Error state (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading system status...</p>}
      {error && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}
      
      {/* Status Sections (inside card body) */}
      {!loading && !error && status && (
        // Use simple divs for sections for now, consider grid later if needed
        <div className="space-y-6 mt-4">
          {/* Section for Core Components */}
          <div>
            <h2 className="text-lg font-semibold mb-2 text-gray-700">Core Components</h2>
            <ul className="list-disc list-inside space-y-1 pl-2 text-sm text-gray-600">
              {status.core_components && Object.entries(status.core_components).map(([name, state]) => (
                <li key={name}>{name}: <span className={`font-medium ${state === 'running' ? 'text-green-700' : 'text-red-700'}`}>{state}</span></li>
              ))}
              {!status.core_components && <li>No core component status available.</li>}
            </ul>
          </div>

          {/* Section for Agents */}
          <div>
            <h2 className="text-lg font-semibold mb-2 text-gray-700">Agents</h2>
            <ul className="list-disc list-inside space-y-1 pl-2 text-sm text-gray-600">
              {status.agents && Object.entries(status.agents).map(([name, state]) => (
                <li key={name}>{name}: <span className={`font-medium ${state === 'running' ? 'text-green-700' : state === 'disabled' ? 'text-yellow-700' : 'text-red-700'}`}>{state}</span></li>
              ))}
               {!status.agents && <li>No agent status available.</li>}
            </ul>
          </div>

          {/* Section for Services */}
          <div>
            <h2 className="text-lg font-semibold mb-2 text-gray-700">Services</h2>
            <ul className="list-disc list-inside space-y-1 pl-2 text-sm text-gray-600">
              <li>NATS: <span className={`font-medium ${status.nats_status === 'connected' ? 'text-green-700' : 'text-red-700'}`}>{status.nats_status || 'Unknown'}</span></li>
              <li>Database: <span className={`font-medium ${status.db_status === 'connected' ? 'text-green-700' : 'text-red-700'}`}>{status.db_status || 'Unknown'}</span></li>
            </ul>
          </div>
        </div>
      )}
      {!loading && !error && !status && (
         <p className="text-gray-600 py-4 text-center">Could not retrieve status information.</p>
      )}
    </div> // End of card container
  );
};

export default DashboardPage; 