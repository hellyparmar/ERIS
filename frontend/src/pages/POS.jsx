import React, { useState, useEffect, useCallback, useRef, Suspense, lazy } from 'react';
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
    Check,
    LogOut,
    User
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';
import PINLogin from '../components/pos/PINLogin';
const BarcodeScanner = lazy(() => import('../components/inventory/BarcodeScanner'));

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Idle timeout: 30 minutes in milliseconds
const IDLE_TIMEOUT_MS = 30 * 60 * 1000;

const POS = () => {
    const { showToast: addToast } = useToast();

    // ── Auth State ───────────────────────────────────────────────────────────
    const [isAuthenticated, setIsAuthenticated] = useState(() => {
        const token = localStorage.getItem('pos_token');
        const lastActivity = localStorage.getItem('pos_last_activity');
        if (!token || !lastActivity) return false;
        // Check if session has expired
        return Date.now() - parseInt(lastActivity) < IDLE_TIMEOUT_MS;
    });
    const [cashier, setCashier] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('pos_cashier') || 'null');
        } catch {
            return null;
        }
    });
    const idleTimerRef = useRef(null);

    // ── POS State ────────────────────────────────────────────────────────────
    const [cart, setCart] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [paymentMethod, setPaymentMethod] = useState('cash');
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [showReceipt, setShowReceipt] = useState(false);
    const [showBarcodeScanner, setShowBarcodeScanner] = useState(false);
    const [invoiceId] = useState(() => `INV-${Math.floor(Date.now() / 1000).toString().slice(-4)}`);

    // ── Online/Offline detector ──────────────────────────────────────────────
    useEffect(() => {
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, []);

    // ── Idle Auto-Logout ─────────────────────────────────────────────────────
    const resetIdleTimer = useCallback(() => {
        localStorage.setItem('pos_last_activity', Date.now().toString());
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
        idleTimerRef.current = setTimeout(() => {
            handleLogout(true);
        }, IDLE_TIMEOUT_MS);
    }, []); // eslint-disable-line

    useEffect(() => {
        if (!isAuthenticated) return;

        // Start idle timer
        resetIdleTimer();

        // Reset on user activity
        const events = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll'];
        events.forEach(e => window.addEventListener(e, resetIdleTimer));

        return () => {
            events.forEach(e => window.removeEventListener(e, resetIdleTimer));
            if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
        };
    }, [isAuthenticated, resetIdleTimer]);

    // ── Auth Handlers ────────────────────────────────────────────────────────
    const handleLoginSuccess = (data) => {
        setCashier({
            id: data.cashier_id,
            name: data.cashier_name,
            role: data.role
        });
        setIsAuthenticated(true);
        addToast(`Welcome, ${data.cashier_name}!`, 'success');
    };

    const handleLogout = useCallback(async (isIdle = false) => {
        try {
            const token = localStorage.getItem('pos_token');
            if (token) {
                await fetch(`${API_BASE}/auth/pos/logout`, {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` }
                });
            }
        } catch {
            // Logout even if API call fails
        } finally {
            localStorage.removeItem('pos_token');
            localStorage.removeItem('pos_cashier');
            localStorage.removeItem('pos_last_activity');
            setIsAuthenticated(false);
            setCashier(null);
            setCart([]);
            if (isIdle) {
                addToast('Session expired due to inactivity. Please log in again.', 'warning');
            } else {
                addToast('Logged out successfully', 'success');
            }
        }
    }, [addToast]);

    // ── Product Search (mock + API) ───────────────────────────────────────────
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

    // ── Cart Helpers ─────────────────────────────────────────────────────────
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

    // ── Barcode Scan Handler ─────────────────────────────────────────────────
    const handleBarcodeScan = (productData) => {
        if (productData) {
            addToCart({
                id: productData.id,
                name: productData.name,
                price: productData.price,
                sku: productData.sku || productData.barcode
            });
            addToast(`Added: ${productData.name}`, 'success');
        }
        setShowBarcodeScanner(false);
    };

    // ── Checkout ─────────────────────────────────────────────────────────────
    const completeSale = async () => {
        if (cart.length === 0) {
            addToast('Cart is empty', 'error');
            return;
        }

        const token = localStorage.getItem('pos_token');

        try {
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
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` })
                },
                body: JSON.stringify(checkoutData)
            });

            const data = await response.json();

            if (data.success) {
                addToast(`Sale completed! Total: ₹${data.data.total_amount}`, 'success');
                setShowReceipt(true);
                setTimeout(() => {
                    setCart([]);
                    setShowReceipt(false);
                }, 5000);
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

    // ── PIN Login Gate ────────────────────────────────────────────────────────
    if (!isAuthenticated) {
        return <PINLogin onLoginSuccess={handleLoginSuccess} />;
    }

    // ── Main POS UI ───────────────────────────────────────────────────────────
    return (
        <div className="min-h-screen p-6">
            {/* Barcode Scanner Modal */}
            {showBarcodeScanner && (
                <Suspense fallback={<div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center"><div className="animate-spin w-8 h-8 border-2 border-white border-t-transparent rounded-full" /></div>}>
                    <BarcodeScanner
                        onScan={handleBarcodeScan}
                        onClose={() => setShowBarcodeScanner(false)}
                    />
                </Suspense>
            )}

            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <div>
                    <p className="page-subtitle">Quick sales entry and receipt generation</p>
                </div>
                <div className="flex items-center gap-3">
                    {cashier && (
                        <div className="flex items-center gap-2 px-4 py-2 rounded-lg" style={{ background: 'rgba(245,158,11,0.08)', color: 'var(--accent)' }}>
                            <User className="w-4 h-4" />
                            <span className="text-sm font-semibold">{cashier.name}</span>
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>({cashier.role})</span>
                        </div>
                    )}
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${isOnline ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                        {isOnline ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
                        <span className="text-sm font-semibold">{isOnline ? 'Online' : 'Offline'}</span>
                    </div>
                    <button
                        onClick={() => handleLogout(false)}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors text-sm font-semibold"
                    >
                        <LogOut className="w-4 h-4" />
                        Logout
                    </button>
                </div>
            </div>

            <div className="flex gap-6 items-start">
                {/* LEFT: Product Search + Cart (60%) */}
                <div className="flex-[3] space-y-6">
                    {/* Search + Barcode Scan */}
                    <div className="card">
                        <div className="flex gap-3 mb-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5" style={{ color: 'var(--text-muted)' }} />
                                <input
                                    type="text"
                                    placeholder="Search product by name or SKU..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-12 pr-4 py-3 rounded-xl"
                                    style={{ background: 'var(--bg-muted)', border: '1.5px solid var(--border)', color: 'var(--text-primary)' }}
                                />
                            </div>
                            <button
                                onClick={() => setShowBarcodeScanner(true)}
                                className="btn-primary px-6 py-3 rounded-xl flex items-center gap-2 text-sm"
                            >
                                <Camera className="w-5 h-5" />
                                Scan
                            </button>
                        </div>

                        {searchQuery && filteredProducts.length > 0 && (
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                {filteredProducts.map((product) => (
                                    <button
                                        key={product.id}
                                        onClick={() => addToCart(product)}
                                        className="w-full p-3 rounded-xl flex justify-between items-center transition-colors"
                                        style={{ background: 'rgba(245,158,11,0.04)' }}
                                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(245,158,11,0.08)'}
                                        onMouseLeave={e => e.currentTarget.style.background = 'rgba(245,158,11,0.04)'}
                                    >
                                        <div className="text-left">
                                            <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{product.name}</p>
                                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>SKU: {product.sku}</p>
                                        </div>
                                        <div className="text-right flex items-center gap-3">
                                            <span className="font-bold" style={{ color: 'var(--accent)' }}>₹{product.price}</span>
                                            <Plus className="w-4 h-4" style={{ color: 'var(--accent-green)' }} />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                        {searchQuery && filteredProducts.length === 0 && (
                            <p className="text-sm text-center py-4" style={{ color: 'var(--text-muted)' }}>No products found for "{searchQuery}"</p>
                        )}
                    </div>

                    {/* Cart */}
                    <div className="card">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="section-title flex items-center gap-2">
                                <ShoppingCart className="w-5 h-5" />
                                Cart Items ({cart.length})
                            </h3>
                            {cart.length > 0 && (
                                <button
                                    onClick={clearCart}
                                    className="text-sm flex items-center gap-1"
                                    style={{ color: 'var(--accent-red)' }}
                                >
                                    <Trash2 className="w-4 h-4" />
                                    Clear Cart
                                </button>
                            )}
                        </div>

                        {cart.length === 0 ? (
                            <div className="text-center py-12">
                                <ShoppingCart className="w-16 h-16 mx-auto mb-4 opacity-30" style={{ color: 'var(--text-muted)' }} />
                                <p style={{ color: 'var(--text-muted)' }}>Cart is empty. Search or scan a product to begin.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {cart.map((item) => (
                                    <div key={item.id} className="p-4 rounded-xl flex justify-between items-center" style={{ background: 'rgba(245,158,11,0.04)' }}>
                                        <div className="flex-1">
                                            <p className="font-medium" style={{ color: 'var(--text-primary)' }}>{item.name}</p>
                                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>SKU: {item.sku}</p>
                                            <p className="text-sm font-bold mt-1" style={{ color: 'var(--accent)' }}>₹{item.price} × {item.quantity}</p>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex items-center gap-2 rounded-lg p-1" style={{ background: 'var(--bg-muted)' }}>
                                                <button onClick={() => updateQuantity(item.id, -1)} className="p-1 rounded transition-colors hover:bg-white/10">
                                                    <Minus className="w-4 h-4" />
                                                </button>
                                                <span className="px-3 font-bold">{item.quantity}</span>
                                                <button onClick={() => updateQuantity(item.id, 1)} className="p-1 rounded transition-colors hover:bg-white/10">
                                                    <Plus className="w-4 h-4" />
                                                </button>
                                            </div>
                                            <span className="font-bold w-24 text-right">₹{(item.price * item.quantity).toLocaleString()}</span>
                                            <button onClick={() => removeItem(item.id)} className="p-2 rounded-lg transition-colors hover:bg-red-500/10">
                                                <Trash2 className="w-4 h-4" style={{ color: 'var(--accent-red)' }} />
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT: Payment Summary (40%) */}
                <div className="flex-[2] sticky top-6">
                    <div className="card">
                        <h3 className="section-title mb-6">Payment Summary</h3>
                        
                        <div className="space-y-3 mb-6">
                            <div className="flex justify-between" style={{ color: 'var(--text-secondary)' }}>
                                <span>Subtotal</span>
                                <span className="font-semibold">₹{subtotal.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between" style={{ color: 'var(--text-secondary)' }}>
                                <span>GST (18%)</span>
                                <span className="font-semibold">₹{gst.toFixed(2)}</span>
                            </div>
                            <div className="h-px my-3" style={{ background: 'var(--border)' }} />
                            <div className="flex justify-between items-baseline">
                                <span className="text-lg font-bold">Total</span>
                                <span className="text-3xl font-bold" style={{ color: 'var(--accent)' }}>₹{total.toLocaleString()}</span>
                            </div>
                        </div>

                        <div className="mb-6">
                            <label className="card-label block mb-3">Payment Method</label>
                            <div className="grid grid-cols-2 gap-2">
                                {paymentMethods.map((method) => {
                                    const Icon = method.icon;
                                    return (
                                        <button
                                            key={method.id}
                                            onClick={() => setPaymentMethod(method.id)}
                                            className="p-3 rounded-xl border-2 transition-all flex flex-col items-center gap-2 text-sm"
                                            style={{
                                                borderColor: paymentMethod === method.id ? 'var(--accent)' : 'var(--border)',
                                                background: paymentMethod === method.id ? 'rgba(245,158,11,0.08)' : 'transparent'
                                            }}
                                        >
                                            <Icon className="w-5 h-5" style={{ color: paymentMethod === method.id ? 'var(--accent)' : 'var(--text-muted)' }} />
                                            <span className="font-semibold" style={{ color: paymentMethod === method.id ? 'var(--accent)' : 'var(--text-muted)' }}>
                                                {method.label}
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <button
                            onClick={completeSale}
                            disabled={cart.length === 0}
                            className="w-full py-4 rounded-xl text-lg font-semibold flex items-center justify-center gap-3"
                            style={{
                                background: cart.length > 0 ? 'linear-gradient(135deg, #f59e0b, #d97706)' : 'var(--bg-muted)',
                                color: cart.length > 0 ? '#fff' : 'var(--text-muted)',
                                cursor: cart.length > 0 ? 'pointer' : 'not-allowed'
                            }}
                            onMouseEnter={e => {
                                if (cart.length > 0) {
                                    e.currentTarget.style.transform = 'scale(1.02)';
                                    e.currentTarget.style.boxShadow = '0 4px 16px rgba(245,158,11,0.3)';
                                }
                            }}
                            onMouseLeave={e => {
                                if (cart.length > 0) {
                                    e.currentTarget.style.transform = 'scale(1)';
                                    e.currentTarget.style.boxShadow = 'none';
                                }
                            }}
                        >
                            <Check className="w-6 h-6" />
                            Complete Sale
                        </button>

                        {showReceipt && (
                            <div className="flex gap-2 mt-4">
                                <button className="flex-1 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors" style={{ background: 'rgba(245,158,11,0.1)', color: 'var(--accent)' }}>
                                    <Printer className="w-4 h-4" /> Print
                                </button>
                                <button className="flex-1 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors" style={{ background: 'rgba(16,185,129,0.1)', color: 'var(--accent-green)' }}>
                                    <Mail className="w-4 h-4" /> Email
                                </button>
                                <button className="flex-1 py-3 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-colors" style={{ background: 'rgba(245,158,11,0.1)', color: 'var(--accent)' }}>
                                    <Download className="w-4 h-4" /> PDF
                                </button>
                            </div>
                        )}

                        <p className="text-xs text-center mt-4" style={{ color: 'var(--text-muted)' }}>Session auto-expires after 30 min of inactivity</p>
                    </div>

                    {showReceipt && (
                        <div className="card mt-6">
                            <h3 className="section-title mb-4">Receipt Preview</h3>
                            <div className="bg-white text-black p-6 rounded-xl font-mono text-sm">
                                <div className="text-center mb-4">
                                    <h4 className="font-bold text-lg">R-DIOS Store</h4>
                                    <p className="text-xs">Enterprise Retail Intelligence</p>
                                    <p className="text-xs">GST: 29ABCDE1234F1Z5</p>
                                </div>
                                <div className="border-t border-b border-black py-2 my-2">
                                    <p className="text-xs">Date: {new Date().toLocaleString()}</p>
                                    <p className="text-xs">Invoice: #{invoiceId}</p>
                                    <p className="text-xs">Cashier: {cashier?.name || 'N/A'}</p>
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
                                        <span>₹{gst.toFixed(2)}</span>
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
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default POS;
