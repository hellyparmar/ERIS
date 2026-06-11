import { Card } from './index';

export default function UnifiedCard({ children, title, subtitle, actions, className = '', ...props }) {
  return (
    <Card 
      variant="base" 
      title={title} 
      titleRight={actions} 
      className={className} 
      {...props}
    >
      {subtitle && <p className="card-subtitle">{subtitle}</p>}
      {children}
    </Card>
  );
}

export { UnifiedCard };
