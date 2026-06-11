import React from 'react';
import PropTypes from 'prop-types';
import { Database } from 'lucide-react';
import '../../styles/eris-components.css';

/**
 * EmptyState Component - Clean feedback illustration for empty states
 */
export const EmptyState = ({
  icon: Icon = Database,
  title = 'No Results Found',
  subtitle = 'Try adjusting your filters, searching for something else, or creating a new entry.',
  action,
  className = '',
  style = {},
  ...props
}) => {
  return (
    <div 
      className={`eris-empty-state ${className}`}
      style={{
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px dashed var(--border-subtle)',
        borderRadius: '16px',
        padding: 'var(--space-8) var(--space-6)',
        ...style
      }}
      {...props}
    >
      <div className="eris-empty-state__icon" style={{ display: 'flex', justifyContent: 'center' }}>
        <Icon size={48} strokeWidth={1.5} style={{ color: 'var(--text-tertiary)' }} />
      </div>
      <h3 className="eris-empty-state__title" style={{ marginTop: 'var(--space-2)' }}>{title}</h3>
      <p className="eris-empty-state__subtitle" style={{ marginTop: 'var(--space-1)', marginBottom: action ? 'var(--space-4)' : '0' }}>{subtitle}</p>
      {action && <div style={{ display: 'flex', justifyContent: 'center' }}>{action}</div>}
    </div>
  );
};

EmptyState.propTypes = {
  icon: PropTypes.elementType,
  title: PropTypes.string,
  subtitle: PropTypes.string,
  action: PropTypes.node,
  className: PropTypes.string,
  style: PropTypes.object,
};

export default EmptyState;
