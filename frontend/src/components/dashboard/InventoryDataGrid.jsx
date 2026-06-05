
import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

const InventoryDataGrid = ({ data = [] }) => {
    // Use provided data or empty array if none provided
    const gridData = data && data.length > 0 ? data : [];

    return (
        <GlassCard className="h-full bg-card border border-border flex flex-col">
            <div className="p-6 border-b border-border flex justify-between items-center">
                <h3 className="font-bold text-foreground">Inventory Data Grid</h3>
                <div className="flex gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs text-muted-foreground font-mono">LIVE FEED</span>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-0">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="bg-muted text-muted-foreground font-mono uppercase text-xs">
                            <th className="px-6 py-4 font-semibold">Product</th>
                            <th className="px-6 py-4 font-semibold">Current Stock</th>
                            <th className="px-6 py-4 font-semibold">Predicted Demand</th>
                            <th className="px-6 py-4 font-semibold">Petpooja Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {gridData.map((item) => (
                            <tr key={item.id} className="hover:bg-muted/50 transition-colors">
                                <td className="px-6 py-4 font-medium text-foreground">{item.product}</td>
                                <td className="px-6 py-4 text-muted-foreground font-mono">{item.stock} Units</td>
                                <td className="px-6 py-4 font-mono text-blue-600 dark:text-blue-400 fw-bold">{item.predicted} Units</td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2">
                                        <span className={`w-1.5 h-1.5 rounded-full ${item.status === 'Synced' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                                        <span className={`text-xs font-medium ${item.status === 'Synced' ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                                            {item.status === 'Synced' ? 'Synced with Petpooja' : 'Sync Pending'}
                                        </span>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </GlassCard>
    );
};

export default InventoryDataGrid;
