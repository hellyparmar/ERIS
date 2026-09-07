import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Phone, Store, Edit2, Search } from 'lucide-react';
import api from '../lib/api';
import SEO from '../components/SEO';

const Employees = () => {
    const queryClient = useQueryClient();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedOutlet, setSelectedOutlet] = useState('');
    const [selectedShift, setSelectedShift] = useState('');
    const [selectedRole, setSelectedRole] = useState('');
    const [isDrawerOpen, setIsDrawerOpen] = useState(false);
    const [editingEmployee, setEditingEmployee] = useState(null);
    const [formErrors, setFormErrors] = useState({});
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        role: '',
        outlet_id: '',
        shift: '',
        salary: '',
        joining_date: ''
    });

    // Queries
    const { data: userData } = useQuery({
        queryKey: ['user'],
        queryFn: () => api.get('/api/v1/auth/me').then(r => r.data),
        staleTime: Infinity
    });

    const { data: outletsData } = useQuery({
        queryKey: ['outlets'],
        queryFn: () => api.get('/api/v1/outlets').then(r => r.data.data || []),
    });

    const { data: employeesData, isLoading } = useQuery({
        queryKey: ['employees'],
        queryFn: () => api.get('/api/v1/employees').then(r => r.data?.items || r.data?.employees || (Array.isArray(r.data) ? r.data : [])),
    });

    // Mutation: Save employee (add or edit)
    const saveEmployeeMutation = useMutation({
        mutationFn: async (data) => {
            if (editingEmployee) {
                return api.put(`/api/v1/employees/${editingEmployee.id}`, data).then(r => r.data);
            } else {
                return api.post('/api/v1/employees', data).then(r => r.data);
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries(['employees']);
            resetForm();
        }
    });

    // Validation
    const validateForm = () => {
        const errors = {};
        if (!formData.name.trim()) errors.name = 'Name is required';
        if (!formData.phone.trim()) errors.phone = 'Phone is required';
        else if (!/^\d{10}$/.test(formData.phone.replace(/\D/g, ''))) errors.phone = 'Phone must be 10 digits';
        if (!formData.role) errors.role = 'Role is required';
        if (!formData.outlet_id) errors.outlet_id = 'Outlet is required';
        if (!formData.shift) errors.shift = 'Shift is required';
        if (!formData.joining_date) errors.joining_date = 'Joining date is required';
        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };

    // Form handlers
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        if (formErrors[name]) {
            setFormErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    const handleSubmit = () => {
        if (!validateForm()) return;
        saveEmployeeMutation.mutate(formData);
    };

    const resetForm = () => {
        setFormData({
            name: '',
            phone: '',
            role: '',
            outlet_id: '',
            shift: '',
            salary: '',
            joining_date: ''
        });
        setEditingEmployee(null);
        setFormErrors({});
        setIsDrawerOpen(false);
    };

    const openAddDrawer = () => {
        resetForm();
        setIsDrawerOpen(true);
    };

    const openEditDrawer = (employee) => {
        setEditingEmployee(employee);
        setFormData({
            name: employee.name || '',
            phone: employee.phone || '',
            role: employee.role || '',
            outlet_id: employee.outlet_id || '',
            shift: employee.shift || '',
            salary: employee.salary || '',
            joining_date: employee.joining_date || ''
        });
        setIsDrawerOpen(true);
    };

    const getInitials = (name) => {
        return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase().slice(0, 2);
    };

    // Filtering
    const filteredEmployees = useMemo(() => {
        if (!employeesData) return [];
        return employeesData.filter(emp => {
            const matchSearch = emp.name.toLowerCase().includes(searchQuery.toLowerCase());
            const matchOutlet = !selectedOutlet || emp.outlet_id === parseInt(selectedOutlet);
            const matchShift = !selectedShift || emp.shift === selectedShift;
            const matchRole = !selectedRole || emp.role === selectedRole;
            return matchSearch && matchOutlet && matchShift && matchRole;
        });
    }, [employeesData, searchQuery, selectedOutlet, selectedShift, selectedRole]);

    // Shift Summary
    const shiftSummary = useMemo(() => {
        if (!employeesData) return { morning: 0, evening: 0, night: 0 };
        return {
            morning: employeesData.filter(e => e.shift === 'Morning').length,
            evening: employeesData.filter(e => e.shift === 'Evening').length,
            night: employeesData.filter(e => e.shift === 'Night').length
        };
    }, [employeesData]);

    // Role list
    const rolesList = useMemo(() => {
        if (!employeesData) return [];
        return [...new Set(employeesData.map(e => e.role))].filter(Boolean);
    }, [employeesData]);

    const isSuperadmin = userData?.role === 'super_admin' || userData?.role === 'superadmin';
    const isAreaManager = userData?.role === 'area_manager';
    const isOutletManager = userData?.role === 'outlet_manager' || userData?.role === 'manager';
    const isManager = isAreaManager || isOutletManager;
    const canAddEdit = isSuperadmin || isManager;
    const totalEmployees = employeesData?.length || 0;

    const getRoleBadgeClass = (role) => {
        if (role === 'manager' || role === 'outlet_manager') return 'active';
        if (role === 'area_manager') return 'warning';
        if (role === 'superadmin' || role === 'super_admin') return 'critical';
        return 'neutral';
    };

    const getShiftBadgeClass = (shift) => {
        if (shift === 'Morning') return 'active';
        if (shift === 'Evening') return 'neutral';
        return 'warning';
    };

    if (isLoading) {
        return (
            <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <span style={{ fontSize: 13, color: 'var(--c-ink-muted)' }}>Retrieving staff roster...</span>
            </div>
        );
    }

    return (
        <>
            <SEO title="Employee Management" description="Staff management and scheduling directory" />
            <style>{`
                .employee-row:hover {
                    background: var(--c-brown-glow) !important;
                }
            `}</style>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
                {/* Header */}
                <div style={{
                    padding: '16px 22px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-end',
                    borderBottom: '1px solid var(--c-border)',
                    background: 'var(--c-canvas)'
                }}>
                    <div>
                        <h1 className="page-title" >Employees</h1>
                        <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
                            Staff management and scheduling
                        </p>
                    </div>
                    {canAddEdit && (
                        <button className="action-btn primary" onClick={openAddDrawer}>
                            + Add Employee
                        </button>
                    )}
                </div>

                {/* Filter bar */}
                <div className="filter-bar">
                    <div style={{ position: 'relative', flex: '0 1 220px' }}>
                        <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }} />
                        <input type="text" placeholder="Search name..." value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)} style={{ paddingLeft: 30, fontSize: 12 }} />
                    </div>
                    <select value={selectedOutlet} onChange={(e) => setSelectedOutlet(e.target.value)} style={{ width: 'auto' }}>
                        <option value="">All Outlets</option>
                        {outletsData?.map(outlet => (
                            <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                        ))}
                    </select>
                    {['', 'Morning', 'Evening', 'Night'].map(s => (
                        <button key={s} className={`action-btn ${selectedShift === s ? 'primary' : ''}`}
                            onClick={() => setSelectedShift(s)} style={{ padding: '4px 10px', fontSize: '11px' }}>
                            {s || 'All Shifts'}
                        </button>
                    ))}
                    <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)} style={{ width: 'auto' }}>
                        <option value="">All Roles</option>
                        {rolesList.map(role => <option key={role} value={role}>{role}</option>)}
                    </select>
                </div>

                {/* Content */}
                <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: 20 }}>
                    {filteredEmployees.length > 0 ? (
                        <div>
                            <div className="zone-label" style={{ marginBottom: 12 }}>Staff Directory ({filteredEmployees.length})</div>
                            <div style={{ overflowX: 'auto' }}>
                                <table className="eris-table" style={{ width: '100%' }}>
                                    <thead>
                                        <tr>
                                            <th style={{ textAlign: 'left' }}>Employee</th>
                                            <th style={{ textAlign: 'center' }}>Role</th>
                                            <th style={{ textAlign: 'left' }}>Outlet</th>
                                            <th style={{ textAlign: 'center' }}>Shift</th>
                                            <th style={{ textAlign: 'left' }}>Joined</th>
                                            <th style={{ width: 90 }}></th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredEmployees.map((employee) => (
                                            <tr key={employee.id} className="employee-row">
                                                <td>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                                        <div style={{ width: 30, height: 30, borderRadius: '50%', backgroundColor: 'var(--c-strip)', border: '1px solid var(--c-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, color: 'var(--c-brown)', flexShrink: 0 }}>
                                                            {getInitials(employee.name)}
                                                        </div>
                                                        <div>
                                                            <div style={{ fontWeight: 700, fontSize: 13, color: '#1A1208' }}>{employee.name}</div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td style={{ textAlign: 'center' }}>
                                                    <div className={`badge ${getRoleBadgeClass(employee.role)}`}>
                                                        {employee.role?.replace('_', ' ')}
                                                    </div>
                                                </td>
                                                <td>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                                        <Store size={13} style={{ color: 'var(--c-ink-muted)' }} />
                                                        {outletsData?.find(o => o.id === employee.outlet_id)?.name || 'Unknown'}
                                                    </div>
                                                </td>
                                                <td style={{ textAlign: 'center' }}>
                                                    <div className={`badge ${getShiftBadgeClass(employee.shift)}`}>
                                                        {employee.shift}
                                                    </div>
                                                </td>
                                                <td style={{ color: 'var(--c-ink-muted)', fontSize: 12 }}>
                                                    {new Date(employee.joining_date).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}
                                                </td>
                                                <td>
                                                    <div style={{ display: 'flex', gap: 4, alignItems: 'center', justifyContent: 'flex-end' }}>
                                                        <a href={`tel:${employee.phone}`} className="action-btn" style={{ padding: 4 }} title={employee.phone}><Phone size={13} /></a>
                                                        {canAddEdit && (
                                                            <button className="action-btn" style={{ padding: 4 }} onClick={() => openEditDrawer(employee)} title="Edit employee"><Edit2 size={13} /></button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state">
                            <p className="empty-state-desc">No employees found</p>
                        </div>
                    )}

                    <div>
                        <div className="zone-label" style={{ marginBottom: 12 }}>Shift Summary</div>
                        <div className="kpi-strip">
                            {[
                                { label: 'Morning Shift', count: shiftSummary.morning, total: totalEmployees },
                                { label: 'Evening Shift', count: shiftSummary.evening, total: totalEmployees },
                                { label: 'Night Shift', count: shiftSummary.night, total: totalEmployees }
                            ].map(shift => (
                                <div key={shift.label} className="kpi-cell">
                                    <div className="kpi-label">{shift.label}</div>
                                    <div className="kpi-value brown">{shift.count}</div>
                                    <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)', marginTop: 4 }}>
                                        {shift.total > 0 ? `${Math.round((shift.count / shift.total) * 100)}% of staff` : '—'}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Form Drawer Modal overlay */}
            {isDrawerOpen && (
                <div style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'flex-end' }} onClick={resetForm}>
                    <div onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: 420, height: '100vh', background: 'var(--c-canvas)', borderLeft: '1px solid var(--c-border)', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ padding: '16px 20px', background: 'var(--c-canvas-raised)', borderBottom: '1px solid var(--c-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontFamily: 'var(--f-display)', fontSize: '15px', fontWeight: 600, color: 'var(--c-dark)' }}>{editingEmployee ? 'Edit Employee' : 'Add Employee'}</span>
                            <button onClick={resetForm} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }}><X size={18} /></button>
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Name *</span>
                                <input type="text" name="name" value={formData.name} onChange={handleInputChange} placeholder="Employee name" />
                                {formErrors.name && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.name}</span>}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Phone *</span>
                                <input type="tel" name="phone" value={formData.phone} onChange={handleInputChange} placeholder="10 digit number" />
                                {formErrors.phone && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.phone}</span>}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Role *</span>
                                <select name="role" value={formData.role} onChange={handleInputChange}>
                                    <option value="">Select role</option>
                                    <option value="outlet_manager">Outlet Manager</option>
                                    <option value="area_manager">Area Manager</option>
                                    {isSuperadmin && <option value="super_admin">Super Admin</option>}
                                </select>
                                {formErrors.role && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.role}</span>}
                            </div>
                            {isSuperadmin && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                    <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Outlet *</span>
                                    <select name="outlet_id" value={formData.outlet_id} onChange={handleInputChange}>
                                        <option value="">Select outlet</option>
                                        {outletsData?.map(outlet => (
                                            <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                                        ))}
                                    </select>
                                    {formErrors.outlet_id && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.outlet_id}</span>}
                                </div>
                            )}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Shift *</span>
                                <select name="shift" value={formData.shift} onChange={handleInputChange}>
                                    <option value="">Select shift</option>
                                    <option value="Morning">Morning</option>
                                    <option value="Evening">Evening</option>
                                    <option value="Night">Night</option>
                                </select>
                                {formErrors.shift && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.shift}</span>}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Salary</span>
                                <input type="number" name="salary" value={formData.salary} onChange={handleInputChange} placeholder="Annual salary" />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Joining Date *</span>
                                <input type="date" name="joining_date" value={formData.joining_date} onChange={handleInputChange} />
                                {formErrors.joining_date && <span style={{ color: 'var(--c-critical)', fontSize: 11 }}>{formErrors.joining_date}</span>}
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: 8, padding: 20, borderTop: '1px solid var(--c-border)' }}>
                            <button className="action-btn" onClick={resetForm} style={{ flex: 1 }}>Cancel</button>
                            <button className="action-btn primary" onClick={handleSubmit} disabled={saveEmployeeMutation.isPending} style={{ flex: 1 }}>
                                {saveEmployeeMutation.isPending ? 'Saving...' : 'Save'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default Employees;
