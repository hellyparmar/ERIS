/**
 * Unified Pagination Controls Component
 * Handles pagination for all data-heavy pages in the system
 * Supports: page navigation, items per page selection, total count display
 */

import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const PaginationControls = ({
    currentPage = 1,
    totalPages = 1,
    totalItems = 0,
    itemsPerPage = 50,
    onPageChange,
    onItemsPerPageChange,
    isLoading = false,
    className = ''
}) => {
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);

    const handlePreviousPage = () => {
        if (currentPage > 1 && onPageChange) {
            onPageChange(currentPage - 1);
        }
    };

    const handleNextPage = () => {
        if (currentPage < totalPages && onPageChange) {
            onPageChange(currentPage + 1);
        }
    };

    const handlePageInputChange = (e) => {
        const page = parseInt(e.target.value, 10);
        if (!isNaN(page) && page >= 1 && page <= totalPages && onPageChange) {
            onPageChange(page);
        }
    };

    const handleItemsPerPageChange = (e) => {
        const newLimit = parseInt(e.target.value, 10);
        if (onItemsPerPageChange) {
            onItemsPerPageChange(newLimit);
        }
    };

    return (
        <div className={`flex flex-col md:flex-row justify-between items-center gap-4 py-4 px-4 bg-white/5 rounded-lg border border-white/10 ${className}`}>
            {/* Items per page selector */}
            <div className="flex items-center gap-2">
                <label htmlFor="items-per-page" className="text-sm text-muted-foreground whitespace-nowrap">
                    Items per page:
                </label>
                <select
                    id="items-per-page"
                    value={itemsPerPage}
                    onChange={handleItemsPerPageChange}
                    disabled={isLoading}
                    className="px-3 py-1.5 rounded-md bg-secondary text-foreground text-sm border border-white/10 focus:border-blue-500 focus:outline-none disabled:opacity-50"
                >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                </select>
            </div>

            {/* Item count display */}
            <div className="text-sm text-muted-foreground">
                Showing <span className="font-semibold text-foreground">{startItem}</span>-
                <span className="font-semibold text-foreground">{endItem}</span> of{' '}
                <span className="font-semibold text-foreground">{totalItems.toLocaleString()}</span> items
            </div>

            {/* Page navigation */}
            <div className="flex items-center gap-2">
                <button
                    onClick={handlePreviousPage}
                    disabled={currentPage === 1 || isLoading}
                    className="p-2 rounded-md border border-white/10 hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous page"
                >
                    <ChevronLeft size={18} />
                </button>

                <div className="flex items-center gap-1">
                    <input
                        type="number"
                        min={1}
                        max={totalPages}
                        value={currentPage}
                        onChange={handlePageInputChange}
                        disabled={isLoading}
                        className="w-12 px-2 py-1.5 rounded-md bg-secondary text-foreground text-sm border border-white/10 focus:border-blue-500 focus:outline-none text-center disabled:opacity-50"
                    />
                    <span className="text-sm text-muted-foreground">
                        of <span className="font-semibold">{totalPages}</span>
                    </span>
                </div>

                <button
                    onClick={handleNextPage}
                    disabled={currentPage === totalPages || isLoading}
                    className="p-2 rounded-md border border-white/10 hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next page"
                >
                    <ChevronRight size={18} />
                </button>
            </div>
        </div>
    );
};

export default PaginationControls;
