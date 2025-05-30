import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { agentsApi } from '../services/api';
import {
  MagnifyingGlassIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';

interface Agent {
  id: string;
  name: string;
  agent_type: string;
  status: string;
  description: string;
  created_at: string;
  updated_at: string;
  last_seen: string;
  hostname: string;
  ip_address: string;
  port: number;
  enabled: boolean;
}

interface AgentsResponse {
  agents: Agent[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const Agents: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof Agent>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [discovering, setDiscovering] = useState(false);

  const { data: agentsData, isLoading } = useQuery<AgentsResponse>({
    queryKey: ['agents', searchTerm, sortField, sortDirection],
    queryFn: () => agentsApi.getAgents({
      search: searchTerm,
      sort_by: sortField === 'last_seen' ? 'last_seen' :
              sortField === 'created_at' ? 'created_at' :
              sortField === 'updated_at' ? 'updated_at' : sortField,
      sort_direction: sortDirection,
    })
  });

  const handleSort = (field: keyof Agent) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const SortIcon: React.FC<{ field: keyof Agent }> = ({ field }) => {
    if (field !== sortField) return null;
    return sortDirection === 'asc' ? (
      <ArrowUpIcon className="h-4 w-4" />
    ) : (
      <ArrowDownIcon className="h-4 w-4" />
    );
  };

  const statusColors = {
    online: 'bg-green-100 text-green-800',
    offline: 'bg-red-100 text-red-800',
    error: 'bg-yellow-100 text-yellow-800',
    unknown: 'bg-gray-100 text-gray-800',
    maintenance: 'bg-blue-100 text-blue-800',
    active: 'bg-green-100 text-green-800',
  };

  const fetchDiscoveredAgents = async () => {
    setDiscovering(true);
    try {
      await agentsApi.discoverAgents();
    } catch (error) {
      console.error('Error discovering new agents:', error);
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-gray-900">Agents</h2>
        <p className="mt-1 text-sm text-gray-500">
          View and manage security agents
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 items-center gap-4">
          <div className="relative flex-1">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
            </div>
            <input
              type="text"
              className="block w-full rounded-md border-0 py-1.5 pl-10 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <button
          onClick={fetchDiscoveredAgents}
          disabled={discovering}
          className="px-4 py-2 border border-transparent bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 shadow disabled:opacity-50"
        >
          {discovering ? 'Discovering...' : 'Discover New Agents'}
        </button>
      </div>

      {/* Table */}
      <div className="mt-4 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      scope="col"
                      className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6 cursor-pointer"
                      onClick={() => handleSort('name')}
                    >
                      <div className="flex items-center gap-1">
                        Name
                        <SortIcon field="name" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => handleSort('agent_type')}
                    >
                      <div className="flex items-center gap-1">
                        Type
                        <SortIcon field="agent_type" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => handleSort('status')}
                    >
                      <div className="flex items-center gap-1">
                        Status
                        <SortIcon field="status" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => handleSort('last_seen')}
                    >
                      <div className="flex items-center gap-1">
                        Last Seen
                        <SortIcon field="last_seen" />
                      </div>
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      Hostname
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      IP Address
                    </th>
                    <th
                      scope="col"
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900"
                    >
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {isLoading ? (
                    <tr>
                      <td colSpan={7} className="py-4 text-center text-sm text-gray-500">
                        Loading...
                      </td>
                    </tr>
                  ) : !agentsData?.agents || agentsData.agents.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-4 text-center text-sm text-gray-500">
                        No agents found
                      </td>
                    </tr>
                  ) : (
                    agentsData.agents.map((agent) => (
                      <tr key={agent.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                          {agent.name}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {agent.agent_type}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <span
                            className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                              statusColors[agent.status] || statusColors.unknown
                            }`}
                          >
                            {agent.status}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : 'Never'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {agent.hostname}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {agent.ip_address}:{agent.port}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1">
                          <button
                            onClick={() => handleEdit(agent)}
                            className="px-2 py-1 text-xs border border-transparent bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-blue-400 transition duration-150"
                            title="Edit Agent"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDelete(agent.id)}
                            className="px-2 py-1 text-xs border border-transparent bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-red-400 transition duration-150"
                            title="Delete Agent"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
