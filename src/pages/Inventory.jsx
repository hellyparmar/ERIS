/**
 * Enterprise Retail Intelligence System v3.0
 * INVENTORY PAGE - Real-time Product Management
 */

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Search, Filter, Grid, List, Plus, Download, Upload } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import '../modern-design.css';

const Inventory = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [stockFilter, setStockFilter] = useState('all');
    const [viewMode, setViewMode] = useState('table');
    const [sortBy, setSortBy] = useState('name');

    // Mock product data (Petpooja F&B Context)
    const [products] = useState([
        { id: 1, sku: 'ING001', name: 'Fresh Paneer (Malai)', category: 'Raw Materials', stock: 15, minStock: 20, price: 320, status: 'low_stock', location: 'Fridge A' },
        { id: 2, sku: 'ING002', name: 'Basmati Rice (Premium)', category: 'Raw Materials', stock: 120, minStock: 50, price: 85, status: 'in_stock', location: 'Store Room B' },
        { id: 3, sku: 'BEV001', name: 'Coca Cola 300ml', category: 'Beverages', stock: 240, minStock: 100, price: 40, status: 'in_stock', location: 'Fridge C' },
        { id: 4, sku: 'PKG001', name: 'Burger Box (Large)', category: 'Packaging', stock: 0, minStock: 200, price: 12, status: 'out_of_stock', location: 'Shelf D-1' },
        { id: 5, sku: 'FRZ001', name: 'McCain French Fries', category: 'Frozen Food', stock: 45, minStock: 30, price: 210, status: 'in_stock', location: 'Freezer 1' },
        { id: 6, sku: 'CON001', name: 'Tomato Ketchup Sachet', category: 'Condiments', stock: 850, minStock: 1000, price: 1.5, status: 'low_stock', location: 'Shelf A-3' },
        { id: 7, sku: 'SUP001', name: 'Paper Napkins', category: 'Supplies', stock: 5000, minStock: 2000, price: 0.8, status: 'in_stock', location: 'Store Room A' },
        { id: 8, sku: 'ING003', name: 'Amul Butter (500g)', category: 'Raw Materials', stock: 12, minStock: 15, price: 275, status: 'low_stock', location: 'Fridge B' },
    ]);

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

    const getStockStatus = (product) => {
        if (product.status === 'out_of_stock') {
            return { text: 'Out of Stock', color: 'bg-red-600/20 border border-red-500/40 text-red-400', badgeBg: 'bg-red-600' };
        } else if (product.status === 'low_stock') {
            return { text: 'Low Stock', color: 'bg-yellow-600/20 border border-yellow-500/40 text-yellow-400', badgeBg: 'bg-yellow-600' };
        }
        return { text: 'In Stock', color: 'bg-green-600/20 border border-green-500/40 text-green-400', badgeBg: 'bg-green-600' };
    };

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
            >
                <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">
                    Inventory Management
                </h1>
                <p className="text-muted-foreground">Real-time stock tracking and optimization</p>
            </motion.div>

            {/* Search & Filters */}
            <GlassCard variant="gradient" className="animate-slide-up stagger-1">
                <div className="p-6 space-y-4">
                    {/* Search Bar */}
                    <div className="flex gap-4 items-stretch">
                        <div className="flex-1 relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500" size={20} />
                            <input
                                type="text"
                                placeholder="Search by product name or SKU..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 bg-gray-50 dark:bg-white/10 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition h-full"
                            />
                        </div>
                        <GradientButton variant="primary" className="flex items-center justify-center gap-2 h-full whitespace-nowrap px-6">
                            <Plus size={20} /> Add Product
                        </GradientButton>
                    </div>

                    {/* Filters */}
                    <div className="flex flex-wrap gap-4">
                        <div className="flex-1 min-w-[200px]">
                            <label className="text-gray-400 text-sm mb-2 block">Category</label>
                            <select
                                value={selectedCategory}
                                onChange={(e) => setSelectedCategory(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-white/10 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 transition"
                            >
                                {categories.map(cat => (
                                    <option key={cat} value={cat} className="bg-gray-800">
                                        {cat === 'all' ? 'All Categories' : cat}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex-1 min-w-[200px]">
                            <label className="text-gray-400 text-sm mb-2 block">Stock Level</label>
                            <select
                                value={stockFilter}
                                onChange={(e) => setStockFilter(e.target.value)}
                                className="w-full px-4 py-2 bg-gray-50 dark:bg-white/10 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:outline-none focus:border-blue-500 transition"
                            >
                                <option value="all" className="bg-gray-800">All Stock Levels</option>
                                <option value="in" className="bg-gray-800">In Stock</option>
                                <option value="low" className="bg-gray-800">Low Stock</option>
                                <option value="out" className="bg-gray-800">Out of Stock</option>
                            </select>
                        </div>

                        <div className="flex gap-2 items-end">
                            <button
                                onClick={() => setViewMode('table')}
                                className={`p-2 rounded-lg transition ${viewMode === 'table' ? 'bg-blue-600' : 'bg-white/10 hover:bg-white/20'}`}
                            >
                                <List size={20} />
                            </button>
                            <button
                                onClick={() => setViewMode('grid')}
                                className={`p-2 rounded-lg transition ${viewMode === 'grid' ? 'bg-blue-600' : 'bg-white/10 hover:bg-white/20'}`}
                            >
                                <Grid size={20} />
                            </button>
                        </div>
                    </div>

                    {/* Bulk Actions */}
                    <div className="flex gap-2">
                        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-white text-sm flex items-center gap-2">
                            <Download size={16} /> Export CSV
                        </button>
                        <button className="px-4 py-2 bg-gray-100 dark:bg-white/10 hover:bg-gray-200 dark:hover:bg-white/20 rounded-lg transition text-gray-700 dark:text-white text-sm flex items-center gap-2">
                            <Upload size={16} /> Import CSV
                        </button>
                    </div>
                </div>
            </GlassCard>

            {/* Results Count */}
            <div className="text-gray-400">
                Showing {filteredProducts.length} of {products.length} products
            </div>

            {/* Product List/Grid */}
            {viewMode === 'table' ? (
                <GlassCard variant="gradient" className="animate-slide-up stagger-2">
                    <div className="p-6">
                        <h2 className="text-xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-6">
                            Product Inventory
                        </h2>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">SKU</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Product</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Category</th>
                                        <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Stock</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Status</th>
                                        <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Price</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Location</th>
                                        <th className="text-center py-3 px-4 text-muted-foreground font-semibold text-sm uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredProducts.map((product, idx) => {
                                        const status = getStockStatus(product);
                                        const stockPercentage = (product.stock / product.minStock) * 100;
                                        return (
                                            <motion.tr
                                                key={product.id}
                                                className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5 transition-all"
                                                initial={{ opacity: 0, x: -20 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: idx * 0.05 }}
                                            >
                                                <td className="py-4 px-4">
                                                    <span className="font-mono text-sm text-muted-foreground bg-muted/30 px-2 py-1 rounded">
                                                        {product.sku}
                                                    </span>
                                                </td>
                                                <td className="py-4 px-4 text-foreground font-semibold">{product.name}</td>
                                                <td className="py-4 px-4 text-muted-foreground">{product.category}</td>
                                                <td className="py-4 px-4 text-right">
                                                    <div className="flex flex-col items-end gap-1">
                                                        <span className={`text-lg font-bold ${product.stock === 0 ? 'text-danger' :
                                                                product.stock < product.minStock ? 'text-warning' :
                                                                    'bg-gradient-to-r from-success to-primary bg-clip-text text-transparent'
                                                            }`}>
                                                            {product.stock}
                                                        </span>
                                                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                                                            <div
                                                                className={`h-full transition-all ${stockPercentage >= 100 ? 'bg-gradient-to-r from-success to-primary' :
                                                                        stockPercentage > 50 ? 'bg-warning' :
                                                                            'bg-danger'
                                                                    }`}
                                                                style={{ width: `${Math.min(stockPercentage, 100)}%` }}
                                                            />
                                                        </div>
                                                        <span className="text-xs text-muted-foreground">Min: {product.minStock}</span>
                                                    </div>
                                                </td>
                                                <td className="py-4 px-4">
                                                    <span className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold ${status.color}`}>
                                                        <span className={`w-2 h-2 rounded-full ${status.badgeBg} animate-pulse-custom`} />
                                                        {status.text}
                                                    </span>
                                                </td>
                                                <td className="py-4 px-4 text-right">
                                                    <span className="font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent">
                                                        ₹{product.price.toLocaleString()}
                                                    </span>
                                                </td>
                                                <td className="py-4 px-4 text-muted-foreground text-sm">{product.location}</td>
                                                <td className="py-4 px-4">
                                                    <div className="flex justify-center gap-2">
                                                        <button className="px-3 py-1.5 bg-gradient-to-r from-primary to-purple hover:shadow-lg hover:shadow-primary/30 rounded-lg text-white text-sm transition-all font-medium">
                                                            Edit
                                                        </button>
                                                        <button className="px-3 py-1.5 bg-danger/10 hover:bg-danger/20 text-danger rounded-lg text-sm transition-all font-medium border border-danger/30">
                                                            Delete
                                                        </button>
                                                    </div>
                                                </td>
                                            </motion.tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </GlassCard>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredProducts.map((product) => {
                        const status = getStockStatus(product);
                        return (
                            <motion.div
                                key={product.id}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                            >
                                <GlassCard variant="gradient" className="h-full flex flex-col hover:shadow-glow-primary transition-all">
                                    <div className="p-6 flex-1 flex flex-col">
                                        <div className="flex justify-between items-start mb-4">
                                            <span className="text-gray-500 dark:text-gray-400 text-sm font-mono">{product.sku}</span>
                                            <span className={`px-2 py-1 rounded text-xs ${status.color}`}>
                                                {status.text}
                                            </span>
                                        </div>
                                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 line-clamp-1" title={product.name}>{product.name}</h3>
                                        <p className="text-gray-400 text-sm mb-4">{product.category}</p>
                                        <div className="flex justify-between items-center mb-4 mt-auto">
                                            <div>
                                                <p className="text-xs text-gray-500">Stock</p>
                                                <div className="flex flex-col">
                                                    <span className={`text-xl font-bold ${product.stock < product.minStock ? 'text-red-500 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>
                                                        {product.stock}
                                                    </span>
                                                    <span className="text-[10px] text-gray-500">/ {product.minStock}</span>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs text-gray-500">Price</p>
                                                <p className="text-xl font-bold text-gray-900 dark:text-white">₹{product.price}</p>
                                            </div>
                                        </div>
                                        <div className="flex gap-2 pt-4 border-t border-white/5">
                                            <button className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 rounded !text-white text-sm transition font-bold tracking-wide">
                                                Edit
                                            </button>
                                            <button className="px-3 py-2 bg-red-600 hover:bg-red-700 rounded !text-white text-sm transition font-bold tracking-wide">
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                </GlassCard>
                            </motion.div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default Inventory;
