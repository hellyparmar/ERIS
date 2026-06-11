import { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Plus, Eye, Trash2, X, Printer, ChevronUp, ChevronDown,
  CheckCircle2, Clock, AlertTriangle, FileText, Download, ChevronLeft, ChevronRight
} from 'lucide-react';
import '../styles/invoices.css';

const API_BASE = 'http://localhost:8000/api/v1';
const PER_PAGE = 10;

const fmt = (n) => `₹${(n || 0).toLocaleString('en-IN')}`;

/* ── Status Badge ── */
function StatusBadge({ status }) {
  const map = {
    paid:    { icon: <CheckCircle2 size={12}/>, label: 'Paid',    cls: 'inv-status--paid' },
    pending: { icon: <Clock size={12}/>,        label: 'Pending', cls: 'inv-status--pending' },
    overdue: { icon: <AlertTriangle size={12}/>,label: 'Overdue', cls: 'inv-status--overdue' },
    draft:   { icon: <FileText size={12}/>,     label: 'Draft',   cls: 'inv-status--draft' },
  };
  const s = map[status] || map.draft;
  return <span className={`inv-status ${s.cls}`}>{s.icon}{s.label}</span>;
}

/* ── Skeleton Rows ── */
function SkeletonRows() {
  return Array.from({length:6}).map((_,i) => (
    <tr key={i}>
      {[120,140,90,90,100,80,80,70].map((w,j) => (
        <td key={j} style={{padding:'14px 16px'}}>
          <div className="inv-skeleton-cell" style={{width:w}}/>
        </td>
      ))}
    </tr>
  ));
}

/* ── View Modal ── */
function ViewModal({ invoice, contacts, onClose }) {
  if (!invoice) return null;
  const supplier = contacts?.find(c => c.id === invoice.supplier_id);
  const items = invoice.items || [];
  const subtotal = items.reduce((s,i) => s + i.unit_price * i.quantity, 0);
  const tax = invoice.tax_amount || subtotal * 0.18;
  const total = invoice.total || subtotal + tax;
  return (
    <div className="inv-modal-overlay" onClick={onClose}>
      <motion.div className="inv-modal" onClick={e=>e.stopPropagation()}
        initial={{opacity:0,scale:0.95,y:16}} animate={{opacity:1,scale:1,y:0}} exit={{opacity:0,scale:0.95,y:16}}
        transition={{duration:0.2}}>
        <div className="inv-modal__header">
          <h2>Invoice {invoice.invoice_number}</h2>
          <button className="inv-modal__close" onClick={onClose}><X size={16}/></button>
        </div>
        <div className="inv-modal__body">
          <div>
            <p className="inv-modal__section-title">Invoice Details</p>
            <div className="inv-detail-grid">
              <div className="inv-detail-item"><label>Invoice #</label><p className="inv-id">{invoice.invoice_number}</p></div>
              <div className="inv-detail-item"><label>Status</label><p><StatusBadge status={invoice.status}/></p></div>
              <div className="inv-detail-item"><label>Supplier</label><p>{supplier?.company_name||'—'}</p></div>
              <div className="inv-detail-item"><label>Issue Date</label><p>{new Date(invoice.issue_date).toLocaleDateString()}</p></div>
              <div className="inv-detail-item"><label>Due Date</label><p>{new Date(invoice.due_date).toLocaleDateString()}</p></div>
            </div>
          </div>
          {items.length > 0 && (
            <div>
              <p className="inv-modal__section-title">Line Items</p>
              <table className="inv-items-table">
                <thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr></thead>
                <tbody>{items.map((it,idx)=>(
                  <tr key={idx}>
                    <td>{it.description}</td>
                    <td>{it.quantity}</td>
                    <td>{fmt(it.unit_price)}</td>
                    <td>{fmt(it.quantity*it.unit_price)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
          <div className="inv-summary">
            <div className="inv-summary-row"><span>Subtotal</span><span>{fmt(subtotal)}</span></div>
            <div className="inv-summary-row"><span>Tax (GST 18%)</span><span>{fmt(tax)}</span></div>
            <div className="inv-summary-row inv-summary-row--total"><span>Total</span><span>{fmt(total)}</span></div>
          </div>
        </div>
        <div className="inv-modal__footer">
          <button className="inv-btn inv-btn--secondary" onClick={()=>window.print()}>
            <Printer size={15}/>Print
          </button>
          <button className="inv-btn inv-btn--primary" onClick={onClose}>Close</button>
        </div>
      </motion.div>
    </div>
  );
}

/* ── Create Modal ── */
function CreateModal({ contacts, onClose, onSuccess }) {
  const qc = useQueryClient();
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
      return axios.post(`${API_BASE}/invoices`,{
        supplier_id:parseInt(data.supplier_id), outlet_id:parseInt(data.outlet_id)||1,
        invoice_number:`INV-${Date.now()}`, issue_date:data.issue_date, due_date:data.due_date,
        items, tax_rate:data.tax_rate, tax_amount, total:subtotal+tax_amount, status:'pending', notes:data.notes
      });
    },
    onSuccess: ()=>{ qc.invalidateQueries({queryKey:['invoices']}); onClose(); }
  });
  const setItem = (idx,field,val) => setForm(p=>{ const it=[...p.items]; it[idx]={...it[idx],[field]:val}; return {...p,items:it}; });
  const subtotal = form.items.reduce((s,i)=>s+(parseFloat(i.unit_price||0)*parseFloat(i.quantity||0)),0);
  const tax = subtotal*(form.tax_rate/100);
  return (
    <div className="inv-modal-overlay" onClick={onClose}>
      <motion.div className="inv-modal" onClick={e=>e.stopPropagation()}
        initial={{opacity:0,scale:0.95,y:16}} animate={{opacity:1,scale:1,y:0}} exit={{opacity:0,scale:0.95,y:16}}
        transition={{duration:0.2}} style={{maxWidth:720}}>
        <div className="inv-modal__header">
          <h2>Create Invoice</h2>
          <button className="inv-modal__close" onClick={onClose}><X size={16}/></button>
        </div>
        <div className="inv-modal__body">
          <form id="inv-form" onSubmit={e=>{e.preventDefault();mutation.mutate(form);}} className="inv-form">
            <div className="inv-form-grid">
              <div className="inv-form-group">
                <label className="inv-form-label">Supplier *</label>
                <select className="inv-form-select" value={form.supplier_id} onChange={e=>setForm(p=>({...p,supplier_id:e.target.value}))} required>
                  <option value="">Select supplier</option>
                  {contacts?.map(c=><option key={c.id} value={c.id}>{c.company_name}</option>)}
                </select>
              </div>
              <div className="inv-form-group">
                <label className="inv-form-label">Outlet ID</label>
                <input className="inv-form-input" value={form.outlet_id} onChange={e=>setForm(p=>({...p,outlet_id:e.target.value}))} placeholder="1"/>
              </div>
              <div className="inv-form-group">
                <label className="inv-form-label">Issue Date</label>
                <input type="date" className="inv-form-input" value={form.issue_date} onChange={e=>setForm(p=>({...p,issue_date:e.target.value}))}/>
              </div>
              <div className="inv-form-group">
                <label className="inv-form-label">Due Date</label>
                <input type="date" className="inv-form-input" value={form.due_date} onChange={e=>setForm(p=>({...p,due_date:e.target.value}))}/>
              </div>
            </div>
            <div>
              <p className="inv-modal__section-title">Line Items</p>
              <div className="inv-items-area">
                {form.items.map((item,idx)=>(
                  <div key={idx} className="inv-item-row">
                    <input className="inv-form-input" placeholder="Description" value={item.description} onChange={e=>setItem(idx,'description',e.target.value)}/>
                    <input type="number" className="inv-form-input" placeholder="Qty" min="1" step="0.01" value={item.quantity} onChange={e=>setItem(idx,'quantity',parseFloat(e.target.value)||0)}/>
                    <input type="number" className="inv-form-input" placeholder="Unit price" min="0" step="0.01" value={item.unit_price} onChange={e=>setItem(idx,'unit_price',parseFloat(e.target.value)||0)}/>
                    <div className="inv-item-total">{fmt(item.quantity*item.unit_price)}</div>
                    {form.items.length>1 && <button type="button" className="inv-remove-btn" onClick={()=>setForm(p=>({...p,items:p.items.filter((_,i)=>i!==idx)}))}><X size={13}/></button>}
                  </div>
                ))}
                <button type="button" className="inv-add-item-btn" onClick={()=>setForm(p=>({...p,items:[...p.items,{description:'',quantity:1,unit_price:0}]}))}>
                  <Plus size={14}/>Add Item
                </button>
              </div>
            </div>
            <div className="inv-tax-box">
              <div className="inv-summary-row"><span>Subtotal</span><span>{fmt(subtotal)}</span></div>
              <div className="inv-summary-row" style={{alignItems:'center',gap:8}}>
                <span>Tax Rate (%)</span>
                <input type="number" style={{width:60}} className="inv-form-input" min="0" max="100" step="0.1" value={form.tax_rate} onChange={e=>setForm(p=>({...p,tax_rate:parseFloat(e.target.value)||0}))}/>
                <span style={{marginLeft:'auto'}}>{fmt(tax)}</span>
              </div>
              <div className="inv-summary-row inv-summary-row--total"><span>Total</span><span>{fmt(subtotal+tax)}</span></div>
            </div>
            <div className="inv-form-group">
              <label className="inv-form-label">Notes</label>
              <textarea className="inv-form-textarea" rows={2} placeholder="Additional notes..." value={form.notes} onChange={e=>setForm(p=>({...p,notes:e.target.value}))}/>
            </div>
          </form>
        </div>
        <div className="inv-modal__footer">
          <button className="inv-btn inv-btn--secondary" onClick={onClose}>Cancel</button>
          <button className="inv-btn inv-btn--primary" type="submit" form="inv-form" disabled={mutation.isPending}>
            {mutation.isPending?'Creating…':'Create Invoice'}
          </button>
        </div>
      </motion.div>
    </div>
  );
}

/* ── Main Page ── */
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

  const { data: invoices=[], isLoading } = useQuery({
    queryKey:['invoices'],
    queryFn: async()=>{ const r=await axios.get(`${API_BASE}/invoices`); return r.data; }
  });
  const { data: contacts=[] } = useQuery({
    queryKey:['contacts'],
    queryFn: async()=>{ const r=await axios.get(`${API_BASE}/contacts`); return r.data; }
  });

  const deleteMut = useMutation({ mutationFn: id=>axios.delete(`${API_BASE}/invoices/${id}`), onSuccess:()=>qc.invalidateQueries({queryKey:['invoices']}) });
  const paidMut   = useMutation({ mutationFn: id=>axios.patch(`${API_BASE}/invoices/${id}`,{status:'paid'}), onSuccess:()=>qc.invalidateQueries({queryKey:['invoices']}) });

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
      if (q && !inv.invoice_number?.toLowerCase().includes(q) && !sup?.company_name?.toLowerCase().includes(q)) return false;
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
    <div className="invoices-page">
      {/* Header */}
      <div className="inv-header">
        <div className="inv-header__left">
          <p>Manage sales and track payments</p>
        </div>
        <div className="inv-header__actions">
          <button className="inv-btn inv-btn--secondary"><Download size={15}/>Export</button>
          <button className="inv-btn inv-btn--primary" onClick={()=>setCreating(true)}><Plus size={15}/>New Invoice</button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="inv-kpis">
        {[
          {key:'paid',    label:'Total Paid',    icon:<CheckCircle2 size={20}/>, cls:'--green', sub:`From ${stats.paid.cnt} invoices`},
          {key:'pending', label:'Total Pending', icon:<Clock size={20}/>,        cls:'--amber', sub:'Requires attention'},
          {key:'overdue', label:'Total Overdue', icon:<AlertTriangle size={20}/>,cls:'--red',   sub:`${stats.overdue.cnt} overdue invoices`},
        ].map(({key,label,icon,cls,sub})=>(
          <motion.div key={key} className="inv-kpi" whileHover={{y:-2}} transition={{duration:0.18}}>
            <div className="inv-kpi__top">
              <div className={`inv-kpi__icon inv-kpi__icon${cls}`}>{icon}</div>
              <span className={`inv-kpi__badge inv-kpi__badge${cls}`}>{stats[key].cnt}</span>
            </div>
            <div className="inv-kpi__value">{fmt(stats[key].val)}</div>
            <div className="inv-kpi__label">{label}</div>
            <div className="inv-kpi__sub">{sub}</div>
          </motion.div>
        ))}
      </div>

      {/* Filters */}
      <div className="inv-filters">
        <div className="inv-search">
          <Search size={16} className="inv-search__icon"/>
          <input placeholder="Search by invoice ID, supplier…" value={search} onChange={e=>{setSearch(e.target.value);setPage(1);}}/>
          {search && <button className="inv-search__clear" onClick={()=>setSearch('')}><X size={14}/></button>}
        </div>
        <select className="inv-filter-select" value={status} onChange={e=>{setStatus(e.target.value);setPage(1);}}>
          <option value="all">All Status</option>
          <option value="paid">Paid</option>
          <option value="pending">Pending</option>
          <option value="overdue">Overdue</option>
          <option value="draft">Draft</option>
        </select>
        <input type="date" className="inv-filter-date" value={dateFrom} onChange={e=>{setDateFrom(e.target.value);setPage(1);}} title="From"/>
        <input type="date" className="inv-filter-date" value={dateTo}   onChange={e=>{setDateTo(e.target.value);setPage(1);}}   title="To"/>
        {hasFilters && (
          <button className="inv-filter-reset" onClick={()=>{setSearch('');setStatus('all');setDateFrom('');setDateTo('');setPage(1);}}>
            <X size={13}/> Reset
          </button>
        )}
      </div>

      {/* Table */}
      <div className="inv-table-card">
        <div className="inv-table-wrap">
          <table className="inv-table">
            <thead>
              <tr>
                {[
                  {col:'invoice_number',label:'Invoice #'},
                  {col:'supplier_id',   label:'Supplier'},
                  {col:'issue_date',    label:'Issue Date'},
                  {col:'due_date',      label:'Due Date'},
                  {col:'total',         label:'Total'},
                  {col:'tax_amount',    label:'Tax'},
                  {col:'status',        label:'Status'},
                  {col:null,            label:'Actions'},
                ].map(({col,label})=>(
                  <th key={label} className={sortCol===col?'sorted':''} onClick={()=>col&&handleSort(col)}>
                    <span className="inv-th-inner">{label}{col&&<SortIcon col={col}/>}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? <SkeletonRows/> : pageRows.length===0 ? (
                <tr><td colSpan={8}>
                  <div className="inv-empty">
                    <div className="inv-empty__icon"><FileText size={28}/></div>
                    <h3>No invoices found</h3>
                    <p>{hasFilters?'Try adjusting your filters or search term.':'Create your first invoice to get started.'}</p>
                    {!hasFilters && <button className="inv-btn inv-btn--primary" onClick={()=>setCreating(true)}><Plus size={14}/>Create Invoice</button>}
                  </div>
                </td></tr>
              ) : pageRows.map((inv,i)=>{
                const sup = contacts.find(c=>c.id===inv.supplier_id);
                const due = new Date(inv.due_date);
                const today = new Date();
                const daysLeft = Math.ceil((due-today)/(1000*60*60*24));
                const isOverdue = inv.status==='pending'&&due<today;
                const isWarning = !isOverdue&&daysLeft<=7&&inv.status==='pending';
                return (
                  <motion.tr key={inv.id} initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} transition={{delay:i*0.03,duration:0.2}} onClick={()=>setViewing(inv)}>
                    <td><span className="inv-id">{inv.invoice_number}</span></td>
                    <td><span className="inv-supplier">{sup?.company_name||'—'}</span></td>
                    <td><span className="inv-date">{new Date(inv.issue_date).toLocaleDateString()}</span></td>
                    <td><span className={isOverdue?'inv-due--overdue':isWarning?'inv-due--warning':'inv-date'}>{new Date(inv.due_date).toLocaleDateString()}</span></td>
                    <td><span className="inv-amount">{fmt(inv.total)}</span></td>
                    <td><span className="inv-tax">{fmt(inv.tax_amount)}</span></td>
                    <td><StatusBadge status={inv.status}/></td>
                    <td onClick={e=>e.stopPropagation()}>
                      <div className="inv-actions">
                        <button className="inv-action-btn" title="View" onClick={()=>setViewing(inv)}><Eye size={15}/></button>
                        {inv.status!=='paid'&&<button className="inv-action-btn inv-action-btn--success" title="Mark Paid" onClick={()=>{ if(confirm('Mark as paid?')) paidMut.mutate(inv.id); }}><CheckCircle2 size={15}/></button>}
                        <button className="inv-action-btn inv-action-btn--danger" title="Delete" onClick={()=>{ if(confirm('Delete invoice?')) deleteMut.mutate(inv.id); }}><Trash2 size={15}/></button>
                      </div>
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!isLoading && filtered.length > PER_PAGE && (
          <div className="inv-pagination">
            <span className="inv-pagination__info">
              Showing {Math.min((page-1)*PER_PAGE+1, filtered.length)}–{Math.min(page*PER_PAGE, filtered.length)} of {filtered.length}
            </span>
            <div className="inv-pagination__controls">
              <button className="inv-page-btn" disabled={page===1} onClick={()=>setPage(p=>p-1)}><ChevronLeft size={14}/></button>
              {Array.from({length:Math.min(totalPages,5)},(_,i)=>i+1).map(n=>(
                <button key={n} className={`inv-page-btn${page===n?' inv-page-btn--active':''}`} onClick={()=>setPage(n)}>{n}</button>
              ))}
              <button className="inv-page-btn" disabled={page===totalPages} onClick={()=>setPage(p=>p+1)}><ChevronRight size={14}/></button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <AnimatePresence>
        {viewing  && <ViewModal   invoice={viewing}  contacts={contacts} onClose={()=>setViewing(null)}/>}
        {creating && <CreateModal contacts={contacts} onClose={()=>setCreating(false)}/>}
      </AnimatePresence>
    </div>
  );
}
