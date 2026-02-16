import { useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function PINLogin({ onLoginSuccess }) {
    const [pin, setPin] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleNumberClick = (num) => {
        if (pin.length < 4) {
            setPin(pin + num);
        }
    };

    const handleClear = () => {
        setPin('');
        setError('');
    };

    const handleLogin = async () => {
        if (pin.length !== 4) {
            setError('PIN must be 4 digits');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await fetch(`${API_BASE}/auth/pos/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin, store_id: 1 })
            });

            if (!response.ok) {
                throw new Error('Invalid PIN');
            }

            const data = await response.json();

            // Store auth data
            localStorage.setItem('pos_token', data.access_token);
            localStorage.setItem('pos_cashier', JSON.stringify({
                id: data.cashier_id,
                name: data.cashier_name,
                role: data.role
            }));
            localStorage.setItem('pos_last_activity', Date.now());

            onLoginSuccess(data);
        } catch (err) {
            setError(err.message || 'Login failed');
            setPin('');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-96">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800 mb-2">POS Login</h1>
                    <p className="text-gray-600">Enter your 4-digit PIN</p>
                </div>

                {/* PIN Display */}
                <div className="flex justify-center gap-3 mb-6">
                    {[0, 1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="w-14 h-14 rounded-lg border-2 border-gray-300 flex items-center justify-center text-2xl font-bold"
                        >
                            {pin[i] ? '●' : ''}
                        </div>
                    ))}
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm text-center">
                        {error}
                    </div>
                )}

                {/* Numeric Keypad */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
                        <button
                            key={num}
                            onClick={() => handleNumberClick(num.toString())}
                            disabled={loading}
                            className="h-16 text-2xl font-semibold bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                        >
                            {num}
                        </button>
                    ))}
                    <button
                        onClick={handleClear}
                        disabled={loading}
                        className="h-16 text-lg font-semibold bg-red-100 hover:bg-red-200 text-red-700 rounded-lg transition-colors disabled:opacity-50"
                    >
                        Clear
                    </button>
                    <button
                        onClick={() => handleNumberClick('0')}
                        disabled={loading}
                        className="h-16 text-2xl font-semibold bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors disabled:opacity-50"
                    >
                        0
                    </button>
                    <button
                        onClick={handleLogin}
                        disabled={loading || pin.length !== 4}
                        className="h-16 text-lg font-semibold bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Logging in...' : 'Login'}
                    </button>
                </div>

                <div className="text-center text-sm text-gray-500 mt-4">
                    <p>Test PINs: 1234 (Cashier) | 9999 (Manager)</p>
                </div>
            </div>
        </div>
    );
}
