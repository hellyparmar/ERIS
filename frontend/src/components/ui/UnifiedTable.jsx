import React from 'react';

/**
 * UnifiedTable Component - Clean table with minimal styling
 * Standardized table component with consistent styling and accessibility
 *
 * Features:
 * - Clean header background
 * - Alternating row colors for readability
 * - Simple borders
 * - Semantic color tokens
 */
const UnifiedTable = ({
    columns = [],
    data = [],
    className = "",
    emptyMessage = "No data available"
}) => {
    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="w-full border-collapse border border-border-sm rounded-lg overflow-hidden">
                <thead>
                    <tr className="bg-muted/50 border-b border-border-sm">
                        {columns.map((column, index) => (
                            <th
                                key={index}
                                className="px-4 py-3 text-left text-sm font-medium text-primary whitespace-nowrap"
                                style={{ width: column.width }}
                            >
                                {column.header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.length === 0 ? (
                        <tr>
                            <td
                                colSpan={columns.length}
                                className="px-4 py-8 text-center text-sm text-muted"
                            >
                                {emptyMessage}
                            </td>
                        </tr>
                    ) : (
                        data.map((row, rowIndex) => (
                            <tr
                                key={rowIndex}
                                className={`border-b border-border-sm hover:bg-muted/30 transition-colors duration-150 ${rowIndex % 2 === 0 ? 'bg-surface' : 'bg-muted/20'}`}
                            >
                                {columns.map((column, colIndex) => (
                                    <td
                                        key={colIndex}
                                        className="px-4 py-3 align-middle text-sm text-primary"
                                    >
                                        {column.render
                                            ? column.render(row[column.accessor], row, rowIndex)
                                            : row[column.accessor]
                                        }
                                    </td>
                                ))}
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default UnifiedTable;
