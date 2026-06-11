import { Skeleton } from './index';

export default function LoadingSkeleton({ variant = 'text', count = 1, className = '' }) {
  const heightMap = {
    card: '208px',
    'table-row': '48px',
    text: '16px',
    chart: '256px',
  };

  const height = heightMap[variant] || '16px';
  const radius = variant === 'text' ? 999 : 12;

  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <Skeleton 
          key={idx} 
          height={height} 
          radius={radius} 
          className={className} 
          style={{ marginBottom: 12 }}
        />
      ))}
    </>
  );
}

export { LoadingSkeleton };
