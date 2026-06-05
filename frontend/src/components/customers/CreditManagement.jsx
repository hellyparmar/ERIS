import { useState, useEffect } from 'react';
import { CreditCard, AlertCircle, TrendingUp, Users, DollarSign } from 'lucide-react';
import UnifiedCard from '../ui/UnifiedCard';

const CreditManagement = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchCreditStats();
    }, []);

    const fetchCreditStats = async () => {
        setLoading(true);
        try {
            // This endpoint would need to be created in the backend
            // For now, using mock data
            setStats({
                total_credit_issued: 500000,
                total_outstanding: 125000,
                customers_with_credit: 45,
                overdue_customers: 8,
                collection_rate: 75
            });
        } catch (error) {
            console.error('Error fetching credit stats:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Credit Management</h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">Track customer credit limits and payments</p>
            </div>

            {/* Stats Overview */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total Credit</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    ₹{(stats.total_credit_issued / 1000).toFixed(0)}K
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                <CreditCard className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Outstanding</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    ₹{(stats.total_outstanding / 1000).toFixed(0)}K
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
                                <DollarSign className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Customers</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    {stats.customers_with_credit}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                                <Users className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Overdue</p>
                                <p className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                                    {stats.overdue_customers}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center">
                                <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Collection Rate</p>
                                <p className="text-2xl font-bold text-green-600 dark:text-green-400 mt-1">
                                    {stats.collection_rate}%
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                            </div>
                        </div>
                    </UnifiedCard>
                </div>
            )}

            {/* Credit Guidelines */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <UnifiedCard>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Credit Limit Guidelines</h3>
                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
                                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">1</span>
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-900 dark:text-white">New Customers</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Start with ₹5,000 - ₹10,000 credit limit based on initial purchase
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center flex-shrink-0">
                                <span className="text-sm font-bold text-purple-600 dark:text-purple-400">2</span>
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-900 dark:text-white">Regular Customers</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Increase to ₹25,000 - ₹50,000 after 3+ months of good payment history
                                </p>
                            </div>
                        </div>

                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center flex-shrink-0">
                                <span className="text-sm font-bold text-green-600 dark:text-green-400">3</span>
                            </div>
                            <div>
                                <h4 className="font-medium text-gray-900 dark:text-white">VIP Customers</h4>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Offer ₹100,000+ credit limit for high-value, trusted customers
                                </p>
                            </div>
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Payment Terms</h3>
                    <div className="space-y-4">
                        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <h4 className="font-medium text-blue-900 dark:text-blue-300 mb-2">Standard Terms</h4>
                            <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                                <li>• Payment due within 30 days</li>
                                <li>• 2% early payment discount (within 10 days)</li>
                                <li>• Late fee: 2% per month after 30 days</li>
                            </ul>
                        </div>

                        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                            <h4 className="font-medium text-purple-900 dark:text-purple-300 mb-2">VIP Terms</h4>
                            <ul className="space-y-2 text-sm text-purple-800 dark:text-purple-200">
                                <li>• Payment due within 45 days</li>
                                <li>• 3% early payment discount (within 15 days)</li>
                                <li>• No late fees for first 15 days overdue</li>
                            </ul>
                        </div>
                    </div>
                </UnifiedCard>
            </div>

            {/* Overdue Customers Alert */}
            {stats && stats.overdue_customers > 0 && (
                <UnifiedCard>
                    <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900 flex items-center justify-center flex-shrink-0">
                            <AlertCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                                {stats.overdue_customers} Customers with Overdue Payments
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400 mb-4">
                                These customers have outstanding balances exceeding their credit limits. Follow up required.
                            </p>
                            <button className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors">
                                View Overdue Customers
                            </button>
                        </div>
                    </div>
                </UnifiedCard>
            )}

            {/* Quick Actions */}
            <UnifiedCard>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button className="flex items-center justify-center gap-2 px-4 py-3 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors">
                        <CreditCard className="w-5 h-5" />
                        Assign Credit Limit
                    </button>
                    <button className="flex items-center justify-center gap-2 px-4 py-3 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors">
                        <DollarSign className="w-5 h-5" />
                        Record Payment
                    </button>
                    <button className="flex items-center justify-center gap-2 px-4 py-3 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-200 dark:hover:bg-purple-800 transition-colors">
                        <TrendingUp className="w-5 h-5" />
                        View Reports
                    </button>
                </div>
            </UnifiedCard>
        </div>
    );
};

export default CreditManagement;
