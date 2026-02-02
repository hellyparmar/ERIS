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
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';
import ThemeToggle from '../ui/ThemeToggle';

const Sidebar = () => {
    const location = useLocation();
    const { isDark } = useTheme();

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
        { id: 'ai-assistant', path: '/ai-assistant', label: 'AI Assistant', icon: Sparkles, color: 'text-violet-500' },
        { id: 'integrations', path: '/integrations', label: 'Integrations', icon: Network, color: 'text-orange-500' },
        { id: 'team', path: '/team', label: 'Team', icon: Users, color: 'text-green-500' },
        { id: 'enterprise', path: '/enterprise', label: 'Enterprise', icon: Building2, color: 'text-slate-500' }
    ];

    return (
        <aside
            className={`w-64 h-screen flex flex-col transition-colors duration-300 ${isDark ? 'bg-gray-900 border-r border-gray-800' : 'bg-white border-r border-gray-200'}`}
            role="navigation"
            aria-label="Main navigation"
        >
            <div className="flex-1 p-6 overflow-y-auto">
                {/* Logo/Brand */}
                <div className="mb-8">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gradient-to-br from-blue-600 to-purple-900" aria-hidden="true">
                            <Building2 className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <span className="text-xl font-bold gradient-text">
                                R-DIOS
                            </span>
                            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">
                                Enterprise Intelligence
                            </p>
                        </div>
                    </div>
                </div>

                {/* Navigation Menu */}
                <nav className="space-y-2" aria-label="Primary navigation">
                    {menuItems.map(({ id, path, label, icon: Icon, color }) => {
                        const isActive = location.pathname === path;

                        return (
                            <Link
                                key={id}
                                to={path}
                                className={`
                                    w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ease-in-out
                                    ${isActive
                                        ? 'bg-gradient-to-r from-blue-600/20 to-purple-600/20 text-blue-600 dark:text-blue-300 border border-blue-500/30 shadow-lg shadow-blue-500/20'
                                        : 'text-gray-600 dark:text-gray-300 hover:bg-blue-100/60 dark:hover:bg-white/10 hover:text-blue-700 dark:hover:text-white hover:shadow-md hover:shadow-blue-500/10 dark:hover:shadow-blue-500/20 hover:border hover:border-blue-300/40 dark:hover:border-blue-500/50'
                                    }
                                `}
                                aria-current={isActive ? 'page' : undefined}
                                aria-label={`Navigate to ${label}`}
                            >
                                <Icon className={`w-5 h-5 ${isActive ? color : ''}`} aria-hidden="true" />
                                <span className="font-medium">{label}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>

            {/* Bottom Actions */}
            <div className="p-6 border-t border-gray-200 dark:border-border space-y-3">
                {/* Theme Toggle Button */}
                <ThemeToggle className="w-full flex justify-center bg-gray-100 dark:bg-secondary/50 hover:bg-gray-200 dark:hover:bg-secondary text-gray-700 dark:text-gray-300" />
            </div>
        </aside>
    );
};

export default Sidebar;
