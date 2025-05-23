import React, { useState, useEffect } from 'react';
import apiClient from '../../api/apiClient';
import type { Agent } from '../../pages/AgentsPage';
import toast from 'react-hot-toast';

interface EditAgentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAgentUpdated: (updatedAgent: Agent) => void;
  agent: Agent | null;
}

const EditAgentModal: React.FC<EditAgentModalProps> = ({ isOpen, onClose, onAgentUpdated, agent }) => {
  const [name, setName] = useState('');
  const [modulePath, setModulePath] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (agent) {
      setName(agent.name);
      setModulePath(agent.module_path);
      setDescription(agent.description || '');
      setError(null);
    } else {
      setName('');
      setModulePath('');
      setDescription('');
      setError(null);
    }
  }, [agent]);

  const resetFormAndClose = () => {
    setError(null);
    setIsSubmitting(false);
    onClose();
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!agent) return;

    setError(null);
    setIsSubmitting(true);

    if (!name || !modulePath) {
      setError('Name and Module Path are required.');
      setIsSubmitting(false);
      return;
    }

    try {
      const updatedData = {
        name,
        module_path: modulePath,
        description: description || null,
        is_enabled: agent.is_enabled
      };
      
      const response = await apiClient.put<Agent>(`/agents/${agent.agent_id}`, updatedData);
      onAgentUpdated(response.data);
      resetFormAndClose();
      toast.success(`Agent '${response.data.name}' updated successfully.`);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update agent. Please check the details and API status.';
      console.error(`Failed to update agent ${agent.agent_id}:`, err);
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !agent) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="relative bg-white rounded-lg shadow-xl w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center p-4 border-b border-gray-200 rounded-t-lg">
          <h2 className="text-xl font-semibold text-gray-800">Edit Agent: {agent.name} (ID: {agent.agent_id})</h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label htmlFor="editAgentName" className="block text-sm font-medium text-gray-700 mb-1">Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              id="editAgentName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="editModulePath" className="block text-sm font-medium text-gray-700 mb-1">Module Path <span className="text-red-500">*</span></label>
            <input
              type="text"
              id="editModulePath"
              value={modulePath}
              onChange={(e) => setModulePath(e.target.value)}
              placeholder="e.g., opmas.agents.example_agent"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono"
              required
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="editDescription" className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              id="editDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              disabled={isSubmitting}
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm -mt-2 mb-2">{error}</p>
          )}

          <div className="flex items-center justify-end pt-4 border-t border-gray-200 rounded-b space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm border border-gray-300 bg-white text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 transition duration-150 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow disabled:opacity-50"
            >
              {isSubmitting ? 'Updating...' : 'Update Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditAgentModal; 