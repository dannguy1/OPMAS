import React, { useState, useEffect } from 'react';
import { Playbook } from '../pages/PlaybooksPage';

interface EditPlaybookModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (playbookId: string, playbookData: { name: string; finding_type: string; description?: string }) => Promise<void>;
  playbook: Playbook | null;
}

const EditPlaybookModal: React.FC<EditPlaybookModalProps> = ({ isOpen, onClose, onSubmit, playbook }) => {
  const [name, setName] = useState('');
  const [findingType, setFindingType] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && playbook) {
      setName(playbook.name);
      setFindingType(playbook.finding_type);
      setDescription(playbook.description || '');
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen, playbook]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!playbook) {
      setError('No playbook selected for editing.');
      return;
    }

    if (!name.trim() || !findingType.trim()) {
      setError('Playbook Name and Triggering Finding Type are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(String(playbook.playbook_id), {
        name: name.trim(),
        finding_type: findingType.trim(),
        description: description.trim() || undefined
      });
    } catch (err: any) {
      const errorMsg = err.message || 'An unexpected error occurred.';
      setError(errorMsg);
      console.error("Edit Playbook failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen || !playbook) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Edit Playbook</h2>

        <form onSubmit={handleSubmit}>
          {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

          <div className="mb-4">
            <label htmlFor="playbookName" className="block text-sm font-medium text-gray-700 mb-1">
              Playbook Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="playbookName"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., Remediate S3 Bucket Public Access"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="findingType" className="block text-sm font-medium text-gray-700 mb-1">
              Triggering Finding Type <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="findingType"
              value={findingType}
              onChange={(e) => setFindingType(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="e.g., S3_BUCKET_PUBLIC_READ"
            />
            <p className="text-xs text-gray-500 mt-1">The exact Finding Type string that should trigger this playbook.</p>
          </div>

          <div className="mb-6">
            <label htmlFor="playbookDescription" className="block text-sm font-medium text-gray-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              id="playbookDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              placeholder="Describe the purpose of this playbook..."
            />
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
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditPlaybookModal;
