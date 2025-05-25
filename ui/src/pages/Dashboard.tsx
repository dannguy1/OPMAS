import React from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import {
  DocumentMagnifyingGlassIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  BookOpenIcon,
} from '@heroicons/react/24/outline';

const stats = [
  { name: 'Total Findings', value: '0', icon: DocumentMagnifyingGlassIcon },
  { name: 'Pending Actions', value: '0', icon: ClipboardDocumentListIcon },
  { name: 'Active Agents', value: '0', icon: UserGroupIcon },
  { name: 'Active Playbooks', value: '0', icon: BookOpenIcon },
];

export const Dashboard: React.FC = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/api/v1/dashboard/stats').then(res => res.data)
  });

  const { data: recentActivity, isLoading: recentActivityLoading } = useQuery({
    queryKey: ['recentActivity'],
    queryFn: () => api.get('/api/v1/dashboard/activity/recent'),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {/* Stats cards will go here */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {/* Icon */}
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Findings
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats?.totalFindings || 0}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-8">
        <h3 className="text-lg font-medium leading-6 text-gray-900">
          Recent Activity
        </h3>
        <div className="mt-4 overflow-hidden rounded-lg bg-white shadow">
          <div className="p-6">
            {recentActivityLoading ? (
              <div className="text-center text-gray-500">Loading...</div>
            ) : recentActivity?.data?.length === 0 ? (
              <div className="text-center text-gray-500">No recent activity</div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {recentActivity?.data?.map((activity: any) => (
                  <li key={activity.id} className="py-4">
                    <div className="flex space-x-3">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium">
                            {activity.description}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {new Date(activity.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <p className="text-sm text-gray-500">
                          {activity.details}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
