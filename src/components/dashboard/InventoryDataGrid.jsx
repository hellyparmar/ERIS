
import React from 'react';
import { MoreHorizontal } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

const InventoryDataGrid = () => {
    const data = [
        { id: 1, product: "Nike Air Max 270", stock: 142, predicted: 165, status: "Synced" },
        { id: 2, product: "Adidas Ultraboost", stock: 89, predicted: 120, status: "Synced" },
        { id: 3, product: "Puma RS-X", stock: 45, predicted: 80, status: "Pending" },
        { id: 4, product: "Reebok Classic", stock: 210, predicted: 190, status: "Synced" },
        { id: 5, product: "New Balance 574", stock: 34, predicted: 65, status: "Synced" },
        { id: 6, product: "Asics Gel-Kayano", stock: 78, predicted: 95, status: "Synced" },
        { id: 7, product: "Vans Old Skool", stock: 156, predicted: 150, status: "Pending" },
    ];

    return (
        <GlassCard className="h-full bg-white dark:bg-gray-900/50 border-gray-200 dark:border-gray-800 flex flex-col">
            <div className="p-6 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
                <h3 className="font-bold text-gray-900 dark:text-white">Inventory Data Grid</h3>
                <div className="flex gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-xs text-gray-500 font-mono">LIVE FEED</span>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-0">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="bg-gray-50 dark:bg-black/20 text-gray-500 dark:text-gray-400 font-mono uppercase text-xs">
                            <th className="px-6 py-4 font-semibold">Product</th>
                            <th className="px-6 py-4 font-semibold">Current Stock</th>
                            <th className="px-6 py-4 font-semibold">Predicted Demand</th>
                            <th className="px-6 py-4 font-semibold">Petpooja Status</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                        {data.map((item) => (
                            <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                                <td className="px-6 py-4 font-medium text-gray-900 dark:text-gray-200">{item.product}</td>
                                <td className="px-6 py-4 text-gray-600 dark:text-gray-400 font-mono">{item.stock} Units</td>
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
