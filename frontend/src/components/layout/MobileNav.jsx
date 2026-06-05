
import { LayoutDashboard, Utensils, ChefHat, BarChart3, Menu } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../hooks/useTheme';

const MobileNav = () => {
    const location = useLocation();
    const { isDark } = useTheme();

    const menuItems = [
        { id: 'dashboard', path: '/', label: 'Home', icon: LayoutDashboard },
        { id: 'petpooja', path: '/petpooja', label: 'POS', icon: Utensils },
        { id: 'kitchen', path: '/petpooja/kitchen', label: 'KDS', icon: ChefHat },
        { id: 'analytics', path: '/analytics', label: 'Stats', icon: BarChart3 },
    ];

    return (
        <div className={`md:hidden fixed bottom-0 left-0 right-0 border-t z-50 ${isDark ? 'bg-[#101012] border-white/10' : 'bg-white border-slate-200'}`}>
            <div className="flex justify-around items-center p-2">
                {menuItems.map(({ id, path, label, icon: Icon }) => {
                    const isActive = location.pathname === path;
                    return (
                        <Link
                            key={id}
                            to={path}
                            className={`flex flex-col items-center gap-1 p-2 rounded-lg transition-colors
                                ${isActive
                                    ? 'text-blue-500'
                                    : 'text-gray-500 dark:text-gray-400'
                                }`}
                        >
                            <Icon size={20} />
                            <span className="text-[10px] font-medium">{label}</span>
                        </Link>
                    );
                })}
            </div>
        </div>
    );
};

export default MobileNav;
