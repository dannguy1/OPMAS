import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom'; // For linking to steps page
import apiClient from '../api/apiClient';
import toast from 'react-hot-toast'; // Import toast
import AddPlaybookModal from '../components/AddPlaybookModal'; // Import Add modal
import EditPlaybookModal from '../components/EditPlaybookModal'; // Import Edit modal

// --- Interfaces matching API response ---
// Keep existing interfaces: PlaybookStep, Playbook, PlaybooksApiResponse
// Add export to Playbook interface so EditPlaybookModal can use it
export interface PlaybookStep {
  step_id: number;
  step_order: number;
  action_type: string;
  command_template?: string;
  description?: string;
}

export interface Playbook {
  playbook_id: number;
  finding_type: string;
  name: string;
  description?: string;
  steps: PlaybookStep[];
}

interface PlaybooksApiResponse {
    playbooks: Playbook[];
    total: number;
    limit: number;
    offset: number;
}
// ----------------------------------------

const PlaybooksPage: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  // State for modals
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [playbookToEdit, setPlaybookToEdit] = useState<Playbook | null>(null);
  // TODO: Add state for pagination

  const fetchPlaybooks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PlaybooksApiResponse>(
          '/playbooks',
          { params: { limit: 50, offset: 0 } } // Fetch initial page
      );
      setPlaybooks(response.data.playbooks || []);
      // TODO: Set pagination state
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load playbooks. Is the Management API running?';
      console.error("Failed to fetch playbooks:", err);
      setError(errorMsg);
      toast.error(errorMsg);
      setPlaybooks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlaybooks(); // Fetch on initial load
  }, []);

  // --- Modal Trigger Functions ---
  const openAddModal = () => {
    setError(null); // Clear page-level errors when opening modal
    setIsAddModalOpen(true);
  };

  const openEditModal = (playbook: Playbook) => {
    setError(null); // Clear page-level errors when opening modal
    setPlaybookToEdit(playbook);
    setIsEditModalOpen(true);
  };

  // --- Modal Submit Handlers ---
  const handleAddSubmit = async (newPlaybookData: { name: string; finding_type: string; description?: string }) => {
    // setLoading(true); // Optional: Indicate loading on the page, though modal has its own indicator
    setError(null);
    try {
      const response = await apiClient.post<Playbook>('/playbooks', newPlaybookData);
      const createdPlaybook = response.data;
      setPlaybooks(currentPlaybooks => [createdPlaybook, ...currentPlaybooks]);
      toast.success(`Playbook '${createdPlaybook.name}' added successfully.`);
      setIsAddModalOpen(false); // Close modal on success
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add playbook.';
      console.error("Failed to add playbook:", err);
      toast.error(errorMsg);
      // Throw error so modal can display it
      throw new Error(errorMsg);
    } finally {
      // setLoading(false);
    }
  };

  const handleEditSubmit = async (playbookId: string, updatedPlaybookData: { name: string; finding_type: string; description?: string }) => {
    setError(null);
    try {
      const response = await apiClient.put<Playbook>(`/playbooks/${Number(playbookId)}`, updatedPlaybookData);
      const updatedPlaybook = response.data;
      setPlaybooks(currentPlaybooks =>
          currentPlaybooks.map(pb =>
              pb.playbook_id === updatedPlaybook.playbook_id ? updatedPlaybook : pb
          )
      );
      toast.success(`Playbook '${updatedPlaybook.name}' updated successfully.`);
      setIsEditModalOpen(false); // Close modal on success
      setPlaybookToEdit(null); // Clear the editing state
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || `Failed to update playbook ${playbookId}.`;
      console.error(`Failed to update playbook ${playbookId}:`, err);
      toast.error(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const handleDeletePlaybook = async (playbookId: number) => {
     if (window.confirm(`Are you sure you want to delete playbook ${playbookId}? This cannot be undone.`)) {
         try {
            setError(null); // Clear previous errors
            await apiClient.delete(`/playbooks/${playbookId}`);
            console.info(`Successfully deleted playbook ${playbookId}`);
            setPlaybooks(currentPlaybooks =>
                currentPlaybooks.filter(pb => pb.playbook_id !== playbookId)
            );
            toast.success(`Playbook ${playbookId} deleted successfully.`);
         } catch (err: any) {
             const errorMsg = err.response?.data?.detail || `Failed to delete playbook ${playbookId}.`;
             console.error(`Failed to delete playbook ${playbookId}:`, err);
             setError(errorMsg);
             toast.error(errorMsg);
         }
     }
  };

  return (
    // Apply card style wrapper
    <div className="bg-white p-6 rounded-lg shadow-md">

      {/* Card Header */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">Playbook Management</h1>
        {/* Update button to open modal */}
        <button
            onClick={openAddModal}
            className="px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow disabled:opacity-50"
            disabled={loading} // Keep disabled while page is initially loading
         >
            Add Playbook
         </button>
      </div>

      {/* Loading/Error Messages (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading playbooks...</p>}
      {/* Display page-level error only if not related to modals */}
      {error && !isAddModalOpen && !isEditModalOpen && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}

      {/* Table Section (inside card body) */}
      {!loading && (
        <div className="overflow-x-auto">
           {/* Apply consistent table styles */}
           <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
             {/* thead style */}
             <thead className="bg-gray-50">
               <tr>
                 {/* th styles */}
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Playbook Name</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Triggering Finding Type</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Steps</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Description</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
               </tr>
             </thead>
             {/* tbody style */}
             <tbody className="bg-white divide-y divide-gray-200">
               {playbooks.length > 0 ? (
                 playbooks.map((playbook) => (
                   // tr style
                   <tr key={playbook.playbook_id}>
                     {/* td styles */}
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-blue-600 hover:underline border-r border-gray-200">
                        <Link to={`/playbooks/${playbook.playbook_id}/steps`}>{playbook.name}</Link>
                     </td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 border-r border-gray-200">{playbook.finding_type}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 border-r border-gray-200 text-center">{playbook.steps.length}</td>
                     <td className="px-4 py-3 text-sm text-gray-500 border-r border-gray-200">{playbook.description || 'N/A'}</td>
                     {/* Use outline buttons for actions */}
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1">
                        {/* Update Edit button to open modal */}
                        <button
                           onClick={() => openEditModal(playbook)}
                           className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150"
                           title="Edit Playbook Metadata"
                        >
                           Edit
                        </button>
                        {/* Delete Button - btn-outline-danger btn-sm */}
                        <button
                           onClick={() => handleDeletePlaybook(playbook.playbook_id)}
                           className="px-2 py-1 text-xs border border-red-500 bg-white text-red-600 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150"
                           title="Delete Playbook"
                        >
                           Delete
                        </button>
                     </td>
                   </tr>
                 ))
               ) : (
                 <tr>
                   {/* Adjusted colspan */}
                   <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">No playbooks found.</td>
                 </tr>
               )}
             </tbody>
           </table>
        </div>
      )}

      {/* Render Modals */}
      <AddPlaybookModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSubmit={handleAddSubmit}
      />
      <EditPlaybookModal
        isOpen={isEditModalOpen}
        onClose={() => { setIsEditModalOpen(false); setPlaybookToEdit(null); }}
        onSubmit={handleEditSubmit}
        playbook={playbookToEdit}
      />

    </div> // End card wrapper
  );
};

export default PlaybooksPage;
