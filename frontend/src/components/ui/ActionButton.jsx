import { Button } from './index';

export default function ActionButton({ children, variant = 'primary', icon, ...props }) {
  // Map ActionButton variants to master Button variants
  const variantMap = {
    primary: 'primary',
    destructive: 'danger',
    secondary: 'secondary',
    accept: 'success',
    dismiss: 'secondary',
    outline: 'secondary'
  };

  return (
    <Button 
      variant={variantMap[variant] || 'primary'} 
      icon={icon} 
      {...props}
    >
      {children}
    </Button>
  );
}

export { ActionButton };
