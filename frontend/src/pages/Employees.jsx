import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X, Mail, Phone, Store, Edit2, Search } from 'lucide-react';
import api from '../services/api';
import Badge from '../components/ui/Badge';
import '../styles/employees.css';

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
        staleTime: 30000
    });

    const { data: employeesData, isLoading } = useQuery({
        queryKey: ['employees'],
        queryFn: () => api.get('/api/v1/employees').then(r => r.data.data || []),
        staleTime: 30000
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
            <div className="employees-container">
                <div className="employees-header">
                    <div className="employees-title-group">
                        <h1 className="employees-title">Employees</h1>
                        <span className="employees-count-badge">--</span>
                    </div>
                </div>
                <div className="employees-grid">
                    {Array(6).fill(0).map((_, i) => (
                        <div key={i} className="employee-card employee-skeleton">
                            <div className="skeleton-avatar"></div>
                            <div className="skeleton-line" style={{ width: '70%', height: '16px', marginTop: '12px' }}></div>
                            <div className="skeleton-line" style={{ width: '50%', height: '14px', marginTop: '8px' }}></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="employees-container">
            {/* Header */}
            <div className="employees-header">
                <div className="employees-title-group">
                    <h1 className="employees-title">Employees</h1>
                    <span className="employees-count-badge">{totalEmployees}</span>
                </div>
                {canAddEdit && (
                    <button className="employees-add-button" onClick={openAddDrawer}>
                        + Add Employee
                    </button>
                )}
            </div>

            {/* Filter Bar */}
            <div className="employees-filters">
                <div className="filter-search">
                    <Search size={18} className="filter-search-icon" />
                    <input
                        type="text"
                        placeholder="Search by name or email..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="filter-input"
                    />
                </div>
                <select value={selectedOutlet} onChange={(e) => setSelectedOutlet(e.target.value)} className="filter-select">
                    <option value="">All Outlets</option>
                    {outletsData?.map(outlet => (
                        <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
                    ))}
                </select>
                <select value={selectedShift} onChange={(e) => setSelectedShift(e.target.value)} className="filter-select">
                    <option value="">All Shifts</option>
                    <option value="Morning">Morning</option>
                    <option value="Evening">Evening</option>
                    <option value="Night">Night</option>
                </select>
                <select value={selectedRole} onChange={(e) => setSelectedRole(e.target.value)} className="filter-select">
                    <option value="">All Roles</option>
                    {rolesList.map(role => (
                        <option key={role} value={role}>{role}</option>
                    ))}
                </select>
            </div>

            {/* Employee Cards Grid */}
            {filteredEmployees.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredEmployees.map(employee => (
                        <div key={employee.id} className="employee-card">
                            <div className="employee-avatar" style={{ backgroundColor: getAvatarColor(employee.name) }}>
                                <span className="avatar-initials">{getInitials(employee.name)}</span>
                            </div>
                            <div className="employee-info">
                                <div className="employee-name-row">
                                    <h3 className="employee-name">{employee.name}</h3>
                                    <Badge variant={employee.role === 'manager' ? 'primary' : 'secondary'} size="sm">
                                        {employee.role}
                                    </Badge>
                                </div>
                                <div className="employee-outlet">
                                    <Store size={14} />
                                    <span>{outletsData?.find(o => o.id === employee.outlet_id)?.name || 'Unknown'}</span>
                                </div>
                                <div className="employee-shift">
                                    <Badge 
                                        variant={
                                            employee.shift === 'Morning' ? 'info' :
                                            employee.shift === 'Evening' ? 'warning' : 'accent'
                                        }
                                        size="sm"
                                    >
                                        {employee.shift}
                                    </Badge>
                                </div>
                                <div className="employee-date">
                                    Joined {new Date(employee.joining_date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                                </div>
                                <div className="employee-links">
                                    <a href={`mailto:${employee.email}`} className="link-icon" title={employee.email}>
                                        <Mail size={16} />
                                    </a>
                                    <a href={`tel:${employee.phone}`} className="link-icon" title={employee.phone}>
                                        <Phone size={16} />
                                    </a>
                                </div>
                            </div>
                            {canAddEdit && (
                                <button className="employee-edit-button" onClick={() => openEditDrawer(employee)} title="Edit employee">
                                    <Edit2 size={16} />
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <div className="employees-empty">
                    <p>No employees found</p>
                </div>
            )}

            {/* Shift Summary */}
            <div className="shift-summary">
                <h2 className="shift-summary-title">Shift Summary</h2>
                <div className="shift-cards">
                    {[
                        { label: 'Morning', count: shiftSummary.morning, total: totalEmployees, color: '#3B82F6' },
                        { label: 'Evening', count: shiftSummary.evening, total: totalEmployees, color: '#F59E0B' },
                        { label: 'Night', count: shiftSummary.night, total: totalEmployees, color: '#6D28D9' }
                    ].map(shift => (
                        <div key={shift.label} className="shift-card">
                            <div className="shift-donut">
                                <svg viewBox="0 0 100 100">
                                    <circle cx="50" cy="50" r="45" fill="none" stroke="#E5E7EB" strokeWidth="8" />
                                    <circle 
                                        cx="50" cy="50" r="45" fill="none" stroke={shift.color} strokeWidth="8"
                                        strokeDasharray={`${shift.count * 282.7 / (shift.total || 1)} 282.7`}
                                        strokeLinecap="round"
                                    />
                                </svg>
                                <div className="donut-center">{shift.count}</div>
                            </div>
                            <div className="shift-label">{shift.label}</div>
                            <div className="shift-percentage">{shift.total > 0 ? Math.round((shift.count / shift.total) * 100) : 0}%</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Add/Edit Drawer */}
            <div className={`employees-drawer ${isDrawerOpen ? 'open' : ''}`}>
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
                    <button className="button-cancel" onClick={resetForm}>Cancel</button>
                    <button 
                        className="button-save" 
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
