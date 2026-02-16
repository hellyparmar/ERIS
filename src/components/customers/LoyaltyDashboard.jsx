import { useState, useEffect } from 'react';
import { Award, TrendingUp, Gift, Clock, ChevronRight } from 'lucide-react';
import UnifiedCard from '../ui/UnifiedCard';

const LoyaltyDashboard = () => {
    const [tiers, setTiers] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchTierInfo();
    }, []);

    const fetchTierInfo = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/loyalty/tiers`);
            const data = await response.json();

            if (data.success) {
                setTiers(data.data);
            }
        } catch (error) {
            console.error('Error fetching tier info:', error);
        } finally {
            setLoading(false);
        }
    };

    const getTierColor = (tier) => {
        const colors = {
            Platinum: 'from-gray-400 to-gray-600',
            Gold: 'from-yellow-400 to-yellow-600',
            Silver: 'from-gray-300 to-gray-500',
            Bronze: 'from-orange-400 to-orange-600'
        };
        return colors[tier] || 'from-gray-400 to-gray-600';
    };

    const getTierIcon = (tier) => {
        return <Award className="w-8 h-8" />;
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
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Loyalty Program</h2>
                <p className="text-gray-600 dark:text-gray-400 mt-1">Reward your customers with tier-based benefits</p>
            </div>

            {/* Program Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <UnifiedCard>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Points Rate</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">1 pt / ₹10</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Earn on every purchase</p>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                            <TrendingUp className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Redemption Value</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">₹0.10 / pt</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Redeem for discounts</p>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                            <Gift className="w-6 h-6 text-green-600 dark:text-green-400" />
                        </div>
                    </div>
                </UnifiedCard>

                <UnifiedCard>
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm text-gray-600 dark:text-gray-400">Points Expiry</p>
                            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">365 Days</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">From earn date</p>
                        </div>
                        <div className="w-12 h-12 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center">
                            <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                        </div>
                    </div>
                </UnifiedCard>
            </div>

            {/* Tier Benefits */}
            {tiers && (
                <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Loyalty Tiers</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {Object.entries(tiers).map(([tierName, tierData]) => (
                            <UnifiedCard key={tierName}>
                                <div className="space-y-4">
                                    {/* Tier Header */}
                                    <div className="flex items-center justify-between">
                                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r ${getTierColor(tierName)} text-white`}>
                                            {getTierIcon(tierName)}
                                            <span className="font-bold">{tierName}</span>
                                        </div>
                                    </div>

                                    {/* Points Required */}
                                    <div>
                                        <p className="text-sm text-gray-600 dark:text-gray-400">Points Required</p>
                                        <p className="text-2xl font-bold text-gray-900 dark:text-white">
                                            {tierData.points_required.toLocaleString()}+
                                        </p>
                                    </div>

                                    {/* Benefits */}
                                    <div>
                                        <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Benefits:</p>
                                        <ul className="space-y-2">
                                            {tierData.benefits.map((benefit, index) => (
                                                <li key={index} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                                                    <ChevronRight className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                                                    <span>{benefit}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </UnifiedCard>
                        ))}
                    </div>
                </div>
            )}

            {/* How It Works */}
            <UnifiedCard>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">How It Works</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">1</span>
                        </div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Earn Points</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Customers earn 1 point for every ₹10 spent on purchases
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">2</span>
                        </div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Tier Upgrade</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Automatically upgrade to higher tiers as points accumulate
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl font-bold text-green-600 dark:text-green-400">3</span>
                        </div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Redeem Rewards</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Redeem points for discounts (1 point = ₹0.10)
                        </p>
                    </div>
                </div>
            </UnifiedCard>
        </div>
    );
};

export default LoyaltyDashboard;
