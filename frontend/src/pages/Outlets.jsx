import React, { useState, useMemo } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { MapPin, Phone, Mail, Users, TrendingUp, Plus, Edit, Trash2, Eye, Search, Filter, Clock, AlertCircle } from 'lucide-react';
import api from '../services/api';
import Badge from '../components/ui/Badge';
import '../styles/outlets.css';

const Outlets = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedStatus, setSelectedStatus] = useState('');
    const [selectedCity, setSelectedCity] = useState('');
    const [selectedOutlet, setSelectedOutlet] = useState(null);
    const [isDetailsOpen, setIsDetailsOpen] = useState(false);
    // eslint-disable-next-line no-unused-vars
    const [isAddFormOpen, setIsAddFormOpen] = useState(false);

    // Fetch outlets data
    const { data: outletsData, isLoading, refetch } = useQuery({
        queryKey: ['outlets', selectedStatus, selectedCity],
        queryFn: () => {
            const params = new URLSearchParams();
            if (selectedStatus) params.append('status', selectedStatus);
            if (selectedCity) params.append('city', selectedCity);
            return api.get(`/api/v1/outlets?${params}`).then(r => r.data.data || []);
        },
        staleTime: 30000
    });

    // Filter outlets
    const filteredOutlets = useMemo(() => {
        if (!outletsData) return [];
        return outletsData.filter(outlet => {
            const matchSearch = outlet.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                outlet.city?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                outlet.phone?.includes(searchQuery);
            return matchSearch;
        });
    }, [outletsData, searchQuery]);

    // Get unique cities
    const cities = useMemo(() => {
        if (!outletsData) return [];
        return [...new Set(outletsData.map(o => o.city).filter(Boolean))];
    }, [outletsData]);

    // Delete outlet mutation
    const deleteOutletMutation = useMutation({
        mutationFn: (id) => api.delete(`/api/v1/outlets/${id}`),
        onSuccess: () => {
            refetch();
        }
    });

    const openOutletDetails = (outlet) => {
        setSelectedOutlet(outlet);
        setIsDetailsOpen(true);
    };

    const closeOutletDetails = () => {
        setIsDetailsOpen(false);
        setTimeout(() => setSelectedOutlet(null), 300);
    };

    const handleDeleteOutlet = (id) => {
        if (window.confirm('Are you sure you want to delete this outlet?')) {
            deleteOutletMutation.mutate(id);
        }
    };

    // Format currency
    const formatCurrency = (value) => {
        // eslint-disable-next-line no-undef
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(value || 0);
    };

    const getStatusColor = (status) => {
        switch(status) {
            case 'active': return 'success';
            case 'inactive': return 'secondary';
            case 'maintenance': return 'warning';
            default: return 'secondary';
        }
    };

    // Skeleton loader
    if (isLoading) {
        return (
            <div className="outlets-container">
                <div className="outlets-header">
                    <h1 className="outlets-title">Outlets & Stores</h1>
                </div>
                <div className="skeleton-filters"></div>
                <div className="skeleton-grid"></div>
            </div>
        );
    }

    return (
        <div className="outlets-container">
            {/* Header */}
            <div className="outlets-header">
                <div className="outlets-title-group">
                    <h1 className="outlets-title">Outlets & Stores</h1>
                    <span className="outlets-count-badge">{filteredOutlets.length}</span>
                </div>
                <button className="btn-add-outlet" onClick={() => setIsAddFormOpen(true)}>
                    <Plus size={18} />
                    Add Outlet
                </button>
            </div>

            {/* Filters */}
            <div className="outlets-filters">
                <div className="filter-search">
                    <Search size={18} className="filter-search-icon" />
                    <input
                        type="text"
                        placeholder="Search by name, city, or phone..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="filter-input"
                    />
                </div>
                <select value={selectedCity} onChange={(e) => setSelectedCity(e.target.value)} className="filter-select">
                    <option value="">All Cities</option>
                    {cities.map(city => (
                        <option key={city} value={city}>{city}</option>
                    ))}
                </select>
                <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)} className="filter-select">
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="maintenance">Maintenance</option>
                </select>
            </div>

            {/* Outlets Grid */}
            {filteredOutlets.length > 0 ? (
                <div className="outlets-grid">
                    {filteredOutlets.map((outlet) => (
                        <div key={outlet.id} className="outlet-card">
                            <div className="outlet-card-header">
                                <div className="outlet-info-header">
                                    <h3 className="outlet-name">{outlet.name}</h3>
                                    <Badge variant={getStatusColor(outlet.status)} size="sm">
                                        {outlet.status}
                                    </Badge>
                                </div>
                                <div className="outlet-menu">
                                    <button className="menu-button" onClick={() => openOutletDetails(outlet)} title="View Details">
                                        <Eye size={16} />
                                    </button>
                                    <button className="menu-button" title="Edit">
                                        <Edit size={16} />
                                    </button>
                                    <button className="menu-button delete" onClick={() => handleDeleteOutlet(outlet.id)} title="Delete">
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            {/* Location Info */}
                            <div className="outlet-location">
                                <MapPin size={16} />
                                <div className="location-text">
                                    <p className="location-address">{outlet.address}</p>
                                    <p className="location-city">{outlet.city}, {outlet.state} {outlet.postal_code}</p>
                                </div>
                            </div>

                            {/* Contact Info */}
                            <div className="outlet-contacts">
                                <div className="contact-item">
                                    <Phone size={14} />
                                    <a href={`tel:${outlet.phone}`}>{outlet.phone}</a>
                                </div>
                                <div className="contact-item">
                                    <Mail size={14} />
                                    <a href={`mailto:${outlet.email}`}>{outlet.email}</a>
                                </div>
                            </div>

                            {/* Metrics */}
                            <div className="outlet-metrics">
                                <div className="metric">
                                    <Users size={14} />
                                    <div className="metric-content">
                                        <div className="metric-label">Staff</div>
                                        <div className="metric-value">{outlet.staff_count || 0}</div>
                                    </div>
                                </div>
                                <div className="metric">
                                    <TrendingUp size={14} />
                                    <div className="metric-content">
                                        <div className="metric-label">Revenue</div>
                                        <div className="metric-value">{formatCurrency(outlet.monthly_revenue)}</div>
                                    </div>
                                </div>
                                <div className="metric">
                                    <Clock size={14} />
                                    <div className="metric-content">
                                        <div className="metric-label">Hours</div>
                                        <div className="metric-value">{outlet.opening_time} - {outlet.closing_time}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="outlet-footer">
                                <span className="outlet-id">ID: {outlet.code}</span>
                                <span className="outlet-since">Since {new Date(outlet.created_at).getFullYear()}</span>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="outlets-empty">
                    <MapPin size={48} />
                    <p>No outlets found</p>
                </div>
            )}

            {/* Details Modal */}
            {isDetailsOpen && selectedOutlet && (
                <div className={`outlet-modal ${isDetailsOpen ? 'open' : ''}`} onClick={closeOutletDetails}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h2 className="modal-title">{selectedOutlet.name}</h2>
                            <button className="modal-close" onClick={closeOutletDetails}>×</button>
                        </div>
                        <div className="modal-body">
                            {/* Status */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Status</h3>
                                <Badge variant={getStatusColor(selectedOutlet.status)} size="md">
                                    {selectedOutlet.status}
                                </Badge>
                            </div>

                            {/* Location Details */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Location Details</h3>
                                <div className="detail-grid">
                                    <div className="detail-field">
                                        <label>Address</label>
                                        <p>{selectedOutlet.address}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>City</label>
                                        <p>{selectedOutlet.city}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>State</label>
                                        <p>{selectedOutlet.state}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Postal Code</label>
                                        <p>{selectedOutlet.postal_code}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Contact Information */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Contact Information</h3>
                                <div className="detail-grid">
                                    <div className="detail-field">
                                        <label>Phone</label>
                                        <p><a href={`tel:${selectedOutlet.phone}`}>{selectedOutlet.phone}</a></p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Email</label>
                                        <p><a href={`mailto:${selectedOutlet.email}`}>{selectedOutlet.email}</a></p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Manager</label>
                                        <p>{selectedOutlet.manager_name || '-'}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Manager Phone</label>
                                        <p>{selectedOutlet.manager_phone || '-'}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Operating Hours */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Operating Hours</h3>
                                <div className="detail-grid">
                                    <div className="detail-field">
                                        <label>Opening Time</label>
                                        <p>{selectedOutlet.opening_time}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Closing Time</label>
                                        <p>{selectedOutlet.closing_time}</p>
                                    </div>
                                    <div className="detail-field">
                                        <label>Days Open</label>
                                        <p>{selectedOutlet.days_open || 'All Days'}</p>
                                    </div>
                                </div>
                            </div>

                            {/* Performance Metrics */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Performance Metrics</h3>
                                <div className="detail-grid metrics-grid">
                                    <div className="metric-card">
                                        <div className="metric-label">Monthly Revenue</div>
                                        <div className="metric-value">{formatCurrency(selectedOutlet.monthly_revenue)}</div>
                                    </div>
                                    <div className="metric-card">
                                        <div className="metric-label">Annual Revenue</div>
                                        <div className="metric-value">{formatCurrency(selectedOutlet.annual_revenue)}</div>
                                    </div>
                                    <div className="metric-card">
                                        <div className="metric-label">Staff Count</div>
                                        <div className="metric-value">{selectedOutlet.staff_count || 0}</div>
                                    </div>
                                    <div className="metric-card">
                                        <div className="metric-label">Customer Count</div>
                                        <div className="metric-value">{selectedOutlet.customer_count || 0}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Inventory */}
                            <div className="detail-section">
                                <h3 className="detail-section-title">Inventory Status</h3>
                                <div className="inventory-info">
                                    <div className="inventory-item">
                                        <span>Total Items</span>
                                        <strong>{selectedOutlet.inventory_count || 0}</strong>
                                    </div>
                                    <div className="inventory-item warning">
                                        <span>Low Stock</span>
                                        <strong>{selectedOutlet.low_stock_count || 0}</strong>
                                    </div>
                                </div>
                            </div>

                            {/* Additional Info */}
                            {selectedOutlet.notes && (
                                <div className="detail-section">
                                    <h3 className="detail-section-title">Notes</h3>
                                    <p className="detail-notes">{selectedOutlet.notes}</p>
                                </div>
                            )}
                        </div>
                        <div className="modal-footer">
                            <button className="btn-close" onClick={closeOutletDetails}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Outlets;
