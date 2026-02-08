/**
 * Enterprise Retail Intelligence System v3.0
 * INVENTORY PAGE - Real-time Product Management
 * Refactored with Enterprise Design System
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Plus, Download, Upload, Edit2, Trash2 } from 'lucide-react';
import UnifiedCard from '../components/ui/UnifiedCard';
import UnifiedTable from '../components/ui/UnifiedTable';
import ActionButton from '../components/ui/ActionButton';
import { useToast } from '../components/ui/Toast';

const Inventory = () => {
    const { addToast } = useToast();
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [stockFilter, setStockFilter] = useState('all');
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 7;

    // Fetch inventory from API
    useEffect(() => {
        fetchInventory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [refreshTrigger]);

    const fetchInventory = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:8000/api/v1/inventory/list');
            const data = await response.json();
            if (data.success && data.data.items) {
                // Transform API data to match component expectations
                const transformed = data.data.items.map(item => ({
                    id: item.id,
                    sku: item.sku,
                    name: item.name,
                    category: item.category,
                    stock: item.current_stock,
                    minStock: item.reorder_point,
                    price: parseFloat(item.unit_price),
                    status: item.stock_status,
                    location: item.warehouse_location || 'Main Warehouse'
                }));
                setProducts(transformed);
            }
        } catch (error) {
            console.error('Failed to fetch inventory:', error);
            addToast('Failed to load inventory', 'error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (productId) => {
        if (!window.confirm('Are you sure you want to delete this product?')) return;

        try {
            const response = await fetch(`http://localhost:8000/api/v1/inventory/delete/${productId}`, {
                method: 'DELETE'
            });
            const data = await response.json();

            if (data.success) {
                addToast('Product deleted successfully', 'success');
                setRefreshTrigger(prev => prev + 1);
            } else {
                addToast(data.error || 'Failed to delete product', 'error');
            }
        } catch (error) {
            console.error('Delete failed:', error);
            addToast('Failed to delete product', 'error');
        }
    };

    const categories = ['all', 'Raw Materials', 'Beverages', 'Frozen Food', 'Packaging', 'Condiments', 'Supplies'];

    // Filter and search logic
    const filteredProducts = products.filter(product => {
        const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            product.sku.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
        const matchesStock = stockFilter === 'all' ||
            (stockFilter === 'low' && product.status === 'low_stock') ||
            (stockFilter === 'out' && product.status === 'out_of_stock') ||
            (stockFilter === 'in' && product.status === 'in_stock');

        return matchesSearch && matchesCategory && matchesStock;
    });

    // Pagination logic
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    const paginatedProducts = filteredProducts.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    );

    // Reset to page 1 when filters change
    useEffect(() => {
        setCurrentPage(1);
    }, [searchTerm, selectedCategory, stockFilter]);

    const getStockBadge = (product) => {
        if (product.status === 'out_of_stock') {
            return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-destructive/10 text-destructive border border-destructive/20">
                <span className="w-2 h-2 rounded-full bg-destructive" />
                Out of Stock
            </span>;
        } else if (product.status === 'low_stock') {
            return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-600 dark:text-yellow-500 border border-yellow-500/20">
                <span className="w-2 h-2 rounded-full bg-yellow-500" />
                Low Stock
            </span>;
        }
        return <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-green-500/10 text-green-600 dark:text-green-500 border border-green-500/20">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            In Stock
        </span>;
    };

    // Table columns configuration
    const columns = [
        {
            header: 'SKU',
            accessor: 'sku',
            render: (value) => (
                <span className="font-mono text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
                    {value}
                </span>
            )
        },
        {
            header: 'Product',
            accessor: 'name',
            render: (value) => <span className="font-semibold text-foreground">{value}</span>
        },
        {
            header: 'Category',
            accessor: 'category'
        },
        {
            header: 'Stock',
            accessor: 'stock',
            render: (value, row) => {
                const stockPercentage = (row.stock / row.minStock) * 100;
                return (
                    <div className="flex flex-col items-end gap-1 min-w-0">
                        <span className={`text-lg font-bold ${row.stock === 0 ? 'text-destructive' :
                            row.stock < row.minStock ? 'text-yellow-600 dark:text-yellow-500' :
                                'text-green-600 dark:text-green-500'
                            }`}>
                            {row.stock}
                        </span>
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                                className={`h-full transition-all ${stockPercentage >= 100 ? 'bg-green-500' :
                                    stockPercentage > 50 ? 'bg-yellow-500' :
                                        'bg-destructive'
                                    }`}
                                style={{ width: `${Math.min(stockPercentage, 100)}%` }}
                            />
                        </div>
                        <span className="text-xs text-muted-foreground">Min: {row.minStock}</span>
                    </div>
                );
            }
        },
        {
            header: 'Status',
            accessor: 'status',
            render: (value, row) => getStockBadge(row)
        },
        {
            header: 'Price',
            accessor: 'price',
            render: (value) => (
                <span className="font-bold text-foreground">
                    ₹{value.toLocaleString()}
                </span>
            )
        },
        {
            header: 'Location',
            accessor: 'location'
        },
        {
            header: 'Actions',
            accessor: 'id',
            render: (value, row) => (
                <div className="flex justify-center gap-2">
                    <button
                        className="px-3 py-1 text-xs border border-border rounded hover:bg-secondary transition-colors text-foreground"
                        onClick={() => console.log('Edit', row)}
                    >
                        Edit
                    </button>
                    <button
                        className="px-3 py-1 text-xs border border-transparent text-red-500 hover:border-red-500 hover:bg-red-500/10 rounded transition-all"
                        onClick={() => handleDelete(row.id)}
                    >
                        Delete
                    </button>
                </div>
            )
        }
    ];

    return (
        <div className="min-h-screen space-y-6">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">
                    Inventory Management
                </h1>
                <p className="text-muted-foreground">Real-time stock tracking and optimization</p>
            </motion.div>

            {/* Search & Filters */}
            <UnifiedCard>
                <div className="space-y-4">
                    {/* Search Bar */}
                    <div className="flex gap-4 items-stretch flex-wrap">
                        <div className="flex-1 min-w-[300px] relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" size={20} />
                            <input
                                type="text"
                                placeholder="Search by product name or SKU..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 bg-background border border-input rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
                            />
                        </div>
                        <ActionButton variant="primary" icon={Plus} className="whitespace-nowrap bg-blue-600 hover:bg-blue-700 text-white">
                            Add Product
                        </ActionButton>
                    </div>

                    {/* Filters */}
                    <div className="flex flex-wrap gap-4">
                        <div className="flex-1 min-w-[200px]">
                            <label className="text-muted-foreground text-sm mb-2 block">Category</label>
                            <select
                                value={selectedCategory}
                                onChange={(e) => setSelectedCategory(e.target.value)}
                                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
                            >
                                {categories.map(cat => (
                                    <option key={cat} value={cat} className="bg-background">
                                        {cat === 'all' ? 'All Categories' : cat}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex-1 min-w-[200px]">
                            <label className="text-muted-foreground text-sm mb-2 block">Stock Level</label>
                            <select
                                value={stockFilter}
                                onChange={(e) => setStockFilter(e.target.value)}
                                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-ring transition"
                            >
                                <option value="all" className="bg-background">All Stock Levels</option>
                                <option value="in" className="bg-background">In Stock</option>
                                <option value="low" className="bg-background">Low Stock</option>
                                <option value="out" className="bg-background">Out of Stock</option>
                            </select>
                        </div>
                    </div>

                    {/* Bulk Actions */}
                    <div className="flex gap-2 flex-wrap">
                        <ActionButton variant="secondary" icon={Download}>
                            Export CSV
                        </ActionButton>
                        <ActionButton variant="secondary" icon={Upload}>
                            Import CSV
                        </ActionButton>
                    </div>
                </div>
            </UnifiedCard>

            {/* Results Count */}
            <div className="text-muted-foreground text-sm">
                Showing {paginatedProducts.length} of {filteredProducts.length} products (Page {currentPage} of {Math.max(1, totalPages)})
            </div>

            {/* Product Table with Fixed 7 Rows */}
            <UnifiedCard title="Product Inventory">
                <div className="w-full">
                    <UnifiedTable
                        columns={columns}
                        data={paginatedProducts}
                        emptyMessage="No products found. Try adjusting your filters."
                    />

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-center gap-2 mt-6 pb-4">
                            <button
                                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                disabled={currentPage === 1}
                                className="p-2 rounded hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                aria-label="Previous page"
                            >
                                ← Prev
                            </button>

                            {[...Array(totalPages)].map((_, i) => (
                                <button
                                    key={i + 1}
                                    onClick={() => setCurrentPage(i + 1)}
                                    className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
                                        currentPage === i + 1
                                            ? 'bg-primary text-primary-foreground shadow-md'
                                            : 'hover:bg-secondary text-foreground'
                                    }`}
                                >
                                    {i + 1}
                                </button>
                            ))}

                            <button
                                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                disabled={currentPage === totalPages}
                                className="p-2 rounded hover:bg-secondary disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                aria-label="Next page"
                            >
                                Next →
                            </button>
                        </div>
                    )}
                </div>
            </UnifiedCard>
        </div>
    );
};

export default Inventory;
