import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
    return (
        <AnimatePresence>
            {selectedCount > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className={`fixed top-20 left-1/2 transform -translate-x-1/2 z-50 ${className}`}
                >
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-2xl px-6 py-4 flex items-center gap-6">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                                <Check size={16} />
                            </div>
                            <span className="font-semibold">
                                {selectedCount} item{selectedCount > 1 ? 's' : ''} selected
                            </span>
                        </div>

                        <div className="h-6 w-px bg-white/30" />

                        <div className="flex items-center gap-2">
                            {onExport && (
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={onExport}
                                    className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                                    title="Export selected"
                                >
                                    <Download size={16} />
                                    <span className="text-sm font-medium">Export</span>
                                </motion.button>
                            )}

                            {onUpdate && (
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={onUpdate}
                                    className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
                                    title="Update selected"
                                >
                                    <Edit size={16} />
                                    <span className="text-sm font-medium">Update</span>
                                </motion.button>
                            )}

                            {onDelete && (
                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={onDelete}
                                    className="flex items-center gap-2 px-4 py-2 bg-red-500/80 hover:bg-red-600 rounded-lg transition-colors"
                                    title="Delete selected"
                                >
                                    <Trash2 size={16} />
                                    <span className="text-sm font-medium">Delete</span>
                                </motion.button>
                            )}

                            <button
                                onClick={onClearSelection}
                                className="ml-2 p-2 hover:bg-white/20 rounded-lg transition-colors"
                                title="Clear selection"
                            >
                                <X size={16} />
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

export default BulkActionToolbar;
