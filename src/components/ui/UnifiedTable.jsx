import React from 'react';

/**
 * UnifiedTable Component - Enterprise Design System
 * Standardized table component with consistent styling and accessibility
 * 
 * Features:
 * - Light gray header background (bg-muted/40)
 * - Simple bottom borders (no zebra striping)
 * - Vertical alignment middle
 * - Semantic color tokens
 * - NO gradient backgrounds in cells
 */
const UnifiedTable = ({
    columns = [],
    data = [],
    className = "",
    emptyMessage = "No data available"
}) => {
    return (
        <div className={`overflow-x-auto ${className}`}>
            <table className="w-full border-collapse">
                <thead>
                    <tr className="bg-black/20 border-b border-white/5 shadow-sm">
                        {columns.map((column, index) => (
                            <th
                                key={index}
                                className="px-4 py-3 text-left text-sm font-medium text-foreground whitespace-nowrap"
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
                                className="px-4 py-8 text-center text-sm text-muted-foreground"
                            >
                                {emptyMessage}
                            </td>
                        </tr>
                    ) : (
                        data.map((row, rowIndex) => (
                            <tr
                                key={rowIndex}
                                className="border-b border-white/10 hover:bg-white/5 transition-colors group"
                            >
                                {columns.map((column, colIndex) => (
                                    <td
                                        key={colIndex}
                                        className="px-4 py-3 align-middle text-sm text-foreground"
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
