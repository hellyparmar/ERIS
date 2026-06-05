import React, { useState, useRef, useEffect } from 'react';
import { Download, FileSpreadsheet, FileText, X, ChevronDown, File } from 'lucide-react';
import { exportToCSV, exportToExcel, exportToPDF } from '@/lib/api';

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

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

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
            const response = await fetch(`${API_BASE}${endpoint}`, {
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
                className={`flex items-center gap-2 px-4 py-2 ${isDark ? 'bg-amber-500 hover:bg-amber-600 text-white' : 'bg-gray-900 hover:bg-gray-800 text-white'} rounded-lg shadow-soft hover:shadow-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
            >
                <Download size={16} />
                <span className="font-medium">{isExporting ? 'Exporting...' : 'Export'}</span>
                <ChevronDown size={16} className={`transition-transform duration-150 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
                <div
                    className="absolute right-0 mt-2 w-48 bg-surface border border-border-sm shadow-medium rounded-lg overflow-hidden z-50"
                >
                    {formats.map((format) => {
                        const Icon = format.icon;
                        return (
                            <button
                                key={format.value}
                                onClick={() => handleExport(format.value)}
                                className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted transition-colors duration-150 text-left"
                            >
                                <Icon size={18} className={format.color} />
                                <div>
                                    <p className="text-sm font-medium text-primary">
                                        Export as {format.label}
                                    </p>
                                    <p className="text-xs text-muted">
                                        {format.value === 'pdf' && 'Professional report'}
                                        {format.value === 'excel' && 'Spreadsheet format'}
                                        {format.value === 'csv' && 'Raw data'}
                                    </p>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}

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
