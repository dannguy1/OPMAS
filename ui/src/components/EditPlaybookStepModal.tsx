import React, { useState, useEffect } from 'react';
import { PlaybookStep } from '../pages/PlaybookStepsPage'; // Import the PlaybookStep type

interface EditPlaybookStepModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (stepId: number, stepData: { action_type: string; description?: string; command_template?: string }) => Promise<void>; // Make async
  stepToEdit: PlaybookStep | null;
}

const EditPlaybookStepModal: React.FC<EditPlaybookStepModalProps> = ({ isOpen, onClose, onSubmit, stepToEdit }) => {
  const [actionType, setActionType] = useState('');
  const [description, setDescription] = useState('');
  const [commandTemplate, setCommandTemplate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && stepToEdit) {
      setActionType(stepToEdit.action_type);
      setDescription(stepToEdit.description || '');
      setCommandTemplate(stepToEdit.command_template || '');
      setError(null);
      setIsSubmitting(false);
    } else if (!isOpen) {
      // Clear form if closed
      setActionType('');
      setDescription('');
      setCommandTemplate('');
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen, stepToEdit]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!stepToEdit) {
      setError('No step selected for editing.');
      return;
    }

    if (!actionType.trim()) {
      setError('Action Type is required.');
      return;
    }
    
    const trimmedDescription = description.trim() || undefined;
    const trimmedCommandTemplate = commandTemplate.trim() || undefined;

    // Check if data actually changed
    if (actionType.trim() === stepToEdit.action_type &&
        trimmedDescription === stepToEdit.description &&
        trimmedCommandTemplate === stepToEdit.command_template) {
      console.info("No changes detected for step, closing modal.");
      onClose();
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(stepToEdit.step_id, { 
        action_type: actionType.trim(), 
        description: trimmedDescription,
        command_template: trimmedCommandTemplate
      });
      // Parent component handles closing on success
    } catch (err: any) {
      const errorMsg = err.message || 'An unexpected error occurred while saving the step.';
      setError(errorMsg);
      console.error("Edit Step failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !stepToEdit) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg" 
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Edit Playbook Step (ID: {stepToEdit.step_id})</h2>
        
        <form onSubmit={handleSubmit}>
          {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
          
          {/* Fields are same as Add modal, just pre-filled */}
          <div className="mb-4">
            <label htmlFor="editStepActionType" className="block text-sm font-medium text-gray-700 mb-1">
              Action Type <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="editStepActionType"
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="editStepDescription" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              id="editStepDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
          </div>

           <div className="mb-6">
            <label htmlFor="editStepCommandTemplate" className="block text-sm font-medium text-gray-700 mb-1">
              Command Template (Optional)
            </label>
            <textarea
              id="editStepCommandTemplate"
              value={commandTemplate}
              onChange={(e) => setCommandTemplate(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono"
            />
             <p className="text-xs text-gray-500 mt-1">Use Jinja2 syntax (e.g., `&lbrace;&lbrace; finding.details.some_field &rbrace;&rbrace;`).</p>
          </div>

          <div className="flex justify-end space-x-3 border-t pt-4">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-gray-400 transition duration-150 text-sm disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 transition duration-150 text-sm shadow disabled:opacity-50"
            >
              {isSubmitting ? 'Saving Step...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditPlaybookStepModal; 