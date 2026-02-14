// Pagination Component (React + TypeScript)
// Reusable pagination component for inventory and other list pages

import React, { useState } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
  onPageChange: (page: number) => void;
  onLimitChange: (limit: number) => void;
  loading?: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  totalItems,
  itemsPerPage,
  onPageChange,
  onLimitChange,
  loading = false,
}) => {
  const [inputPage, setInputPage] = useState<string>(String(currentPage));

  // Calculate display range
  const startItem = (currentPage - 1) * itemsPerPage + 1;
  const endItem = Math.min(currentPage * itemsPerPage, totalItems);

  // Handle direct page input
  const handlePageInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputPage(value);
    
    if (value && !isNaN(Number(value))) {
      const page = Math.min(Math.max(1, Number(value)), totalPages);
      onPageChange(page);
      setInputPage(String(page));
    }
  };

  return (
    <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-200">
      {/* Items per page selector */}
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-600 font-medium">
          Items per page:
        </label>
        <select
          value={itemsPerPage}
          onChange={(e) => onLimitChange(Number(e.target.value))}
          disabled={loading}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value={50}>50</option>
          <option value={100}>100</option>
          <option value={250}>250</option>
        </select>
      </div>

      {/* Page info */}
      <div className="text-sm text-gray-600">
        Showing{' '}
        <span className="font-medium">
          {startItem.toLocaleString()} to {endItem.toLocaleString()}
        </span>{' '}
        of <span className="font-medium">{totalItems.toLocaleString()}</span> items
      </div>

      {/* Navigation buttons */}
      <div className="flex items-center gap-2">
        {/* First page button */}
        <button
          onClick={() => {
            onPageChange(1);
            setInputPage('1');
          }}
          disabled={currentPage === 1 || loading}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          title="First page"
          aria-label="First page"
        >
          ⟨⟨
        </button>

        {/* Previous page button */}
        <button
          onClick={() => {
            const newPage = currentPage - 1;
            onPageChange(newPage);
            setInputPage(String(newPage));
          }}
          disabled={currentPage === 1 || loading}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          title="Previous page"
          aria-label="Previous page"
        >
          ⟨
        </button>

        {/* Page input */}
        <div className="flex items-center gap-1">
          <span className="text-sm text-gray-600">Page</span>
          <input
            type="number"
            value={inputPage}
            onChange={handlePageInput}
            onBlur={() => setInputPage(String(currentPage))}
            min="1"
            max={totalPages}
            disabled={loading}
            className="w-16 text-center border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Current page"
          />
          <span className="text-sm text-gray-600">of {totalPages}</span>
        </div>

        {/* Next page button */}
        <button
          onClick={() => {
            const newPage = currentPage + 1;
            onPageChange(newPage);
            setInputPage(String(newPage));
          }}
          disabled={currentPage === totalPages || loading}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          title="Next page"
          aria-label="Next page"
        >
          ⟩
        </button>

        {/* Last page button */}
        <button
          onClick={() => {
            onPageChange(totalPages);
            setInputPage(String(totalPages));
          }}
          disabled={currentPage === totalPages || loading}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
          title="Last page"
          aria-label="Last page"
        >
          ⟩⟩
        </button>
      </div>
    </div>
  );
};

// Example usage:
/*
import { useInventory } from '../hooks/useInventory';
import { Pagination } from '../components/Pagination';

export function InventoryPage() {
  const {
    items,
    loading,
    error,
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    setCurrentPage,
    setItemsPerPage,
  } = useInventory();

  return (
    <div>
      <h1>Inventory</h1>
      {/* Items table */}
      <table>
        <tbody>
          {items.map(item => (
            <tr key={item.id}>
              <td>{item.product_name}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* Pagination */}
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalItems}
        itemsPerPage={itemsPerPage}
        onPageChange={setCurrentPage}
        onLimitChange={setItemsPerPage}
        loading={loading}
      />
    </div>
  );
}
*/
