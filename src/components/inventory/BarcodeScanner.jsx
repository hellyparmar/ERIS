import { useEffect, useRef, useState } from 'react';
import Quagga from 'quagga';
import { Camera, X } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function BarcodeScanner({ onScan, onClose }) {
    const scannerRef = useRef(null);
    const [isScanning, setIsScanning] = useState(false);
    const [error, setError] = useState('');
    const [lastScan, setLastScan] = useState('');

    useEffect(() => {
        if (!scannerRef.current) return;

        // Initialize Quagga
        Quagga.init({
            inputStream: {
                type: 'LiveStream',
                target: scannerRef.current,
                constraints: {
                    width: 640,
                    height: 480,
                    facingMode: 'environment' // Use back camera on mobile
                }
            },
            decoder: {
                readers: [
                    'ean_reader',      // EAN-13, EAN-8
                    'upc_reader',      // UPC-A, UPC-E
                    'code_128_reader'  // Code 128
                ]
            },
            locate: true
        }, (err) => {
            if (err) {
                console.error('Quagga init error:', err);
                setError('Camera access denied or not available');
                return;
            }

            Quagga.start();
            setIsScanning(true);
        });

        // Handle barcode detection
        Quagga.onDetected(async (result) => {
            const code = result.codeResult.code;

            // Prevent duplicate scans
            if (code === lastScan) return;
            setLastScan(code);

            // Lookup product
            try {
                const response = await fetch(`${API_BASE}/inventory/scan/${code}`);
                if (response.ok) {
                    const data = await response.json();
                    onScan(data.data);
                    Quagga.stop();
                    onClose();
                } else {
                    setError(`Product not found for barcode: ${code}`);
                    setTimeout(() => setError(''), 3000);
                }
            } catch (err) {
                console.error('Barcode lookup error:', err);
                setError('Failed to lookup barcode');
            }
        });

        return () => {
            Quagga.stop();
        };
    }, [lastScan, onScan, onClose]);

    return (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4">
                {/* Header */}
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-2xl font-bold text-gray-800">Scan Barcode</h2>
                    <button
                        onClick={() => {
                            Quagga.stop();
                            onClose();
                        }}
                        className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        <X className="w-6 h-6 text-gray-600" />
                    </button>
                </div>

                {/* Scanner */}
                <div className="relative bg-black rounded-lg overflow-hidden mb-4">
                    <div ref={scannerRef} className="w-full h-96" />
                    {!isScanning && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            <Camera className="w-16 h-16 text-gray-400 animate-pulse" />
                        </div>
                    )}
                </div>

                {/* Error Message */}
                {error && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm mb-4">
                        {error}
                    </div>
                )}

                {/* Instructions */}
                <div className="text-center text-gray-600 text-sm">
                    <p>Position the barcode within the camera view</p>
                    <p className="text-xs text-gray-400 mt-1">
                        Supports EAN-13, UPC-A, Code 128
                    </p>
                </div>
            </div>
        </div>
    );
}
