import { cn } from '@/lib/utils'

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'risk-basso' | 'risk-medio' | 'risk-alto' | 'risk-critico'
}

const variantClasses: Record<string, string> = {
  default: 'bg-text-muted/20 text-text-secondary',
  'risk-basso': 'bg-risk-basso/20 text-risk-basso',
  'risk-medio': 'bg-risk-medio/20 text-risk-medio',
  'risk-alto': 'bg-risk-alto/20 text-risk-alto',
  'risk-critico': 'bg-risk-critico/20 text-risk-critico',
}

export function Badge({ className, variant = 'default', children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold',
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
