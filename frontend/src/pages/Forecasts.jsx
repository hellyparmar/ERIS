import { useEffect, useMemo, useState } from 'react';
import { Cpu, LineChart as LineChartIcon, RefreshCw } from 'lucide-react';
import {
    Area,
    CartesianGrid,
    ComposedChart,
    Legend,
    Line,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';

import SEO from '../components/SEO';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../lib/api';

const MODEL_LABELS = {
    prophet: 'Prophet',
    xgboost: 'XGBoost',
    ensemble: 'Ensemble',
};

const MODEL_COLORS = {
    prophet: '#8B5E3C',
    xgboost: '#5D7B6F',
    ensemble: '#D97706',
};

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const formatMetric = (value) => {
    if (value == null) return '—';
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(2) : '—';
};

const extractError = (error, fallback) =>
    error?.response?.data?.detail || error?.message || fallback;

const Forecasts = () => {
    const { user } = useAuth();
    const canRetrain = user?.role === 'admin' || user?.role === 'manager';
    const { addToast } = useToast();
    const [outlets, setOutlets] = useState([]);
    const [products, setProducts] = useState([]);
    const [selectedOutlet, setSelectedOutlet] = useState('');
    const [selectedProduct, setSelectedProduct] = useState('');
    const [timeHorizon, setTimeHorizon] = useState(30);
    const [forecastPoints, setForecastPoints] = useState([]);
    const [modelMetrics, setModelMetrics] = useState({});
    const [loading, setLoading] = useState(false);
    const [retraining, setRetraining] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const [errorMessage, setErrorMessage] = useState('');
    const [visibleModels, setVisibleModels] = useState({
        prophet: true,
        xgboost: true,
        ensemble: true,
    });

    useEffect(() => {
        let active = true;

        const loadOutlets = async () => {
            try {
                const { data } = await api.get('/api/v1/outlets');
                const rows = Array.isArray(data) ? data.filter((outlet) => outlet.is_active !== false) : [];
                if (!active) return;
                setOutlets(rows);
                setSelectedOutlet((current) => current || String(rows[0]?.id || ''));
                if (rows.length === 0) setErrorMessage('No active outlets are available. Seed or create an outlet first.');
            } catch (error) {
                if (!active) return;
                setErrorMessage(extractError(error, 'Unable to load outlets.'));
            }
        };

        loadOutlets();
        return () => { active = false; };
    }, []);

    useEffect(() => {
        let active = true;
        if (!selectedOutlet) {
            setProducts([]);
            setSelectedProduct('');
            return () => { active = false; };
        }

        const loadProducts = async () => {
            try {
                const { data } = await api.get('/api/v1/inventory', {
                    params: { outlet_id: Number(selectedOutlet) },
                });
                const items = Array.isArray(data) ? data : data?.items || [];
                const unique = [...new Map(
                    items
                        .filter((item) => item.product?.id != null)
                        .map((item) => [String(item.product.id), item.product]),
                ).values()];
                if (!active) return;
                setProducts(unique);
                setSelectedProduct((current) =>
                    unique.some((product) => String(product.id) === current)
                        ? current
                        : String(unique[0]?.id || ''),
                );
                if (unique.length === 0) {
                    setForecastPoints([]);
                    setModelMetrics({});
                    setErrorMessage('This outlet has no inventoried products to forecast.');
                }
            } catch (error) {
                if (!active) return;
                setProducts([]);
                setSelectedProduct('');
                setErrorMessage(extractError(error, 'Unable to load products for this outlet.'));
            }
        };

        loadProducts();
        return () => { active = false; };
    }, [selectedOutlet]);

    useEffect(() => {
        let active = true;
        if (!selectedOutlet || !selectedProduct) return () => { active = false; };

        const pollJob = async (taskId) => {
            for (let attempt = 0; attempt < 90; attempt += 1) {
                if (!active) return null;
                const { data } = await api.get(`/api/v1/forecasting/status/${taskId}`);
                if (data.status === 'complete') return data.result;
                if (data.status === 'failed') {
                    throw new Error(data.result?.message || 'Forecast generation failed.');
                }
                await sleep(2000);
            }
            throw new Error('Forecast generation timed out. Try a shorter horizon or more historical data.');
        };

        const loadForecast = async () => {
            setLoading(true);
            setErrorMessage('');
            try {
                const { data } = await api.post('/api/v1/forecasting/sales', null, {
                    params: {
                        outlet_id: Number(selectedOutlet),
                        product_id: Number(selectedProduct),
                        horizon: timeHorizon,
                        model: 'ensemble',
                    },
                });
                const result = await pollJob(data.task_id);
                if (!active) return;
                const rows = Array.isArray(result?.forecasts) ? result.forecasts : [];
                if (rows.length === 0) throw new Error('The model completed without forecast points.');
                setForecastPoints(rows.map((point) => ({
                    date: String(point.date || '').split('T')[0],
                    prophet: point.prophet ?? null,
                    prophetLower: point.prophetLower ?? null,
                    prophetUpper: point.prophetUpper ?? null,
                    xgboost: point.xgboost ?? null,
                    ensemble: point.forecast ?? null,
                    lowerBound: point.lower_bound ?? null,
                    upperBound: point.upper_bound ?? null,
                })));
                setModelMetrics(result?.metrics || {});
            } catch (error) {
                if (!active) return;
                setForecastPoints([]);
                setModelMetrics({});
                const message = extractError(error, 'Unable to generate a forecast.');
                setErrorMessage(message);
                addToast(message, 'error');
            } finally {
                if (active) setLoading(false);
            }
        };

        loadForecast();
        return () => { active = false; };
    }, [addToast, refreshKey, selectedOutlet, selectedProduct, timeHorizon]);

    const summary = useMemo(() => {
        const values = forecastPoints
            .map((point) => Number(point.ensemble))
            .filter(Number.isFinite);
        const total = values.reduce((sum, value) => sum + value, 0);
        return {
            total: Math.round(total),
            dailyAverage: values.length ? Math.round(total / values.length) : 0,
            peak: values.length ? Math.round(Math.max(...values)) : 0,
            points: values.length,
        };
    }, [forecastPoints]);

    const toggleModel = (model) => {
        setVisibleModels((current) => ({ ...current, [model]: !current[model] }));
    };

    const retrainModels = async () => {
        if (!selectedOutlet || retraining) return;
        setRetraining(true);
        try {
            const { data } = await api.post(
                `/api/v1/forecasting/retrain?outlet_id=${Number(selectedOutlet)}`,
            );
            addToast(`Forecast pipeline queued (${data.task_id.slice(0, 8)}…).`, 'info');
            for (let attempt = 0; attempt < 90; attempt += 1) {
                const statusResponse = await api.get(`/api/v1/forecasting/status/${data.task_id}`);
                if (statusResponse.data.status === 'complete') {
                    addToast('Forecast models were trained and saved.', 'success');
                    setRefreshKey((value) => value + 1);
                    return;
                }
                if (statusResponse.data.status === 'failed') {
                    throw new Error('Model training failed. Check that the outlet has enough sales history.');
                }
                await sleep(2000);
            }
            throw new Error('Model training timed out.');
        } catch (error) {
            addToast(extractError(error, 'Unable to retrain forecast models.'), 'error');
        } finally {
            setRetraining(false);
        }
    };

    return (
        <>
            <SEO title="Demand Forecasting" description="Measured multi-model demand forecasts" />
            <div style={{ minHeight: 'calc(100vh - 50px)', background: 'var(--c-canvas)' }}>
                <div style={{ padding: '16px 22px', display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'end', borderBottom: '1px solid var(--c-border)' }}>
                    <div>
                        <h1 className="page-title">Predictive Sales Forecasting</h1>
                        <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>
                            Prophet and XGBoost forecasts trained on recorded sales, combined by validation error.
                        </p>
                    </div>
                    {canRetrain && <button className="action-btn primary" onClick={retrainModels} disabled={!selectedOutlet || retraining}>
                        <Cpu size={14} style={{ marginRight: 6 }} />
                        {retraining ? 'Training…' : 'Retrain models'}
                    </button>}
                </div>

                <div className="content-section">
                    <div className="filter-bar" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'end' }}>
                        <label style={{ display: 'grid', gap: 4, minWidth: 210 }}>
                            <span className="zone-label">Outlet</span>
                            <select value={selectedOutlet} onChange={(event) => setSelectedOutlet(event.target.value)} disabled={!outlets.length}>
                                {!outlets.length && <option value="">No outlets</option>}
                                {outlets.map((outlet) => <option key={outlet.id} value={outlet.id}>{outlet.name}</option>)}
                            </select>
                        </label>
                        <label style={{ display: 'grid', gap: 4, minWidth: 230 }}>
                            <span className="zone-label">Product</span>
                            <select value={selectedProduct} onChange={(event) => setSelectedProduct(event.target.value)} disabled={!products.length}>
                                {!products.length && <option value="">No products</option>}
                                {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
                            </select>
                        </label>
                        <div style={{ display: 'grid', gap: 4 }}>
                            <span className="zone-label">Horizon</span>
                            <div style={{ display: 'flex', gap: 4 }}>
                                {[7, 14, 30].map((days) => (
                                    <button
                                        className={`action-btn${timeHorizon === days ? ' primary' : ''}`}
                                        key={days}
                                        onClick={() => setTimeHorizon(days)}
                                    >
                                        {days} days
                                    </button>
                                ))}
                            </div>
                        </div>
                        <button className="action-btn" onClick={() => setRefreshKey((value) => value + 1)} disabled={loading || !selectedProduct}>
                            <RefreshCw size={13} style={{ marginRight: 6 }} /> Refresh
                        </button>
                    </div>
                </div>

                <div className="kpi-strip">
                    <div className="kpi-cell"><div className="kpi-label">Forecast units</div><div className="kpi-value brown">{summary.total.toLocaleString('en-IN')}</div></div>
                    <div className="kpi-cell"><div className="kpi-label">Daily average</div><div className="kpi-value">{summary.dailyAverage.toLocaleString('en-IN')}</div></div>
                    <div className="kpi-cell"><div className="kpi-label">Peak day</div><div className="kpi-value">{summary.peak.toLocaleString('en-IN')}</div></div>
                    <div className="kpi-cell"><div className="kpi-label">Forecast points</div><div className="kpi-value">{summary.points}</div></div>
                </div>

                <div className="content-section-alt">
                    <div className="section-header" style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                        <div className="zone-label"><LineChartIcon size={13} style={{ marginRight: 6 }} />Measured forecast output</div>
                        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                            {Object.keys(MODEL_LABELS).map((model) => (
                                <label key={model} style={{ fontSize: 11, display: 'flex', gap: 5, alignItems: 'center', color: 'var(--c-ink-muted)' }}>
                                    <input type="checkbox" checked={visibleModels[model]} onChange={() => toggleModel(model)} />
                                    {MODEL_LABELS[model]}
                                </label>
                            ))}
                        </div>
                    </div>

                    {loading ? (
                        <div style={{ padding: 72, textAlign: 'center', color: 'var(--c-ink-muted)' }}>Training models and calculating the forecast…</div>
                    ) : errorMessage ? (
                        <div className="empty-state" style={{ padding: 48, textAlign: 'center' }}>
                            <strong>Forecast unavailable</strong>
                            <p style={{ color: 'var(--c-ink-muted)' }}>{errorMessage}</p>
                        </div>
                    ) : (
                        <div style={{ height: 390, marginTop: 18 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={forecastPoints} margin={{ top: 12, right: 24, left: 8, bottom: 12 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--c-border)" />
                                    <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={28} />
                                    <YAxis tick={{ fontSize: 10 }} />
                                    <Tooltip />
                                    <Legend />
                                    {visibleModels.ensemble && <Area type="monotone" dataKey="upperBound" stroke="none" fill="#D97706" fillOpacity={0.08} name="Ensemble upper bound" />}
                                    {visibleModels.ensemble && <Area type="monotone" dataKey="lowerBound" stroke="none" fill="var(--c-canvas)" fillOpacity={1} name="Ensemble lower bound" />}
                                    {Object.entries(MODEL_LABELS).map(([model, label]) => visibleModels[model] && (
                                        <Line
                                            key={model}
                                            type="monotone"
                                            dataKey={model}
                                            name={label}
                                            stroke={MODEL_COLORS[model]}
                                            strokeWidth={model === 'ensemble' ? 3 : 1.5}
                                            dot={false}
                                            connectNulls
                                        />
                                    ))}
                                </ComposedChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </div>

                <div className="content-section">
                    <div>
                        <div className="zone-label">Validation metrics</div>
                        <div style={{ overflowX: 'auto', marginTop: 12 }}>
                            <table className="eris-table" style={{ width: '100%' }}>
                                <thead><tr><th>Model</th><th>MAPE</th><th>RMSE</th><th>MAE</th></tr></thead>
                                <tbody>
                                    {Object.keys(MODEL_LABELS).map((model) => {
                                        return (
                                            <tr key={model}>
                                                <td>{MODEL_LABELS[model]}</td>
                                                <td className="mono">{formatMetric(modelMetrics[model]?.mape)}%</td>
                                                <td className="mono">{formatMetric(modelMetrics[model]?.rmse)}</td>
                                                <td className="mono">{formatMetric(modelMetrics[model]?.mae)}</td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                        <p style={{ fontSize: 11, color: 'var(--c-ink-muted)', marginTop: 10 }}>
                            Metrics come from the held-out validation window. Missing values are shown as “—”.
                        </p>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Forecasts;
