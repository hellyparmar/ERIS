import { Tooltip as MasterTooltip } from './index';

export default function Tooltip({ children, content, position = 'top' }) {
  return (
    <MasterTooltip content={content} position={position}>
      {children}
    </MasterTooltip>
  );
}

export { MasterTooltip as Tooltip };
