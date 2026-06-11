import React, { useState, useMemo, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  ComposedChart, AreaChart, BarChart, Area, Line, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine
} from 'recharts';
import { ChevronDown, TrendingUp, Calendar, AlertCircle } from 'lucide-react';
import api, { authAPI } from '../services/api';
import StatCard from '../components/ui/StatCard';
import Badge from '../components/ui/Badge';
import '../styles/forecasting.css';

// Skeleton Components
const ChartSkeleton = () => (
  <div className="skeleton-chart">
    <div className="skeleton-line" style={{ width: '100%', height: '300px' }} />
  </div>
);

const TableSkeleton = () => (
  <div className="skeleton-table">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="skeleton-row">
        <div className="skeleton-cell" style={{ flex: 1 }} />
        <div className="skeleton-cell" style={{ flex: 1 }} />
        <div className="skeleton-cell" style={{ flex: 1 }} />
        <div className="skeleton-cell" style={{ flex: 1 }} />
        <div className="skeleton-cell" style={{ flex: 1 }} />
      </div>
    ))}
  </div>
);

// Format currency with Indian rupees
const fmtINR = (value) => {
  if (!value && value !== 0) return '₹0';
  return '₹' + Math.floor(value).toLocaleString('en-IN');
};

// Format percentage
const fmtPercent = (value) => {
  if (!value && value !== 0) return '0%';
  return Math.round(value * 10) / 10 + '%';
};

export default function Forecasting() {
  // State
  const [selectedOutlet, setSelectedOutlet] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState('all');
  const [forecastPeriod, setForecastPeriod] = useState(30);
  const [expandedFactors, setExpandedFactors] = useState(false);
  const [isGeneratingForecast, setIsGeneratingForecast] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const elapsedRef = useRef(0);

  React.useEffect(() => {
    if (!isGeneratingForecast) return;

    elapsedRef.current = 0;
    setElapsedTime(0);
    
    const interval = setInterval(() => {
      elapsedRef.current += 1;
      setElapsedTime(elapsedRef.current);
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isGeneratingForecast]);

  // Get User Context
  const { data: userData } = useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      const response = await authAPI.getUser();
      return response.data;
    },
  });
  
  const isSuperAdmin = userData?.role === 'super_admin';

  // Fetch Outlets
  const { data: outletsData } = useQuery({
    queryKey: ['outlets'],
    queryFn: async () => {
      const response = await api.get('/api/v1/outlets');
      return response.data;
    },
    enabled: isSuperAdmin,
  });

  // Fetch Products
  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: async () => {
      const response = await api.get('/api/v1/products');
      return response.data;
    },
  });

  // Fetch Sales Forecast
  const { data: salesForecastData, isLoading: salesLoading, refetch: refetchSalesForecast } = useQuery({
    queryKey: ['sales-forecast', selectedOutlet, selectedProduct, forecastPeriod],
    queryFn: async () => {
      setIsGeneratingForecast(true);
      setElapsedTime(0);
      try {
        const params = { days: forecastPeriod };
        if (selectedOutlet !== 'all') params.outlet_id = selectedOutlet;
        if (selectedProduct !== 'all') params.product_id = selectedProduct;
        
        const response = await api.get('/api/v1/forecasting/sales', { params });
        return response.data;
      } finally {
        setIsGeneratingForecast(false);
      }
    },
    enabled: false,
  });

  // Fetch Inventory Forecast
  const { data: inventoryForecastData, isLoading: inventoryLoading } = useQuery({
    queryKey: ['inventory-forecast', selectedOutlet, forecastPeriod],
    queryFn: async () => {
      const params = { days: forecastPeriod };
      if (selectedOutlet !== 'all') params.outlet_id = selectedOutlet;
      
      const response = await api.get('/api/v1/forecasting/inventory', { params });
      return response.data;
    },
    enabled: !!salesForecastData,
  });

  // Fetch Factor Analysis
  const { data: factorAnalysisData } = useQuery({
    queryKey: ['factor-analysis', selectedOutlet],
    queryFn: async () => {
      const params = {};
      if (selectedOutlet !== 'all') params.outlet_id = selectedOutlet;
      
      const response = await api.get('/api/v1/forecasting/factors', { params });
      return response.data;
    },
    enabled: !!salesForecastData,
  });

  // Run Forecast Mutation
  const runForecastMutation = useMutation({
    mutationFn: async () => {
      return refetchSalesForecast();
    },
  });

  // Format Sales Forecast Chart Data
  const chartData = useMemo(() => {
    if (!salesForecastData?.chart_data) return [];
    
    return salesForecastData.chart_data.map(item => ({
      date: item.date,
      actual: item.actual,
      predicted: item.predicted,
      upper_bound: item.upper_bound,
      lower_bound: item.lower_bound,
      is_historical: item.is_historical,
    }));
  }, [salesForecastData]);

  // Find today's date in chart for reference line
  const todayIndex = chartData.findIndex(d => !d.is_historical && d.actual);

  // Get factor impacts
  const factorImpacts = useMemo(() => {
    if (!salesForecastData?.factor_impacts) return [];
    return salesForecastData.factor_impacts.slice(0, 3);
  }, [salesForecastData]);

  // Get reorder timeline data
  const reorderData = useMemo(() => {
    if (!inventoryForecastData?.reorder_timeline) return [];
    return inventoryForecastData.reorder_timeline.slice(0, 10);
  }, [inventoryForecastData]);

  // Get factor analysis chart data
  const factorChartData = useMemo(() => {
    if (!factorAnalysisData?.correlation_data) return [];
    return factorAnalysisData.correlation_data;
  }, [factorAnalysisData]);

  // Format last updated time
  const lastUpdated = salesForecastData?.last_updated 
    ? new Date(salesForecastData.last_updated).toLocaleString('en-IN')
    : 'Never';

  return (
    <div className="forecasting">
      {/* Header */}
      <div className="forecasting-header">
        <p className="page-subtitle">AI-powered predictions using Prophet model</p>
      </div>

      {/* Controls Bar */}
      <div className="forecasting-controls">
        {isSuperAdmin && (
          <select
            value={selectedOutlet}
            onChange={(e) => setSelectedOutlet(e.target.value)}
            className="control-select"
          >
            <option value="all">All Outlets</option>
            {outletsData?.map(outlet => (
              <option key={outlet.id} value={outlet.id}>{outlet.name}</option>
            ))}
          </select>
        )}

        <select
          value={selectedProduct}
          onChange={(e) => setSelectedProduct(e.target.value)}
          className="control-select"
        >
          <option value="all">All Products</option>
          {productsData?.map(product => (
            <option key={product.id} value={product.id}>{product.name}</option>
          ))}
        </select>

        <div className="period-buttons">
          {[7, 14, 30, 90].map(days => (
            <button
              key={days}
              onClick={() => setForecastPeriod(days)}
              className={`period-button ${forecastPeriod === days ? 'active' : ''}`}
            >
              {days}d
            </button>
          ))}
        </div>

        <button
          onClick={() => runForecastMutation.mutate()}
          disabled={isGeneratingForecast}
          className="run-forecast-button"
        >
          {isGeneratingForecast ? 'Running Forecast...' : 'Run Forecast'}
        </button>

        <div className="last-updated">
          Last updated: <span>{lastUpdated}</span>
        </div>
      </div>

      {/* Progress Indicator */}
      {isGeneratingForecast && elapsedTime > 3 && (
        <div className="progress-indicator">
          <div className="progress-spinner" />
          <p>Training forecast model… ({elapsedTime}s)</p>
        </div>
      )}

      {/* Sales Forecast Section */}
      <div className="forecast-card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Sales Forecast</h2>
            <p className="card-subtitle">{forecastPeriod}-day ahead prediction</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Badge variant="blue" text="Prophet Model" />
            {salesForecastData?.mape && (
              <Badge variant="green" text={`MAPE: ${fmtPercent(salesForecastData.mape)}`} />
            )}
          </div>
        </div>

        <div className="chart-container">
          {salesLoading ? (
            <ChartSkeleton />
          ) : chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                <defs>
                  <linearGradient id="confidenceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#E5E7EB" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#E5E7EB" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  stroke="#D1D5DB"
                />
                <YAxis
                  tick={{ fontSize: 12, fill: '#6B7280' }}
                  stroke="#D1D5DB"
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E5E7EB',
                    borderRadius: '8px',
                  }}
                  formatter={(value) => value ? fmtINR(value) : 'N/A'}
                />
                
                {/* Confidence Interval Band */}
                <Area
                  type="monotone"
                  dataKey="upper_bound"
                  fill="url(#confidenceGradient)"
                  stroke="transparent"
                  isAnimationActive={false}
                />
                
                {/* Historical Actuals as Dots */}
                <Line
                  type="monotone"
                  dataKey="actual"
                  stroke="#6B7280"
                  strokeWidth={0}
                  dot={{ fill: '#6B7280', r: 3 }}
                  isAnimationActive={false}
                />
                
                {/* Predicted Values */}
                <Line
                  type="monotone"
                  dataKey="predicted"
                  stroke="#1A1A1A"
                  strokeWidth={2}
                  dot={false}
                  strokeDasharray="5 5"
                  isAnimationActive={false}
                />
                
                {/* Reference Line for Today */}
                {todayIndex > 0 && (
                  <ReferenceLine
                    x={chartData[todayIndex].date}
                    stroke="#D1D5DB"
                    strokeDasharray="3 3"
                    label={{ value: 'Today', position: 'top', fill: '#6B7280', fontSize: 12 }}
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: '#9CA3AF' }}>
              Run a forecast to see predictions
            </div>
          )}
        </div>

        {/* Factor Impact Cards */}
        {factorImpacts.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {factorImpacts.map((factor, idx) => (
              <div key={idx} className="impact-card">
                <div className="impact-label">{factor.name}</div>
                <div className={`impact-value ${factor.impact > 0 ? 'positive' : 'negative'}`}>
                  {factor.impact > 0 ? '+' : ''}{fmtPercent(factor.impact)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inventory Depletion Forecast Section */}
      <div className="forecast-card">
        <div className="card-header">
          <div>
            <h2 className="card-title">Reorder Timeline</h2>
            <p className="card-subtitle">Top 10 products by urgency</p>
          </div>
        </div>

        <div className="overflow-x-auto md:overflow-x-visible">
          {inventoryLoading ? (
            <TableSkeleton />
          ) : reorderData.length > 0 ? (
            <>
              <table className="reorder-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Category</th>
                    <th>Current Stock</th>
                    <th>Daily Rate</th>
                    <th>Days Until Reorder</th>
                    <th>Suggested Order Date</th>
                    <th>Suggested Qty</th>
                  </tr>
                </thead>
                <tbody>
                  {reorderData.map((row, idx) => {
                    const daysColor = 
                      row.days_until_reorder < 7 ? 'red' :
                      row.days_until_reorder < 14 ? 'amber' :
                      'green';
                    
                    return (
                      <tr key={idx}>
                        <td className="product-cell">
                          <div style={{ fontWeight: '600', color: '#1A1A1A' }}>
                            {row.product_name}
                          </div>
                        </td>
                        <td>{row.category}</td>
                        <td>{row.current_stock}</td>
                        <td>{row.daily_sales_rate.toFixed(2)}</td>
                        <td>
                          <span className={`days-badge days-${daysColor}`}>
                            {row.days_until_reorder}d
                          </span>
                        </td>
                        <td>{row.suggested_order_date}</td>
                        <td>{row.suggested_qty}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              <button className="generate-reorder-button">
                Generate Reorder List
              </button>
            </>
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: '#9CA3AF' }}>
              Run a forecast to see reorder timeline
            </div>
          )}
        </div>
      </div>

      {/* Factors Analysis Accordion */}
      <div className="forecast-card">
        <button
          onClick={() => setExpandedFactors(!expandedFactors)}
          className="accordion-toggle"
        >
          <h2 className="card-title">Factors Analysis</h2>
          <ChevronDown
            size={20}
            style={{
              transform: expandedFactors ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
            }}
          />
        </button>

        {expandedFactors && (
          <div className="accordion-content">
            {factorChartData.length > 0 ? (
              <>
                <div className="factor-chart">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={factorChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                      <XAxis
                        dataKey="factor"
                        tick={{ fontSize: 12, fill: '#6B7280' }}
                        stroke="#D1D5DB"
                      />
                      <YAxis
                        tick={{ fontSize: 12, fill: '#6B7280' }}
                        stroke="#D1D5DB"
                        label={{ value: 'Correlation', angle: -90, position: 'insideLeft' }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#FFFFFF',
                          border: '1px solid #E5E7EB',
                          borderRadius: '8px',
                        }}
                        formatter={(value) => fmtPercent(value)}
                      />
                      <Bar
                        dataKey="correlation"
                        fill="#3B82F6"
                        radius={[8, 8, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="factor-explanation">
                  <h3>Top Factors Affecting Sales</h3>
                  <ul>
                    {factorAnalysisData?.top_factors?.map((factor, idx) => (
                      <li key={idx}>
                        <strong>{factor.name}:</strong> {factor.description}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <div style={{ padding: '20px', color: '#9CA3AF' }}>
                Run a forecast to see factor analysis
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
