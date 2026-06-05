import React from 'react'
import { cn } from '../../utils/utils'

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'error'
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    const variants = {
      default: 'bg-blue-50 border-blue-200 text-blue-800',
      success: 'bg-green-50 border-green-200 text-green-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      error: 'bg-red-50 border-red-200 text-red-800',
    }

    return (
      <div
        ref={ref}
        className={cn(
          'px-4 py-4 border rounded-lg',
          variants[variant],
          className
        )}
        {...props}
      />
    )
  }
)

Alert.displayName = 'Alert'

interface AlertTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

const AlertTitle = React.forwardRef<HTMLHeadingElement, AlertTitleProps>(
  ({ className, ...props }, ref) => (
    <h5 ref={ref} className={cn('mb-1 font-medium leading-tight', className)} {...props} />
  )
)

AlertTitle.displayName = 'AlertTitle'

interface AlertDescriptionProps extends React.HTMLAttributes<HTMLDivElement> {}

const AlertDescription = React.forwardRef<HTMLDivElement, AlertDescriptionProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('text-sm', className)} {...props} />
  )
)

AlertDescription.displayName = 'AlertDescription'

export { Alert, AlertTitle, AlertDescription }
