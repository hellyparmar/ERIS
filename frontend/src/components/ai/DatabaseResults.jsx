import React from 'react';
import { Database, BarChart3 } from 'lucide-react';

const DatabaseResults = ({ queryResult }) => {
  if (!queryResult || !queryResult.success) {
    return null;
  }

  const { data, row_count, execution_time_ms, template_matched } = queryResult;

  if (!data || data.length === 0) {
    return null;
  }

  // Get column headers from first row
  const columns = Object.keys(data[0]);

  // Determine if this is a simple metric (single value) or detailed results
  const isMetric = row_count === 1 && columns.length === 1;

  if (isMetric) {
    // Display metric as a highlighted value
    const value = data[0][columns[0]];
    const formattedValue = typeof value === 'number' 
      ? value.toLocaleString('en-IN', { 
          style: 'currency', 
          currency: 'INR',
          minimumFractionDigits: 0
        })
      : value;

    return (
      <div className="mt-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <BarChart3 size={16} className="text-indigo-600" />
          <span className="text-xs font-semibold text-indigo-600">Database Result</span>
        </div>
        <div className="text-2xl font-bold text-gray-800">
          {formattedValue}
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Query executed in {execution_time_ms.toFixed(2)}ms
        </div>
      </div>
    );
  }

  // Display as table for multiple rows
  return (
    <div className="mt-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex items-center gap-2 mb-3">
        <Database size={16} className="text-gray-600" />
        <span className="text-xs font-semibold text-gray-600">
          {row_count} Result{row_count !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-300">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left font-semibold text-gray-700 bg-gray-100"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className="border-b border-gray-200 hover:bg-gray-100">
                {columns.map((col) => (
                  <td key={`${idx}-${col}`} className="px-3 py-2 text-gray-700">
                    {typeof row[col] === 'number'
                      ? row[col].toLocaleString('en-IN', {
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 2
                        })
                      : String(row[col]).substring(0, 50)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-gray-500 mt-3">
        Executed in {execution_time_ms.toFixed(2)}ms • Query: {template_matched}
      </div>
    </div>
  );
};

export default DatabaseResults;
