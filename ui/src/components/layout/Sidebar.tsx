import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  DocumentMagnifyingGlassIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  BookOpenIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onClose }) => {
  const navigation = [
    { name: 'Dashboard', to: '/', icon: HomeIcon },
    { name: 'Findings', to: '/findings', icon: DocumentMagnifyingGlassIcon },
    { name: 'Intended Actions', to: '/actions', icon: ClipboardDocumentListIcon },
    { name: 'Agent Management', to: '/agents', icon: UserGroupIcon },
    { name: 'Playbook Management', to: '/playbooks', icon: BookOpenIcon },
    { name: 'Core Config', to: '/config', icon: Cog6ToothIcon },
  ];

  const navLinkClasses = ({ isActive }: { isActive: boolean }) =>
    `group flex items-center px-2 py-2 text-sm font-medium rounded-md ${
      isActive
        ? 'bg-gray-100 text-gray-900'
        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
    }`;

  return (
    <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
      <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
        <div className="flex flex-shrink-0 items-center px-4">
          <img
            className="h-8 w-auto"
            src="/logo.svg"
            alt="OPMAS"
          />
        </div>
        <nav className="mt-5 flex-1 space-y-1 bg-white px-2">
          {navigation.map((item) => (
            <NavLink
              key={item.name}
              to={item.to}
              className={navLinkClasses}
              onClick={onClose}
            >
              <item.icon
                className="mr-3 h-6 w-6 flex-shrink-0 text-gray-400"
                aria-hidden="true"
              />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </div>
      <div className="flex flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div>
            <p className="text-sm font-medium text-gray-700">OPMAS</p>
            <p className="text-xs text-gray-500">Version 1.0.0</p>
          </div>
        </div>
      </div>
    </div>
  );
};
