import './stat-card.css';

export default function StatCard({
  title,
  value,
  change,
  changeType = 'up', // 'up' or 'down'
  colorVariant = 'yellow', // 'yellow', 'pink', 'green', 'blue', 'purple'
  icon,
  trend,
}) {
  const getCardClass = () => {
    return `stat-card stat-card-${colorVariant}`;
  };

  const getTrendClass = () => {
    if (changeType === 'up') return 'trend-positive';
    if (changeType === 'down') return 'trend-negative';
    return 'trend-neutral';
  };

  return (
    <div className={getCardClass()}>
      <div className="stat-card-header">
        <h3 className="stat-card-title">{title}</h3>
        {icon && <div className="stat-card-icon">{icon}</div>}
      </div>

      <div className="stat-card-body">
        <div className="stat-card-value">{value}</div>
        {trend && (
          <div className={`stat-card-trend ${getTrendClass()}`}>
            <span className="trend-value">{change}</span>
            <span className="trend-period">{trend}</span>
          </div>
        )}
      </div>
    </div>
  );
}
