import { useState } from 'react';
import { Search, UserPlus, Filter, Users, Award, CreditCard } from 'lucide-react';
import UnifiedCard from '../ui/UnifiedCard';

const CustomerList = () => {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
        search: '',
        segment: '',
        tier: ''
    });
    const [pagination, setPagination] = useState({
        page: 1,
        per_page: 20,
        total: 0,
        total_pages: 0
    });

    const fetchCustomers = async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams({
                page: pagination.page,
                per_page: pagination.per_page,
                ...(filters.search && { search: filters.search }),
                ...(filters.segment && { segment: filters.segment }),
                ...(filters.tier && { tier: filters.tier })
            });

            const response = await fetch(`${import.meta.env.VITE_API_URL}/customers?${params}`);
            const data = await response.json();

            if (data.success) {
                setCustomers(data.data.customers);
                setPagination(prev => ({
                    ...prev,
                    total: data.data.total,
                    total_pages: data.data.total_pages
                }));
            }
        } catch (error) {
            console.error('Error fetching customers:', error);
        } finally {
            setLoading(false);
        }
    };

    const getSegmentBadge = (segment) => {
        const colors = {
            VIP: 'bg-purple-100 text-purple-800',
            Regular: 'bg-blue-100 text-blue-800',
            New: 'bg-green-100 text-green-800'
        };
        return colors[segment] || 'bg-gray-100 text-gray-800';
    };

    const getTierBadge = (tier) => {
        const colors = {
            Platinum: 'bg-gradient-to-r from-gray-400 to-gray-600 text-white',
            Gold: 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white',
            Silver: 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800',
            Bronze: 'bg-gradient-to-r from-orange-400 to-orange-600 text-white'
        };
        return colors[tier] || 'bg-gray-100 text-gray-800';
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Customers</h2>
                    <p className="text-gray-600 dark:text-gray-400 mt-1">Manage customer profiles and relationships</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                    <UserPlus className="w-5 h-5" />
                    Add Customer
                </button>
            </div>

            {/* Filters */}
            <UnifiedCard>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                            type="text"
                            placeholder="Search customers..."
                            value={filters.search}
                            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        />
                    </div>

                    <select
                        value={filters.segment}
                        onChange={(e) => setFilters({ ...filters, segment: e.target.value })}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                        <option value="">All Segments</option>
                        <option value="VIP">VIP</option>
                        <option value="Regular">Regular</option>
                        <option value="New">New</option>
                    </select>

                    <select
                        value={filters.tier}
                        onChange={(e) => setFilters({ ...filters, tier: e.target.value })}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                        <option value="">All Tiers</option>
                        <option value="Platinum">Platinum</option>
                        <option value="Gold">Gold</option>
                        <option value="Silver">Silver</option>
                        <option value="Bronze">Bronze</option>
                    </select>

                    <button
                        onClick={fetchCustomers}
                        className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                    >
                        <Filter className="w-5 h-5" />
                        Apply Filters
                    </button>
                </div>
            </UnifiedCard>

            {/* Customer Table */}
            <UnifiedCard>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-200 dark:border-gray-700">
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Customer
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Contact
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Segment
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Loyalty Tier
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Lifetime Value
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {loading ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                                        Loading customers...
                                    </td>
                                </tr>
                            ) : customers.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                                        No customers found
                                    </td>
                                </tr>
                            ) : (
                                customers.map((customer) => (
                                    <tr key={customer.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                                                    <Users className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                                </div>
                                                <div>
                                                    <div className="font-medium text-gray-900 dark:text-white">{customer.name}</div>
                                                    <div className="text-sm text-gray-500 dark:text-gray-400">
                                                        {customer.total_purchases} purchases
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 dark:text-white">{customer.phone}</div>
                                            {customer.email && (
                                                <div className="text-sm text-gray-500 dark:text-gray-400">{customer.email}</div>
                                            )}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getSegmentBadge(customer.segment)}`}>
                                                {customer.segment}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2">
                                                <Award className="w-4 h-4" />
                                                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getTierBadge(customer.loyalty_tier)}`}>
                                                    {customer.loyalty_tier}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                                                ₹{customer.lifetime_value.toLocaleString()}
                                            </div>
                                            <div className="text-xs text-gray-500 dark:text-gray-400">
                                                {customer.loyalty_points} points
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm font-medium">
                                                View Details
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {pagination.total_pages > 1 && (
                    <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="text-sm text-gray-700 dark:text-gray-300">
                            Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} customers
                        </div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
                                disabled={pagination.page === 1}
                                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Previous
                            </button>
                            <button
                                onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
                                disabled={pagination.page === pagination.total_pages}
                                className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                            >
                                Next
                            </button>
                        </div>
                    </div>
                )}
            </UnifiedCard>
        </div>
    );
};

export default CustomerList;
