import React from 'react';
import { Trash2, Download, Edit, Check, X } from 'lucide-react';

/**
 * BulkActionToolbar Component
 * Appears when items are selected in a table
 */
const BulkActionToolbar = ({
    selectedCount,
    onDelete,
    onExport,
    onUpdate,
    onClearSelection,
    className = ""
}) => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    return (
        <>
            {selectedCount > 0 && (
                <div
                    className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 ${className}`}
                >
                    <div className={`bg-surface border border-border-sm shadow-medium rounded-lg px-6 py-4 flex items-center gap-6`}>
                        <div className="flex items-center gap-2">
                            <div className={`w-8 h-8 ${isDark ? 'bg-amber-500/20 text-amber-500' : 'bg-gray-900/20 text-gray-900'} rounded-lg flex items-center justify-center`}>
                                <Check size={16} />
                            </div>
                            <span className="font-semibold text-primary">
                                {selectedCount} item{selectedCount > 1 ? 's' : ''} selected
                            </span>
                        </div>

                        <div className="h-6 w-px bg-border-sm" />

                        <div className="flex items-center gap-2">
                            {onExport && (
                                <button
                                    onClick={onExport}
                                    className={`flex items-center gap-2 px-4 py-2 ${isDark ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-gray-900 hover:bg-gray-800 text-white'} rounded-lg transition-colors duration-150`}
                                    title="Export selected"
                                >
                                    <Download size={16} />
                                    <span className="text-sm font-medium">Export</span>
                                </button>
                            )}

                            {onUpdate && (
                                <button
                                    onClick={onUpdate}
                                    className={`flex items-center gap-2 px-4 py-2 ${isDark ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-gray-900 hover:bg-gray-800 text-white'} rounded-lg transition-colors duration-150`}
                                    title="Update selected"
                                >
                                    <Edit size={16} />
                                    <span className="text-sm font-medium">Update</span>
                                </button>
                            )}

                            {onDelete && (
                                <button
                                    onClick={onDelete}
                                    className="flex items-center gap-2 px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors duration-150"
                                    title="Delete selected"
                                >
                                    <Trash2 size={16} />
                                    <span className="text-sm font-medium">Delete</span>
                                </button>
                            )}

                            <button
                                onClick={onClearSelection}
                                className="ml-2 p-2 hover:bg-muted rounded-lg transition-colors duration-150"
                                title="Clear selection"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default BulkActionToolbar;
