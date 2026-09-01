import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, X, Save, RefreshCw, CheckCircle2, AlertCircle, ExternalLink,
  Eye, EyeOff, Server, Database, User, Key,
  Loader2, Zap, Settings as SettingsIcon
} from 'lucide-react';
import SEO from '../components/SEO';
import api from '../lib/api';
import { useToast } from '../components/ui/Toast';
import '../styles/integrations.css';

/* ── Active Supported Integrations ────────────────────────── */
const INTEGRATIONS = [
  {
    id: 'odoo',
    name: 'Odoo ERP',
    desc: 'Sync products, inventory, customers, and accounting data via XML-RPC.',
    category: 'ERP',
    emoji: '🟢',
    color: '#16A34A',
    bg: '#DCFCE7',
    fields: [
      { key: 'url',      label: 'Server URL',    icon: Server,   type: 'text',     placeholder: 'https://your-instance.odoo.com' },
      { key: 'db_name',  label: 'Database Name', icon: Database, type: 'text',     placeholder: 'odoo_db' },
      { key: 'username', label: 'Username',      icon: User,     type: 'text',     placeholder: 'admin@company.com' },
      { key: 'api_key',  label: 'API Key',       icon: Key,      type: 'password', placeholder: '••••••••••••' },
    ],
    toggles: [
      { key: 'sync_products', label: 'Sync Products' },
      { key: 'sync_customers', label: 'Sync Customers' }
    ],
    defaults: { url: '', db_name: '', username: '', api_key: '', sync_products: true, sync_customers: true },
    guide: [
      'Log in to your Odoo instance.',
      'Go to Profile → Account Security.',
      'Click "Generate New API Key".',
      'Copy and paste the API key above along with your database name.'
    ],
  },
  {
    id: 'zoho',
    name: 'Zoho Books',
    desc: 'Sync invoices, payment statuses, and tax ledgers via Zoho REST API.',
    category: 'Accounting',
    emoji: '🟡',
    color: '#D97706',
    bg: '#FEF3C7',
    fields: [
      { key: 'org_id',        label: 'Organization ID', icon: Database, type: 'text',     placeholder: '60001234567' },
      { key: 'client_id',     label: 'Client ID',       icon: Key,      type: 'text',     placeholder: '1000.XXXXXXXXXX' },
      { key: 'client_secret', label: 'Client Secret',   icon: Key,      type: 'password', placeholder: '••••••••••••' },
    ],
    toggles: [
      { key: 'sync_invoices', label: 'Sync Invoices' }
    ],
    defaults: { org_id: '', client_id: '', client_secret: '', sync_invoices: true },
    guide: [
      'Go to Zoho Developer Console (accounts.zoho.in/developerconsole).',
      'Register a new Server-based Application with ZohoBooks.fullaccess.all scope.',
      'Copy Client ID and Client Secret from the console.',
      'Obtain your Organization ID from Zoho Books Settings → Organization Profile.'
    ],
  },
];

/* ── Field Input ── */
function FieldInput({ field, value, onChange }) {
  const [visible, setVisible] = useState(false);
  const Icon = field.icon;
  return (
    <div className="intg-field">
      <label><Icon size={13}/>{field.label}</label>
      <div className="intg-input-wrap">
        <Icon size={14} className="intg-input-icon"/>
        <input
          className="intg-input"
          type={field.type === 'password' && !visible ? 'password' : 'text'}
          value={value || ''}
          onChange={e => onChange(field.key, e.target.value)}
          placeholder={field.placeholder}
        />
        {field.type === 'password' && (
          <button className="intg-eye-btn" type="button" onClick={() => setVisible(v => !v)}>
            {visible ? <EyeOff size={14}/> : <Eye size={14}/>}
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Modal ── */
function IntegrationModal({
  integ,
  config,
  onChange,
  onClose,
  connected,
  onTest,
  onSave,
  onDisconnect,
  syncInterval,
  setSync,
  testState,
  saveLoading
}) {
  return (
    <div className="intg-modal-overlay" onClick={onClose}>
      <motion.div className="intg-modal" onClick={e => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 16 }}
        transition={{ duration: 0.2 }}>

        <div className="intg-modal__header">
          <div className="intg-modal__header-icon" style={{ background: integ.bg }}>
            <span>{integ.emoji}</span>
          </div>
          <div className="intg-modal__header-text">
            <h2>{integ.name}</h2>
            <p style={{ color: connected ? '#059669' : 'var(--text-muted)' }}>
              {connected ? '● Configured & Active' : 'Not configured'}
            </p>
          </div>
          <button className="intg-modal__close" onClick={onClose}><X size={16}/></button>
        </div>

        <div className="intg-modal__body">
          <div>
            <p className="intg-divider">Connection Credentials</p>
            <div className="intg-form" style={{ marginTop: 14 }}>
              {integ.fields.map(f => (
                <FieldInput key={f.key} field={f} value={config[f.key]} onChange={onChange}/>
              ))}
            </div>
          </div>

          <div>
            <p className="intg-divider">Sync Options</p>
            <div className="intg-sync-options" style={{ marginTop: 14 }}>
              {integ.toggles.map(t => (
                <label key={t.key} className="intg-toggle-row">
                  <span>{t.label}</span>
                  <span className="intg-toggle">
                    <input
                      type="checkbox"
                      checked={!!config[t.key]}
                      onChange={e => onChange(t.key, e.target.checked)}
                    />
                    <span className="intg-toggle-slider"/>
                  </span>
                </label>
              ))}
              <div className="intg-interval-row">
                <span>Sync Interval</span>
                <select className="intg-select" value={syncInterval} onChange={e => setSync(e.target.value)}>
                  <option value="rt">Real-time</option>
                  <option value="1h">1 Hour</option>
                  <option value="4h">4 Hours</option>
                  <option value="24h">Daily</option>
                </select>
              </div>
            </div>
          </div>

          <AnimatePresence>
            {testState.msg && (
              <motion.div
                className={`intg-status-alert ${testState.type}`}
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                {testState.type === 'success' ? <CheckCircle2 size={15}/> : <AlertCircle size={15}/>}
                <span>{testState.msg}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <p className="intg-divider">Setup Instructions</p>
            <div className="intg-guide" style={{ marginTop: 14 }}>
              {integ.guide.map((step, i) => (
                <div key={i} className="intg-guide__step">
                  <div className="intg-guide__num">{i + 1}</div>
                  <p className="intg-guide__text">{step}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="intg-modal__footer">
          {connected && (
            <button className="intg-btn intg-btn--danger" onClick={onDisconnect}>
              Disconnect
            </button>
          )}
          <button className="intg-btn intg-btn--secondary" onClick={onTest} disabled={testState.loading}>
            {testState.loading ? <Loader2 size={14} className="intg-spin"/> : <RefreshCw size={14}/>}
            {testState.loading ? 'Testing…' : 'Test Connection'}
          </button>
          <button className="intg-btn intg-btn--primary" onClick={onSave} disabled={saveLoading}>
            {saveLoading ? <Loader2 size={14} className="intg-spin"/> : <Save size={14}/>}
            {saveLoading ? 'Saving…' : 'Save Configuration'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

/* ── Card ── */
function IntegrationCard({ integ, connected, onClick }) {
  return (
    <motion.div
      className={`intg-card ${connected ? 'connected' : ''}`}
      onClick={onClick}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -5 }}
      transition={{ duration: 0.2 }}
    >
      <div className="intg-card__stripe" style={{ background: `linear-gradient(90deg, ${integ.color}, transparent)` }}/>
      <div className="intg-card__top">
        <div className="intg-card__icon" style={{ background: integ.bg }}>
          <span style={{ fontSize: 26 }}>{integ.emoji}</span>
        </div>
        <div className="intg-card__info">
          <div className="intg-card__name">{integ.name}</div>
          <div className="intg-card__desc">{integ.desc}</div>
          <span className="intg-card__category">{integ.category}</span>
        </div>
      </div>
      <div className="intg-card__status">
        <span className={`intg-card__status-dot ${connected ? 'connected' : 'idle'}`}/>
        <span className={connected ? 'status-connected' : 'status-idle'}>
          {connected ? 'Configured' : 'Not Configured'}
        </span>
      </div>
      <button
        className={`intg-card__cta ${connected ? 'connected-cta' : ''}`}
        onClick={e => { e.stopPropagation(); onClick(); }}
      >
        {connected ? <><SettingsIcon size={13}/>Manage</> : <><Zap size={13}/>Configure</>}
      </button>
    </motion.div>
  );
}

/* ── Main Page ── */
export default function Integrations() {
  const { addToast } = useToast();
  const [search, setSearch] = useState('');
  const [connections, setConnections] = useState({ odoo: false, zoho: false });
  const [configs, setConfigs] = useState(Object.fromEntries(INTEGRATIONS.map(i => [i.id, { ...i.defaults }])));
  const [syncs, setSyncs] = useState(Object.fromEntries(INTEGRATIONS.map(i => [i.id, '1h'])));
  const [activeModal, setActiveModal] = useState(null);
  const [testState, setTestState] = useState({ loading: false, type: '', msg: '' });
  const [saveLoading, setSaveLoading] = useState(false);

  // Load existing configurations from backend on mount
  useEffect(() => {
    async function loadConfigs() {
      try {
        const odooRes = await api.get('/api/v1/integrations/odoo/config');
        if (odooRes.data?.configured) {
          setConnections(p => ({ ...p, odoo: true }));
          setConfigs(p => ({
            ...p,
            odoo: {
              ...p.odoo,
              url: odooRes.data.url || '',
              db_name: odooRes.data.db_name || '',
              username: odooRes.data.username || '',
              api_key: odooRes.data.api_key || '',
              sync_products: odooRes.data.sync_products ?? true,
              sync_customers: odooRes.data.sync_customers ?? true,
            }
          }));
        }
      } catch (err) {
        console.error('Failed to load Odoo config', err);
      }

      try {
        const zohoRes = await api.get('/api/v1/integrations/zoho/config');
        if (zohoRes.data?.configured) {
          setConnections(p => ({ ...p, zoho: true }));
          setConfigs(p => ({
            ...p,
            zoho: {
              ...p.zoho,
              org_id: zohoRes.data.org_id || '',
              client_id: zohoRes.data.client_id || '',
              sync_invoices: zohoRes.data.sync_invoices ?? true,
            }
          }));
        }
      } catch (err) {
        console.error('Failed to load Zoho config', err);
      }
    }
    loadConfigs();
  }, []);

  const openModal = (id) => {
    setActiveModal(id);
    setTestState({ loading: false, type: '', msg: '' });
  };

  // Real backend test connection
  const handleTest = async () => {
    if (!activeModal) return;
    setTestState({ loading: true, type: '', msg: '' });

    try {
      const cfg = configs[activeModal];
      let res;

      if (activeModal === 'odoo') {
        res = await api.post('/api/v1/integrations/odoo/test-connection', {
          url: cfg.url,
          db_name: cfg.db_name,
          username: cfg.username,
          api_key: cfg.api_key,
          sync_products: cfg.sync_products,
          sync_customers: cfg.sync_customers,
          mock_mode: false
        });

        if (res.data?.success) {
          setTestState({
            loading: false,
            type: 'success',
            msg: `Successfully connected to Odoo Server v${res.data.version || ''} (UID: ${res.data.uid})`
          });
        } else {
          setTestState({
            loading: false,
            type: 'error',
            msg: res.data?.error || 'Connection failed. Please verify credentials.'
          });
        }
      } else if (activeModal === 'zoho') {
        res = await api.post('/api/v1/integrations/zoho/test-connection', {
          org_id: cfg.org_id,
          client_id: cfg.client_id,
          client_secret: cfg.client_secret,
          mock_mode: false
        });

        if (res.data?.connected) {
          setTestState({
            loading: false,
            type: 'success',
            msg: `Successfully authenticated with Zoho Books (${res.data.organization_count || 1} organization linked)`
          });
        } else {
          setTestState({
            loading: false,
            type: 'error',
            msg: res.data?.error || 'Failed to authenticate with Zoho Books.'
          });
        }
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.detail?.error ||
        (typeof err.response?.data?.detail === 'string' ? err.response?.data?.detail : null) ||
        err.message ||
        'Connection test failed';

      setTestState({
        loading: false,
        type: 'error',
        msg: `Connection Error: ${errorMsg}`
      });
    }
  };

  // Real backend save configuration
  const handleSave = async () => {
    if (!activeModal) return;
    setSaveLoading(true);

    try {
      const cfg = configs[activeModal];

      if (activeModal === 'odoo') {
        await api.post('/api/v1/integrations/odoo/config', {
          url: cfg.url,
          db_name: cfg.db_name,
          username: cfg.username,
          api_key: cfg.api_key,
          sync_products: cfg.sync_products,
          sync_customers: cfg.sync_customers
        });
        setConnections(p => ({ ...p, odoo: true }));
        addToast('Odoo configuration encrypted and saved', 'success');
      } else if (activeModal === 'zoho') {
        await api.post('/api/v1/integrations/zoho/config', {
          org_id: cfg.org_id,
          client_id: cfg.client_id,
          client_secret: cfg.client_secret,
          sync_invoices: cfg.sync_invoices
        });
        setConnections(p => ({ ...p, zoho: true }));
        addToast('Zoho Books configuration saved', 'success');
      }
      setActiveModal(null);
    } catch (err) {
      addToast(err.response?.data?.detail || err.message || 'Failed to save configuration', 'error');
    } finally {
      setSaveLoading(false);
    }
  };

  // Real backend disconnect
  const handleDisconnect = async () => {
    if (!activeModal) return;
    try {
      if (activeModal === 'odoo') {
        await api.delete('/api/v1/integrations/odoo/config');
      } else if (activeModal === 'zoho') {
        await api.delete('/api/v1/integrations/zoho/config');
      }
      setConnections(p => ({ ...p, [activeModal]: false }));
      addToast(`${activeModal === 'odoo' ? 'Odoo' : 'Zoho Books'} disconnected`, 'info');
      setActiveModal(null);
    } catch (err) {
      addToast(err.response?.data?.detail || 'Failed to disconnect', 'error');
    }
  };

  const filtered = useMemo(() =>
    INTEGRATIONS.filter(i =>
      !search ||
      i.name.toLowerCase().includes(search.toLowerCase()) ||
      i.category.toLowerCase().includes(search.toLowerCase())
    ),
    [search]
  );

  const connectedList = filtered.filter(i => connections[i.id]);
  const availableList = filtered.filter(i => !connections[i.id]);
  const activeInteg = INTEGRATIONS.find(i => i.id === activeModal);

  return (
    <>
      <SEO title="System Integrations" description="Manage Odoo ERP and Zoho Books connectors" />
      <div className="intg-page">
        <div className="intg-header">
          <div className="intg-header__left">
            <h1 className="page-title">Integrations</h1>
            <p>Connect enterprise ERP and accounting platforms to sync retail data automatically</p>
          </div>
          <div className="intg-search">
            <Search size={15} className="intg-search__icon"/>
            <input
              placeholder="Search integrations…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </div>

        {connectedList.length > 0 && (
          <div>
            <div className="intg-section-label">
              <h2>Connected</h2>
              <span>{connectedList.length}</span>
            </div>
            <div className="intg-grid">
              {connectedList.map((integ, i) => (
                <motion.div
                  key={integ.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <IntegrationCard integ={integ} connected onClick={() => openModal(integ.id)}/>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {availableList.length > 0 && (
          <div>
            <div className="intg-section-label">
              <h2>Available Connectors</h2>
              <span>{availableList.length}</span>
            </div>
            <div className="intg-grid">
              {availableList.map((integ, i) => (
                <motion.div
                  key={integ.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.06 }}
                >
                  <IntegrationCard integ={integ} connected={false} onClick={() => openModal(integ.id)}/>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {filtered.length === 0 && (
          <div className="intg-empty">
            <Search size={36} style={{ color: 'var(--text-faint)' }}/>
            <h3>No integrations found</h3>
            <p>Try a different search term.</p>
            <button className="intg-btn intg-btn--secondary" onClick={() => setSearch('')}>
              Clear Search
            </button>
          </div>
        )}

        <AnimatePresence>
          {activeModal && activeInteg && (
            <IntegrationModal
              integ={activeInteg}
              config={configs[activeModal]}
              onChange={(k, v) => setConfigs(p => ({ ...p, [activeModal]: { ...p[activeModal], [k]: v } }))}
              onClose={() => setActiveModal(null)}
              connected={connections[activeModal]}
              onTest={handleTest}
              onSave={handleSave}
              onDisconnect={handleDisconnect}
              syncInterval={syncs[activeModal]}
              setSync={v => setSyncs(p => ({ ...p, [activeModal]: v }))}
              testState={testState}
              saveLoading={saveLoading}
            />
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
