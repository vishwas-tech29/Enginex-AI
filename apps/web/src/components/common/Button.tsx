import { ButtonHTMLAttributes, forwardRef } from 'react';

type Variant = 'primary' | 'secondary' | 'ghost' | 'heroSecondary';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  isLoading?: boolean;
}

const variantClasses: Record<Variant, string> = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700',
  secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200',
  ghost: 'bg-transparent text-slate-700 hover:bg-slate-100',
  // Dark, glassy pill — used on the homepage hero (hero-theme scope), not
  // the light-themed app shell the other variants are for.
  heroSecondary: 'liquid-glass rounded-full text-[hsl(var(--hero-fg))] hover:bg-white/5',
};

const baseClasses: Record<Variant, string> = {
  primary: 'rounded-md px-4 py-2 text-sm',
  secondary: 'rounded-md px-4 py-2 text-sm',
  ghost: 'rounded-md px-4 py-2 text-sm',
  heroSecondary: '',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', isLoading, disabled, className = '', children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${baseClasses[variant]} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {isLoading ? 'Loading…' : children}
    </button>
  ),
);

Button.displayName = 'Button';
