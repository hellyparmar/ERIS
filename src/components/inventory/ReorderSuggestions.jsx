import { useState, useEffect } from 'react';
import { TrendingUp, Package, DollarSign, AlertCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ReorderSuggestions() {
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [minConfidence, setMinConfidence] = useState(50);

    // Fetch suggestions
    const fetchSuggestions = async () => {
        try {
            const response = await fetch(
                `${API_BASE}/inventory/reorder-suggestions?min_confidence=${minConfidence}&limit=20`
            );
            const data = await response.json();

            if (data.success) {
                setSuggestions(data.data.suggestions);
            }
        } catch (error) {
            console.error('Failed to fetch reorder suggestions:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSuggestions();
    }, [minConfidence]);

    // Get confidence badge color
    const getConfidenceBadge = (score) => {
        if (score >= 80) return { bg: 'bg-green-100', text: 'text-green-700', label: 'High' };
        if (score >= 60) return { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Medium' };
        return { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Low' };
    };

    // Get urgency badge color
    const getUrgencyBadge = (score) => {
        if (score >= 75) return { bg: 'bg-red-100', text: 'text-red-700', label: 'Urgent' };
        if (score >= 50) return { bg: 'bg-orange-100', text: 'text-orange-700', label: 'High' };
        return { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Medium' };
    };

    if (loading) {
        return <div className="p-6 text-center text-gray-600">Loading suggestions...</div>;
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">Reorder Suggestions</h2>
                    <p className="text-gray-600">AI-driven recommendations based on sales velocity</p>
                </div>

                {/* Confidence Filter */}
                <div className="flex items-center gap-3">
                    <label className="text-sm font-medium text-gray-700">Min Confidence:</label>
                    <select
                        value={minConfidence}
                        onChange={(e) => setMinConfidence(Number(e.target.value))}
                        className="px-3 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value={0}>All (0%)</option>
                        <option value={50}>Medium (50%)</option>
                        <option value={70}>High (70%)</option>
                        <option value={90}>Very High (90%)</option>
                    </select>
                </div>
            </div>

            {/* Suggestions List */}
            <div className="space-y-4">
                {suggestions.length === 0 ? (
                    <div className="text-center py-12 bg-gray-50 rounded-lg">
                        <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">No reorder suggestions</p>
                        <p className="text-sm text-gray-400">All stock levels are healthy or confidence too low</p>
                    </div>
                ) : (
                    suggestions.map((suggestion) => {
                        const confidenceBadge = getConfidenceBadge(suggestion.confidence_score);
                        const urgencyBadge = getUrgencyBadge(suggestion.urgency_score);

                        return (
                            <div
                                key={suggestion.product_id}
                                className="bg-white border-2 border-gray-200 rounded-lg p-5 hover:border-blue-300 transition-colors"
                            >
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-lg font-bold text-gray-800">{suggestion.product_name}</h3>
                                            <span className={`px-2 py-1 text-xs font-semibold rounded ${urgencyBadge.bg} ${urgencyBadge.text}`}>
                                                {urgencyBadge.label}
                                            </span>
                                            <span className={`px-2 py-1 text-xs font-semibold rounded ${confidenceBadge.bg} ${confidenceBadge.text}`}>
                                                {confidenceBadge.label} Confidence
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600 mb-3">{suggestion.category}</p>
                                    </div>

                                    <div className="text-right">
                                        <div className="text-2xl font-bold text-blue-600">
                                            {suggestion.suggested_quantity}
                                        </div>
                                        <div className="text-xs text-gray-500">units</div>
                                    </div>
                                </div>

                                {/* Stats Grid */}
                                <div className="grid grid-cols-4 gap-4 mb-4">
                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <div className="text-xs text-gray-500 mb-1">Current Stock</div>
                                        <div className="text-lg font-bold text-gray-800">{suggestion.current_stock}</div>
                                    </div>

                                    <div className="bg-gray-50 rounded-lg p-3">
                                        <div className="text-xs text-gray-500 mb-1">Reorder Point</div>
                                        <div className="text-lg font-bold text-gray-800">{suggestion.reorder_point}</div>
                                    </div>

                                    <div className="bg-blue-50 rounded-lg p-3">
                                        <div className="text-xs text-blue-600 mb-1 flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3" />
                                            7-Day Sales
                                        </div>
                                        <div className="text-lg font-bold text-blue-700">{suggestion.daily_sales_7d}/day</div>
                                    </div>

                                    <div className="bg-green-50 rounded-lg p-3">
                                        <div className="text-xs text-green-600 mb-1 flex items-center gap-1">
                                            <DollarSign className="w-3 h-3" />
                                            Est. Cost
                                        </div>
                                        <div className="text-lg font-bold text-green-700">₹{suggestion.estimated_cost.toFixed(0)}</div>
                                    </div>
                                </div>

                                {/* Reasoning */}
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                                    <div className="flex items-start gap-2">
                                        <AlertCircle className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                        <div className="text-sm text-blue-700">{suggestion.reasoning}</div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-3">
                                    <button className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 transition-colors">
                                        Create Purchase Order
                                    </button>
                                    <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors">
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
