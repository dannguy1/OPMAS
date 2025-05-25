import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import toast from 'react-hot-toast'; // Import toast

// Interface for core config (simple key-value dictionary)
type CoreConfig = Record<string, any>; // string keys, any type of value

const CoreConfigPage: React.FC = () => {
  const [config, setConfig] = useState<CoreConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState<Record<string, boolean>>({}); // Track edit state per key
  const [editValues, setEditValues] = useState<Record<string, string>>({}); // Track edited values (as strings)

  useEffect(() => {
    fetchConfig();
  }, []);

    const fetchConfig = async () => {
      setLoading(true);
      setError(null);
    setEditMode({}); // Reset edit mode on fetch
    setEditValues({}); // Reset edit values on fetch
    try {
      // API returns a single dictionary object
      const response = await apiClient.get<CoreConfig>('/config/core');
      setConfig(response.data || {});
      // Initialize edit values based on fetched config
      const initialEditValues: Record<string, string> = {};
      if (response.data) {
        for (const key in response.data) {
           initialEditValues[key] = JSON.stringify(response.data[key]); // Store as JSON string initially
        }
      }
      setEditValues(initialEditValues);

    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to load core configuration. Is the Management API running or endpoint available?';
        console.error("Failed to fetch core config:", err);
      setError(errorMsg);
      toast.error(errorMsg);
      setConfig({});
      } finally {
        setLoading(false);
      }
    };

  const handleEditToggle = (key: string) => {
      setEditMode(prev => ({ ...prev, [key]: !prev[key] }));
      // If exiting edit mode without saving, reset value to original config
      if (editMode[key] && config) {
          setEditValues(prev => ({ ...prev, [key]: JSON.stringify(config[key]) }));
      }
  };

  const handleValueChange = (key: string, value: string) => {
      setEditValues(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async (key: string) => {
    if (!config) return;

    // Remove or comment out the declaration of originalValue if present
    // const originalValue = config[key];
    const editedValueString = editValues[key];
    let newValue: any;

    try {
        // Attempt to parse the edited string back into its original type (best effort)
        newValue = JSON.parse(editedValueString);
    } catch (parseError) {
        // If parsing fails (e.g., user typed invalid JSON), treat it as a string
        newValue = editedValueString;
        console.warn(`Could not parse edited value for key '${key}' as JSON. Saving as string.`);
    }

    // TODO: Implement PUT/POST call to /api/config/core to save the *entire* config or *individual* key
    // This requires backend implementation first.
    alert(`Saving ${key}=${JSON.stringify(newValue)} (API call not yet implemented)`);

    // --- Placeholder: Update local state as if save succeeded ---
    // Note: This is temporary. A real implementation would update after API success.
    setConfig(prevConfig => ({ ...prevConfig, [key]: newValue }));
    setEditMode(prev => ({ ...prev, [key]: false })); // Exit edit mode
    // ----------------------------------------------------------

    // Example API call structure (needs backend endpoint):
    /*
    try {
      // Option 1: Update the whole config object
      // const updatedConfig = { ...config, [key]: newValue };
      // await apiClient.put<CoreConfig>('/config/core', updatedConfig);

      // Option 2: Update just one key (requires specific backend endpoint, e.g., PUT /config/core/{key})
      // await apiClient.put(`/config/core/${key}`, { value: newValue });

      setConfig(prevConfig => ({ ...prevConfig, [key]: newValue }));
      setEditMode(prev => ({ ...prev, [key]: false }));
      // Add success notification
      toast.success(`Configuration key '${key}' updated successfully.`);
    } catch (err: any) {
      console.error(`Failed to save config key ${key}:`, err);
      setError(`Failed to save ${key}.`);
      // Revert edit value?
      // setEditValues(prev => ({ ...prev, [key]: JSON.stringify(originalValue) }));
      // Add error notification
      toast.error(`Failed to save configuration key '${key}'.`);
    }
    */
  };

  return (
    // Apply card style wrapper
    <div className="bg-white p-6 rounded-lg shadow-md">

      {/* Card Header */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">Core Configuration</h1>
        {/* Placeholder for potential header actions */}
        <div></div>
      </div>

      {/* Loading/Error Messages (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading configuration...</p>}
      {error && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}

      {/* Table Section (inside card body) */}
      {!loading && !error && config && (
        <div className="overflow-x-auto">
          {/* Remove outer container styling, apply table styles */}
          <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
            {/* thead style */}
            <thead className="bg-gray-50">
              <tr>
                {/* th styles */}
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 w-1/3">Key</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 w-2/3">Value</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            {/* tbody style */}
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(config).map(([key, value]) => (
                // tr style
                <tr key={key}>
                  {/* td styles */}
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200 font-mono align-top">{key}</td>
                  <td className="px-4 py-3 whitespace-pre-wrap text-sm text-gray-700 border-r border-gray-200 font-mono align-top">
                    {editMode[key] ? (
                      <textarea
                        value={editValues[key]}
                        onChange={(e) => handleValueChange(key, e.target.value)}
                        rows={3} // Adjust rows as needed
                        className="w-full px-2 py-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                      />
                    ) : (
                      <pre className="whitespace-pre-wrap break-words">{JSON.stringify(value, null, 2)}</pre>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm font-medium space-x-1 align-top">
                    {editMode[key] ? (
                      <>
                        {/* Save Button - btn-outline-success btn-sm */}
                        <button
                          onClick={() => handleSave(key)}
                          className="px-2 py-1 text-xs rounded border border-green-500 bg-white text-green-600 hover:bg-green-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-green-400 transition duration-150"
                        >
                          Save
                        </button>
                        {/* Cancel Button - btn-outline-secondary btn-sm */}
                        <button
                          onClick={() => handleEditToggle(key)}
                          className="px-2 py-1 text-xs border border-gray-300 bg-white text-gray-700 rounded hover:bg-gray-100 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-gray-400 transition duration-150"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      // Edit Button - btn-outline-primary btn-sm
                    <button
                        onClick={() => handleEditToggle(key)}
                        className="px-2 py-1 text-xs border border-blue-500 bg-white text-blue-600 rounded hover:bg-blue-50 focus:outline-none focus:ring-1 focus:ring-offset-1 focus:ring-blue-400 transition duration-150"
                    >
                        Edit
                    </button>
                    )}
                  </td>
                </tr>
              ))}
              {Object.keys(config).length === 0 && (
                  <tr>
                      <td colSpan={3} className="px-4 py-6 text-center text-sm text-gray-500">
                          No configuration items found or loaded.
                      </td>
                  </tr>
              )}
            </tbody>
          </table>
          {/* Remove note for now, can be added back if needed */}
          {/* <p className="text-xs text-gray-500 mt-2">Note: Editing functionality requires backend implementation to persist changes.</p> */}
        </div>
      )}
    </div> // End card wrapper
  );
};

export default CoreConfigPage;
