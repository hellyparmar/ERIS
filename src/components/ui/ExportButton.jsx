import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, FileText, FileSpreadsheet, File, ChevronDown } from 'lucide-react';

/**
 * ExportButton Component
 * Reusable button with format selector dropdown for exporting data
 */
const ExportButton = ({
    endpoint,
    filename = "export",
    filters = {},
    onExportStart,
    onExportComplete,
    onExportError,
    className = ""
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExporting, setIsExporting] = useState(false);

    const formats = [
        { value: 'pdf', label: 'PDF', icon: FileText, color: 'text-red-500' },
        { value: 'excel', label: 'Excel', icon: FileSpreadsheet, color: 'text-green-500' },
        { value: 'csv', label: 'CSV', icon: File, color: 'text-blue-500' }
    ];

    const handleExport = async (format) => {
        setIsOpen(false);
        setIsExporting(true);

        if (onExportStart) onExportStart(format);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`http://localhost:8000${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    format: format,
                    ...filters
                })
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            // Get the blob
            const blob = await response.blob();

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;

            // Get filename from response headers or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition && contentDisposition.match(/filename="?(.+)"?/);
            const downloadFilename = filenameMatch ? filenameMatch[1] : `${filename}.${format === 'excel' ? 'xlsx' : format}`;

            link.setAttribute('download', downloadFilename);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);

            if (onExportComplete) onExportComplete(format);
        } catch (error) {
            console.error('Export error:', error);
            if (onExportError) onExportError(error);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="relative inline-block">
            <button
                onClick={() => setIsOpen(!isOpen)}
                disabled={isExporting}
                className={`flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
            >
                <Download size={16} className={isExporting ? 'animate-bounce' : ''} />
                <span className="font-medium">{isExporting ? 'Exporting...' : 'Export'}</span>
                <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden z-50"
                    >
                        {formats.map((format) => {
                            const Icon = format.icon;
                            return (
                                <button
                                    key={format.value}
                                    onClick={() => handleExport(format.value)}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                                >
                                    <Icon size={18} className={format.color} />
                                    <div>
                                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                                            Export as {format.label}
                                        </p>
                                        <p className="text-xs text-gray-500 dark:text-gray-400">
                                            {format.value === 'pdf' && 'Professional report'}
                                            {format.value === 'excel' && 'Spreadsheet format'}
                                            {format.value === 'csv' && 'Raw data'}
                                        </p>
                                    </div>
                                </button>
                            );
                        })}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Backdrop to close dropdown */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsOpen(false)}
                />
            )}
        </div>
    );
};

export default ExportButton;
