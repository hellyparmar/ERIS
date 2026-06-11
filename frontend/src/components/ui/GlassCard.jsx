import { GlassCard as MasterGlassCard } from './index';

export default function GlassCard({ children, ...props }) {
  return (
    <MasterGlassCard {...props}>
      {children}
    </MasterGlassCard>
  );
}

export { MasterGlassCard as GlassCard };
