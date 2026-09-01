import { useState, useMemo, useCallback, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import {
  Search, Plus, Eye, Trash2, X, Printer, ChevronUp, ChevronDown,
  CheckCircle2, Clock, AlertTriangle, FileText, Download, ChevronLeft, ChevronRight
} from 'lucide-react';
import SEO from '../components/SEO';
import { useToast } from '../components/ui/Toast';

const PER_PAGE = 10;

const fmt = (n) => `₹${(n || 0).toLocaleString('en-IN')}`;

function StatusBadge({ status }) {
  const map = {
    paid:    { label: 'Paid',    cls: 'active' },
    pending: { label: 'Pending', cls: 'warning' },
    overdue: { label: 'Overdue', cls: 'critical' },
    draft:   { label: 'Draft',   cls: 'neutral' },
  };
  const s = map[status] || map.draft;
  return <div className={`badge ${s.cls}`}>{s.label}</div>;
}

function ViewModal({ invoice, contacts, onClose }) {
  if (!invoice) return null;
  const supplier = contacts?.find(c => c.id === invoice.supplier_id);
  const items = invoice.items || [];
  const subtotal = items.reduce((s,i) => s + i.unit_price * i.quantity, 0);
  const tax = invoice.tax_amount || subtotal * 0.18;
  const total = invoice.total || subtotal + tax;
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 24 }}
      onClick={onClose}>
      <div onClick={e=>e.stopPropagation()}
        style={{ maxWidth: 640, width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden',
          background: 'var(--c-canvas)', border: '1px solid var(--c-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--c-border)', background: 'var(--c-canvas-raised)' }}>
          <span style={{ fontFamily: 'var(--f-display)', fontSize: '15px', fontWeight: 600, color: 'var(--c-dark)' }}>Invoice {invoice.invoice_number}</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }}><X size={18}/></button>
        </div>
        <div style={{ padding: 20, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div>
            <div className="zone-label" style={{ marginBottom: 12 }}>Invoice Details</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, fontSize: '13px' }}>
              <div><div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)', marginBottom: 2 }}>Invoice #</div><div style={{ fontFamily: 'var(--f-mono)', color: 'var(--c-brown)', fontWeight: 600 }}>{invoice.invoice_number}</div></div>
              <div><div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)', marginBottom: 4 }}>Status</div><StatusBadge status={invoice.status}/></div>
              <div><div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)', marginBottom: 2 }}>Supplier</div><div>{supplier?.name||'—'}</div></div>
              <div><div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)', marginBottom: 2 }}>Issue Date</div><div>{new Date(invoice.issue_date).toLocaleDateString()}</div></div>
              <div><div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)', marginBottom: 2 }}>Due Date</div><div>{new Date(invoice.due_date).toLocaleDateString()}</div></div>
            </div>
          </div>
          {items.length > 0 && (
            <div>
              <div className="zone-label" style={{ marginBottom: 12 }}>Line Items</div>
              <div style={{ overflowX: 'auto' }}>
                <table className="eris-table" style={{ width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Description</th>
                      <th style={{ textAlign: 'right' }}>Qty</th>
                      <th style={{ textAlign: 'right' }}>Unit Price</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it, idx) => (
                      <tr key={idx}>
                        <td>{it.description}</td>
                        <td style={{ textAlign: 'right' }}>{it.quantity}</td>
                        <td className="mono" style={{ textAlign: 'right' }}>{fmt(it.unit_price)}</td>
                        <td className="mono" style={{ textAlign: 'right' }}>{fmt(it.quantity*it.unit_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          <div style={{ borderTop: '1px solid var(--c-border)', padding: '12px 0', display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--c-ink-muted)' }}>
              <span>Subtotal</span><span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(subtotal)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--c-ink-muted)' }}>
              <span>Tax (GST 18%)</span><span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(tax)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 700, color: 'var(--c-dark)', borderTop: '1px solid var(--c-border)', paddingTop: 10, marginTop: 4 }}>
              <span>Total</span><span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(total)}</span>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', padding: '12px 20px', borderTop: '1px solid var(--c-border)', background: 'var(--c-canvas-raised)' }}>
          <button className="action-btn" onClick={onClose}><Printer size={13} style={{ marginRight: 6 }} />Print</button>
          <button className="action-btn primary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}

function CreateModal({ contacts, onClose }) {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const [errorMsg, setErrorMsg] = useState('');
  const [form, setForm] = useState({
    supplier_id:'', outlet_id:'1',
    issue_date: new Date().toISOString().split('T')[0],
    due_date: (() => { const d=new Date(); d.setDate(d.getDate()+30); return d.toISOString().split('T')[0]; })(),
    items:[{description:'',quantity:1,unit_price:0}],
    tax_rate:18, notes:''
  });
  const mutation = useMutation({
    mutationFn: async (data) => {
      const items = data.items.filter(i=>i.description&&i.quantity&&i.unit_price);
      const subtotal = items.reduce((s,i)=>s+(i.quantity*i.unit_price),0);
      const tax_amount = subtotal*(data.tax_rate/100);
      return api.post('/api/v1/gst/invoices', {
        supplier_id:parseInt(data.supplier_id), outlet_id:parseInt(data.outlet_id)||1,
        invoice_number:`INV-${Date.now()}`, issue_date:data.issue_date, due_date:data.due_date,
        items, tax_rate:data.tax_rate, tax_amount, total:subtotal+tax_amount, status:'pending', notes:data.notes
      });
    },
    onSuccess: (data)=>{ 
      if (data?.data?.error) {
        setErrorMsg(data.data.error);
        return;
      }
      addToast('Invoice created successfully', 'success');
      qc.invalidateQueries({queryKey:['invoices']}); 
      onClose(); 
    },
    onError: (err) => {
      setErrorMsg(err.response?.data?.detail || err.message || 'Failed to create invoice');
    }
  });
  const setItem = (idx,field,val) => setForm(p=>{ const it=[...p.items]; it[idx]={...it[idx],[field]:val}; return {...p,items:it}; });
  const subtotal = form.items.reduce((s,i)=>s+(parseFloat(i.unit_price||0)*parseFloat(i.quantity||0)),0);
  const tax = subtotal*(form.tax_rate/100);
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 24 }}
      onClick={onClose}>
      <div onClick={e=>e.stopPropagation()}
        style={{ maxWidth: 680, width: '100%', maxHeight: '90vh', display: 'flex', flexDirection: 'column', overflow: 'hidden',
          background: 'var(--c-canvas)', border: '1px solid var(--c-border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--c-border)', background: 'var(--c-canvas-raised)' }}>
          <span style={{ fontFamily: 'var(--f-display)', fontSize: '15px', fontWeight: 600, color: 'var(--c-dark)' }}>Create Invoice</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }}><X size={18}/></button>
        </div>
        <div style={{ padding: 20, overflowY: 'auto' }}>
          <form id="inv-form" onSubmit={e=>{e.preventDefault(); setErrorMsg(''); mutation.mutate(form);}} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {errorMsg && <div style={{ color: 'var(--c-critical)', fontSize: 13 }}>{errorMsg}</div>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Supplier *</span>
                <select value={form.supplier_id} onChange={e=>setForm(p=>({...p,supplier_id:e.target.value}))} required>
                  <option value="">Select supplier</option>
                  {contacts?.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Outlet ID</span>
                <input value={form.outlet_id} onChange={e=>setForm(p=>({...p,outlet_id:e.target.value}))} placeholder="1"/>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Issue Date</span>
                <input type="date" value={form.issue_date} onChange={e=>setForm(p=>({...p,issue_date:e.target.value}))}/>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Due Date</span>
                <input type="date" value={form.due_date} onChange={e=>setForm(p=>({...p,due_date:e.target.value}))}/>
              </div>
            </div>
            <div>
              <div className="zone-label" style={{ marginBottom: 8 }}>Line Items</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {form.items.map((item,idx)=>(
                  <div key={idx} style={{ display: 'grid', gridTemplateColumns: '1fr 70px 100px 80px auto', gap: 8, alignItems: 'center' }}>
                    <input placeholder="Description" value={item.description} onChange={e=>setItem(idx,'description',e.target.value)}/>
                    <input type="number" placeholder="Qty" min="1" step="0.01" value={item.quantity} onChange={e=>setItem(idx,'quantity',parseFloat(e.target.value)||0)}/>
                    <input type="number" placeholder="Unit price" min="0" step="0.01" value={item.unit_price} onChange={e=>setItem(idx,'unit_price',parseFloat(e.target.value)||0)}/>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-dark)', textAlign: 'right', fontFamily: 'var(--f-mono)' }}>{fmt(item.quantity*item.unit_price)}</div>
                    {form.items.length>1 && <button type="button" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-critical)' }} onClick={()=>setForm(p=>({...p,items:p.items.filter((_,i)=>i!==idx)}))}><X size={14}/></button>}
                  </div>
                ))}
                <button type="button" className="action-btn" style={{ alignSelf: 'flex-start', borderStyle: 'dashed' }}
                  onClick={()=>setForm(p=>({...p,items:[...p.items,{description:'',quantity:1,unit_price:0}]}))}>
                  <Plus size={13} style={{ marginRight: 6 }} /> Add Item
                </button>
              </div>
            </div>
            <div style={{ borderTop: '1px solid var(--c-border)', padding: '12px 0', display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, color: 'var(--c-ink-muted)' }}>
                <span>Subtotal</span><span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(subtotal)}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 13, color: 'var(--c-ink-muted)' }}>
                <span>Tax Rate (%)</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <input type="number" style={{ width: 60, padding: '2px 6px' }} min="0" max="100" step="0.1" value={form.tax_rate} onChange={e=>setForm(p=>({...p,tax_rate:parseFloat(e.target.value)||0}))}/>
                  <span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(tax)}</span>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 700, color: 'var(--c-dark)', borderTop: '1px solid var(--c-border)', paddingTop: 10, marginTop: 4 }}>
                <span>Total</span><span style={{ fontFamily: 'var(--f-mono)' }}>{fmt(subtotal+tax)}</span>
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <span style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--c-ink-muted)' }}>Notes</span>
              <textarea rows={2} placeholder="Additional notes..." value={form.notes} onChange={e=>setForm(p=>({...p,notes:e.target.value}))}/>
            </div>
          </form>
        </div>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', padding: '12px 20px', borderTop: '1px solid var(--c-border)', background: 'var(--c-canvas-raised)' }}>
          <button className="action-btn" onClick={onClose}>Cancel</button>
          <button className="action-btn primary" type="submit" form="inv-form" disabled={mutation.isPending}>
            {mutation.isPending ? 'Creating…' : 'Create Invoice'}
          </button>
        </div>
      </div>
    </div>
  );
}

function InvoiceDueChart({ invoices }) {
  const weeks = useMemo(() => {
    const buckets = {};
    const today = new Date();
    invoices.forEach(inv => {
      if (!inv.due_date) return;
      const d = new Date(inv.due_date);
      const weekStart = new Date(d);
      weekStart.setDate(d.getDate() - d.getDay());
      const key = weekStart.toISOString().split('T')[0];
      const diff = Math.ceil((d - today) / (1000 * 60 * 60 * 24));
      if (diff < -30) return;
      buckets[key] = buckets[key] || { week: key, total: 0, count: 0 };
      buckets[key].total += inv.total || 0;
      buckets[key].count += 1;
    });
    return Object.values(buckets).sort((a, b) => a.week.localeCompare(b.week)).slice(0, 8);
  }, [invoices]);

  const maxTotal = Math.max(...weeks.map(w => w.total), 1);

  if (weeks.length === 0) return null;

  return (
    <div>
      <div className="zone-label" style={{ marginBottom: 12 }}>Invoice Due Calendar</div>
      <div className="chart-zone">
        <div className="chart-inner" style={{ display: 'flex', gap: 8, alignItems: 'flex-end', height: 80, padding: '0 4px' }}>
          {weeks.map((w) => {
            const pct = (w.total / maxTotal) * 100;
            const past = new Date(w.week) < new Date();
            return (
              <div key={w.week} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                <div style={{ flex: 1, width: '100%', display: 'flex', alignItems: 'flex-end', justifyContent: 'center' }}>
                  <div style={{
                    width: '100%', maxWidth: 28, height: Math.max(4, pct * 0.7),
                    background: past ? 'var(--c-critical)' : 'var(--c-brown)', opacity: past ? 0.4 : 1,
                    transition: 'height 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
                  }} />
                </div>
                <span style={{ fontSize: 9, color: 'var(--c-ink-muted)', whiteSpace: 'nowrap', fontFamily: 'var(--f-mono)' }}>
                  {new Date(w.week).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function Invoices() {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo]   = useState('');
  const [sortCol, setSortCol] = useState('issue_date');
  const [sortDir, setSortDir] = useState('desc');
  const [page, setPage] = useState(1);
  const [viewing, setViewing] = useState(null);
  const [creating, setCreating] = useState(false);
  const qc = useQueryClient();

  // Handle ?action=new
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('action') === 'new') {
      setCreating(true);
    }
  }, []);

  const { data: invoices=[], isLoading } = useQuery({
    queryKey:['invoices'],
    queryFn: async()=>{ const r=await api.get('/api/v1/gst/invoices'); return r.data.invoices ?? []; }
  });
  const { data: contacts=[] } = useQuery({
    queryKey:['suppliers'],
    queryFn: async()=>{ const r=await api.get('/api/v1/suppliers/'); return r.data?.data?.suppliers || r.data?.suppliers || []; }
  });

  const deleteMut = useMutation({ mutationFn: id=>Promise.reject(new Error("Deleting GST invoices is not allowed")), onError: (e)=>alert(e.message) });
  const paidMut   = useMutation({ mutationFn: id=>api.post(`/api/v1/gst/invoices/${id}/pay`), onSuccess:()=>qc.invalidateQueries({queryKey:['invoices']}) });

  const handleSort = useCallback((col) => {
    if (sortCol===col) setSortDir(d=>d==='asc'?'desc':'asc');
    else { setSortCol(col); setSortDir('asc'); }
    setPage(1);
  },[sortCol]);

  const hasFilters = search||status!=='all'||dateFrom||dateTo;

  const filtered = useMemo(()=>{
    let list = invoices.filter(inv=>{
      const sup = contacts.find(c=>c.id===inv.supplier_id);
      const q = search.toLowerCase();
      if (q && !inv.invoice_number?.toLowerCase().includes(q) && !sup?.name?.toLowerCase().includes(q)) return false;
      if (status!=='all' && inv.status!==status) return false;
      const d = new Date(inv.issue_date);
      if (dateFrom && d<new Date(dateFrom)) return false;
      if (dateTo   && d>new Date(dateTo))   return false;
      return true;
    });
    list.sort((a,b)=>{
      let av=a[sortCol], bv=b[sortCol];
      if (sortCol==='issue_date'||sortCol==='due_date') { av=new Date(av); bv=new Date(bv); }
      if (sortCol==='total'||sortCol==='tax_amount') { av=av||0; bv=bv||0; }
      return sortDir==='asc' ? (av>bv?1:-1) : (av<bv?1:-1);
    });
    return list;
  },[invoices,contacts,search,status,dateFrom,dateTo,sortCol,sortDir]);

  const stats = useMemo(()=>({
    paid:    {val:invoices.filter(i=>i.status==='paid').reduce((s,i)=>s+(i.total||0),0),    cnt:invoices.filter(i=>i.status==='paid').length},
    pending: {val:invoices.filter(i=>i.status==='pending').reduce((s,i)=>s+(i.total||0),0), cnt:invoices.filter(i=>i.status==='pending').length},
    overdue: {val:invoices.filter(i=>i.status==='overdue').reduce((s,i)=>s+(i.total||0),0), cnt:invoices.filter(i=>i.status==='overdue').length},
  }),[invoices]);

  const totalPages = Math.max(1, Math.ceil(filtered.length/PER_PAGE));
  const pageRows   = filtered.slice((page-1)*PER_PAGE, page*PER_PAGE);

  const SortIcon = ({col}) => {
    if (sortCol!==col) return <ChevronUp size={12} style={{opacity:.3}}/>;
    return sortDir==='asc' ? <ChevronUp size={12}/> : <ChevronDown size={12}/>;
  };

  return (
    <>
      <style>{`
        .invoices-row:hover {
          background: var(--c-brown-glow) !important;
        }
      `}</style>
      <SEO title="Invoices Directory" description="Track invoices, due cycles, tax values, and vendors" />
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
            <h1 className="page-title" >Invoices</h1>
            <p style={{ fontSize: '11px', color: 'var(--c-ink-muted)', margin: '4px 0 0' }}>Manage sales and track payments</p>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="action-btn" style={{ padding: '6px 12px' }}><Download size={13} style={{ marginRight: 6 }} />Export</button>
            <button className="action-btn primary" onClick={()=>setCreating(true)}><Plus size={13} style={{ marginRight: 6 }} />New Invoice</button>
          </div>
        </div>

        {/* Content body */}
        <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          <InvoiceDueChart invoices={invoices} />

          {/* KPI Strip */}
          <div className="kpi-strip">
            {[
              {key:'paid',    label:'Total Paid',    color:'var(--c-sage)',    class: 'sage'},
              {key:'pending', label:'Total Pending', color:'var(--c-brown)',   class: 'brown'},
              {key:'overdue', label:'Total Overdue', color:'var(--c-critical)',class: 'critical'},
            ].map(({key,label,class: cls})=>(
              <div key={key} className="kpi-cell">
                <div className="kpi-label">{label}</div>
                <div className={`kpi-value ${cls}`}>{fmt(stats[key].val)}</div>
                <div style={{ fontSize: '10px', color: 'var(--c-ink-muted)', marginTop: 4 }}>
                  {stats[key].cnt} {key === 'paid' ? 'paid' : key === 'pending' ? 'pending' : 'overdue'} invoices
                </div>
              </div>
            ))}
          </div>

          {/* Filter Ba          <div className="filter-bar">
            <div style={{ flex: 1, minWidth: 200, position: 'relative' }}>
              <Search size={14} style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-muted)' }}/>
              <input placeholder="Search invoice ID, supplier…" value={search} onChange={e=>{setSearch(e.target.value);setPage(1);}}
                style={{ paddingLeft: 30, fontSize: 12 }}/>
              {search && <button onClick={()=>setSearch('')} style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--c-ink-muted)' }}><X size={13}/></button>}
            </div>
            <select style={{ width: 140 }} value={status} onChange={e=>{setStatus(e.target.value);setPage(1);}}>
              <option value="all">All Status</option>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
              <option value="overdue">Overdue</option>
              <option value="draft">Draft</option>
            </select>
            <input type="date" style={{ width: 130 }} value={dateFrom} onChange={e=>{setDateFrom(e.target.value);setPage(1);}} title="From"/>
            <input type="date" style={{ width: 130 }} value={dateTo} onChange={e=>{setDateTo(e.target.value);setPage(1);}} title="To"/>
            {hasFilters && (
              <button className="action-btn" style={{ color: 'var(--c-critical)', marginLeft: 'auto' }} onClick={()=>{setSearch('');setStatus('all');setDateFrom('');setDateTo('');setPage(1);}}>
                <X size={13} style={{ marginRight: 6 }} /> Reset
              </button>
            )}
          </div>  </div>

          {/* Table */}
          <div style={{ overflowX: 'auto' }}>
            <table className="eris-table" style={{ width: '100%', minWidth: 780 }}>
              <thead>
                <tr>
                  {[
                    {col:'invoice_number',label:'Invoice #', align:'left'},
                    {col:'supplier_id',   label:'Supplier', align:'left'},
                    {col:'issue_date',    label:'Issue Date', align:'left'},
                    {col:'due_date',      label:'Due Date', align:'left'},
                    {col:'total',         label:'Total', align:'right'},
                    {col:'tax_amount',    label:'Tax', align:'right'},
                    {col:'status',        label:'Status', align:'center'},
                    {col:null,            label:'Actions', align:'center'},
                  ].map(({col,label,align})=>(
                    <th key={label} onClick={()=>col&&handleSort(col)}
                      style={{ cursor: col ? 'pointer' : 'default', textAlign: align }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {label}{col&&<SortIcon col={col}/>}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  [...Array(6)].map((_,i)=>(
                    <tr key={i}>
                      {[120,140,90,90,100,80,80,70].map((w,j)=>(
                        <td key={j}><div className="skeleton" style={{ width: w, height: 16 }} /></td>
                      ))}
                    </tr>
                  ))
                ) : pageRows.length===0 ? (
                  <tr><td colSpan={8}>
                    <div className="empty-state" style={{ padding: '40px 0' }}>
                      <p className="empty-state-desc">{hasFilters ? 'No invoices match active filters.' : 'No invoices configured yet.'}</p>
                    </div>
                  </td></tr>
                ) : pageRows.map((inv, idx)=>{
                  const sup = contacts.find(c=>c.id===inv.supplier_id);
                  const due = new Date(inv.due_date);
                  const today = new Date();
                  const daysLeft = Math.ceil((due-today)/(1000*60*60*24));
                  const isOverdue = inv.status==='pending'&&due<today;
                  const isWarning = !isOverdue&&daysLeft<=7&&inv.status==='pending';
                  return (
                    <tr key={inv.id} className="invoices-row" style={{ cursor: 'pointer' }} onClick={()=>setViewing(inv)}>
                      <td><span className="mono" style={{ fontWeight: 600, color: 'var(--c-brown)' }}>{inv.invoice_number}</span></td>
                      <td><span style={{ fontWeight: 600 }}>{sup?.name||'—'}</span></td>
                      <td style={{ color: 'var(--c-ink-muted)' }}>{new Date(inv.issue_date).toLocaleDateString()}</td>
                      <td style={{ color: isOverdue?'var(--c-critical)':isWarning?'var(--c-brown)':'var(--c-ink-muted)', fontWeight: isOverdue||isWarning?600:400 }}>{new Date(inv.due_date).toLocaleDateString()}</td>
                      <td className="mono" style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(inv.total)}</td>
                      <td className="mono" style={{ textAlign: 'right', color: 'var(--c-ink-muted)' }}>{fmt(inv.tax_amount)}</td>
                      <td style={{ textAlign: 'center' }}><StatusBadge status={inv.status}/></td>
                      <td style={{ textAlign: 'center' }} onClick={e=>e.stopPropagation()}>
                        <div style={{ display: 'flex', gap: 4, justifyContent: 'center' }}>
                          <button className="action-btn" style={{ padding: '4px 8px' }} title="View" onClick={()=>setViewing(inv)}><Eye size={13}/></button>
                          {inv.status!=='paid'&&<button className="action-btn" style={{ padding: '4px 8px', color: 'var(--c-sage)' }} title="Mark Paid" onClick={()=>{ if(confirm('Mark as paid?')) paidMut.mutate(inv.id); }}><CheckCircle2 size={13}/></button>}
                          <button className="action-btn" style={{ padding: '4px 8px', color: 'var(--c-critical)' }} title="Delete" onClick={()=>{ if(confirm('Delete invoice?')) deleteMut.mutate(inv.id); }}><Trash2 size={13}/></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {!isLoading && filtered.length > PER_PAGE && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: 'var(--c-canvas-raised)', border: '1px solid var(--c-border)', flexWrap: 'wrap' }}>
              <span style={{ fontSize: 12, color: 'var(--c-ink-muted)' }}>
                Showing {Math.min((page-1)*PER_PAGE+1, filtered.length)}–{Math.min(page*PER_PAGE, filtered.length)} of {filtered.length}
              </span>
              <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                <button className="action-btn" style={{ padding: '4px 8px' }} disabled={page===1} onClick={()=>setPage(p=>p-1)}><ChevronLeft size={13}/></button>
                {Array.from({length:Math.min(totalPages,5)},(_,i)=>i+1).map(n=>(
                  <button key={n} className={`action-btn ${page===n ? 'primary' : ''}`} style={{ padding: '4px 8px' }} onClick={()=>setPage(n)}>{n}</button>
                ))}
                <button className="action-btn" style={{ padding: '4px 8px' }} disabled={page===totalPages} onClick={()=>setPage(p=>p+1)}><ChevronRight size={13}/></button>
              </div>
            </div>
          )}

        </div>

      </div>

      {viewing  && <ViewModal invoice={viewing} contacts={contacts} onClose={()=>setViewing(null)}/>}
      {creating && <CreateModal contacts={contacts} onClose={()=>setCreating(false)}/>}
    </>
  );
}
