import { MetricCard } from './index';

export default function StatCard({
  title,
  value,
  change,
  changeType = 'up',
  colorVariant = 'yellow',
  icon,
  trend,
}) {
  const colorMap = {
    yellow: 'warning',
    pink: 'danger',
    green: 'success',
    blue: 'info',
    purple: 'accent'
  };

  const trendVal = change ? parseFloat(change.replace(/[^0-9.-]/g, '')) : undefined;
  const isDown = changeType === 'down' || (change && change.includes('-'));

  return (
    <MetricCard
      title={title}
      value={value}
      trend={trendVal ? (isDown ? -trendVal : trendVal) : undefined}
      trendLabel={trend}
      icon={icon ? () => icon : null}
      color={colorMap[colorVariant] || 'accent'}
    />
  );
}
