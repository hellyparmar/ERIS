/**
 * Enterprise Retail Intelligence System v3.0
 * SIDEBAR - Modern Dark Theme with Theme Toggle
 */

import {
    LayoutDashboard,
    BarChart3,
    Package,
    Users,
    Building2,
    TrendingUp,
    AlertTriangle,
    Network,
    Moon,
    Sun,
    Sparkles,
    UserCog,
    Brain,
    Database,
    Layers,
    Truck,
    FileText,
    Gift,
    Settings,
    UserCircle,
    Store,
    Scale
} from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';
import { useCallback } from 'react';
import Button from '../ui/Button';

const Sidebar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { isDark, toggleTheme, theme } = useTheme();

    const handleThemeToggle = useCallback(() => {
        toggleTheme();
    }, [toggleTheme]);

    const handleNavigation = useCallback((path) => {
        navigate(path);
    }, [navigate]);

    // Standard Navigation Items
    const menuItems = [
        { id: 'dashboard', path: '/', label: 'Dashboard', icon: LayoutDashboard, color: 'text-blue-500' },
        { id: 'analytics', path: '/analytics', label: 'Analytics', icon: BarChart3, color: 'text-purple-500' },
        { id: 'customers', path: '/customers', label: 'Customer Insights', icon: UserCircle, color: 'text-pink-500' },
        { id: 'multi-store', path: '/multi-store', label: 'Multi-Store', icon: Store, color: 'text-amber-500' },
        { id: 'inventory', path: '/inventory', label: 'Inventory', icon: Package, color: 'text-indigo-500' },
        { id: 'forecasts', path: '/forecasts', label: 'Forecasts', icon: TrendingUp, color: 'text-cyan-500' },
        { id: 'alerts', path: '/alerts', label: 'Alerts', icon: AlertTriangle, color: 'text-red-500' },
        { id: 'invoices', path: '/invoices', label: 'Invoices', icon: FileText, color: 'text-yellow-500' },
        { id: 'loyalty', path: '/loyalty', label: 'Loyalty & Credit', icon: Gift, color: 'text-rose-500' },
        { id: 'compliance', path: '/compliance', label: 'Compliance', icon: Scale, color: 'text-teal-500' },
        { id: 'integrations', path: '/integrations', label: 'Integrations', icon: Network, color: 'text-orange-500' },
        { id: 'team', path: '/team', label: 'Team', icon: Users, color: 'text-green-500' },
        { id: 'enterprise', path: '/enterprise', label: 'Enterprise', icon: Building2, color: 'text-slate-500' }
    ];

    return (
        <aside
            className={`w-56 h-screen flex flex-col transition-colors duration-300 ${isDark ? 'bg-gray-900 border-r border-gray-800' : 'bg-white border-r border-gray-200'}`}
            role="navigation"
            aria-label="Main navigation"
        >
            {/* Header Section with Logo and Theme Toggle */}
            <div className={`flex items-center justify-between p-2 border-b gap-2 ${isDark ? 'border-gray-800 bg-gray-800/50' : 'border-gray-200 bg-gray-50'}`}>
                <div className="flex items-center gap-2 flex-1 min-w-0">
                    <img
                        src="/rdios-logo.png"
                        alt="R-DIOS Logo"
                        className={`w-12 h-12 object-contain flex-shrink-0 transition-opacity duration-300 ${isDark ? 'opacity-100' : 'opacity-80 hover:opacity-100'}`}
                        style={{
                            filter: isDark ? 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.3))' : 'drop-shadow(0 0 4px rgba(0, 0, 0, 0.1))'
                        }}
                    />
                    <div className="min-w-0">
                        <h1 className="text-sm font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent leading-tight">
                            R-DIOS
                        </h1>
                        <p className={`text-[10px] uppercase tracking-widest font-semibold ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                            Enterprise Intelligence
                        </p>
                    </div>
                </div>

                {/* Theme Toggle Button */}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleThemeToggle}
                    aria-label="Toggle theme"
                    className={`flex-shrink-0 p-1.5 rounded-lg transition-all duration-300 ${
                        isDark 
                            ? 'hover:bg-gray-700 text-yellow-400' 
                            : 'hover:bg-gray-200 text-blue-600'
                    }`}
                >
                    {theme === 'dark' ? (
                        <Sun className="w-4 h-4" />
                    ) : (
                        <Moon className="w-4 h-4" />
                    )}
                </Button>
            </div>

            {/* Navigation Menu - All Items Visible */}
            <div className="flex-1 overflow-hidden p-2">
                <nav className="space-y-0 h-full flex flex-col" aria-label="Primary navigation">
                    {menuItems.map(({ id, path, label, icon: Icon, color }) => {
                        const isActive = location.pathname === path;

                        return (
                            <button
                                key={id}
                                onClick={() => handleNavigation(path)}
                                className={`
                                    w-full flex items-center justify-start text-left gap-1.5 px-2 py-0.5 text-base transition-all duration-200 ease-in-out relative group cursor-pointer
                                    ${isActive
                                        ? 'border-l-4 border-blue-500 bg-gradient-to-r from-blue-600/20 to-transparent text-blue-400 pl-2 backdrop-blur-sm shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                                        : 'text-muted-foreground hover:text-foreground hover:bg-white/5 border-l-4 border-transparent'
                                    }
                                `}
                                style={isActive ? { textShadow: '0 0 10px rgba(59, 130, 246, 0.4)' } : {}}
                                aria-current={isActive ? 'page' : undefined}
                                aria-label={`Navigate to ${label}`}
                            >
                                <Icon
                                    className={`w-3.5 h-3.5 flex-shrink-0 transition-all duration-200 ${isActive ? '' : 'group-hover:scale-110'}`}
                                    aria-hidden="true"
                                    fill={isActive ? "currentColor" : "none"}
                                    fillOpacity={isActive ? 0.2 : 0}
                                />
                                <span className={`font-medium truncate leading-tight ${isActive ? 'font-semibold' : ''}`}>{label}</span>
                            </button>
                        );
                    })}
                </nav>
            </div>
        </aside>
    );
};

export default Sidebar;
