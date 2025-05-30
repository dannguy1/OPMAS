import React, { useState } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon, PencilIcon, CheckIcon } from '@heroicons/react/24/outline';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { actionsApi } from '../../services/api';
import toast from 'react-hot-toast';

interface Action {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  dueDate: string;
  createdAt: string;
  updatedAt: string;
  findingId: string;
  findingTitle: string;
  assignedTo: string;
  completionNotes?: string;
  completedAt?: string;
}

interface ActionDetailsModalProps {
  action: Action | null;
  isOpen: boolean;
  onClose: () => void;
}

const priorityColors = {
  high: 'bg-red-100 text-red-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-green-100 text-green-800',
};

const statusColors = {
  pending: 'bg-gray-100 text-gray-800',
  in_progress: 'bg-blue-100 text-blue-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
] as const;

export const ActionDetailsModal: React.FC<ActionDetailsModalProps> = ({
  action,
  isOpen,
  onClose,
}) => {
  const queryClient = useQueryClient();
  const [isEditingAssignee, setIsEditingAssignee] = useState(false);
  const [newAssignee, setNewAssignee] = useState('');
  const [isEditingCompletion, setIsEditingCompletion] = useState(false);
  const [completionNotes, setCompletionNotes] = useState(action?.completionNotes || '');

  const updateStatusMutation = useMutation({
    mutationFn: ({ actionId, status }: { actionId: string; status: Action['status'] }) =>
      actionsApi.patch(`/actions/${actionId}/status`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] });
      toast.success('Action status updated successfully');
    },
    onError: (error) => {
      toast.error('Failed to update action status');
      console.error('Error updating action status:', error);
    },
  });

  const updateAssigneeMutation = useMutation({
    mutationFn: ({ actionId, assignedTo }: { actionId: string; assignedTo: string }) =>
      actionsApi.patch(`/actions/${actionId}/assign`, { assignedTo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] });
      toast.success('Action assignment updated successfully');
      setIsEditingAssignee(false);
    },
    onError: (error) => {
      toast.error('Failed to update action assignment');
      console.error('Error updating action assignment:', error);
    },
  });

  const updateCompletionMutation = useMutation({
    mutationFn: ({ actionId, notes }: { actionId: string; notes: string }) =>
      actionsApi.patch(`/actions/${actionId}/complete`, { notes }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['actions'] });
      toast.success('Action completion updated successfully');
      setIsEditingCompletion(false);
    },
    onError: (error) => {
      toast.error('Failed to update action completion');
      console.error('Error updating action completion:', error);
    },
  });

  const handleStatusChange = (newStatus: Action['status']) => {
    if (!action) return;
    updateStatusMutation.mutate({ actionId: action.id, status: newStatus });
  };

  const handleAssigneeChange = () => {
    if (!action) return;
    updateAssigneeMutation.mutate({ actionId: action.id, assignedTo: newAssignee });
  };

  const startEditingAssignee = () => {
    if (!action) return;
    setNewAssignee(action.assignedTo);
    setIsEditingAssignee(true);
  };

  const handleCompletionUpdate = () => {
    if (!action) return;
    updateCompletionMutation.mutate({ actionId: action.id, notes: completionNotes });
  };

  if (!action) return null;

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div className="absolute right-0 top-0 hidden pr-4 pt-4 sm:block">
                  <button
                    type="button"
                    className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                    onClick={onClose}
                  >
                    <span className="sr-only">Close</span>
                    <XMarkIcon className="h-6 w-6" aria-hidden="true" />
                  </button>
                </div>
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                    <Dialog.Title as="h3" className="text-lg font-semibold leading-6 text-gray-900">
                      {action.title}
                    </Dialog.Title>
                    <div className="mt-4 space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-500">Description</h4>
                        <p className="mt-1 text-sm text-gray-900">{action.description}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Priority</h4>
                          <span
                            className={`mt-1 inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                              priorityColors[action.priority]
                            }`}
                          >
                            {action.priority}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Status</h4>
                          <div className="mt-1">
                            <select
                              value={action.status}
                              onChange={(e) => handleStatusChange(e.target.value as Action['status'])}
                              disabled={updateStatusMutation.isPending}
                              className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm ${
                                statusColors[action.status]
                              }`}
                            >
                              {statusOptions.map((option) => (
                                <option key={option.value} value={option.value}>
                                  {option.label}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Due Date</h4>
                          <p className="mt-1 text-sm text-gray-900">
                            {new Date(action.dueDate).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Assigned To</h4>
                          <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
                            <dt className="text-sm font-medium text-gray-500">Assigned To</dt>
                            <dd className="mt-1 text-sm text-gray-900">
                              {isEditingAssignee ? (
                                <div className="flex items-center space-x-2">
                                  <input
                                    type="text"
                                    value={newAssignee}
                                    onChange={(e) => setNewAssignee(e.target.value)}
                                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                    placeholder="Enter assignee name"
                                  />
                                  <button
                                    onClick={handleAssigneeChange}
                                    disabled={updateAssigneeMutation.isPending}
                                    className="inline-flex items-center rounded-md bg-blue-600 px-2.5 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50"
                                  >
                                    <CheckIcon className="h-4 w-4" />
                                  </button>
                                </div>
                              ) : (
                                <div className="flex items-center justify-between">
                                  <span>{action.assignedTo}</span>
                                  <button
                                    onClick={startEditingAssignee}
                                    className="inline-flex items-center rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                                  >
                                    <PencilIcon className="h-4 w-4" />
                                  </button>
                                </div>
                              )}
                            </dd>
                          </div>
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-medium text-gray-500">Related Finding</h4>
                        <p className="mt-1 text-sm text-gray-900">{action.findingTitle}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Created</h4>
                          <p className="mt-1 text-sm text-gray-900">
                            {new Date(action.createdAt).toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-gray-500">Last Updated</h4>
                          <p className="mt-1 text-sm text-gray-900">
                            {new Date(action.updatedAt).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      {action.status === 'completed' && (
                        <div>
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-medium text-gray-500">Completion Notes</h4>
                            <button
                              onClick={() => setIsEditingCompletion(true)}
                              className="inline-flex items-center rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                          </div>
                          {isEditingCompletion ? (
                            <div className="mt-2 space-y-2">
                              <textarea
                                value={completionNotes}
                                onChange={(e) => setCompletionNotes(e.target.value)}
                                rows={3}
                                className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                placeholder="Enter completion notes..."
                              />
                              <div className="flex justify-end space-x-2">
                                <button
                                  onClick={() => setIsEditingCompletion(false)}
                                  className="inline-flex items-center rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                                >
                                  Cancel
                                </button>
                                <button
                                  onClick={handleCompletionUpdate}
                                  disabled={updateCompletionMutation.isPending}
                                  className="inline-flex items-center rounded-md bg-blue-600 px-2.5 py-1.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 disabled:opacity-50"
                                >
                                  Save Notes
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div className="mt-1">
                              <p className="text-sm text-gray-900">
                                {action.completionNotes || 'No completion notes provided.'}
                              </p>
                              {action.completedAt && (
                                <p className="mt-1 text-xs text-gray-500">
                                  Completed on {new Date(action.completedAt).toLocaleString()}
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
};
