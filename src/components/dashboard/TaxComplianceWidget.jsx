
import React from 'react';
import { Download, ShieldCheck } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

const TaxComplianceWidget = () => {
    // Mock data for tax period
    const daysRemaining = 12;
    const totalDays = 30; // Monthly cycle
    const percentage = ((totalDays - daysRemaining) / totalDays) * 100;
    const radius = 36; // Radius of circular progress
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
        <GlassCard className="h-full relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <ShieldCheck size={80} className="text-blue-500" />
            </div>

            <div className="p-5 flex flex-col h-full justify-between relative z-10">
                <div className="flex justify-between items-start mb-2">
                    <div>
                        <h3 className="font-bold text-gray-900 dark:text-white text-lg">Tax-Pay & Compliance</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400">GST Filing Period: Jan 2026</p>
                    </div>
                    {/* Status Badge */}
                    <span className="px-2 py-1 rounded bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 text-xs font-bold border border-yellow-200 dark:border-yellow-700">
                        PENDING
                    </span>
                </div>

                <div className="flex items-center gap-6 my-2">
                    {/* Circular Progress */}
                    <div className="relative w-24 h-24 flex items-center justify-center">
                        <svg className="transform -rotate-90 w-full h-full">
                            <circle
                                cx="50%"
                                cy="50%"
                                r={radius}
                                stroke="currentColor"
                                strokeWidth="8"
                                fill="transparent"
                                className="text-gray-200 dark:text-gray-700"
                            />
                            <circle
                                cx="50%"
                                cy="50%"
                                r={radius}
                                stroke="currentColor"
                                strokeWidth="8"
                                fill="transparent"
                                strokeDasharray={circumference}
                                strokeDashoffset={strokeDashoffset}
                                strokeLinecap="round"
                                className="text-blue-600 dark:text-blue-500 transition-all duration-1000 ease-out"
                            />
                        </svg>
                        <div className="absolute flex flex-col items-center text-center">
                            <span className="text-2xl font-bold text-gray-900 dark:text-white">{daysRemaining}</span>
                            <span className="text-[10px] text-gray-500 font-medium uppercase">Days Left</span>
                        </div>
                    </div>

                    {/* Context Info */}
                    <div className="flex-1">
                        <div className="mb-3">
                            <p className="text-sm text-gray-600 dark:text-gray-300">Total Tax Liability</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white">₹1,24,500</p>
                            <p className="text-xs text-green-500 mt-1 flex items-center gap-1">
                                No penalties applied
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-3 mt-2">
                    <button className="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white py-2 px-4 rounded-lg font-medium shadow-lg hover:shadow-blue-500/25 transition-all text-sm flex items-center justify-center gap-2">
                        <ShieldCheck size={16} />
                        File & Pay Taxes
                    </button>
                    <button className="p-2 text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors" title="Download Tax Report">
                        <Download size={20} />
                    </button>
                </div>
            </div>
        </GlassCard>
    );
};

export default TaxComplianceWidget;
