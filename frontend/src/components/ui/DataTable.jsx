import './data-table.css';

export default function DataTable({
  columns = [],
  data = [],
  loading = false,
  emptyMessage = 'No data available',
}) {
  if (loading) {
    return (
      <div className="data-table-wrapper">
        <div className="data-table">
          <table>
            <thead>
              <tr>
                {columns.map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...Array(5)].map((_, i) => (
                <tr key={i} className="skeleton-row">
                  {columns.map((col) => (
                    <td key={col.key}>
                      <div className="skeleton-line"></div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="data-table">
        <div className="empty-state">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div className="data-table-wrapper">
      <div className="data-table">
        <table>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key}>{col.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, idx) => (
              <tr key={idx} className={idx % 2 === 0 ? 'even' : 'odd'}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
