import { Table } from './index';

export default function UnifiedTable({ columns = [], data = [], className = '', emptyMessage = 'No data available' }) {
  // Map UnifiedTable props structure to Table component props structure
  const headers = columns.map(c => ({
    key: c.accessor,
    label: c.header,
    align: 'left',
    width: c.width,
    render: c.render ? (val, row) => c.render(val, row) : undefined
  }));

  return (
    <Table
      headers={headers}
      rows={data}
      className={className}
      emptyMessage={emptyMessage}
    />
  );
}

export { UnifiedTable };
