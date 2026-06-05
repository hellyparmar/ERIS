import React from 'react';

const variantClasses = {
  card: 'h-52 rounded-3xl',
  'table-row': 'h-12 rounded-2xl',
  text: 'h-4 rounded-full',
  chart: 'h-64 rounded-3xl',
};

const LoadingSkeleton = ({ variant = 'text', count = 1, className = '' }) => {
  const shape = variantClasses[variant] || variantClasses.text;
  const baseClasses = 'relative overflow-hidden bg-slate-200/90 dark:bg-slate-700/80';

  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`${baseClasses} ${shape} ${className}`}
          style={{
            backgroundImage: 'linear-gradient(90deg, rgba(255,255,255,0), rgba(255,255,255,0.7), rgba(255,255,255,0))',
            backgroundSize: '200% 100%',
            animation: 'skeleton-shimmer 1.6s infinite',
          }}
        />
      ))}
    </>
  );
};

if (typeof document !== 'undefined' && !document.getElementById('loading-skeleton-keyframes')) {
  const style = document.createElement('style');
  style.id = 'loading-skeleton-keyframes';
  style.textContent = `
    @keyframes skeleton-shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `;
  document.head.appendChild(style);
}

export default LoadingSkeleton;
