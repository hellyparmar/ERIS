import { Card as MasterCard } from './index';

export default function Card({ children, className = '', variant = 'base', ...props }) {
  // Map variant name to visual match
  const v = variant === 'glass' ? 'base' : variant === 'default' ? 'base' : variant;
  return (
    <MasterCard variant={v} className={className} {...props}>
      {children}
    </MasterCard>
  );
}

export { MasterCard as Card };
