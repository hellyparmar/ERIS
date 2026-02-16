import { useState, useEffect } from 'react';
import { Users, Award, CreditCard, TrendingUp } from 'lucide-react';
import CustomerList from '../components/customers/CustomerList';
import UnifiedCard from '../components/ui/UnifiedCard';

const Customers = () => {
    const [activeTab, setActiveTab] = useState('list');
    const [stats, setStats] = useState(null);

    const fetchStats = async () => {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/customers/stats`);
            const data = await response.json();

            if (data.success) {
                setStats(data.data);
            }
        } catch (error) {
            console.error('Error fetching customer stats:', error);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    const tabs = [
        { id: 'list', label: 'Customer List', icon: Users },
        { id: 'loyalty', label: 'Loyalty Program', icon: Award },
        { id: 'credit', label: 'Credit Management', icon: CreditCard },
        { id: 'analytics', label: 'Analytics', icon: TrendingUp }
    ];

    return (
        <div className="p-6 space-y-6">
            {/* Stats Overview */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total Customers</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    {stats.total_customers.toLocaleString()}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">VIP Customers</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    {stats.vip_customers.toLocaleString()}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center">
                                <Award className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Total LTV</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    ₹{(stats.total_lifetime_value / 1000).toFixed(1)}K
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                                <TrendingUp className="w-6 h-6 text-green-600 dark:text-green-400" />
                            </div>
                        </div>
                    </UnifiedCard>

                    <UnifiedCard>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-600 dark:text-gray-400">Avg LTV</p>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                                    ₹{stats.average_lifetime_value.toLocaleString()}
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
                                <CreditCard className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                            </div>
                        </div>
                    </UnifiedCard>
                </div>
            )}

            {/* Tabs */}
            <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex space-x-8">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === tab.id
                                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                {tab.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Tab Content */}
            <div className="mt-6">
                {activeTab === 'list' && <CustomerList />}
                {activeTab === 'loyalty' && (
                    <UnifiedCard>
                        <div className="text-center py-12">
                            <Award className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                Loyalty Program Dashboard
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Loyalty program management coming soon
                            </p>
                        </div>
                    </UnifiedCard>
                )}
                {activeTab === 'credit' && (
                    <UnifiedCard>
                        <div className="text-center py-12">
                            <CreditCard className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                Credit Management
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Credit management dashboard coming soon
                            </p>
                        </div>
                    </UnifiedCard>
                )}
                {activeTab === 'analytics' && (
                    <UnifiedCard>
                        <div className="text-center py-12">
                            <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                                Customer Analytics
                            </h3>
                            <p className="text-gray-600 dark:text-gray-400">
                                Advanced analytics coming soon
                            </p>
                        </div>
                    </UnifiedCard>
                )}
            </div>
        </div>
    );
};

export default Customers;
