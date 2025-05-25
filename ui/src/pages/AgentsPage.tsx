import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // For linking to rules page
import apiClient from '../api/apiClient';
import AddAgentModal from '../components/agent/AddAgentModal'; // Import the modal component
import EditAgentModal from '../components/agent/EditAgentModal'; // Import the edit modal component
import toast from 'react-hot-toast'; // Import toast

// --- Interfaces matching API response ---
export interface Agent {
  agent_id: number;
  name: string;
  module_path: string;
  description?: string;
  is_enabled: boolean;
}

interface AgentsApiResponse {
    agents: Agent[];
    total: number;
    limit: number;
    offset: number;
}

// Note: Exporting Agent interface so AddAgentModal can use it
interface DiscoveredAgent {
    name: string;
    package_path: string;  // Changed from module_path to package_path
    description?: string;
}
// ---------------------------------------------------------

const AgentsPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // TODO: Add state for pagination
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [discoveredAgents, setDiscoveredAgents] = useState<DiscoveredAgent[]>([]);
  const [discovering, setDiscovering] = useState<boolean>(false);
  const [discoveryError, setDiscoveryError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<AgentsApiResponse>(
            '/agents',
            { params: { limit: 50, offset: 0 } } // Fetch initial page
        );
        setAgents(response.data.agents || []);
        // TODO: Set pagination state
      } catch (err) {
        console.error("Failed to fetch agents:", err);
        setError('Failed to load agents. Is the Management API running?');
        setAgents([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  const handleToggleEnable = async (agentId: number, currentStatus: boolean) => {
    // alert(`Toggling agent ${agentId} from ${currentStatus ? 'enabled' : 'disabled'} (API call not implemented)`);
    // TODO: Implement PUT call to /api/config/agents/{agentId}
    const newStatus = !currentStatus;
    const originalAgents = [...agents]; // Store original state for potential revert on error

    // Optimistically update UI
    setAgents(prevAgents =>
        prevAgents.map(agent =>
            agent.agent_id === agentId ? { ...agent, is_enabled: newStatus } : agent
        )
    );
    setError(null); // Clear previous *inline* errors

    try {
        // API endpoint might need adjustment based on actual API structure
        await apiClient.put(`/agents/${agentId}`, { is_enabled: newStatus });
        // Optional: Add success notification here
        toast.success(`Agent ${agentId} ${newStatus ? 'enabled' : 'disabled'} successfully.`);
    } catch (err: any) {
        const errorMsg = err.response?.data?.detail || `Failed to update agent ${agentId}.`;
        console.error(`Failed to toggle agent ${agentId}:`, err);
        setError(`Failed to update agent ${agentId}. Reverting change.`); // Keep inline error temporarily?
        toast.error(errorMsg); // Show toast notification for the error
        // Revert UI change on error
        setAgents(originalAgents);
        // Optional: Add error notification here
    }
  };

  const handleAddAgent = () => {
    alert(`Adding new agent (UI/API call not implemented)`);
    // TODO: Implement UI (modal/form) and POST call to /api/config/agents
    //setIsAddModalOpen(true);
    // Clear initial data when opening manually
    setIsAddModalOpen(true);
    console.log('handleAddAgent: Setting isAddModalOpen to true');
  };

  // Callback function for the modal to add the new agent to the list
  const handleAgentAdded = (newAgent: Agent) => {
    setAgents(prevAgents => [...prevAgents, newAgent]);
    // Optionally: Could also re-fetch the entire list if needed
    // fetchAgents();
  };

  // --- Discovery Functions ---
  const fetchDiscoveredAgents = async () => {
      setDiscovering(true);
      setDiscoveryError(null);
      setDiscoveredAgents([]);
      try {
          console.log('Fetching discovered agents...');
          const response = await apiClient.get<DiscoveredAgent[]>('/agents/discover');
          console.log('Discovered agents response:', response.data);

          // Filter out already added agents
          const filteredAgents = response.data.filter(discovered =>
              !agents.some(existing => existing.module_path === discovered.package_path)
          );
          console.log('Filtered discovered agents:', filteredAgents);

          setDiscoveredAgents(filteredAgents);
          if (filteredAgents.length === 0) {
              setDiscoveryError(response.data.length === 0
                  ? "No new agent modules found in the filesystem."
                  : "All discovered agents have already been added.");
          }
      } catch (err: any) {
          console.error("Failed to discover agents:", err);
          const errorMsg = err.response?.data?.detail || 'Failed to discover agents. Check API logs.';
          setDiscoveryError(errorMsg);
          setDiscoveredAgents([]);
      } finally {
          setDiscovering(false);
      }
  };

  const handleAddDiscovered = async (agent: DiscoveredAgent) => {
      try {
          console.log('Adding discovered agent:', agent);

          // Ensure all required fields are present
          if (!agent.name || !agent.package_path) {
              throw new Error('Missing required fields from discovered agent');
          }

          const payload = {
              name: agent.name.trim(),
              package_path: agent.package_path.trim(),  // Changed from module_path to package_path to match API model
              description: agent.description?.trim() || null,
              is_enabled: true
          };

          console.log('Sending payload to create agent:', payload);
          const response = await apiClient.post<Agent>('/agents', payload);
          console.log('Create agent response:', response.data);

          handleAgentAdded(response.data);
          toast.success(`Agent '${response.data.name}' added successfully.`);

          // Remove the added agent from discovered list
          setDiscoveredAgents(prev => prev.filter(a => a.package_path !== agent.package_path));

          // Update discovery message if no more agents
          if (discoveredAgents.length <= 1) {
              setDiscoveryError("All discovered agents have been added.");
          }
      } catch (err: any) {
          console.error('Error adding agent:', err);
          console.error('Error response:', err.response?.data);

          let errorMsg = 'Failed to add agent: ';
          if (err.response?.data) {
              if (Array.isArray(err.response.data.detail)) {
                  errorMsg += err.response.data.detail
                      .map((e: any) => e.msg || e.message || JSON.stringify(e))
                      .join(', ');
              } else if (typeof err.response.data.detail === 'string') {
                  errorMsg += err.response.data.detail;
              } else if (typeof err.response.data === 'object') {
                  errorMsg += JSON.stringify(err.response.data);
              } else {
                  errorMsg += 'Unknown error occurred';
              }
          } else if (err.message) {
              errorMsg += err.message;
          }

          console.error('Error message:', errorMsg);
          toast.error(errorMsg);
      }
  };
  // -------------------------

  // Function to open the edit modal
  const handleEditAgent = (agent: Agent) => {
    setEditingAgent(agent);
    setIsEditModalOpen(true);
  };

  // Callback function for the edit modal to update the agent in the list
  const handleAgentUpdated = (updatedAgent: Agent) => {
    setAgents(prevAgents =>
        prevAgents.map(agent =>
            agent.agent_id === updatedAgent.agent_id ? updatedAgent : agent
        )
    );
    // No need to close modal here, it closes itself on success
  };

  const handleDeleteAgent = async (agentId: number) => {
     if (window.confirm(`Are you sure you want to delete agent ${agentId}?`)) {
         alert(`Deleting agent ${agentId} (API call not implemented)`);
         // TODO: Implement DELETE call to /api/config/agents/{agentId}
         // Optimistically remove from UI first?
         // For simplicity, we'll wait for API confirmation before updating UI
         const originalAgents = [...agents];
         setAgents(prevAgents => prevAgents.filter(agent => agent.agent_id !== agentId));
         setError(null); // Clear previous errors

         try {
            await apiClient.delete(`/agents/${agentId}`);
            // Optional: Add success notification
            toast.success(`Agent ${agentId} deleted successfully.`);
         } catch (err: any) {
            const errorMsg = err.response?.data?.detail || `Failed to delete agent ${agentId}.`;
            console.error(`Failed to delete agent ${agentId}:`, err);
            setError(`Failed to delete agent ${agentId}.`); // Keep inline error temporarily?
            toast.error(errorMsg); // Show toast notification
            // Revert UI change on error
            setAgents(originalAgents);
            // Optional: Add error notification
         }
     }
  };

  return (
    // Mimic Bootstrap card: bg-white rounded-lg shadow-md p-6
    <div className="bg-white p-6 rounded-lg shadow-md">

      {/* Mimic Bootstrap card-header: border-b pb-4 mb-4 flex justify-between items-center */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        {/* Title style from card-header */}
        <h1 className="text-xl font-semibold text-gray-800">Agents</h1>
        <div className="flex space-x-3">
          {/* Primary button style from btn btn-primary */}
          <button
            onClick={handleAddAgent}
            className="px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow"
          >
            {/* TODO: Add '+' icon */}
            Add Agent
          </button>
          {/* Secondary button style from btn btn-outline-secondary (more or less) */}
          <button
              onClick={fetchDiscoveredAgents}
              disabled={discovering}
              className="px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow-sm disabled:opacity-50"
          >
              {discovering ? 'Discovering...' : 'Discover New Agents'}
          </button>
        </div>
      </div>

      {/* Loading/Error Messages (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading agents...</p>}
      {error && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}

      {/* Table Section (inside card body) */}
      {!loading && !error && (
        <div className="overflow-x-auto">
           {/* Mimic Bootstrap table table-bordered */}
           <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
             {/* Lighter thead bg, slightly darker text, less bold */}
             <thead className="bg-gray-50">
               <tr>
                 {/* Adjusted th styles */}
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Name</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Enabled</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Module Path</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Description</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
               </tr>
             </thead>
             {/* tbody style - divide-y, bg-white implicitly */}
             <tbody className="bg-white divide-y divide-gray-200">
               {agents.length > 0 ? (
                 agents.map((agent) => (
                   // tr style - no specific background, uses tbody divide
                   <tr key={agent.agent_id}>
                     {/* td styles - padding, border */}
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600 hover:underline border-r border-gray-200">
                        <Link to={`/agents/${agent.agent_id}/rules`}>{agent.name}</Link>
                     </td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm border-r border-gray-200">
                        {/* Mimic Bootstrap badge bg-success/bg-danger */}
                        <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${agent.is_enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                            {agent.is_enabled ? 'Enabled' : 'Disabled'}
                        </span>
                     </td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 border-r border-gray-200 font-mono">{agent.module_path}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border-r border-gray-200">{agent.description || 'N/A'}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1">
                        {/* Strictly mimic btn btn-outline-secondary btn-sm for Edit/Delete */}
                        {/* Enable/Disable Button - Keep distinct color hints but use outline style */}
                        <button
                            title={agent.is_enabled ? 'Disable Agent' : 'Enable Agent'}
                            onClick={() => handleToggleEnable(agent.agent_id, agent.is_enabled)}
                            className={`px-2 py-1 text-xs rounded border transition duration-150 focus:outline-none focus:ring-1 focus:ring-offset-1
                              ${agent.is_enabled
                                ? 'border-yellow-500 bg-white text-yellow-600 hover:bg-yellow-50 focus:ring-yellow-400'
                                : 'border-green-500 bg-white text-green-600 hover:bg-green-50 focus:ring-green-400'
                              }`}
                        >
                           {agent.is_enabled ? 'Disable' : 'Enable'}
                        </button>
                        {/* Edit Button - btn-outline-secondary btn-sm */}
                        <button
                            title="Edit Agent"
                            onClick={() => handleEditAgent(agent)}
                            className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150"
                        >
                            Edit
                        </button>
                        {/* Delete Button - btn-outline-danger btn-sm */}
                        <button
                            title="Delete Agent"
                            onClick={() => handleDeleteAgent(agent.agent_id)}
                            className="px-2 py-1 text-xs border border-red-500 bg-white text-red-600 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150"
                        >
                            Delete
                        </button>
                     </td>
                   </tr>
                 ))
               ) : (
                 <tr>
                   <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                       {loading ? '' : (error ? 'Error loading agents.' : 'No agents found in the database.')}
                   </td>
                 </tr>
               )}
             </tbody>
           </table>
        </div>
      )}

      {/* Discovered Agents Section */}
      {(discovering || discoveredAgents.length > 0 || discoveryError) && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
            <h2 className="text-lg font-semibold mb-2">Discovered Agents</h2>
            {discovering && <p className="text-gray-600">Scanning filesystem...</p>}
            {discoveryError && <p className="text-orange-600 mb-2">{discoveryError}</p>}
            {!discovering && discoveredAgents.length > 0 && (
                <ul className="list-disc pl-5 space-y-1">
                    {discoveredAgents.map((agent, index) => (
                        <li key={`${agent.package_path}-${index}`} className="text-sm">
                            <span className="font-medium font-mono">{agent.name}</span> ({agent.package_path})
                            <button
                                onClick={() => handleAddDiscovered(agent)}
                                className="ml-3 px-2 py-0.5 text-xs border border-green-700 bg-green-600 hover:bg-green-700 text-white rounded focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-green-500 transition duration-150"
                            >
                                Add
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
      )}

      {/* Modals */}
      <AddAgentModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onAgentAdded={handleAgentAdded}
      />
      <EditAgentModal
        isOpen={isEditModalOpen}
        onClose={() => {
            setIsEditModalOpen(false);
            setEditingAgent(null);
        }}
        onAgentUpdated={handleAgentUpdated}
        agent={editingAgent}
      />

    </div> // End of white card container
  );
};

export default AgentsPage;
