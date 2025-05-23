import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

const MainLayout: React.FC = () => {
  const navLinkClasses = (
    { isActive }: { isActive: boolean }
  ) =>
    // Adjusted styles based on Bootstrap source
    `block p-3 rounded transition-colors duration-150 
     ${isActive 
        ? 'bg-gray-700 text-white font-semibold' 
        : 'text-gray-400 hover:bg-gray-700 hover:text-white'
     }`;
     // Removed focus ring for now, can be added back if needed

  return (
    <div className="flex flex-col h-screen">
      {/* Top Bar (bg-dark equivalent) */}
      <header className="bg-gray-900 text-white p-3 shadow-md flex justify-between items-center z-10 flex-shrink-0">
        <h1 className="text-xl font-semibold">OPMAS</h1>
        <div>
          <span className="text-sm mr-4">Signed in as: admin</span>
          {/* Adjusted btn-outline-secondary btn-sm: lighter border/text */}
          <button className="px-2 py-1 text-xs border border-gray-500 text-gray-300 rounded hover:bg-gray-700 hover:text-white focus:outline-none focus:ring-1 focus:ring-gray-500 transition-colors duration-150">
            Logout
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar (bg-dark equivalent) */}
        <aside className="w-64 bg-gray-800 text-white p-4 flex flex-col flex-shrink-0 overflow-y-auto">
          <nav className="flex-grow mt-4 space-y-1">
            {/* TODO: Add Icons like reference */}
            <NavLink to="/" className={navLinkClasses} end>
              Dashboard
            </NavLink>
            <NavLink to="/findings" className={navLinkClasses}>
              Findings
            </NavLink>
            <NavLink to="/actions" className={navLinkClasses}>
              Intended Actions
            </NavLink>
            <NavLink to="/agents" className={navLinkClasses}>
              Agent Management
            </NavLink>
            <NavLink to="/playbooks" className={navLinkClasses}>
              Playbook Management
            </NavLink>
            <NavLink to="/config" className={navLinkClasses}>
              Core Config
            </NavLink>
          </nav>
          <div className="mt-auto pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500">OPMAS v1.0</p>
          </div>
        </aside>

        {/* Main Content Area (light gray background) */}
        <main className="flex-1 p-6 overflow-auto bg-gray-100">
          {/* Content cards will have bg-white */}
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout; 