import React, { useState, useEffect } from 'react';
import { MapPin, Users, Activity } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

const LiveRetailMap = () => {
    const [pulses, setPulses] = useState([]);

    // Simulate real-time transaction pulses
    useEffect(() => {
        const interval = setInterval(() => {
            const zones = [
                { id: 'entrance', x: '50%', y: '90%', color: 'bg-blue-500' },
                { id: 'checkout', x: '80%', y: '20%', color: 'bg-green-500' },
                { id: 'mens', x: '20%', y: '40%', color: 'bg-purple-500' },
                { id: 'womens', x: '80%', y: '60%', color: 'bg-pink-500' },
                { id: 'shoes', x: '20%', y: '80%', color: 'bg-orange-500' }
            ];

            // Randomly trigger a pulse
            if (Math.random() > 0.3) {
                const zone = zones[Math.floor(Math.random() * zones.length)];
                const newPulse = {
                    id: Date.now(),
                    ...zone
                };
                setPulses(prev => [...prev.slice(-10), newPulse]); // Keep last 10

                // Remove pulse after animation
                setTimeout(() => {
                    setPulses(prev => prev.filter(p => p.id !== newPulse.id));
                }, 2000);
            }
        }, 800);

        return () => clearInterval(interval);
    }, []);

    return (
        <GlassCard className="h-[400px] relative overflow-hidden flex flex-col">
            <div className="absolute top-4 left-4 z-10">
                <div className="flex items-center gap-2 mb-1">
                    <Activity className="text-red-500 animate-pulse" size={20} />
                    <h3 className="font-bold text-gray-900 dark:text-white">Live Floor Activity</h3>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    Real-time transaction feed
                </div>
            </div>

            {/* Map Container */}
            <div className="flex-1 relative bg-gray-100 dark:bg-gray-900/50 m-4 rounded-xl border border-gray-200 dark:border-gray-800">

                {/* Stylized Floor Plan SVG Background */}
                <svg className="absolute inset-0 w-full h-full text-gray-300 dark:text-gray-800 pointer-events-none" width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none">
                    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" />
                    </pattern>
                    <rect width="100" height="100" fill="url(#grid)" />

                    {/* Zones */}
                    <rect x="10" y="10" width="30" height="30" rx="4" fill="currentColor" fillOpacity="0.1" /> {/* Mens */}
                    <text x="25" y="25" textAnchor="middle" fill="currentColor" fontSize="3" opacity="0.5">MEN'S</text>

                    <rect x="60" y="10" width="30" height="30" rx="4" fill="currentColor" fillOpacity="0.1" /> {/* Checkout */}
                    <text x="75" y="25" textAnchor="middle" fill="currentColor" fontSize="3" opacity="0.5">CHECKOUT</text>

                    <rect x="60" y="50" width="30" height="30" rx="4" fill="currentColor" fillOpacity="0.1" /> {/* Womens */}
                    <text x="75" y="65" textAnchor="middle" fill="currentColor" fontSize="3" opacity="0.5">WOMEN'S</text>

                    <rect x="10" y="50" width="30" height="30" rx="4" fill="currentColor" fillOpacity="0.1" /> {/* Shoes */}
                    <text x="25" y="65" textAnchor="middle" fill="currentColor" fontSize="3" opacity="0.5">SHOES</text>

                    <path d="M 45 90 L 55 90" stroke="currentColor" strokeWidth="1" strokeLinecap="round" /> {/* Entrance */}
                    <text x="50" y="95" textAnchor="middle" fill="currentColor" fontSize="3" opacity="0.5">ENTRANCE</text>
                </svg>

                {/* Pulses */}
                
                    {pulses.map(pulse => (
                        <div
                            key={pulse.id}
                            }
                            }
                            className={`absolute w-8 h-8 rounded-full ${pulse.color} blur-sm`}
                            style={{
                                left: pulse.x,
                                top: pulse.y,
                                transform: 'translate(-50%, -50%)'
                            }}
                        />
                    ))}
                    {pulses.map(pulse => (
                        <div
                            key={`dot-${pulse.id}`}
                            }
                            }
                            className={`absolute w-2 h-2 rounded-full bg-white shadow-lg`}
                            style={{
                                left: pulse.x,
                                top: pulse.y,
                                transform: 'translate(-50%, -50%)'
                            }}
                        />
                    ))}
                
            </div>

            {/* Legend */}
            <div className="absolute bottom-6 left-6 right-6 flex justify-center gap-4 text-xs text-gray-500">
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Sale</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> Entry</div>
                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-500"></span> Browns</div>
            </div>
        </GlassCard>
    );
};

export default LiveRetailMap;
