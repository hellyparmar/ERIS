import React, { useState } from 'react';
import {
    ShoppingCart,
    Search,
    Camera,
    Printer,
    Mail,
    Download,
    Trash2,
    Plus,
    Minus,
    CreditCard,
    Smartphone,
    Wallet,
    DollarSign,
    Wifi,
    WifiOff,
    Check
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const POS = () => {
    const { addToast } = useToast();
    const [cart, setCart] = useState([
        { id: 1, name: 'Wireless Headphones', price: 1250, quantity: 2, sku: 'WH-001' },
        { id: 2, name: 'Smart Watch', price: 4500, quantity: 1, sku: 'SW-002' }
    ]);
    const [searchQuery, setSearchQuery] = useState('');
    const [paymentMethod, setPaymentMethod] = useState('cash');
    const [isOnline] = useState(true);
    const [showReceipt, setShowReceipt] = useState(false);
    const [invoiceId] = useState(() => `INV-${Math.floor(Date.now() / 1000).toString().slice(-4)}`);

    // Mock products for search
    const products = [
        { id: 3, name: 'Laptop Stand', price: 380, sku: 'LS-003' },
        { id: 4, name: 'USB-C Cable', price: 60, sku: 'UC-004' },
        { id: 5, name: 'Phone Case', price: 60, sku: 'PC-005' },
        { id: 6, name: 'Screen Protector', price: 50, sku: 'SP-006' },
        { id: 7, name: 'Power Bank', price: 200, sku: 'PB-007' }
    ];

    const filteredProducts = products.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.sku.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const gstRate = 0.18;
    const gst = subtotal * gstRate;
    const total = subtotal + gst;

    const updateQuantity = (id, delta) => {
        setCart(cart.map(item =>
            item.id === id
                ? { ...item, quantity: Math.max(1, item.quantity + delta) }
                : item
        ));
    };

    const removeItem = (id) => {
        setCart(cart.filter(item => item.id !== id));
    };

    const addToCart = (product) => {
        const existing = cart.find(item => item.id === product.id);
        if (existing) {
            updateQuantity(product.id, 1);
        } else {
            setCart([...cart, { ...product, quantity: 1 }]);
        }
        setSearchQuery('');
    };

    const completeSale = async () => {
        if (cart.length === 0) {
            addToast('Cart is empty', 'error');
            return;
        }

        try {
            // Transform cart to API format
            const checkoutData = {
                items: cart.map(item => ({
                    product_id: item.id,
                    quantity: item.quantity,
                    unit_price: item.price
                })),
                payment_method: paymentMethod,
                discount: 0.0
            };

            const response = await fetch(`${API_BASE}/api/v1/pos/checkout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(checkoutData)
            });

            const data = await response.json();

            if (data.success) {
                addToast(`Sale completed! Total: ₹${data.data.total_amount}`, 'success');
                setShowReceipt(true);
                // Clear cart after successful checkout
                setTimeout(() => {
                    setCart([]);
                    setShowReceipt(false);
                }, 3000);
            } else {
                addToast(data.error || 'Checkout failed', 'error');
            }
        } catch (error) {
            console.error('Checkout error:', error);
            addToast('Failed to process checkout', 'error');
        }
    };

    const clearCart = () => {
        setCart([]);
        setShowReceipt(false);
    };

    const paymentMethods = [
        { id: 'cash', label: 'Cash', icon: DollarSign },
        { id: 'card', label: 'Card', icon: CreditCard },
        { id: 'upi', label: 'UPI', icon: Smartphone },
        { id: 'wallet', label: 'Wallet', icon: Wallet }
    ];

    return (
        <div className="min-h-screen space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple bg-clip-text text-transparent mb-2">Point of Sale</h1>
                    <p className="text-muted-foreground">Quick sales entry and receipt generation</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${isOnline ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                        {isOnline ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                        <span className="text-sm font-semibold">{isOnline ? 'Online' : 'Offline'}</span>
                    </div>
                    <span className="text-xs text-muted-foreground">Last sync: 2m ago</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Product Search & Cart */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Search */}
                    <GlassCard className="p-6">
                        <div className="flex gap-3 mb-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search product by name or scan barcode..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3 rounded-lg bg-secondary/50 border border-border text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <button className="px-6 py-3 rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-lg transition-all flex items-center gap-2">
                                <Camera className="w-5 h-5" />
                                Scan
                            </button>
                        </div>

                        {/* Search Results */}
                        {searchQuery && filteredProducts.length > 0 && (
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                {filteredProducts.map((product) => (
                                    <button
                                        key={product.id}
                                        onClick={() => addToCart(product)}
                                        className="w-full p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 hover:from-primary/10 hover:to-purple/10 transition-all text-left flex justify-between items-center"
                                    >
                                        <div>
                                            <p className="font-medium text-foreground">{product.name}</p>
                                            <p className="text-xs text-muted-foreground">SKU: {product.sku}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="font-bold gradient-text">₹{product.price}</p>
                                            <Plus className="w-4 h-4 text-green-400 ml-auto" />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </GlassCard>

                    {/* Cart */}
                    <GlassCard className="p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xl font-bold gradient-text flex items-center gap-2">
                                <ShoppingCart className="w-5 h-5" />
                                Cart Items ({cart.length})
                            </h3>
                            {cart.length > 0 && (
                                <button
                                    onClick={clearCart}
                                    className="text-red-400 hover:text-red-300 text-sm flex items-center gap-1"
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Clear Cart
                                </button>
                            )}
                        </div>

                        {cart.length === 0 ? (
                            <div className="text-center py-12">
                                <ShoppingCart className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                                <p className="text-muted-foreground">Cart is empty. Search and add products to begin.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {cart.map((item) => (
                                    <div key={item.id} className="p-4 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5 flex justify-between items-center">
                                        <div className="flex-1">
                                            <p className="font-medium text-foreground">{item.name}</p>
                                            <p className="text-xs text-muted-foreground">SKU: {item.sku}</p>
                                            <p className="text-sm font-bold gradient-text mt-1">₹{item.price} × {item.quantity}</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex items-center gap-2 bg-black/20 rounded-lg p-1">
                                                <button
                                                    onClick={() => updateQuantity(item.id, -1)}
                                                    className="p-1 hover:bg-white/10 rounded transition-colors"
                                                >
                                                    <Minus className="w-4 h-4 text-foreground" />
                                                </button>
                                                <span className="px-3 font-bold text-foreground">{item.quantity}</span>
                                                <button
                                                    onClick={() => updateQuantity(item.id, 1)}
                                                    className="p-1 hover:bg-white/10 rounded transition-colors"
                                                >
                                                    <Plus className="w-4 h-4 text-foreground" />
                                                </button>
                                            </div>
                                            <p className="font-bold text-foreground w-24 text-right">₹{(item.price * item.quantity).toLocaleString()}</p>
                                            <button
                                                onClick={() => removeItem(item.id)}
                                                className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                                            >
                                                <Trash2 className="w-4 h-4 text-red-400" />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </GlassCard>
                </div>

                {/* Right: Payment & Receipt */}
                <div className="space-y-6">
                    {/* Payment Summary */}
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-6">Payment Summary</h3>
                        <div className="space-y-3 mb-6">
                            <div className="flex justify-between text-muted-foreground">
                                <span>Subtotal:</span>
                                <span className="font-semibold">₹{subtotal.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between text-muted-foreground">
                                <span>GST (18%):</span>
                                <span className="font-semibold">₹{gst.toLocaleString()}</span>
                            </div>
                            <div className="h-px bg-border my-3" />
                            <div className="flex justify-between">
                                <span className="text-lg font-bold text-foreground">Total:</span>
                                <span className="text-2xl font-bold gradient-text">₹{total.toLocaleString()}</span>
                            </div>
                        </div>

                        {/* Payment Method */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-muted-foreground mb-3">Payment Method</label>
                            <div className="grid grid-cols-2 gap-2">
                                {paymentMethods.map((method) => {
                                    const Icon = method.icon;
                                    return (
                                        <button
                                            key={method.id}
                                            onClick={() => setPaymentMethod(method.id)}
                                            className={`p-3 rounded-lg border-2 transition-all flex flex-col items-center gap-2 ${paymentMethod === method.id
                                                ? 'border-primary bg-primary/10'
                                                : 'border-border bg-secondary/20 hover:bg-secondary/40'
                                                }`}
                                        >
                                            <Icon className={`w-5 h-5 ${paymentMethod === method.id ? 'text-primary' : 'text-muted-foreground'}`} />
                                            <span className={`text-xs font-semibold ${paymentMethod === method.id ? 'text-primary' : 'text-muted-foreground'}`}>
                                                {method.label}
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="space-y-3">
                            <GradientButton
                                onClick={completeSale}
                                disabled={cart.length === 0}
                                className="w-full"
                            >
                                <Check className="w-5 h-5 mr-2" />
                                Complete Sale
                            </GradientButton>
                            {showReceipt && (
                                <div className="flex gap-2">
                                    <button className="flex-1 px-4 py-2 rounded-lg bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 transition-colors flex items-center justify-center gap-2">
                                        <Printer className="w-4 h-4" />
                                        Print
                                    </button>
                                    <button className="flex-1 px-4 py-2 rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors flex items-center justify-center gap-2">
                                        <Mail className="w-4 h-4" />
                                        Email
                                    </button>
                                    <button className="flex-1 px-4 py-2 rounded-lg bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 transition-colors flex items-center justify-center gap-2">
                                        <Download className="w-4 h-4" />
                                        PDF
                                    </button>
                                </div>
                            )}
                        </div>
                    </GlassCard>

                    {/* Receipt Preview */}
                    {showReceipt && (
                        <GlassCard className="p-6">
                            <h3 className="text-xl font-bold gradient-text mb-4">Receipt Preview</h3>
                            <div className="bg-white text-black p-6 rounded-lg font-mono text-sm">
                                <div className="text-center mb-4">
                                    <h4 className="font-bold text-lg">R-DIOS Store</h4>
                                    <p className="text-xs">Enterprise Retail Intelligence</p>
                                    <p className="text-xs">GST: 29ABCDE1234F1Z5</p>
                                </div>
                                <div className="border-t border-b border-black py-2 my-2">
                                    <p className="text-xs">Date: {new Date().toLocaleString()}</p>
                                    <p className="text-xs">Invoice: #{invoiceId}</p>
                                </div>
                                {cart.map((item) => (
                                    <div key={item.id} className="flex justify-between text-xs mb-1">
                                        <span>{item.name} x{item.quantity}</span>
                                        <span>₹{(item.price * item.quantity).toLocaleString()}</span>
                                    </div>
                                ))}
                                <div className="border-t border-black mt-2 pt-2">
                                    <div className="flex justify-between text-xs">
                                        <span>Subtotal:</span>
                                        <span>₹{subtotal.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between text-xs">
                                        <span>GST (18%):</span>
                                        <span>₹{gst.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between font-bold mt-2">
                                        <span>Total:</span>
                                        <span>₹{total.toLocaleString()}</span>
                                    </div>
                                </div>
                                <div className="text-center mt-4 text-xs">
                                    <p>Thank you for shopping with us!</p>
                                    <p>Visit again</p>
                                </div>
                            </div>
                        </GlassCard>
                    )}
                </div>
            </div>
        </div>
    );
};

export default POS;
