import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, Tooltip, Legend, Filler,
} from 'chart.js';
import { Doughnut, Line } from 'react-chartjs-2';
import { LineChart as ForecastIcon } from 'lucide-react';

import api from '../lib/api';
import SEO from '../components/SEO';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

const PERIODS = [
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
  { label: '90D', value: '90d' },
  { label: 'Year', value: '365d' },
];
const COLORS = ['#8B5E3C', '#AEB784', '#622B14', '#5D7B6F', '#D97706', '#64748B'];
const money = (value) => `₹${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

export default function Analytics() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState('30d');

  const { data: summary = {}, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: () => api.get('/api/v1/analytics/dashboard/summary').then((response) => response.data),
  });
  const { data: trend = [], isLoading: trendLoading } = useQuery({
    queryKey: ['analytics-trend', period],
    queryFn: () => api.get('/api/v1/analytics/dashboard/revenue-trend', { params: { period } }).then((response) => response.data),
  });
  const { data: categories = { data: [] }, isLoading: categoryLoading } = useQuery({
    queryKey: ['analytics-categories', period],
    queryFn: () => api.get('/api/v1/analytics/dashboard/category-breakdown', { params: { period } }).then((response) => response.data),
  });
  const { data: products = [], isLoading: productsLoading } = useQuery({
    queryKey: ['analytics-products', period],
    queryFn: () => api.get('/api/v1/analytics/dashboard/top-products', { params: { limit: 10, period } }).then((response) => response.data),
  });
  const { data: outlets = [], isLoading: outletsLoading } = useQuery({
    queryKey: ['analytics-outlets', period],
    queryFn: () => api.get('/api/v1/analytics/dashboard/outlet-performance', { params: { period } }).then((response) => response.data),
  });

  const totals = useMemo(() => {
    const revenue = trend.reduce((sum, point) => sum + Number(point.revenue || 0), 0);
    const transactions = outlets.reduce((sum, outlet) => sum + Number(outlet.transactions || 0), 0);
    return { revenue, transactions, average: transactions ? revenue / transactions : 0 };
  }, [trend, outlets]);

  const lineData = {
    labels: trend.map((point) => new Date(point.date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })),
    datasets: [{
      label: 'Recorded revenue',
      data: trend.map((point) => point.revenue),
      borderColor: '#8B5E3C',
      backgroundColor: 'rgba(139,94,60,0.15)',
      fill: true,
      tension: 0.25,
    }],
  };
  const categoryRows = categories.data || [];
  const categoryData = {
    labels: categoryRows.map((row) => row.category),
    datasets: [{ data: categoryRows.map((row) => row.revenue), backgroundColor: COLORS, borderWidth: 0 }],
  };
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { color: '#64748b' } } },
    scales: {
      x: { ticks: { color: '#64748b', maxTicksLimit: 12 }, grid: { color: 'rgba(100,116,139,.1)' } },
      y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(100,116,139,.1)' } },
    },
  };
  const isLoading = summaryLoading || trendLoading || categoryLoading || productsLoading || outletsLoading;

  return (
    <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
      <SEO title="Sales Analytics" description="Database-backed sales, product, category, and outlet analytics" />
      <div className="content-section" style={{ display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'center' }}>
        <div>
          <h1 className="page-title">Sales Analytics</h1>
          <p style={{ color: 'var(--c-ink-muted)', margin: '4px 0 0', fontSize: 12 }}>Every value below is calculated from recorded sales.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="action-btn" onClick={() => navigate('/forecasts')}><ForecastIcon size={14} /> Forecasts</button>
        </div>
      </div>

      <div className="content-section">
        <div className="filter-bar" style={{ justifyContent: 'flex-end' }}>
          {PERIODS.map((item) => (
            <button key={item.value} className={`action-btn ${period === item.value ? 'primary' : ''}`} onClick={() => setPeriod(item.value)}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="kpi-strip">
        <div className="kpi-cell"><div className="kpi-label">Period Revenue</div><div className="kpi-value brown">{money(totals.revenue)}</div></div>
        <div className="kpi-cell"><div className="kpi-label">Transactions</div><div className="kpi-value">{totals.transactions.toLocaleString('en-IN')}</div></div>
        <div className="kpi-cell"><div className="kpi-label">Average Order</div><div className="kpi-value sage">{money(totals.average)}</div></div>
        <div className="kpi-cell"><div className="kpi-label">Today</div><div className="kpi-value">{money(summary.total_revenue_today)}</div><div className="kpi-delta">{summary.total_transactions_today || 0} orders</div></div>
      </div>

      <div className="content-section-alt">
        <div className="zone-label">Revenue trend</div>
        <div style={{ height: 320, marginTop: 12 }}>
          {isLoading ? <div className="skeleton-chart" /> : trend.length ? <Line data={lineData} options={chartOptions} /> : <div className="empty-state"><p className="empty-state-desc">No recorded sales in this period.</p></div>}
        </div>
      </div>

      <div className="content-section" style={{ padding: 0 }}>
        <div className="two-col">
          <div className="col-body">
            <div className="zone-label">Category mix</div>
            <div style={{ height: 300, marginTop: 12 }}>
              {categoryRows.length ? <Doughnut data={categoryData} options={{ responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }} /> : <div className="empty-state"><p className="empty-state-desc">No categorized sales available.</p></div>}
            </div>
          </div>
          <div className="col-divider" />
          <div className="col-body">
            <div className="zone-label">Top products</div>
            <div className="rank-list" style={{ marginTop: 12 }}>
              {products.length ? products.map((product, index) => (
                <div className="rank-row" key={`${product.name}-${index}`}>
                  <div className="rank-num">#{index + 1}</div>
                  <div className="rank-name">{product.name}<small style={{ display: 'block', color: 'var(--c-ink-muted)' }}>{product.category}</small></div>
                  <div className="rank-value">{money(product.revenue)}</div>
                  <div className="rank-value">{product.quantity_sold} units</div>
                </div>
              )) : <div className="empty-state"><p className="empty-state-desc">No product sales available.</p></div>}
            </div>
          </div>
        </div>
      </div>

      <div className="content-section-alt">
        <div className="zone-label">Outlet performance</div>
        <div style={{ overflowX: 'auto', marginTop: 12 }}>
          <table className="eris-table" style={{ width: '100%' }}>
            <thead><tr><th>Outlet</th><th>City</th><th style={{ textAlign: 'right' }}>Revenue</th><th style={{ textAlign: 'right' }}>Transactions</th></tr></thead>
            <tbody>{outlets.map((outlet) => <tr key={outlet.outlet_id}><td>{outlet.outlet_name}</td><td>{outlet.city}</td><td className="mono" style={{ textAlign: 'right' }}>{money(outlet.revenue)}</td><td className="mono" style={{ textAlign: 'right' }}>{outlet.transactions}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
