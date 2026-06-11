import { Button } from './index';

export default function GradientButton({ children, variant = 'primary', ...props }) {
  // Translate variant names to new standard matching User Requirements
  return (
    <Button variant="primary" {...props}>
      {children}
    </Button>
  );
}

export { Button as GradientButton };
