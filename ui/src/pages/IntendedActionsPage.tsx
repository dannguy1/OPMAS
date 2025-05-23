import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import toast from 'react-hot-toast';

// Interface matching ActionBase Pydantic model from API
interface Action {
  action_id: number;
  finding_id: string;
  playbook_step_id?: number;
  timestamp_utc: string; // Keep as string for display
  action_type: string;
  rendered_command_context?: string;
}

// Define the expected response structure from the API
interface ActionsApiResponse {
    actions: Action[];
    total: number;
    limit: number;
    offset: number;
}

// Helper function to format timestamp (same as FindingsPage)
const formatTimestamp = (isoString: string): string => {
    try {
        return new Date(isoString).toLocaleString();
    } catch (e) {
        return isoString; // Return original if parsing fails
    }
};

const IntendedActionsPage: React.FC = () => {
  const [actions, setActions] = useState<Action[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // TODO: Add state for pagination (total, limit, offset)

  useEffect(() => {
    const fetchActions = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch from the correct /actions endpoint
        const response = await apiClient.get<ActionsApiResponse>(
            '/actions', 
            { params: { limit: 50, offset: 0 } } // Add pagination params
        );
        setActions(response.data.actions || []);
        // TODO: Set pagination state (total, limit, offset) from response.data
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || 'Failed to load intended actions. Is the Management API running?';
        console.error("Failed to fetch intended actions:", err);
        setError(errorMsg);
        toast.error(errorMsg);
        setActions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchActions();
  }, []);

  return (
    // Apply card style wrapper
    <div className="bg-white p-6 rounded-lg shadow-md">

      {/* Card Header */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">Intended Actions</h1>
        {/* Placeholder for potential header actions */}
        <div></div>
      </div>

      {/* Loading/Error Messages (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading actions...</p>}
      {error && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}
      
      {/* Table Section (inside card body) */}
      {!loading && !error && (
        <div className="overflow-x-auto">
           {/* Apply consistent table styles */}
           <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
             {/* thead style */}
             <thead className="bg-gray-50">
               <tr>
                 {/* th styles */}
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Timestamp</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Action Type</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Finding ID</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Command/Context</th>
               </tr>
             </thead>
             {/* tbody style */}
             <tbody className="bg-white divide-y divide-gray-200">
               {actions.length > 0 ? (
                 actions.map((action) => (
                   // tr style
                   <tr key={action.action_id}>
                     {/* td styles */}
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 border-r border-gray-200">{formatTimestamp(action.timestamp_utc)}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200">{action.action_type}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 border-r border-gray-200">{action.finding_id}</td>
                     <td className="px-4 py-3 text-sm text-gray-500">
                         <pre className="text-xs whitespace-pre-wrap font-mono">{action.rendered_command_context || 'N/A'}</pre>
                     </td>
                   </tr>
                 ))
               ) : (
                 <tr>
                   <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">No intended actions found.</td>
                 </tr>
               )}
             </tbody>
           </table>
        </div>
      )}
    </div> // End card wrapper
  );
};

export default IntendedActionsPage; 