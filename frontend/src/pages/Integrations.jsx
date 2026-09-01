import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, X, Save, RefreshCw, CheckCircle2, AlertCircle, ExternalLink,
  Eye, EyeOff, Server, Database, User, Key, Globe,
  Loader2, Zap, Settings
} from 'lucide-react';
import '../styles/integrations.css';

/* ── Integration Catalogue ─────────────────────────────────── */
const INTEGRATIONS = [
  {
    id: 'odoo', name: 'Odoo ERP', desc: 'Sync products, customers and accounting data.', category: 'ERP',
    emoji: '🟢', color: '#16A34A', bg: '#DCFCE7',
    fields: [
      { key:'url',      label:'Server URL',    icon:Server,   type:'text',     placeholder:'https://your-odoo.com' },
      { key:'db_name',  label:'Database Name', icon:Database, type:'text',     placeholder:'your_database' },
      { key:'username', label:'Username',      icon:User,     type:'text',     placeholder:'admin@example.com' },
      { key:'api_key',  label:'API Key',       icon:Key,      type:'password', placeholder:'••••••••••••' },
    ],
    toggles: [{ key:'sync_products', label:'Sync Products' }, { key:'sync_customers', label:'Sync Customers' }],
    defaults: { url:'', db_name:'', username:'', api_key:'', sync_products:true, sync_customers:true },
    guide: ['Log in to your Odoo instance.', 'Go to Profile → Account Security.', 'Click Generate New API Key.', 'Copy and paste the key above.'],
  },
  {
    id: 'zoho', name: 'Zoho Books', desc: 'Sync invoices and financial records.', category: 'Accounting',
    emoji: '🟡', color: '#D97706', bg: '#FEF3C7',
    fields: [
      { key:'org_id',        label:'Organization ID', icon:Database, type:'text',     placeholder:'123456789' },
      { key:'client_id',     label:'Client ID',       icon:Key,      type:'text',     placeholder:'1000.XXXXX' },
      { key:'client_secret', label:'Client Secret',   icon:Key,      type:'password', placeholder:'••••••••••••' },
    ],
    toggles: [{ key:'sync_invoices', label:'Sync Invoices' }],
    defaults: { org_id:'', client_id:'', client_secret:'', sync_invoices:true },
    guide: ['Go to Zoho Developer Console.', 'Register a new Server-based Application.', 'Copy Client ID and Client Secret.'],
  },
  {
    id: 'shopify', name: 'Shopify', desc: 'Sync inventory and orders from your store.', category: 'E-commerce',
    emoji: '🛍️', color: '#16A34A', bg: '#DCFCE7',
    fields: [
      { key:'shop_url',     label:'Shop URL',     icon:Globe, type:'text',     placeholder:'your-store.myshopify.com' },
      { key:'access_token', label:'Access Token', icon:Key,   type:'password', placeholder:'shpat_••••••••••' },
    ],
    toggles: [{ key:'sync_inventory', label:'Sync Inventory' }],
    defaults: { shop_url:'', access_token:'', sync_inventory:true },
    guide: ['Go to Shopify Admin → Apps.', 'Create a Custom App.', 'Reveal Admin API Access Token.'],
  },
  {
    id: 'woocommerce', name: 'WooCommerce', desc: 'Import orders and product catalog.', category: 'E-commerce',
    emoji: '🛒', color: '#96588A', bg: 'rgba(150,88,138,0.12)',
    fields: [
      { key:'store_url',       label:'Store URL',       icon:Globe, type:'text',     placeholder:'https://your-store.com' },
      { key:'consumer_key',    label:'Consumer Key',    icon:Key,   type:'text',     placeholder:'ck_••••••••••' },
      { key:'consumer_secret', label:'Consumer Secret', icon:Key,   type:'password', placeholder:'cs_••••••••••' },
    ],
    toggles: [{ key:'sync_orders', label:'Sync Orders' }],
    defaults: { store_url:'', consumer_key:'', consumer_secret:'', sync_orders:true },
    guide: ['Go to WooCommerce → Settings → Advanced.', 'Click REST API → Add Key.', 'Set Permissions to Read/Write and generate.'],
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
function IntegrationModal({ integ, config, onChange, onClose, connected, onTest, onSave, onDisconnect, syncInterval, setSync, testState, saveLoading }) {
  return (
    <div className="intg-modal-overlay" onClick={onClose}>
      <motion.div className="intg-modal" onClick={e => e.stopPropagation()}
        initial={{ opacity:0, scale:0.95, y:16 }} animate={{ opacity:1, scale:1, y:0 }}
        exit={{ opacity:0, scale:0.95, y:16 }} transition={{ duration:0.2 }}>

        <div className="intg-modal__header">
          <div className="intg-modal__header-icon" style={{ background: integ.bg }}>
            <span>{integ.emoji}</span>
          </div>
          <div className="intg-modal__header-text">
            <h2>{integ.name}</h2>
            <p style={{ color: connected ? '#059669' : 'var(--text-muted)' }}>
              {connected ? '● Connected' : 'Not configured'}
            </p>
          </div>
          <button className="intg-modal__close" onClick={onClose}><X size={16}/></button>
        </div>

        <div className="intg-modal__body">
          <div>
            <p className="intg-divider">Connection Details</p>
            <div className="intg-form" style={{ marginTop:14 }}>
              {integ.fields.map(f => <FieldInput key={f.key} field={f} value={config[f.key]} onChange={onChange}/>)}
            </div>
          </div>

          <div>
            <p className="intg-divider">Sync Options</p>
            <div className="intg-sync-options" style={{ marginTop:14 }}>
              {integ.toggles.map(t => (
                <label key={t.key} className="intg-toggle-row">
                  <span>{t.label}</span>
                  <span className="intg-toggle">
                    <input type="checkbox" checked={!!config[t.key]} onChange={e => onChange(t.key, e.target.checked)}/>
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
              <motion.div className={`intg-status-alert ${testState.type}`}
                initial={{ opacity:0, height:0 }} animate={{ opacity:1, height:'auto' }} exit={{ opacity:0, height:0 }}>
                {testState.type === 'success' ? <CheckCircle2 size={15}/> : <AlertCircle size={15}/>}
                {testState.msg}
              </motion.div>
            )}
          </AnimatePresence>

          <div>
            <p className="intg-divider">How to Connect</p>
            <div className="intg-guide" style={{ marginTop:14 }}>
              {integ.guide.map((step, i) => (
                <div key={i} className="intg-guide__step">
                  <div className="intg-guide__num">{i+1}</div>
                  <p className="intg-guide__text">{step}</p>
                </div>
              ))}
            </div>
            <button className="intg-btn intg-btn--secondary" style={{ marginTop:14, fontSize:12 }}>
              <ExternalLink size={13}/> View Documentation
            </button>
          </div>
        </div>

        <div className="intg-modal__footer">
          {connected && <button className="intg-btn intg-btn--danger" onClick={onDisconnect}>Disconnect</button>}
          <button className="intg-btn intg-btn--secondary" onClick={onTest} disabled={testState.loading}>
            {testState.loading ? <Loader2 size={14} className="intg-spin"/> : <RefreshCw size={14}/>}
            {testState.loading ? 'Testing…' : 'Test Connection'}
          </button>
          <button className="intg-btn intg-btn--primary" onClick={onSave} disabled={saveLoading}>
            {saveLoading ? <Loader2 size={14} className="intg-spin"/> : <Save size={14}/>}
            {saveLoading ? 'Saving…' : 'Save Changes'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

/* ── Card ── */
function IntegrationCard({ integ, connected, onClick }) {
  return (
    <motion.div className={`intg-card ${connected ? 'connected' : ''}`} onClick={onClick}
      initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} whileHover={{ y:-5 }} transition={{ duration:0.2 }}>
      <div className="intg-card__stripe" style={{ background:`linear-gradient(90deg, ${integ.color}, transparent)` }}/>
      <div className="intg-card__top">
        <div className="intg-card__icon" style={{ background: integ.bg }}>
          <span style={{ fontSize:26 }}>{integ.emoji}</span>
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
          {connected ? 'Connected' : 'Not Configured'}
        </span>
      </div>
      <button className={`intg-card__cta ${connected ? 'connected-cta' : ''}`} onClick={e => { e.stopPropagation(); onClick(); }}>
        {connected ? <><Settings size={13}/>Reconfigure</> : <><Zap size={13}/>Connect</>}
      </button>
    </motion.div>
  );
}

/* ── Main Page ── */
export default function Integrations() {
  const [search, setSearch] = useState('');
  const [connections, setConnections] = useState({ odoo:false, zoho:false, shopify:false, woocommerce:false });
  const [configs, setConfigs] = useState(Object.fromEntries(INTEGRATIONS.map(i => [i.id, { ...i.defaults }])));
  const [syncs, setSyncs] = useState(Object.fromEntries(INTEGRATIONS.map(i => [i.id, '1h'])));
  const [activeModal, setActiveModal] = useState(null);
  const [testState, setTestState] = useState({ loading:false, type:'', msg:'' });
  const [saveLoading, setSaveLoading] = useState(false);

  const openModal = (id) => { setActiveModal(id); setTestState({ loading:false, type:'', msg:'' }); };

  const handleTest = () => {
    setTestState({ loading:true, type:'', msg:'' });
    setTimeout(() => {
      const ok = Math.random() > 0.15;
      setTestState({ loading:false, type: ok?'success':'error', msg: ok ? `Connected to ${INTEGRATIONS.find(i=>i.id===activeModal)?.name} successfully!` : 'Connection failed. Please verify your credentials.' });
      if (ok) setConnections(p => ({ ...p, [activeModal]:true }));
    }, 1500);
  };

  const handleSave = () => { setSaveLoading(true); setTimeout(()=>setSaveLoading(false), 900); };
  const handleDisconnect = () => { setConnections(p => ({ ...p, [activeModal]:false })); setActiveModal(null); };

  const filtered = useMemo(() => INTEGRATIONS.filter(i => !search || i.name.toLowerCase().includes(search.toLowerCase()) || i.category.toLowerCase().includes(search.toLowerCase())), [search]);
  const connectedList = filtered.filter(i => connections[i.id]);
  const availableList = filtered.filter(i => !connections[i.id]);
  const activeInteg = INTEGRATIONS.find(i => i.id === activeModal);

  return (
    <div className="intg-page">
      <div className="intg-header">
        <div className="intg-header__left">
          <p>Connect third-party services and sync your data automatically</p>
        </div>
        <div className="intg-search">
          <Search size={15} className="intg-search__icon"/>
          <input placeholder="Search integrations…" value={search} onChange={e => setSearch(e.target.value)}/>
        </div>
      </div>

      {connectedList.length > 0 && (
        <div>
          <div className="intg-section-label"><h2>Connected</h2><span>{connectedList.length}</span></div>
          <div className="intg-grid">
            {connectedList.map((integ,i) => (
              <motion.div key={integ.id} initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} transition={{ delay:i*0.06 }}>
                <IntegrationCard integ={integ} connected onClick={() => openModal(integ.id)}/>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {availableList.length > 0 && (
        <div>
          <div className="intg-section-label"><h2>Available</h2><span>{availableList.length}</span></div>
          <div className="intg-grid">
            {availableList.map((integ,i) => (
              <motion.div key={integ.id} initial={{ opacity:0, y:12 }} animate={{ opacity:1, y:0 }} transition={{ delay:i*0.06 }}>
                <IntegrationCard integ={integ} connected={false} onClick={() => openModal(integ.id)}/>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {filtered.length === 0 && (
        <div className="intg-empty">
          <Search size={36} style={{ color:'var(--text-faint)' }}/>
          <h3>No integrations found</h3>
          <p>Try a different search term.</p>
          <button className="intg-btn intg-btn--secondary" onClick={() => setSearch('')}>Clear Search</button>
        </div>
      )}

      <AnimatePresence>
        {activeModal && activeInteg && (
          <IntegrationModal
            integ={activeInteg}
            config={configs[activeModal]}
            onChange={(k,v) => setConfigs(p => ({ ...p, [activeModal]: { ...p[activeModal], [k]:v } }))}
            onClose={() => setActiveModal(null)}
            connected={connections[activeModal]}
            onTest={handleTest}
            onSave={handleSave}
            onDisconnect={handleDisconnect}
            syncInterval={syncs[activeModal]}
            setSync={v => setSyncs(p => ({ ...p, [activeModal]:v }))}
            testState={testState}
            saveLoading={saveLoading}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
