import React, { useState, useEffect } from 'react';
import { AgentRule } from '../pages/AgentRulesPage';

interface AddAgentRuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (ruleData: { name: string; config: AgentRule['config'] }) => Promise<void>;
}

const AddAgentRuleModal: React.FC<AddAgentRuleModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [ruleName, setRuleName] = useState('');
  const [ruleType, setRuleType] = useState('classification');
  const [classificationPatterns, setClassificationPatterns] = useState<string[]>(['']);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setRuleName('');
      setRuleType('classification');
      setClassificationPatterns(['']);
      setError(null);
      setIsSubmitting(false);
    }
  }, [isOpen]);

  const handleAddPattern = () => {
    setClassificationPatterns([...classificationPatterns, '']);
  };

  const handleRemovePattern = (index: number) => {
    setClassificationPatterns(patterns => patterns.filter((_, i) => i !== index));
  };

  const handlePatternChange = (index: number, value: string) => {
    setClassificationPatterns(patterns =>
      patterns.map((pattern, i) => i === index ? value : pattern)
    );
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!ruleName.trim()) {
      setError('Rule Name is required.');
      return;
    }

    const validPatterns = classificationPatterns.filter(p => p.trim() !== '');
    if (validPatterns.length === 0) {
      setError('At least one classification pattern is required.');
      return;
    }

    const ruleConfig: AgentRule['config'] = {
      type: ruleType,
      patterns: validPatterns,
      enabled: true
    };

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: ruleName.trim(),
        config: ruleConfig
      });
    } catch (err: any) {
      const errorMsg = err.message || 'An unexpected error occurred while adding the rule.';
      setError(errorMsg);
      console.error("Add Rule failed:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-[600px] shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium leading-6 text-gray-900 mb-4">Add Classification Rule</h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rule Name
              </label>
              <input
                type="text"
                value={ruleName}
                onChange={(e) => setRuleName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter rule name"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Classification Patterns
              </label>
              <div className="space-y-2">
                {classificationPatterns.map((pattern, index) => (
                  <div key={index} className="flex gap-2">
                    <input
                      type="text"
                      value={pattern}
                      onChange={(e) => handlePatternChange(index, e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter pattern (e.g., wpa_supplicant)"
                    />
                    <button
                      type="button"
                      onClick={() => handleRemovePattern(index)}
                      className="px-2 py-1 text-red-600 hover:text-red-800"
                      title="Remove pattern"
                    >
                      ×
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={handleAddPattern}
                  className="mt-2 px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Add Pattern
                </button>
              </div>
            </div>

            {error && (
              <div className="mb-4 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="mt-5 flex justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {isSubmitting ? 'Adding...' : 'Add Rule'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddAgentRuleModal;
