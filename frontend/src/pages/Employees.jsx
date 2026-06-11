import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Mail, Phone, Store, Edit2, Search } from 'lucide-react';
import api from '../services/api';
import '../styles/fresh-design.css';

const drawerStyles = `
.drawer-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 999; }
.drawer-panel {
  position: fixed; top: 0; right: 0; bottom: 0; width: 420px; max-width: 100vw;
  background: var(--surface-1); border-left: 1px solid var(--border);
  z-index: 1000; transform: translateX(100%); transition: transform 0.2s ease;
  display: flex; flex-direction: column;
}
.drawer-panel.open { transform: translateX(0); }
.drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid var(--border);
}
.drawer-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.drawer-close {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  padding: 4px; border-radius: 4px;
}
.drawer-close:hover { color: var(--text-primary); }
.drawer-content { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.drawer-footer {
  display: flex; gap: 8px; justify-content: flex-end;
  padding: 16px 24px; border-top: 1px solid var(--border);
}
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-label { font-size: 12px; font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }
.form-input {
  width: 100%; padding: 8px 12px; border: 1px solid var(--border);
  border-radius: 6px; font-size: 14px; background: var(--input-bg);
  color: var(--text-primary); outline: none; box-sizing: border-box;
}
.form-input:focus { border-color: var(--accent); }
.form-input.error { border-color: var(--error); }
.form-error { font-size: 12px; color: var(--error); }
`;

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
        email: '',
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
        queryFn: () => api.get('/api/v1/employees').then(r => r.data.data || []),
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
        if (!formData.email.trim()) errors.email = 'Email is required';
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) errors.email = 'Invalid email format';
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
            email: '',
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
            email: employee.email || '',
            phone: employee.phone || '',
            role: employee.role || '',
            outlet_id: employee.outlet_id || '',
            shift: employee.shift || '',
            salary: employee.salary || '',
            joining_date: employee.joining_date || ''
        });
        setIsDrawerOpen(true);
    };

    // Avatar color palette (8 colors, deterministic by first letter)
    const avatarColors = ['#FEE2E2', '#FEF3C7', '#DCFCE7', '#DBEAFE', '#EDE9FE', '#FCE7F3', '#CCFBF1', '#F5F3FF'];
    const getAvatarColor = (name) => {
        const firstLetter = name.charAt(0).toUpperCase();
        return avatarColors[firstLetter.charCodeAt(0) % avatarColors.length];
    };

    const getInitials = (name) => {
        return name.split(' ').map(n => n.charAt(0)).join('').toUpperCase().slice(0, 2);
    };

    // Filtering
    const filteredEmployees = useMemo(() => {
        if (!employeesData) return [];
        return employeesData.filter(emp => {
            const matchSearch = emp.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                emp.email.toLowerCase().includes(searchQuery.toLowerCase());
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

    const isSuperadmin = userData?.role === 'superadmin';
    const isManager = userData?.role === 'manager';
    const canAddEdit = isSuperadmin || isManager;
    const totalEmployees = employeesData?.length || 0;

    // Skeleton loader
    if (isLoading) {
        return (
            <div className="fresh-page">
                <div style={{ marginBottom: 32 }}>
                    <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Staff management and scheduling</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {Array(5).fill(0).map((_, i) => (
                        <div key={i} style={{ height: 48, background: 'var(--surface-2)', borderRadius: 8, opacity: 0.3 + (5 - i) * 0.12 }} />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="fresh-page">
            <style>{drawerStyles}</style>

            {/* Header */}
            <div style={{ marginBottom: 32 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                    {canAddEdit && (
                        <button className="fresh-btn primary" onClick={openAddDrawer}>
                            + Add Employee
                        </button>
                    )}
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Staff management and scheduling</p>
            </div>

            {/* Filter Bar */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ position: 'relative', flex: '0 1 220px' }}>
                    <Search size={15} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        type="text"
                        placeholder="Search by name or email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        style={{
                            width: '100%', padding: '7px 12px 7px 32px', border: '1px solid var(--border)',
                            borderRadius: 6, fontSize: 13, background: 'var(--input-bg)', color: 'var(--text-primary)',
                            outline: 'none', boxSizing: 'border-box'
                        }}
                    />
                </div>
                <select
                    value={selectedOutlet}
                    onChange={(e) => setSelectedOutlet(e.target.value)}
                    style={{
                        padding: '7px 12px', border: '1px solid var(--border)', borderRadius: 6,
                        fontSize: 13, background: 'var(--input-bg)', color: 'var(--text-primary)', outline: 'none'
                    }}
                >
                    <option value="">All Outlets</option>
                    {outletsData?.map(outlet => (
                        <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                    ))}
                </select>
                <div className="fresh-pills">
                    {['', 'Morning', 'Evening', 'Night'].map(s => (
                        <button
                            key={s}
                            className={`fresh-pill ${selectedShift === s ? 'active' : ''}`}
                            onClick={() => setSelectedShift(s)}
                        >
                            {s || 'All'}
                        </button>
                    ))}
                </div>
                <select
                    value={selectedRole}
                    onChange={(e) => setSelectedRole(e.target.value)}
                    style={{
                        padding: '7px 12px', border: '1px solid var(--border)', borderRadius: 6,
                        fontSize: 13, background: 'var(--input-bg)', color: 'var(--text-primary)', outline: 'none'
                    }}
                >
                    <option value="">All Roles</option>
                    {rolesList.map(role => (
                        <option key={role} value={role}>{role}</option>
                    ))}
                </select>
            </div>

            {/* Employee Table */}
            {filteredEmployees.length > 0 ? (
                <div className="fresh-section">
                    <div className="fresh-section-header">
                        <span className="fresh-section-title">
                            All Employees <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({filteredEmployees.length})</span>
                        </span>
                    </div>
                    <table className="fresh-table">
                        <thead>
                            <tr>
                                <th>Employee</th>
                                <th>Role</th>
                                <th>Outlet</th>
                                <th>Shift</th>
                                <th>Joined</th>
                                <th style={{ width: 90 }}></th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredEmployees.map(employee => (
                                <tr key={employee.id}>
                                    <td>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                            <div style={{
                                                width: 30, height: 30, borderRadius: '50%',
                                                backgroundColor: getAvatarColor(employee.name),
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: 11, fontWeight: 600, color: '#1e293b', flexShrink: 0
                                            }}>
                                                {getInitials(employee.name)}
                                            </div>
                                            <div>
                                                <div style={{ fontWeight: 500, fontSize: 14, color: 'var(--text-primary)' }}>{employee.name}</div>
                                                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>{employee.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`fresh-badge ${employee.role === 'manager' ? 'green' : employee.role === 'superadmin' ? 'red' : 'yellow'}`}>
                                            {employee.role}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                            <Store size={14} />
                                            {outletsData?.find(o => o.id === employee.outlet_id)?.name || 'Unknown'}
                                        </div>
                                    </td>
                                    <td>
                                        <span className={`fresh-badge ${employee.shift === 'Morning' ? 'green' : employee.shift === 'Evening' ? 'yellow' : 'red'}`}>
                                            {employee.shift}
                                        </span>
                                    </td>
                                    <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                                        {new Date(employee.joining_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                                    </td>
                                    <td>
                                        <div style={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                                            <a href={`mailto:${employee.email}`} style={{ color: 'var(--text-muted)', padding: 4 }} title={employee.email}>
                                                <Mail size={14} />
                                            </a>
                                            <a href={`tel:${employee.phone}`} style={{ color: 'var(--text-muted)', padding: 4 }} title={employee.phone}>
                                                <Phone size={14} />
                                            </a>
                                            {canAddEdit && (
                                                <button
                                                    className="fresh-btn"
                                                    style={{ padding: '2px 6px', fontSize: 12, lineHeight: '20px', height: 26 }}
                                                    onClick={() => openEditDrawer(employee)}
                                                    title="Edit employee"
                                                >
                                                    <Edit2 size={14} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div className="fresh-section">
                    <div style={{ padding: '48px 24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                        No employees found
                    </div>
                </div>
            )}

            {/* Shift Summary */}
            <div className="fresh-section">
                <div className="fresh-section-header">
                    <span className="fresh-section-title">Shift Summary</span>
                </div>
                <div className="fresh-metrics">
                    {[
                        { label: 'Morning', count: shiftSummary.morning, total: totalEmployees },
                        { label: 'Evening', count: shiftSummary.evening, total: totalEmployees },
                        { label: 'Night', count: shiftSummary.night, total: totalEmployees }
                    ].map(shift => (
                        <div key={shift.label} className="fresh-metric">
                            <div className="fresh-metric-value">{shift.count}</div>
                            <div className="fresh-metric-label">{shift.label}</div>
                            <div className={`fresh-metric-trend ${shift.count > 0 ? 'up' : ''}`}>
                                {shift.total > 0 ? `${Math.round((shift.count / shift.total) * 100)}%` : '—'}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Add/Edit Drawer */}
            {isDrawerOpen && (
                <div className="drawer-overlay" onClick={resetForm} />
            )}
            <div className={`drawer-panel ${isDrawerOpen ? 'open' : ''}`}>
                <div className="drawer-header">
                    <h2 className="drawer-title">{editingEmployee ? 'Edit Employee' : 'Add Employee'}</h2>
                    <button className="drawer-close" onClick={resetForm}>
                        <X size={20} />
                    </button>
                </div>
                <div className="drawer-content">
                    <div className="form-group">
                        <label className="form-label">Name *</label>
                        <input
                            type="text"
                            name="name"
                            value={formData.name}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.name ? 'error' : ''}`}
                            placeholder="Employee name"
                        />
                        {formErrors.name && <span className="form-error">{formErrors.name}</span>}
                    </div>
                    <div className="form-group">
                        <label className="form-label">Email *</label>
                        <input
                            type="email"
                            name="email"
                            value={formData.email}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.email ? 'error' : ''}`}
                            placeholder="email@example.com"
                        />
                        {formErrors.email && <span className="form-error">{formErrors.email}</span>}
                    </div>
                    <div className="form-group">
                        <label className="form-label">Phone *</label>
                        <input
                            type="tel"
                            name="phone"
                            value={formData.phone}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.phone ? 'error' : ''}`}
                            placeholder="1234567890"
                        />
                        {formErrors.phone && <span className="form-error">{formErrors.phone}</span>}
                    </div>
                    <div className="form-group">
                        <label className="form-label">Role *</label>
                        <select
                            name="role"
                            value={formData.role}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.role ? 'error' : ''}`}
                        >
                            <option value="">Select role</option>
                            <option value="staff">Staff</option>
                            <option value="manager">Manager</option>
                            {isSuperadmin && <option value="superadmin">Superadmin</option>}
                        </select>
                        {formErrors.role && <span className="form-error">{formErrors.role}</span>}
                    </div>
                    {isSuperadmin && (
                        <div className="form-group">
                            <label className="form-label">Outlet *</label>
                            <select
                                name="outlet_id"
                                value={formData.outlet_id}
                                onChange={handleInputChange}
                                className={`form-input ${formErrors.outlet_id ? 'error' : ''}`}
                            >
                                <option value="">Select outlet</option>
                                {outletsData?.map(outlet => (
                                    <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                                ))}
                            </select>
                            {formErrors.outlet_id && <span className="form-error">{formErrors.outlet_id}</span>}
                        </div>
                    )}
                    <div className="form-group">
                        <label className="form-label">Shift *</label>
                        <select
                            name="shift"
                            value={formData.shift}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.shift ? 'error' : ''}`}
                        >
                            <option value="">Select shift</option>
                            <option value="Morning">Morning</option>
                            <option value="Evening">Evening</option>
                            <option value="Night">Night</option>
                        </select>
                        {formErrors.shift && <span className="form-error">{formErrors.shift}</span>}
                    </div>
                    <div className="form-group">
                        <label className="form-label">Salary</label>
                        <input
                            type="number"
                            name="salary"
                            value={formData.salary}
                            onChange={handleInputChange}
                            className="form-input"
                            placeholder="Annual salary"
                        />
                    </div>
                    <div className="form-group">
                        <label className="form-label">Joining Date *</label>
                        <input
                            type="date"
                            name="joining_date"
                            value={formData.joining_date}
                            onChange={handleInputChange}
                            className={`form-input ${formErrors.joining_date ? 'error' : ''}`}
                        />
                        {formErrors.joining_date && <span className="form-error">{formErrors.joining_date}</span>}
                    </div>
                </div>
                <div className="drawer-footer">
                    <button className="fresh-btn" onClick={resetForm}>Cancel</button>
                    <button
                        className="fresh-btn primary"
                        onClick={handleSubmit}
                        disabled={saveEmployeeMutation.isPending}
                    >
                        {saveEmployeeMutation.isPending ? 'Saving...' : 'Save'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Employees;
