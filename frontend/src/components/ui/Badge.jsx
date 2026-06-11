import { Badge as MasterBadge } from './index';

export default function Badge({ children, label, variant = 'neutral', ...props }) {
  return (
    <MasterBadge variant={variant} {...props}>
      {children || label}
    </MasterBadge>
  );
}

export { MasterBadge as Badge };
