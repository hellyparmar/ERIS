import { useState, useEffect } from 'react';
import { Package, Plus, Minus, Edit, History } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const ADJUSTMENT_TYPES = [
    { value: 'add', label: 'Add Stock', icon: Plus, color: 'green' },
    { value: 'remove', label: 'Remove Stock', icon: Minus, color: 'red' },
    { value: 'set', label: 'Set Stock', icon: Edit, color: 'blue' }
];

const REASONS = [
    { value: 'damage', label: 'Damage' },
    { value: 'theft', label: 'Theft' },
    { value: 'expiry', label: 'Expiry' },
    { value: 'recount', label: 'Physical Recount' },
    { value: 'supplier_return', label: 'Supplier Return' },
    { value: 'customer_return', label: 'Customer Return' },
    { value: 'transfer_in', label: 'Transfer In' },
    { value: 'transfer_out', label: 'Transfer Out' },
    { value: 'other', label: 'Other' }
];

export default function StockAdjustment() {
    const [products, setProducts] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [adjustmentType, setAdjustmentType] = useState('add');
    const [quantity, setQuantity] = useState('');
    const [reason, setReason] = useState('recount');
    const [notes, setNotes] = useState('');
    const [history, setHistory] = useState([]);
    const [showHistory, setShowHistory] = useState(false);
    const [loading, setLoading] = useState(false);

    // Fetch products
    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            const response = await fetch(`${API_BASE}/products`);
            const data = await response.json();
            if (data.success) {
                setProducts(data.data);
            }
        } catch (error) {
            console.error('Failed to fetch products:', error);
        }
    };

    // Fetch adjustment history
    const fetchHistory = async (productId = null) => {
        try {
            const url = productId
                ? `${API_BASE}/inventory/adjustments?product_id=${productId}&limit=10`
                : `${API_BASE}/inventory/adjustments?limit=20`;

            const response = await fetch(url);
            const data = await response.json();
            if (data.success) {
                setHistory(data.data.adjustments);
            }
        } catch (error) {
            console.error('Failed to fetch history:', error);
        }
    };

    // Submit adjustment
    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!selectedProduct || !quantity) {
            alert('Please select a product and enter quantity');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`${API_BASE}/inventory/adjust`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: selectedProduct.id,
                    adjustment_type: adjustmentType,
                    quantity: parseInt(quantity),
                    reason,
                    notes,
                    user_id: 1 // TODO: Get from auth context
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`Stock adjusted successfully! New level: ${data.data.new_stock_level} units`);
                // Reset form
                setQuantity('');
                setNotes('');
                fetchHistory(selectedProduct.id);
            } else {
                alert(`Error: ${data.error || 'Failed to adjust stock'}`);
            }
        } catch (error) {
            console.error('Failed to adjust stock:', error);
            alert('Failed to adjust stock');
        } finally {
            setLoading(false);
        }
    };

    const selectedType = ADJUSTMENT_TYPES.find(t => t.value === adjustmentType);

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold text-gray-800">Stock Adjustment</h2>
                    <p className="text-gray-600">Record manual stock changes with audit trail</p>
                </div>

                <button
                    onClick={() => {
                        setShowHistory(!showHistory);
                        if (!showHistory) fetchHistory();
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                    <History className="w-4 h-4" />
                    {showHistory ? 'Hide History' : 'View History'}
                </button>
            </div>

            {/* Adjustment Form */}
            {!showHistory && (
                <form onSubmit={handleSubmit} className="bg-white border-2 border-gray-200 rounded-lg p-6 space-y-6">
                    {/* Product Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Product</label>
                        <select
                            value={selectedProduct?.id || ''}
                            onChange={(e) => {
                                const product = products.find(p => p.id === parseInt(e.target.value));
                                setSelectedProduct(product);
                            }}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        >
                            <option value="">Select a product...</option>
                            {products.map(product => (
                                <option key={product.id} value={product.id}>
                                    {product.name} (Current: {product.current_stock || 0} units)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Adjustment Type */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Adjustment Type</label>
                        <div className="grid grid-cols-3 gap-3">
                            {ADJUSTMENT_TYPES.map(type => {
                                const Icon = type.icon;
                                const isSelected = adjustmentType === type.value;
                                return (
                                    <button
                                        key={type.value}
                                        type="button"
                                        onClick={() => setAdjustmentType(type.value)}
                                        className={`p-4 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${isSelected
                                                ? `border-${type.color}-500 bg-${type.color}-50`
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <Icon className={`w-6 h-6 ${isSelected ? `text-${type.color}-600` : 'text-gray-400'}`} />
                                        <span className={`text-sm font-medium ${isSelected ? `text-${type.color}-700` : 'text-gray-600'}`}>
                                            {type.label}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Quantity */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            {adjustmentType === 'set' ? 'New Stock Level' : 'Quantity'}
                        </label>
                        <input
                            type="number"
                            value={quantity}
                            onChange={(e) => setQuantity(e.target.value)}
                            min="0"
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder={adjustmentType === 'set' ? 'Enter new stock level' : 'Enter quantity'}
                            required
                        />
                    </div>

                    {/* Reason */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Reason</label>
                        <select
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        >
                            {REASONS.map(r => (
                                <option key={r.value} value={r.value}>{r.label}</option>
                            ))}
                        </select>
                    </div>

                    {/* Notes */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">Notes (Optional)</label>
                        <textarea
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            rows={3}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Add any additional details..."
                        />
                    </div>

                    {/* Preview */}
                    {selectedProduct && quantity && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="font-medium text-blue-900 mb-2">Preview</h4>
                            <div className="text-sm text-blue-700 space-y-1">
                                <p>Product: <strong>{selectedProduct.name}</strong></p>
                                <p>Current Stock: <strong>{selectedProduct.current_stock || 0} units</strong></p>
                                <p>
                                    New Stock: <strong>
                                        {adjustmentType === 'add' && (selectedProduct.current_stock || 0) + parseInt(quantity)}
                                        {adjustmentType === 'remove' && Math.max(0, (selectedProduct.current_stock || 0) - parseInt(quantity))}
                                        {adjustmentType === 'set' && parseInt(quantity)}
                                    </strong> units
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={loading || !selectedProduct || !quantity}
                        className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                    >
                        {loading ? 'Submitting...' : 'Submit Adjustment'}
                    </button>
                </form>
            )}

            {/* History View */}
            {showHistory && (
                <div className="space-y-3">
                    {history.length === 0 ? (
                        <div className="text-center py-12 bg-gray-50 rounded-lg">
                            <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-600">No adjustment history</p>
                        </div>
                    ) : (
                        history.map(adj => (
                            <div key={adj.id} className="bg-white border border-gray-200 rounded-lg p-4">
                                <div className="flex justify-between items-start mb-2">
                                    <div>
                                        <h4 className="font-bold text-gray-800">{adj.product_name}</h4>
                                        <p className="text-sm text-gray-600">{adj.category}</p>
                                    </div>
                                    <span className={`px-2 py-1 text-xs font-semibold rounded ${adj.adjustment_type === 'add' ? 'bg-green-100 text-green-700' :
                                            adj.adjustment_type === 'remove' ? 'bg-red-100 text-red-700' :
                                                'bg-blue-100 text-blue-700'
                                        }`}>
                                        {adj.adjustment_type.toUpperCase()}
                                    </span>
                                </div>

                                <div className="grid grid-cols-3 gap-4 mb-2">
                                    <div>
                                        <div className="text-xs text-gray-500">Before</div>
                                        <div className="font-bold text-gray-800">{adj.quantity_before}</div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">Change</div>
                                        <div className={`font-bold ${adj.quantity_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                            {adj.quantity_change > 0 ? '+' : ''}{adj.quantity_change}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-xs text-gray-500">After</div>
                                        <div className="font-bold text-gray-800">{adj.quantity_after}</div>
                                    </div>
                                </div>

                                <div className="text-sm text-gray-600">
                                    <p><strong>Reason:</strong> {adj.reason.replace('_', ' ')}</p>
                                    {adj.notes && <p><strong>Notes:</strong> {adj.notes}</p>}
                                    <p className="text-xs text-gray-400 mt-1">
                                        {new Date(adj.created_at).toLocaleString()} • User ID: {adj.user_id}
                                    </p>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}
