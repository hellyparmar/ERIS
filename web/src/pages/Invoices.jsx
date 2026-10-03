import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, Printer, Search } from 'lucide-react'
import { api } from '../lib/api'
import { useApp, useToast } from '../lib/app'
import { dateTime, money } from '../lib/format'
import { Badge, Card, DataTable, Drawer, PageHead, Pager, Query, Spinner, useDebounced } from '../components/ui'

async function openPdf(id, toast) {
  try {
    const res = await api(`/invoices/${id}/pdf`, { raw: true })
    const url = URL.createObjectURL(await res.blob())
    window.open(url, '_blank', 'noopener')
    setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (e) {
    toast(e.message, 'error')
  }
}

export default function Invoices() {
  const { outletId } = useApp()
  const [params, setParams] = useSearchParams()
  const openId = params.get('id') ? Number(params.get('id')) : null
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const q = useDebounced(search)
  const list = useQuery({ queryKey: ['invoices', q, outletId, page], queryFn: () => api('/invoices', { params: { q, outlet_id: outletId, page, page_size: 25 } }), placeholderData: (p) => p })
  return (
    <>
      <PageHead title="Invoices (demo GST)" subtitle="GST-style tax invoices issued from sales: CGST + SGST within a state, IGST between states, HSN codes and a printable PDF. Issue one from any bill on the Sales page." />
      <div className="watermark-note" style={{ marginBottom: 16 }}>
        DEMO - NOT FOR TAX FILING. The GSTINs are synthetic and invoices are not registered on the Invoice Registration Portal (no IRN / QR code).
      </div>
      <Card flush actions={<div className="search"><Search /><input className="input" placeholder="Invoice no., bill no., buyer or GSTIN" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1) }} aria-label="Search invoices" /></div>}
        title="Invoice history">
        <Query q={list}>{(d) => (
          <>
            <DataTable rows={d.items} onRowClick={(r) => setParams({ id: String(r.id) })}
              empty="No invoices yet - open a bill on the Sales page and choose 'Issue GST invoice'" columns={[
                { key: 'number', label: 'Invoice', render: (r) => <b>{r.number}</b> },
                { key: 'issued_at', label: 'Issued', render: (r) => dateTime(r.issued_at) },
                { key: 'outlet', label: 'Outlet' },
                { key: 'buyer_name', label: 'Buyer', render: (r) => r.buyer_name || <span className="muted">Walk-in</span> },
                { key: 'supply_type', label: 'Supply', render: (r) => (r.supply_type === 'intra_state' ? 'CGST + SGST' : 'IGST') },
                { key: 'taxable_value', label: 'Taxable', format: 'currency' },
                { key: 'total', label: 'Total', format: 'currency' },
                { key: 'sale_status', label: '', render: (r) => (r.sale_status !== 'completed' ? <Badge tone="bad">cancelled</Badge> : null) },
              ]} />
            {d.pages > 1 && <Pager page={page} pages={d.pages} total={d.total} onPage={setPage} label="invoices" />}
          </>
        )}</Query>
      </Card>
      {openId && <InvoiceDrawer id={openId} onClose={() => setParams({})} />}
    </>
  )
}

function InvoiceDrawer({ id, onClose }) {
  const toast = useToast()
  const q = useQuery({ queryKey: ['invoice', id], queryFn: () => api(`/invoices/${id}`) })
  const inv = q.data
  return (
    <Drawer title={inv ? `Invoice ${inv.number}` : 'Invoice'} onClose={onClose}
      actions={inv && <button className="btn sm primary" onClick={() => openPdf(id, toast)}><Printer />PDF</button>}>
      {q.isLoading ? <Spinner /> : q.isError ? <div className="down">{q.error.message}</div> : (
        <div className="stack" style={{ gap: 14 }}>
          <div className="watermark-note">{inv.watermark}{inv.sale_status !== 'completed' && ' - the sale was voided, so this invoice is cancelled'}</div>
          <Card>
            <dl className="dl">
              <dt>Bill</dt><dd><Link to="/sales">{inv.invoice_no}</Link> · {dateTime(inv.sold_at)} · {inv.payment_method.toUpperCase()}</dd>
              <dt>Seller GSTIN</dt><dd>{inv.seller_gstin || 'not set'} <Badge tone="warn">demo</Badge></dd>
              <dt>Buyer</dt><dd>{inv.buyer_name || 'Walk-in customer'} · {inv.buyer_gstin || 'Unregistered'}</dd>
              <dt>Place of supply</dt><dd>{inv.place_of_supply_name} ({inv.place_of_supply})</dd>
              <dt>Supply type</dt><dd>{inv.supply_type === 'intra_state' ? 'Intra-state - CGST + SGST' : 'Inter-state - IGST'}</dd>
            </dl>
          </Card>
          <Card flush>
            <DataTable rows={inv.items} sortable={false} columns={[
              { key: 'product', label: 'Item', render: (r) => <><b>{r.product}</b><div className="small muted">HSN {r.hsn_code || '-'} · GST {r.tax_rate}%</div></> },
              { key: 'quantity', label: 'Qty', format: 'number' },
              { key: 'taxable_value', label: 'Taxable', format: 'currency' },
              { key: 'tax', label: 'Tax', format: 'currency' },
              { key: 'total', label: 'Amount', format: 'currency' },
            ]} />
          </Card>
          <Card title="Tax summary" flush>
            <DataTable rows={inv.tax_summary} sortable={false} columns={[
              { key: 'rate', label: 'GST %', render: (r) => `${r.rate}%` }, { key: 'taxable_value', label: 'Taxable', format: 'currency' },
              { key: 'cgst', label: 'CGST', format: 'currency' }, { key: 'sgst', label: 'SGST', format: 'currency' }, { key: 'igst', label: 'IGST', format: 'currency' },
            ]} />
          </Card>
          <Card>
            <dl className="dl" style={{ gridTemplateColumns: '1fr auto' }}>
              <dt>Taxable value</dt><dd className="right tabular">{money(inv.taxable_value, { decimals: true })}</dd>
              <dt>CGST</dt><dd className="right tabular">{money(inv.cgst, { decimals: true })}</dd>
              <dt>SGST</dt><dd className="right tabular">{money(inv.sgst, { decimals: true })}</dd>
              <dt>IGST</dt><dd className="right tabular">{money(inv.igst, { decimals: true })}</dd>
              <dt><b>Total</b></dt><dd className="right tabular"><b>{money(inv.total, { decimals: true })}</b></dd>
            </dl>
            <p className="small muted" style={{ marginTop: 8 }}><FileText size={13} style={{ verticalAlign: -2 }} /> {inv.amount_in_words}</p>
          </Card>
        </div>
      )}
    </Drawer>
  )
}
