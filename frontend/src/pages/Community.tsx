// @ts-nocheck
import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Truck, Plus, Tag, ArrowLeftRight, Heart, Store, Package, Search, RefreshCw } from 'lucide-react';
import { PageHeader, MetricCard, Badge, Button, EmptyState } from '../components/ui';
import { communityAPI, inventoryAPI } from '../services/api';
import { fmtINR, fmtDate } from '../utils/format';

const MOCK_LISTINGS = [
  { id:1, product_name:"Haldiram Bhujia 200g", product_category:"Snacks", product_sku:"SKU0012", outlet_name:"Mumbai Andheri", outlet_city:"Mumbai", listing_type:"sell", condition:"new", quantity_available:80, asking_price_per_unit:105, total_value:8400, expiry_date:null, notes:"Excess stock from festival season", status:"active", listed_at: new Date(Date.now()-86400000).toISOString() },
  { id:2, product_name:"Amul Dahi 400g", product_category:"Dairy", product_sku:"SKU0008", outlet_name:"Pune Koregaon", outlet_city:"Pune", listing_type:"sell", condition:"near_expiry", quantity_available:25, asking_price_per_unit:42, total_value:1050, expiry_date:"2026-04-10", notes:"Near expiry — 15 days. Selling at cost.", status:"active", listed_at: new Date(Date.now()-3600000).toISOString() },
  { id:3, product_name:"Lays Classic 26g", product_category:"Snacks", product_sku:"SKU0010", outlet_name:"Jaipur MI Road", outlet_city:"Jaipur", listing_type:"trade", condition:"new", quantity_available:200, asking_price_per_unit:18, total_value:3600, expiry_date:null, notes:"Want to trade for Kurkure or beverages", status:"active", listed_at: new Date(Date.now()-172800000).toISOString() },
  { id:4, product_name:"Red Bull 250ml", product_category:"Beverages", product_sku:"SKU0030", outlet_name:"Bangalore Koramangala", outlet_city:"Bangalore", listing_type:"sell", condition:"new", quantity_available:36, asking_price_per_unit:132, total_value:4752, expiry_date:"2026-08-20", notes:null, status:"active", listed_at: new Date(Date.now()-259200000).toISOString() },
  { id:5, product_name:"Maggi 2min Noodles 70g", product_category:"Packaged Food", product_sku:"SKU0024", outlet_name:"Ahmedabad CG Road", outlet_city:"Ahmedabad", listing_type:"donate", condition:"near_expiry", quantity_available:60, asking_price_per_unit:0, total_value:0, expiry_date:"2026-04-05", notes:"Near expiry — donating to avoid waste", status:"active", listed_at: new Date(Date.now()-43200000).toISOString() },
];

function timeAgo(dateStr: string) {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '—';
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function ListingCard({ listing, onExpressInterest, isInterested }: { listing: any, onExpressInterest: (id: number) => void, isInterested: boolean }) {
  const typeColors = {
    sell: 'success',
    trade: 'info',
    donate: 'warning'
  };
  
  const typeLabels = {
    sell: 'For Sale',
    trade: 'For Trade',
    donate: 'Donate'
  };

  const conditionDisplay = {
    new: { label: 'New', variant: 'success' },
    near_expiry: { label: 'Near Expiry ⚠️', variant: 'warning' },
    returned: { label: 'Returned', variant: 'default' }
  };

  const cond = conditionDisplay[listing.condition] || { label: listing.condition, variant: 'default' };

  return (
    <div className={`border rounded-lg overflow-hidden transition-all hover:shadow-md hover:-translate-y-0.5 bg-white`}>
      {/* Header strip */}
      <div className={`h-0.5 bg-${typeColors[listing.listing_type]}`}></div>
      
      <div className="p-4">
        {/* Header row */}
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-sm font-bold text-gray-900 flex-1 pr-2">{listing.product_name}</h3>
          <Badge variant={typeColors[listing.listing_type]} size="sm">{typeLabels[listing.listing_type]}</Badge>
        </div>

        {/* Product info */}
        <div className="flex items-center gap-2 mb-2">
          <Badge variant="outline" size="xs">{listing.product_category}</Badge>
          <code className="text-xs text-gray-500 font-mono">{listing.product_sku}</code>
        </div>

        {/* Outlet info */}
        <div className="flex items-center gap-1.5 mb-3 text-xs text-gray-600">
          <Store size={14} />
          <span>{listing.outlet_name}, {listing.outlet_city}</span>
        </div>

        {/* Condition */}
        <div className="flex items-center gap-2 mb-3">
          <Badge variant={cond.variant} size="sm">{cond.label}</Badge>
          {listing.condition === 'near_expiry' && listing.expiry_date && (
            <span className="text-xs text-red-600 font-medium">Expires: {fmtDate(listing.expiry_date)}</span>
          )}
        </div>

        {/* Price and quantity */}
        <div className="mb-3 p-2 bg-gray-50 rounded">
          <div className="flex items-baseline gap-1">
            <span className="text-xl font-bold text-gray-900">{listing.quantity_available}</span>
            <span className="text-xs text-gray-600">units</span>
          </div>
          {listing.listing_type !== 'donate' ? (
            <div className="text-xs text-gray-600 mt-1">
              @ {fmtINR(listing.asking_price_per_unit)}/unit • Total: {fmtINR(listing.total_value)}
            </div>
          ) : (
            <div className="text-xs text-green-600 font-medium mt-1">FREE — Community contribution</div>
          )}
        </div>

        {/* Notes */}
        {listing.notes && (
          <p className="text-xs text-gray-600 italic mb-3 line-clamp-2">{listing.notes}</p>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <span className="text-xs text-gray-500">{timeAgo(listing.listed_at)}</span>
          <Button
            size="sm"
            variant={isInterested ? 'secondary' : 'primary'}
            onClick={() => onExpressInterest(listing.id)}
            disabled={isInterested}
          >
            {isInterested ? '✓ Interested' : 'Express Interest'}
          </Button>
        </div>
      </div>
    </div>
  );
}

function CreateListingModal({ isOpen, onClose, onSuccess }: { isOpen: boolean, onClose: () => void, onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    product_id: '',
    quantity: '',
    price_per_unit: '',
    listing_type: 'sell',
    condition: 'new',
    expiry_date: '',
    notes: ''
  });

  const { data: products } = useQuery({
    queryKey: ['inventory-products'],
    queryFn: () => inventoryAPI.list({ limit: 1000 }),
    enabled: isOpen
  });

  const createMutation = useMutation({
    mutationFn: (data: any) => communityAPI.createListing(data),
    onSuccess: () => {
      onSuccess();
      onClose();
      setFormData({
        product_id: '',
        quantity: '',
        price_per_unit: '',
        listing_type: 'sell',
        condition: 'new',
        expiry_date: '',
        notes: ''
      });
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-bold">List Excess Stock</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <form onSubmit={(e) => {
          e.preventDefault();
          createMutation.mutate(formData);
        }} className="space-y-4">
          {/* Product dropdown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product</label>
            <select
              value={formData.product_id}
              onChange={(e) => {
                const product = products?.find(p => p.id === parseInt(e.target.value));
                setFormData(prev => ({
                  ...prev,
                  product_id: e.target.value,
                  price_per_unit: product?.selling_price || ''
                }));
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              required
            >
              <option value="">Select a product...</option>
              {products?.map(p => (
                <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
              ))}
            </select>
          </div>

          {/* Quantity */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Quantity (units)</label>
            <input
              type="number"
              min="1"
              value={formData.quantity}
              onChange={(e) => setFormData(prev => ({ ...prev, quantity: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              required
            />
          </div>

          {/* Price per unit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Price per unit (₹)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={formData.price_per_unit}
              onChange={(e) => setFormData(prev => ({ ...prev, price_per_unit: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          {/* Listing type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Listing Type</label>
            <div className="flex gap-4">
              {['sell', 'trade', 'donate'].map(type => (
                <label key={type} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="listing_type"
                    value={type}
                    checked={formData.listing_type === type}
                    onChange={(e) => setFormData(prev => ({ ...prev, listing_type: e.target.value }))}
                  />
                  <span className="text-sm capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Condition */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
            <select
              value={formData.condition}
              onChange={(e) => setFormData(prev => ({ ...prev, condition: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
            >
              <option value="new">New</option>
              <option value="near_expiry">Near Expiry</option>
              <option value="returned">Returned</option>
            </select>
          </div>

          {/* Expiry date (conditional) */}
          {formData.condition === 'near_expiry' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
              <input
                type="date"
                value={formData.expiry_date}
                onChange={(e) => setFormData(prev => ({ ...prev, expiry_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              />
            </div>
          )}

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
              rows={3}
              placeholder="e.g., Excess stock from festival season..."
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-2 pt-4">
            <Button variant="secondary" onClick={onClose} className="flex-1">Cancel</Button>
            <Button variant="primary" type="submit" loading={createMutation.isPending} className="flex-1">List Stock</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

export default function Community() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [conditionFilter, setConditionFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [interestedListings, setInterestedListings] = useState(new Set());
  const queryClient = useQueryClient();

  // Fetch listings
  const { data: listings, refetch } = useQuery({
    queryKey: ['community-listings'],
    queryFn: () => communityAPI.listings(),
    placeholderData: MOCK_LISTINGS
  });

  // Fetch stats
  const stats = {
    total_listings: MOCK_LISTINGS.length,
    sell_listings: MOCK_LISTINGS.filter(l => l.listing_type === 'sell').length,
    trade_listings: MOCK_LISTINGS.filter(l => l.listing_type === 'trade').length,
    donate_listings: MOCK_LISTINGS.filter(l => l.listing_type === 'donate').length
  };

  // Express interest mutation
  const interestMutation = useMutation({
    mutationFn: (id: number) => communityAPI.expressInterest(id),
    onSuccess: (_, id) => {
      setInterestedListings(prev => new Set(prev).add(id));
    }
  });

  // Filter listings
  const filteredListings = useMemo(() => {
    return (listings || []).filter((listing: any) => {
      const matchesSearch = !searchQuery || 
        listing.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        listing.outlet_name.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesType = typeFilter === 'all' || listing.listing_type === typeFilter;
      const matchesCondition = conditionFilter === 'all' || listing.condition === conditionFilter;
      
      return matchesSearch && matchesType && matchesCondition;
    });
  }, [listings, searchQuery, typeFilter, conditionFilter]);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader 
        title="Community Marketplace"
        subtitle="Trade and sell excess inventory between outlets"
        actions={
          <div className="flex gap-2">
            <Button 
              variant="primary" 
              icon={Plus}
              onClick={() => setShowCreateModal(true)}
            >
              List Excess Stock
            </Button>
            <Button 
              variant="ghost"
              icon={RefreshCw}
              onClick={() => refetch()}
            />
          </div>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Active Listings"
          value={stats?.total_listings || 0}
          icon={Truck}
          variant="accent"
        />
        <MetricCard
          label="For Sale"
          value={stats?.sell_listings || 0}
          icon={Tag}
          variant="success"
        />
        <MetricCard
          label="For Trade"
          value={stats?.trade_listings || 0}
          icon={ArrowLeftRight}
          variant="info"
        />
        <MetricCard
          label="Donations"
          value={stats?.donate_listings || 0}
          icon={Heart}
          variant="warning"
        />
      </div>

      {/* Filter bar */}
      <Card>
        <div className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 text-gray-400" size={18} />
            <input
              type="text"
              placeholder="Search products, outlets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm"
            />
          </div>

          {/* Type filters */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs font-medium text-gray-600 mr-2 self-center">Type:</span>
            {['all', 'sell', 'trade', 'donate'].map(type => (
              <button
                key={type}
                onClick={() => setTypeFilter(type)}
                className={`px-3 py-1.5 text-xs rounded-full font-medium transition-colors ${
                  typeFilter === type
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {type === 'all' ? 'All' : type === 'sell' ? 'For Sale' : type === 'trade' ? 'For Trade' : 'Donations'}
              </button>
            ))}
          </div>

          {/* Condition filters */}
          <div className="flex flex-wrap gap-2">
            <span className="text-xs font-medium text-gray-600 mr-2 self-center">Condition:</span>
            {['all', 'new', 'near_expiry', 'returned'].map(cond => (
              <button
                key={cond}
                onClick={() => setConditionFilter(cond)}
                className={`px-3 py-1.5 text-xs rounded-full font-medium transition-colors ${
                  conditionFilter === cond
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {cond === 'all' ? 'All' : cond === 'new' ? 'New' : cond === 'near_expiry' ? 'Near Expiry' : 'Returned'}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Listings grid */}
      {filteredListings.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No listings found"
          message={searchQuery || typeFilter !== 'all' || conditionFilter !== 'all' ? 'Try adjusting your filters' : 'Be the first to list excess stock'}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredListings.map((listing: any) => (
            <ListingCard
              key={listing.id}
              listing={listing}
              onExpressInterest={(id: number) => interestMutation.mutate(id)}
              isInterested={interestedListings.has(listing.id)}
            />
          ))}
        </div>
      )}

      {/* Create Modal */}
      <CreateListingModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['community-listings', 'community-stats'] })}
      />
    </div>
  );
}
