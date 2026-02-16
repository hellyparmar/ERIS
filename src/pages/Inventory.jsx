/**
 * Enterprise Retail Intelligence System v3.0
 * INVENTORY PAGE - Comprehensive Inventory Management
 * Includes: Product List, Barcode Scanner, Stock Alerts, Reorder Automation, Stock Adjustments
 */

import { useState } from 'react';
import { Package, Scan, AlertTriangle, TrendingUp, Edit } from 'lucide-react';
import UnifiedCard from '../components/ui/UnifiedCard';

// Phase 2 Components
import BarcodeScanner from '../components/inventory/BarcodeScanner';
import StockAlerts from '../components/inventory/StockAlerts';
import ReorderSuggestions from '../components/inventory/ReorderSuggestions';
import StockAdjustment from '../components/inventory/StockAdjustment';

const TABS = [
    { id: 'products', label: 'Product List', icon: Package, color: 'blue' },
    { id: 'scanner', label: 'Barcode Scanner', icon: Scan, color: 'green' },
    { id: 'alerts', label: 'Stock Alerts', icon: AlertTriangle, color: 'red' },
    { id: 'reorder', label: 'Reorder Suggestions', icon: TrendingUp, color: 'purple' },
    { id: 'adjustments', label: 'Stock Adjustments', icon: Edit, color: 'orange' }
];

const Inventory = () => {
    const [activeTab, setActiveTab] = useState('products');
    const [scannedProduct, setScannedProduct] = useState(null);
    const [showScanner, setShowScanner] = useState(false);

    const handleScan = (product) => {
        setScannedProduct(product);
        setShowScanner(false);
        // Could switch to products tab and highlight the scanned product
        setActiveTab('products');
    };

    const renderTabContent = () => {
        switch (activeTab) {
            case 'products':
                return <ProductListTab scannedProduct={scannedProduct} />;
            case 'scanner':
                return (
                    <div className="relative">
                        {showScanner ? (
                            <BarcodeScanner
                                onScan={handleScan}
                                onClose={() => setShowScanner(false)}
                            />
                        ) : (
                            <div className="text-center py-12">
                                <Scan className="w-24 h-24 text-gray-400 mx-auto mb-4" />
                                <h3 className="text-xl font-bold text-gray-800 mb-2">Barcode Scanner</h3>
                                <p className="text-gray-600 mb-6">Scan product barcodes to quickly lookup inventory</p>
                                <button
                                    onClick={() => setShowScanner(true)}
                                    className="px-6 py-3 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 transition-colors"
                                >
                                    Start Scanning
                                </button>
                            </div>
                        )}
                    </div>
                );
            case 'alerts':
                return <StockAlerts />;
            case 'reorder':
                return <ReorderSuggestions />;
            case 'adjustments':
                return <StockAdjustment />;
            default:
                return null;
        }
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-gray-800">Inventory Management</h1>
                <p className="text-gray-600">Comprehensive inventory control and monitoring</p>
            </div>

            {/* Tabs */}
            <UnifiedCard>
                <div className="flex gap-2 border-b border-gray-200 pb-2 overflow-x-auto">
                    {TABS.map(tab => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-all whitespace-nowrap ${isActive
                                        ? `bg-${tab.color}-50 text-${tab.color}-700 border-b-2 border-${tab.color}-500`
                                        : 'text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                <Icon className="w-4 h-4" />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* Tab Content */}
                <div className="mt-6">
                    {renderTabContent()}
                </div>
            </UnifiedCard>
        </div>
    );
};

// Product List Tab (existing inventory table)
const ProductListTab = ({ scannedProduct }) => {
    return (
        <div className="space-y-4">
            {scannedProduct && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-bold text-green-900 mb-2">Recently Scanned</h4>
                    <p className="text-green-700">{scannedProduct.product.name}</p>
                    <p className="text-sm text-green-600">Stock: {scannedProduct.inventory.current_stock} units</p>
                </div>
            )}

            <div className="text-center py-12 bg-gray-50 rounded-lg">
                <Package className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">Product list integration coming soon</p>
                <p className="text-sm text-gray-400">This will show the existing inventory table</p>
            </div>
        </div>
    );
};

export default Inventory;
