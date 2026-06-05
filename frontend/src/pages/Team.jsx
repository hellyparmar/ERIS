/**
 * Enterprise Retail Intelligence System v3.0
 * TEAM PAGE - Team Management
 * 
 * Features:
 * - Premium Grid Layout
 * - Role-based visual hierarchy
 * - Interactive Profile Cards
 */

import { useEffect, useState } from 'react';
import { useLanguage } from '../hooks/useLanguage';
import { Users, Mail, Phone, Shield, Activity, Calendar, MoreVertical, Plus } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import GradientButton from '../components/ui/GradientButton';
import { useToast } from '../components/ui/Toast';

const Team = () => {
    const { t } = useLanguage();
    const { addToast } = useToast();
    const [filter, setFilter] = useState('all');

    // Mock team data
    const teamMembers = [
        {
            id: 1,
            name: 'Rajesh Kumar',
            role: 'Admin',
            department: 'Management',
            email: 'rajesh.k@rdios.com',
            phone: '+91 98765 43210',
            status: 'active',
            gradient: 'from-blue-500 to-purple-600',
            initials: 'RK',
            lastActive: 'Now'
        },
        {
            id: 2,
            name: 'Priya Sharma',
            role: 'Manager',
            department: 'Sales',
            email: 'priya.s@rdios.com',
            phone: '+91 98765 43211',
            status: 'active',
            gradient: 'from-pink-500 to-rose-600',
            initials: 'PS',
            lastActive: '5m ago'
        },
        {
            id: 3,
            name: 'Amit Patel',
            role: 'Analyst',
            department: 'Analytics',
            email: 'amit.p@rdios.com',
            phone: '+91 98765 43212',
            status: 'away',
            gradient: 'from-emerald-500 to-teal-600',
            initials: 'AP',
            lastActive: '1h ago'
        },
        {
            id: 4,
            name: 'Sneha Reddy',
            role: 'Associate',
            department: 'Inventory',
            email: 'sneha.r@rdios.com',
            phone: '+91 98765 43213',
            status: 'active',
            gradient: 'from-orange-500 to-amber-600',
            initials: 'SR',
            lastActive: '10m ago'
        },
        {
            id: 5,
            name: 'Vikram Singh',
            role: 'Manager',
            department: 'Operations',
            email: 'vikram.s@rdios.com',
            phone: '+91 98765 43214',
            status: 'offline',
            gradient: 'from-cyan-500 to-blue-600',
            initials: 'VS',
            lastActive: '2d ago'
        },
        {
            id: 6,
            name: 'Anjali Gupta',
            role: 'Support',
            department: 'Customer Care',
            email: 'anjali.g@rdios.com',
            phone: '+91 98765 43215',
            status: 'active',
            gradient: 'from-violet-500 to-purple-600',
            initials: 'AG',
            lastActive: 'Now'
        }
    ];

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'bg-green-500 box-shadow-green';
            case 'away': return 'bg-yellow-500 box-shadow-yellow';
            case 'offline': return 'bg-gray-500';
            default: return 'bg-gray-400';
        }
    };

    const getRoleGradient = (role) => {
        switch (role) {
            case 'Admin': return 'from-purple-500 to-indigo-600';
            case 'Manager': return 'from-blue-500 to-cyan-600';
            case 'Analyst': return 'from-emerald-500 to-teal-600';
            default: return 'from-gray-500 to-slate-600';
        }
    };

    const filteredMembers = filter === 'all'
        ? teamMembers
        : teamMembers.filter(m => m.role.toLowerCase() === filter || m.status === filter);

    return (
        <div className="space-y-8 fade-in-up min-h-screen p-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent mb-2">Team Management</h1>
                    <p className="text-muted-foreground">Collaborate and manage access controls</p>
                </div>
                <GradientButton
                    className="flex items-center justify-center gap-2 whitespace-nowrap box-shadow-glow"
                    onClick={() => addToast("Invite User Modal Opened", "info")}
                >
                    <Plus size={18} /> Invite Member
                </GradientButton>
            </div>

            {/* Team Metrics - Added to fix reported layout/sizing issues */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <GlassCard className="p-5 flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">Total Members</p>
                        <h3 className="text-2xl font-bold text-foreground mt-1">{teamMembers.length}</h3>
                    </div>
                    <div className="p-4 rounded-xl bg-blue-500 bg-opacity-80 dark:bg-opacity-90 shadow-[0_0_15px_rgba(59,130,246,0.5)] flex items-center justify-center">
                        <Users className="w-6 h-6 text-white" strokeWidth={2.5} />
                    </div>
                </GlassCard>
                <GlassCard className="p-5 flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">Active Now</p>
                        <h3 className="text-2xl font-bold text-foreground mt-1">
                            {teamMembers.filter(m => m.status === 'active').length}
                        </h3>
                    </div>
                    <div className="p-4 rounded-xl bg-green-500 bg-opacity-80 dark:bg-opacity-90 shadow-[0_0_15px_rgba(34,197,94,0.5)] flex items-center justify-center">
                        <Activity className="w-6 h-6 text-white" strokeWidth={2.5} />
                    </div>
                </GlassCard>
                <GlassCard className="p-5 flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">Admins</p>
                        <h3 className="text-2xl font-bold text-foreground mt-1">
                            {teamMembers.filter(m => m.role === 'Admin').length}
                        </h3>
                    </div>
                    <div className="p-4 rounded-xl bg-purple-500 bg-opacity-80 dark:bg-opacity-90 shadow-[0_0_15px_rgba(168,85,247,0.5)] flex items-center justify-center">
                        <Shield className="w-6 h-6 text-white" strokeWidth={2.5} />
                    </div>
                </GlassCard>
                <GlassCard className="p-5 flex items-center justify-between">
                    <div>
                        <p className="text-sm font-medium text-muted-foreground">Managers</p>
                        <h3 className="text-2xl font-bold text-foreground mt-1">
                            {teamMembers.filter(m => m.role === 'Manager').length}
                        </h3>
                    </div>
                    <div className="p-4 rounded-xl bg-orange-500 bg-opacity-80 dark:bg-opacity-90 shadow-[0_0_15px_rgba(249,115,22,0.5)] flex items-center justify-center">
                        <Users className="w-6 h-6 text-white" strokeWidth={2.5} />
                    </div>
                </GlassCard>
            </div>

            {/* Quick Stats & Filters */}
            <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
                {['All', 'Active', 'Admin', 'Manager', 'Analyst'].map((item) => (
                    <button
                        key={item}
                        onClick={() => setFilter(item.toLowerCase())}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all whitespace-nowrap border ${filter === item.toLowerCase()
                            ? 'bg-white/10 border-white/20 text-white shadow-lg backdrop-blur-md'
                            : 'bg-transparent border-transparent text-muted-foreground hover:text-foreground hover:bg-white/5'
                            }`}
                    >
                        {item}
                    </button>
                ))}
            </div>

            {/* Team Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                
                    {filteredMembers.map((member) => (
                        <div
                            key={member.id}
                        >
                            <GlassCard className="h-full group relative overflow-hidden hover:border-blue-500/30 transition-colors duration-300">
                                {/* Banner Gradient */}
                                <div className={`h-24 w-full bg-gradient-to-r ${getRoleGradient(member.role)} opacity-80 group-hover:opacity-100 transition-opacity`} />

                                {/* Avatar */}
                                <div className="absolute top-12 left-6">
                                    <div className="relative">
                                        <div className="w-20 h-20 rounded-2xl bg-white dark:bg-gray-900 p-1 shadow-xl transition-colors">
                                            <div className={`w-full h-full rounded-xl bg-gradient-to-br ${member.gradient} flex items-center justify-center text-white text-2xl font-bold`}>
                                                {member.initials}
                                            </div>
                                        </div>
                                        <div className={`absolute -bottom-1 -right-1 w-5 h-5 border-4 border-white dark:border-gray-900 rounded-full ${getStatusColor(member.status)}`} />
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="absolute top-4 right-4">
                                    <button className="p-2 rounded-full bg-black/20 hover:bg-black/40 text-white/80 hover:text-white transition backdrop-blur-md">
                                        <MoreVertical size={16} />
                                    </button>
                                </div>

                                {/* Content */}
                                <div className="pt-12 p-6">
                                    <div className="mb-4">
                                        <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">{member.name}</h3>
                                        <p className="text-sm text-muted-foreground">{member.role} • {member.department}</p>
                                    </div>

                                    <div className="space-y-3">
                                        <div className="flex items-center gap-3 text-sm text-muted-foreground bg-secondary/50 p-2 rounded-lg">
                                            <Mail size={14} className="text-blue-400" />
                                            <span className="truncate">{member.email}</span>
                                        </div>
                                        <div className="flex items-center gap-3 text-sm text-muted-foreground bg-secondary/50 p-2 rounded-lg">
                                            <Phone size={14} className="text-green-400 shrink-0" />
                                            <span className="truncate">{member.phone}</span>
                                        </div>
                                    </div>

                                    <div className="mt-6 flex items-center justify-between text-xs text-muted-foreground border-t border-border pt-4">
                                        <div className="flex items-center gap-1">
                                            <Activity size={12} />
                                            Last active: <span className="text-foreground">{member.lastActive}</span>
                                        </div>
                                        <button className="text-primary hover:text-primary/80 transition-colors">View Profile</button>
                                    </div>
                                </div>
                            </GlassCard>
                        </div>
                    ))}
                
            </div>
        </div>
    );
};

export default Team;
