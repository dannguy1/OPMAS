import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { rulesApi } from '../services/api';
import toast from 'react-hot-toast';
import AddAgentRuleModal from '../components/AddAgentRuleModal';
import EditAgentRuleModal from '../components/EditAgentRuleModal';

// --- Interfaces (Export AgentRule) ---
export interface AgentRule {
  id: string;  // Changed from rule_id: number to id: string (UUID)
  name: string;  // Changed from rule_name to name
  agent_type: string;  // Changed from agent_id to agent_type
  description?: string;
  config: {  // Changed from rule_config to config
    type: string;
    patterns: string[];
    enabled: boolean;
  };
  enabled: boolean;
  created_at: string;
  updated_at: string;
  owner_id?: string;
}

interface AgentRulesApiResponse {
  items: AgentRule[];
  total: number;
  skip: number;
  limit: number;
}

const AgentRulesPage: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const [rules, setRules] = useState<AgentRule[]>([]);
  const [agentName] = useState<string>('Unknown Agent');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddRuleModalOpen, setIsAddRuleModalOpen] = useState<boolean>(false);
  const [isEditRuleModalOpen, setIsEditRuleModalOpen] = useState<boolean>(false);
  const [ruleToEdit, setRuleToEdit] = useState<AgentRule | null>(null);

  const fetchAgentRules = async () => {
    setLoading(true);
    setError(null);
    if (!agentId) {
      setError("Agent ID not found in URL.");
      setLoading(false);
      return;
    }
    try {
      const response = await rulesApi.getRules({
        search: `agent_type:${agentId}`,
        sort_by: 'name',
        sort_direction: 'asc'
      });
      setRules(response.items || []);
    } catch (err: any) {
      console.error(`Failed to fetch rules for agent ${agentId}:`, err);
      let errorMsg: string;
      if (err.response && err.response.status === 404) {
        errorMsg = `No rules found for agent ${agentId}.`;
        setRules([]);
      } else {
        errorMsg = `Failed to load rules for agent ${agentId}. Is the Management API running?`;
        setRules([]);
      }
      if (!errorMsg.startsWith('No rules found')) {
        setError(errorMsg);
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentRules();
  }, [agentId]);

  const openAddRuleModal = () => {
    setError(null);
    setIsAddRuleModalOpen(true);
  };

  const openEditRuleModal = (rule: AgentRule) => {
    setError(null);
    setRuleToEdit(rule);
    setIsEditRuleModalOpen(true);
  };

  const handleAddRuleSubmit = async (newRuleData: { name: string; config: object }) => {
    if (!agentId) return;
    setError(null);
    try {
      const response = await rulesApi.createRule({
        ...newRuleData,
        agent_type: agentId
      });
      const createdRule = response;
      setRules(currentRules => [createdRule, ...currentRules]);
      toast.success(`Rule '${createdRule.name}' added successfully.`);
      setIsAddRuleModalOpen(false);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add rule.';
      console.error("Failed to add rule:", err);
      toast.error(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const handleEditRuleSubmit = async (ruleId: string, updatedRuleData: { name: string; config: object }) => {
    if (!agentId) return;
    setError(null);
    try {
      const response = await rulesApi.updateRule(ruleId, {
        ...updatedRuleData,
        agent_type: agentId
      });
      const updatedRule = response;
      setRules(currentRules =>
        currentRules.map(r => (r.id === updatedRule.id ? updatedRule : r))
      );
      toast.success(`Rule '${updatedRule.name}' updated successfully.`);
      setIsEditRuleModalOpen(false);
      setRuleToEdit(null);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || `Failed to update rule ${ruleId}.`;
      console.error(`Failed to update rule ${ruleId}:`, err);
      toast.error(errorMsg);
      throw new Error(errorMsg);
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    if (!agentId) return;
    if (window.confirm(`Are you sure you want to delete rule ${ruleId}? This cannot be undone.`)) {
      try {
        setError(null);
        await rulesApi.deleteRule(ruleId);
        console.info(`Successfully deleted rule ${ruleId} for agent ${agentId}`);
        setRules(currentRules =>
          currentRules.filter(r => r.id !== ruleId)
        );
        toast.success(`Rule ${ruleId} deleted successfully.`);
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || `Failed to delete rule ${ruleId}.`;
        console.error(`Failed to delete rule ${ruleId}:`, err);
        setError(errorMsg);
        toast.error(errorMsg);
      }
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <Link to="/agents" className="text-sm text-blue-600 hover:underline mb-4 inline-block"> &larr; Back to Agents</Link>

      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">Rules for Agent {agentName === 'Unknown Agent' ? agentId : agentName}</h1>
        <button
          onClick={openAddRuleModal}
          className="px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow disabled:opacity-50"
          disabled={!agentId}
        >
          Add Rule
        </button>
      </div>

      {loading && <p className="text-gray-600 py-4 text-center">Loading rules...</p>}
      {error && !isAddRuleModalOpen && !isEditRuleModalOpen && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}

      {!loading && (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Rule Name</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Configuration</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rules.length > 0 ? (
                rules.map((rule) => (
                  <tr key={rule.id}>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 align-top">{rule.name}</td>
                    <td className="px-4 py-3 text-sm text-gray-500 border-r border-gray-200 align-top">
                      <pre className="text-xs whitespace-pre-wrap font-mono bg-gray-100 p-2 rounded border border-gray-200">{JSON.stringify(rule.config, null, 2)}</pre>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1 align-top">
                      <button
                        onClick={() => openEditRuleModal(rule)}
                        className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150"
                        title="Edit Rule"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="px-2 py-1 text-xs border border-red-500 bg-white text-red-600 rounded hover:bg-red-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150"
                        title="Delete Rule"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={3} className="px-4 py-3 text-sm text-gray-500 text-center">
                    No rules found for this agent.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {isAddRuleModalOpen && (
        <AddAgentRuleModal
          isOpen={isAddRuleModalOpen}
          onClose={() => setIsAddRuleModalOpen(false)}
          onSubmit={handleAddRuleSubmit}
        />
      )}

      {isEditRuleModalOpen && ruleToEdit && (
        <EditAgentRuleModal
          isOpen={isEditRuleModalOpen}
          onClose={() => {
            setIsEditRuleModalOpen(false);
            setRuleToEdit(null);
          }}
          onSubmit={(data) => handleEditRuleSubmit(ruleToEdit.id, data)}
          rule={ruleToEdit}
        />
      )}
    </div>
  );
};

export default AgentRulesPage;
