import React, { useState } from 'react';
import {
    Users,
    Plus,
    Search,
    Edit,
    Trash2,
    Shield,
    Filter,
    Star,
    TrendingUp,
    Award,
    Calendar,
    DollarSign,
    Download
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const Employees = () => {
    const [selectedRole, setSelectedRole] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    const employees = [
        { id: 1, name: 'John Doe', email: 'john@rdios.com', role: 'Manager', department: 'Sales', status: 'active', attendance: 96, commission: 12500, joinDate: '2024-01-15' },
        { id: 2, name: 'Jane Smith', email: 'jane@rdios.com', role: 'Staff', department: 'Operations', status: 'active', attendance: 94, commission: 8900, joinDate: '2024-02-20' },
        { id: 3, name: 'Bob Wilson', email: 'bob@rdios.com', role: 'Cashier', department: 'Store', status: 'active', attendance: 98, commission: 5600, joinDate: '2024-03-10' },
        { id: 4, name: 'Alice Brown', email: 'alice@rdios.com', role: 'Manager', department: 'Inventory', status: 'active', attendance: 95, commission: 11200, joinDate: '2024-01-25' },
        { id: 5, name: 'Charlie Davis', email: 'charlie@rdios.com', role: 'Staff', department: 'Customer Service', status: 'active', attendance: 92, commission: 7800, joinDate: '2024-04-05' }
    ];

    const roles = [
        { name: 'Admin', count: 2, color: '#8b5cf6' },
        { name: 'Manager', count: 5, color: '#3b82f6' },
        { name: 'Staff', count: 12, color: '#10b981' },
        { name: 'Cashier', count: 8, color: '#f59e0b' }
    ];

    // Role chart data for Recharts
    const roleChartData = roles.map(r => ({
        name: r.name,
        value: r.count,
        color: r.color
    }));

    const filteredEmployees = employees.filter(emp => {
        const matchesRole = selectedRole === 'all' || emp.role === selectedRole;
        const matchesSearch = emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            emp.email.toLowerCase().includes(searchQuery.toLowerCase());
        return matchesRole && matchesSearch;
    });

    return (
        <div className="min-h-screen space-y-8 p-6 animate-fade-in">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-4xl font-bold gradient-text mb-2">Employee Management</h1>
                    <p className="text-muted-foreground">Manage staff, roles, attendance, and commissions</p>
                </div>
                <div className="flex gap-3">
                    <GradientButton onClick={() => { }}>
                        <Download className="w-4 h-4 mr-2" />
                        Export
                    </GradientButton>
                    <GradientButton onClick={() => { }}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Employee
                    </GradientButton>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-blue-500/20">
                            <Users className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Employees</p>
                            <p className="text-2xl font-bold gradient-text">27</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-green-500/20">
                            <Calendar className="w-5 h-5 text-green-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Avg Attendance</p>
                            <p className="text-2xl font-bold gradient-text">94.5%</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-purple-500/20">
                            <DollarSign className="w-5 h-5 text-purple-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Total Commission</p>
                            <p className="text-2xl font-bold gradient-text">₹2.45L</p>
                        </div>
                    </div>
                </GlassCard>

                <GlassCard className="p-4">
                    <div className="flex items-center gap-3">
                        <div className="p-3 rounded-lg bg-amber-500/20">
                            <TrendingUp className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <p className="text-xs text-muted-foreground">Performance</p>
                            <p className="text-2xl font-bold gradient-text">Excellent</p>
                        </div>
                    </div>
                </GlassCard>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Employee List */}
                <div className="lg:col-span-2">
                    <GlassCard className="p-6">
                        <div className="flex gap-3 mb-6">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                                <input
                                    type="text"
                                    placeholder="Search employees..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full pl-12 pr-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                                />
                            </div>
                            <select
                                value={selectedRole}
                                onChange={(e) => setSelectedRole(e.target.value)}
                                className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-foreground focus:border-primary focus:outline-none"
                            >
                                <option value="all">All Roles</option>
                                <option value="Manager">Manager</option>
                                <option value="Staff">Staff</option>
                                <option value="Cashier">Cashier</option>
                            </select>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-border">
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Name</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Role</th>
                                        <th className="text-left py-3 px-4 text-muted-foreground font-semibold text-sm">Department</th>
                                        <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm">Attendance</th>
                                        <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm">Commission</th>
                                        <th className="text-right py-3 px-4 text-muted-foreground font-semibold text-sm">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredEmployees.map((emp) => (
                                        <tr key={emp.id} className="border-b border-border/50 hover:bg-gradient-to-r hover:from-primary/5 hover:to-purple/5">
                                            <td className="py-4 px-4">
                                                <div>
                                                    <p className="font-medium text-foreground">{emp.name}</p>
                                                    <p className="text-xs text-muted-foreground">{emp.email}</p>
                                                </div>
                                            </td>
                                            <td className="py-4 px-4">
                                                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400">
                                                    {emp.role}
                                                </span>
                                            </td>
                                            <td className="py-4 px-4 text-sm text-muted-foreground">{emp.department}</td>
                                            <td className="py-4 px-4 text-right">
                                                <span className={`font-semibold ${emp.attendance >= 95 ? 'text-green-400' : 'text-amber-400'}`}>
                                                    {emp.attendance}%
                                                </span>
                                            </td>
                                            <td className="py-4 px-4 text-right font-semibold text-foreground">₹{emp.commission.toLocaleString()}</td>
                                            <td className="py-4 px-4">
                                                <div className="flex justify-end gap-2">
                                                    <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                        <Edit className="w-4 h-4 text-blue-400" />
                                                    </button>
                                                    <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                                                        <Trash2 className="w-4 h-4 text-red-400" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </GlassCard>
                </div>

                {/* Role Distribution & Stats */}
                <div className="space-y-6">
                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">Role Distribution</h3>
                        <div style={{ height: '200px' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={roleChartData}
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={40}
                                        outerRadius={70}
                                        paddingAngle={2}
                                    >
                                        {roleChartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip
                                        contentStyle={{
                                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                            border: '1px solid rgba(255,255,255,0.1)',
                                            borderRadius: '8px'
                                        }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </GlassCard>

                    <GlassCard className="p-6">
                        <h3 className="text-xl font-bold gradient-text mb-4">Top Performers</h3>
                        <div className="space-y-3">
                            {employees.slice(0, 3).map((emp, idx) => (
                                <div key={emp.id} className="p-3 rounded-lg bg-gradient-to-r from-primary/5 to-purple/5">
                                    <div className="flex items-center gap-3">
                                        <span className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                                            idx === 1 ? 'bg-gray-400/20 text-gray-400' :
                                                'bg-orange-500/20 text-orange-400'
                                            }`}>
                                            {idx + 1}
                                        </span>
                                        <div className="flex-1">
                                            <p className="font-medium text-foreground text-sm">{emp.name}</p>
                                            <p className="text-xs text-muted-foreground">{emp.role}</p>
                                        </div>
                                        <p className="font-bold gradient-text">₹{emp.commission.toLocaleString()}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </GlassCard>
                </div>
            </div>
        </div>
    );
};

export default Employees;
