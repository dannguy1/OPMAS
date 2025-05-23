import React, { useState, useEffect } from 'react';

interface AddPlaybookStepModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (stepData: { action_type: string; description?: string; command_template?: string }) => Promise<void>; // Make async to handle errors
}

const AddPlaybookStepModal: React.FC<AddPlaybookStepModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [actionType, setActionType] = useState('');
  const [description, setDescription] = useState('');
  const [commandTemplate, setCommandTemplate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Reset form when modal opens
      setActionType('');
      setDescription('');
      setCommandTemplate('');
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!actionType.trim()) {
      setError('Action Type is required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit({ 
        action_type: actionType.trim(), 
        description: description.trim() || undefined,
        command_template: commandTemplate.trim() || undefined
      });
      // Parent component (PlaybookStepsPage) will handle closing on success
    } catch (err: any) {
      const errorMsg = err.message || 'An unexpected error occurred while adding the step.';
      setError(errorMsg);
      console.error("Add Step failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm" 
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg" // Slightly wider for command template
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Add New Playbook Step</h2>
        
        <form onSubmit={handleSubmit}>
          {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
          
          <div className="mb-4">
            <label htmlFor="stepActionType" className="block text-sm font-medium text-gray-700 mb-1">
              Action Type <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="stepActionType"
              value={actionType}
              onChange={(e) => setActionType(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., EXECUTE_COMMAND, SEND_NOTIFICATION"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="stepDescription" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              id="stepDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="Describe what this step does..."
            />
          </div>

           <div className="mb-6">
            <label htmlFor="stepCommandTemplate" className="block text-sm font-medium text-gray-700 mb-1">
              Command Template (Optional)
            </label>
            <textarea
              id="stepCommandTemplate"
              value={commandTemplate}
              onChange={(e) => setCommandTemplate(e.target.value)}
              rows={4} // More rows for command
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm font-mono" // Monospace font
              placeholder="Enter command, use Jinja2 format e.g., aws s3api delete-public-access-block --bucket {{ finding.resource_id }}"
            />
            <p className="text-xs text-gray-500 mt-1">Use Jinja2 syntax to access finding details (e.g., `&lbrace;&lbrace; finding.details.some_field &rbrace;&rbrace;`).</p>
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
              {isSubmitting ? 'Adding Step...' : 'Add Step'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddPlaybookStepModal; 