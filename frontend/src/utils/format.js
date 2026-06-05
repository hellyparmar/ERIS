export const fmtINR = (v) => {
  if (v == null || isNaN(v)) return '—';
  if (v >= 10000000) return `₹${(v / 10000000).toFixed(2)} Cr`;
  if (v >= 100000) return `₹${(v / 100000).toFixed(2)} L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(1)}k`;
  return `₹${Number(v).toFixed(2)}`;
};

export const fmtINRFull = (v) =>
  v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN');

export const fmtNum = (v) => {
  if (v == null || isNaN(v)) return '—';
  if (v >= 10000000) return `${(v / 10000000).toFixed(1)}Cr`;
  if (v >= 100000) return `${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
  return String(v);
};

export const fmtPct = (v, showSign = true) => {
  if (v == null || isNaN(v)) return '—';
  const sign = showSign && v > 0 ? '+' : '';
  return `${sign}${Number(v).toFixed(1)}%`;
};

export const fmtDate = (d) => {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

export const timeAgo = (dateStr) => {
  if (!dateStr) return '—';
  const diff = Date.now() - new Date(dateStr).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
};
