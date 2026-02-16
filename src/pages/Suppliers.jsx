import React, { useState } from 'react';
import {
    Truck,
    Plus,
    Search,
    Star,
    FileText,
    Phone,
    Mail,
    MapPin,
    TrendingUp,
    Package,
    DollarSign
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';

const Suppliers = () => {

    const suppliers = [
        { id: 1, name: 'TechSupply Co.', rating: 5, contact: 'contact@techsupply.com', phone: '+91 98765 43210', address: 'Mumbai, Maharashtra', paymentTerms: 'Net 30', onTimeDelivery: 98, activeOrders: 3, totalOrders: 145, totalSpend: 1250000 },
        { id: 2, name: 'Global Electronics', rating: 4, contact: 'sales@globalelec.com', phone: '+91 98765 43211', address: 'Delhi, NCR', paymentTerms: 'Net 45', onTimeDelivery: 95, activeOrders: 2, totalOrders: 98, totalSpend: 850000 },
        { id: 3, name: 'Premium Gadgets Ltd', rating: 4.5, contact: 'info@premiumgadgets.com', phone: '+91 98765 43212', address: 'Bangalore, Karnataka', paymentTerms: 'Net 30', onTimeDelivery: 97, activeOrders: 1, totalOrders: 67, totalSpend: 560000 }
    ];

    const purchaseOrders = [
        { id: 'PO-001', supplier: 'TechSupply Co.', items: 5, amount: 125000, status: 'pending', date: '2026-02-01', deliveryDate: '2026-02-10' },
        { id: 'PO-002', supplier: 'Global Electronics', items: 3, amount: 85000, status: 'delivered', date: '2026-01-25', deliveryDate: '2026-02-05' },
        { id: 'PO-003', supplier: 'Premium Gadgets Ltd', items: 8, amount: 156000, status: 'confirmed', date: '2026-01-30', deliveryDate: '2026-02-08' }
    ];

    const renderStars = (rating) => {
        return Array.from({ length: 5 }, (_, i) => (
            <Star
                key={i}
                className={`w-4 h-4 ${i < rating ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}`}
            />
        ));
    };

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Supplier Management</h1>
                    <p className="text-muted-foreground">Manage suppliers, purchase orders, and procurement</p>
                </div>
                <div className="flex gap-3">
                    <GradientButton onClick={() => { }}>
                        <FileText className="w-4 h-4 mr-2" />
                        Create PO
                    </GradientButton>
                    <GradientButton onClick={() => { }}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Supplier
                    </GradientButton>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <Truck className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Active Suppliers</p>
                            <p className="text-2xl font-bold gradient-text">{suppliers.length}</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <Package className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Active POs</p>
                            <p className="text-2xl font-bold gradient-text">6</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <DollarSign className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Spend</p>
                            <p className="text-2xl font-bold gradient-text">₹26.6L</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <TrendingUp className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Avg On-Time</p>
                            <p className="text-2xl font-bold gradient-text">96.7%</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Suppliers List */}
                <GlassCard className="p-6">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold gradient-text">Active Suppliers</h3>
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Search..."
                                className="pl-10 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground text-sm focus:border-primary focus:outline-none"
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        {suppliers.map((supplier) => (
                            <div
                                key={supplier.id}
                                className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all cursor-pointer"
                            >
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h4 className="font-bold text-foreground mb-1">{supplier.name}</h4>
                                        <div className="flex gap-1 mb-2">{renderStars(supplier.rating)}</div>
                                    </div>
                                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400">
                                        Active
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-3 text-xs">
                                    <div>
                                        <p className="text-muted-foreground">Payment Terms</p>
                                        <p className="font-medium text-foreground">{supplier.paymentTerms}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">On-Time Delivery</p>
                                        <p className="font-medium text-green-400">{supplier.onTimeDelivery}%</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Active Orders</p>
                                        <p className="font-medium text-foreground">{supplier.activeOrders}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Total Spend</p>
                                        <p className="font-medium text-foreground">₹{(supplier.totalSpend / 100000).toFixed(1)}L</p>
                                    </div>
                                </div>
                                <div className="flex gap-2 mt-3">
                                    <button className="flex-1 px-3 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-xs font-semibold transition-colors">
                                        View Details
                                    </button>
                                    <button className="flex-1 px-3 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 text-xs font-semibold transition-colors">
                                        Create PO
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </GlassCard>

                {/* Purchase Orders */}
                <GlassCard className="p-6">
                    <h3 className="text-xl font-bold gradient-text mb-6">Recent Purchase Orders</h3>
                    <div className="space-y-4">
                        {purchaseOrders.map((po) => (
                            <div key={po.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                <div className="flex justify-between items-start mb-3">
                                    <div>
                                        <h4 className="font-bold text-foreground">{po.id}</h4>
                                        <p className="text-sm text-muted-foreground">{po.supplier}</p>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${po.status === 'delivered' ? 'bg-green-500/20 text-green-400' :
                                        po.status === 'confirmed' ? 'bg-blue-500/20 text-blue-400' :
                                            'bg-amber-500/20 text-amber-400'
                                        }`}>
                                        {po.status.charAt(0).toUpperCase() + po.status.slice(1)}
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 gap-3 text-xs mb-3">
                                    <div>
                                        <p className="text-muted-foreground">Items</p>
                                        <p className="font-medium text-foreground">{po.items}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Amount</p>
                                        <p className="font-medium text-foreground">₹{po.amount.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Order Date</p>
                                        <p className="font-medium text-foreground">{po.date}</p>
                                    </div>
                                    <div>
                                        <p className="text-muted-foreground">Delivery Date</p>
                                        <p className="font-medium text-foreground">{po.deliveryDate}</p>
                                    </div>
                                </div>
                                <button className="w-full px-3 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 text-xs font-semibold transition-colors">
                                    View PO Details
                                </button>
                            </div>
                        ))}
                    </div>
                </GlassCard>
            </div>
        </div>
    );
};

export default Suppliers;
