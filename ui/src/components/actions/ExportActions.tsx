import React from 'react';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { actionsApi } from '../../services/api';
import toast from 'react-hot-toast';

interface ExportActionsProps {
  filters?: {
    search?: string;
    priority?: string;
    status?: string;
    sortBy?: string;
    sortDirection?: 'asc' | 'desc';
  };
}

export const ExportActions: React.FC<ExportActionsProps> = ({ filters = {} }) => {
  const { data: actions, isLoading } = useQuery({
    queryKey: ['actions', filters],
    queryFn: () => actionsApi.get('/actions', {
      params: {
        search: filters.search || undefined,
        priority: filters.priority || undefined,
        status: filters.status || undefined,
        sort_by: filters.sortBy,
        sort_direction: filters.sortDirection
      }
    }).then(res => res.data)
  });

  const handleExport = () => {
    if (!actions?.data) {
      toast.error('No actions to export');
      return;
    }

    // Convert actions to CSV format
    const headers = [
      'Title',
      'Description',
      'Priority',
      'Status',
      'Due Date',
      'Assigned To',
      'Finding Title',
      'Created At',
      'Updated At',
      'Completion Notes',
      'Completed At',
    ];

    const csvRows = [
      headers.join(','),
      ...actions.data.map((action: any) => [
        `"${action.title.replace(/"/g, '""')}"`,
        `"${action.description.replace(/"/g, '""')}"`,
        action.priority,
        action.status,
        new Date(action.dueDate).toISOString(),
        `"${action.assignedTo.replace(/"/g, '""')}"`,
        `"${action.findingTitle.replace(/"/g, '""')}"`,
        new Date(action.createdAt).toISOString(),
        new Date(action.updatedAt).toISOString(),
        `"${(action.completionNotes || '').replace(/"/g, '""')}"`,
        action.completedAt ? new Date(action.completedAt).toISOString() : '',
      ].join(',')),
    ];

    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `actions-export-${new Date().toISOString()}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <button
      onClick={handleExport}
      disabled={isLoading}
      className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
    >
      <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
      Export Actions
    </button>
  );
};
