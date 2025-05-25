import React, { useState, useEffect } from 'react';
import apiClient from '../api/apiClient';
import toast from 'react-hot-toast';

// Placeholder interface for Finding data (adjust based on actual API response)
interface Finding {
  finding_id: string;
  timestamp_utc: string;
  finding_type: string;
  device_hostname?: string;
  device_ip?: string;
  agent_id?: number;
  details: object;
}

// Helper function to format timestamp (optional)
const formatTimestamp = (isoString: string): string => {
    try {
        return new Date(isoString).toLocaleString();
    } catch (e) {
        return isoString; // Return original if parsing fails
    }
};

const FindingsPage: React.FC = () => {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFindings = async () => {
      setLoading(true);
      setError(null);
      try {
        // Add pagination params (example: first 50 findings)
        const response = await apiClient.get<{ findings: Finding[], total: number }>
            ('/findings', { params: { limit: 50, offset: 0 } });
        setFindings(response.data.findings || []);
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || 'Failed to load findings. Is the Management API running?';
        console.error("Failed to fetch findings:", err);
        setError(errorMsg);
        toast.error(errorMsg);
        setFindings([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFindings();
  }, []);

  return (
    // Apply card style wrapper
    <div className="bg-white p-6 rounded-lg shadow-md">

      {/* Card Header */}
      <div className="border-b border-gray-200 pb-4 mb-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-800">Findings</h1>
        {/* Placeholder for potential header actions */}
        <div></div>
      </div>

      {/* Loading/Error Messages (inside card body) */}
      {loading && <p className="text-gray-600 py-4 text-center">Loading findings...</p>}
      {error && <p className="text-red-600 font-semibold py-4 text-center">Error: {error}</p>}

      {/* Table Section (inside card body) */}
      {!loading && !error && (
        <div className="overflow-x-auto">
           {/* Remove outer container styling, apply table styles like AgentsPage */}
           <table className="min-w-full divide-y divide-gray-200 border border-gray-200">
             {/* thead style */}
             <thead className="bg-gray-50">
               <tr>
                 {/* th styles */}
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Timestamp</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Type</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">Device</th>
                 <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Details</th>
               </tr>
             </thead>
             {/* tbody style */}
             <tbody className="bg-white divide-y divide-gray-200">
               {findings.length > 0 ? (
                 findings.map((finding) => (
                   // tr style
                   <tr key={finding.finding_id}>
                     {/* td styles */}
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 border-r border-gray-200">{formatTimestamp(finding.timestamp_utc)}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 border-r border-gray-200">{finding.finding_type}</td>
                     <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600 border-r border-gray-200">{finding.device_hostname || finding.device_ip || 'N/A'}</td>
                     <td className="px-4 py-3 text-sm text-gray-500">
                         <pre className="text-xs whitespace-pre-wrap font-mono">{JSON.stringify(finding.details, null, 2)}</pre>
                     </td>
                   </tr>
                 ))
               ) : (
                 <tr>
                   {/* Adjusted colspan */}
                   <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">No findings found.</td>
                 </tr>
               )}
             </tbody>
           </table>
        </div>
      )}
    </div> // End card wrapper
  );
};

export default FindingsPage;
