import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import apiClient from '../api/apiClient';
import toast from 'react-hot-toast';
import AddPlaybookStepModal from '../components/AddPlaybookStepModal';
import EditPlaybookStepModal from '../components/EditPlaybookStepModal';

// --- Interfaces (Export PlaybookStep) ---
export interface PlaybookStep {
  step_id: number;
  step_order: number;
  action_type: string;
  command_template?: string;
  description?: string;
}

interface Playbook {
  playbook_id: number;
  finding_type: string;
  name: string;
  description?: string;
  steps: PlaybookStep[];
}
// ----------------------------------------

const PlaybookStepsPage: React.FC = () => {
  const { playbookId } = useParams<{ playbookId: string }>(); 
  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddStepModalOpen, setIsAddStepModalOpen] = useState<boolean>(false);
  const [isEditStepModalOpen, setIsEditStepModalOpen] = useState<boolean>(false);
  const [stepToEdit, setStepToEdit] = useState<PlaybookStep | null>(null);

  useEffect(() => {
    if (!playbookId) {
      setError("Playbook ID not found in URL.");
      setLoading(false);
      return;
    }

    const fetchPlaybookDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<Playbook>(`/playbooks/${playbookId}`);
        setPlaybook(response.data);
      } catch (err: any) {
        console.error("Failed to fetch playbook details:", err);
        if (err.response && err.response.status === 404) {
            const errorMsg = `Playbook with ID ${playbookId} not found.`;
            setError(errorMsg);
            toast.error(errorMsg);
        } else {
            const errorMsg = 'Failed to load playbook details. Is the Management API running?';
            setError(errorMsg);
            toast.error(errorMsg);
        }
        setPlaybook(null);
      } finally {
        setLoading(false);
      }
    };

    fetchPlaybookDetails();
  }, [playbookId]);

  const handleDeleteStep = async (stepIdToDelete: number) => {
    if (!playbook) return;

    if (window.confirm(`Are you sure you want to delete step ID ${stepIdToDelete}? This cannot be undone.`)) {
        try {
            setError(null);

            await apiClient.delete(`/playbooks/${playbook.playbook_id}/steps/${stepIdToDelete}`);
            console.info(`Successfully deleted step ${stepIdToDelete} from playbook ${playbook.playbook_id}`);

            setPlaybook(currentPlaybook => {
                if (!currentPlaybook) return null;
                return {
                    ...currentPlaybook,
                    steps: currentPlaybook.steps.filter(step => step.step_id !== stepIdToDelete)
                };
            });
            toast.success(`Step ${stepIdToDelete} deleted successfully.`);

        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || `Failed to delete step ${stepIdToDelete}. Check API logs.`;
            console.error(`Failed to delete step ${stepIdToDelete}:`, err);
            if (err.response && err.response.status === 404) {
                 setError(errorMsg);
                 toast.error(errorMsg);
            } else {
                setError(errorMsg);
                toast.error(errorMsg);
            }
        }
    }
  };

  const openAddStepModal = () => {
    setError(null);
    setIsAddStepModalOpen(true);
  };

  const openEditStepModal = (step: PlaybookStep) => {
    setError(null);
    setStepToEdit(step);
    setIsEditStepModalOpen(true);
  };

  const handleAddStepSubmit = async (newStepData: { action_type: string; description?: string; command_template?: string }) => {
    if (!playbook) return;
    setError(null);
    try {
      const response = await apiClient.post<PlaybookStep>(`/playbooks/${playbook.playbook_id}/steps`, newStepData);
      const createdStep = response.data;

      setPlaybook(currentPlaybook => {
        if (!currentPlaybook) return null;
        return {
          ...currentPlaybook,
          steps: [...currentPlaybook.steps, createdStep].sort((a, b) => a.step_order - b.step_order)
        };
      });
      toast.success(`Step '${createdStep.action_type}' added successfully.`);
      setIsAddStepModalOpen(false);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add step.';
      console.error(`Failed to add step to playbook ${playbook.playbook_id}:`, err);
      toast.error(errorMsg); 
      throw new Error(errorMsg);
    }
  };

  const handleEditStepSubmit = async (stepId: number, updatedStepData: { action_type: string; description?: string; command_template?: string }) => {
    if (!playbook) return;
    setError(null);
    try {
      const response = await apiClient.put<PlaybookStep>(`/playbooks/${playbook.playbook_id}/steps/${stepId}`, updatedStepData);
      const updatedStep = response.data;

      setPlaybook(currentPlaybook => {
        if (!currentPlaybook) return null;
        return {
          ...currentPlaybook,
          steps: currentPlaybook.steps.map(step => 
            step.step_id === updatedStep.step_id ? updatedStep : step
          ).sort((a, b) => a.step_order - b.step_order)
        };
      });
      toast.success(`Step ${updatedStep.step_id} updated successfully.`);
      setIsEditStepModalOpen(false);
      setStepToEdit(null);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || `Failed to update step ${stepId}.`;
      console.error(`Failed to update step ${stepId}:`, err);
      toast.error(errorMsg);
      throw new Error(errorMsg);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <Link to="/playbooks" className="text-sm text-blue-600 hover:underline mb-4 inline-block"> &larr; Back to Playbooks</Link>

      {loading && <p className="text-gray-600 py-4 text-center">Loading playbook details...</p>}
      {error && !isAddStepModalOpen && !isEditStepModalOpen && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}
      
      {!loading && !error && playbook && (
        <>
          <div className="border-b border-gray-200 pb-4 mb-4">
             <h1 className="text-xl font-semibold text-gray-800 mb-1">{playbook.name}</h1>
             <p className="text-sm text-gray-700 mb-1">Trigger: <span className="font-medium text-gray-900">{playbook.finding_type}</span></p>
             <p className="text-sm text-gray-500">{playbook.description || 'No description provided.'}</p>
          </div>
          
          <div className="flex justify-between items-center mb-4">
             <h2 className="text-lg font-medium text-gray-700">Steps</h2>
             <button 
                onClick={openAddStepModal}
                className="px-3 py-1 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 text-sm shadow disabled:opacity-50"
             >
                 Add Step
             </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 w-16">Order</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Action Type</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Description</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Command Template</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {playbook.steps.length > 0 ? (
                  playbook.steps.map((step) => (
                    <tr key={step.step_id}>
                      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border-r border-gray-200 align-top">{step.step_order}</td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 align-top">{step.action_type}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 border-r border-gray-200 align-top">{step.description || 'N/A'}</td>
                      <td className="px-4 py-3 text-sm text-gray-500 border-r border-gray-200 align-top">
                        {step.command_template ? (
                           <pre className="text-xs whitespace-pre-wrap font-mono bg-gray-100 p-2 rounded border border-gray-200">{step.command_template}</pre>
                        ) : (
                           <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1 align-top">
                         <button 
                            onClick={() => openEditStepModal(step)}
                            className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150"
                            title="Edit Step"
                         >
                            Edit
                         </button>
                         <button 
                            onClick={() => handleDeleteStep(step.step_id)}
                            className="px-2 py-1 text-xs border border-red-500 bg-white text-red-600 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150"
                            title="Delete Step"
                         >
                            Delete
                         </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">No steps found for this playbook.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      <AddPlaybookStepModal 
        isOpen={isAddStepModalOpen}
        onClose={() => setIsAddStepModalOpen(false)}
        onSubmit={handleAddStepSubmit}
      />
      <EditPlaybookStepModal
        isOpen={isEditStepModalOpen}
        onClose={() => { setIsEditStepModalOpen(false); setStepToEdit(null); }}
        onSubmit={handleEditStepSubmit}
        stepToEdit={stepToEdit}
      />

    </div>
  );
};

export default PlaybookStepsPage; 