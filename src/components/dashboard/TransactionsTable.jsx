
import React, { useState, useRef, useEffect } from 'react';
import { MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react';
import UnifiedCard from '../ui/UnifiedCard';

const TransactionsTable = ({ transactions = [] }) => {
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 5;
    const paginationRef = useRef(null);

    // Use provided transactions or fallback to empty array
    const allTransactions = transactions && transactions.length > 0 ? transactions : [];

    const totalPages = Math.ceil(allTransactions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const currentTransactions = allTransactions.slice(startIndex, startIndex + itemsPerPage);

    // Scroll to pagination controls when page changes
    useEffect(() => {
        if (paginationRef.current) {
            paginationRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }, [currentPage]);

    const getStatusColor = (status) => {
        switch (status) {
            case 'Completed': return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400';
            case 'Pending': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400';
            case 'Failed': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400';
            default: return 'bg-gray-100 text-gray-700';
        }
    };

    return (
        <UnifiedCard className="h-full bg-card/50 flex flex-col shadow-2xl">
            <div className="p-6 flex justify-between items-center">
                <h3 className="font-bold text-card-foreground">Recent Transactions & Status</h3>
                <MoreHorizontal className="text-muted-foreground cursor-pointer hover:text-foreground transition-colors" size={20} />
            </div>

            <div className="flex-1 p-0">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="bg-black/20 text-muted-foreground font-bold text-xs uppercase tracking-wider">
                            <th className="px-6 py-4">Date ↑</th>
                            <th className="px-6 py-4">Transaction ID</th>
                            <th className="px-6 py-4">Customer</th>
                            <th className="px-6 py-4">Amount</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4 text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                        {currentTransactions.map((tx) => (
                            <tr key={tx.id} className="hover:bg-white/5 transition-colors group">
                                <td className="px-6 py-4 text-foreground font-medium">{tx.date}</td>
                                <td className="px-6 py-4 text-muted-foreground font-mono text-xs">{tx.id}</td>
                                <td className="px-6 py-4 text-foreground">{tx.customer}</td>
                                <td className="px-6 py-4 font-bold text-foreground">{tx.amount}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(tx.status)}`}>
                                        {tx.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-center">
                                    <div className="flex items-center justify-center gap-2">
                                        <button className="text-xs text-primary hover:underline font-medium">View</button>
                                        <span className="text-muted-foreground">|</span>
                                        <button className="text-xs text-muted-foreground hover:text-foreground">Invoice</button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {/* Pagination Controls */}
            <div ref={paginationRef} className="p-4 border-t border-border flex justify-end gap-2 text-sm">
                <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="p-1 rounded hover:bg-muted disabled:opacity-50 transition-colors"
                >
                    <ChevronLeft size={16} />
                </button>
                {[...Array(totalPages)].map((_, i) => (
                    <button
                        key={i + 1}
                        onClick={() => setCurrentPage(i + 1)}
                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${currentPage === i + 1
                            ? 'bg-primary text-primary-foreground shadow-md'
                            : 'hover:bg-muted text-muted-foreground hover:text-foreground'
                            }`}
                    >
                        {i + 1}
                    </button>
                ))}
                <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="p-1 rounded hover:bg-muted disabled:opacity-50 transition-colors"
                >
                    <ChevronRight size={16} />
                </button>
            </div>
        </UnifiedCard>
    );
};

export default TransactionsTable;
