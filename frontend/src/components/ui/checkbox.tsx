import * as React from 'react'
import { cn } from '@/lib/utils'
import { Check } from 'lucide-react'

export interface CheckboxProps
    extends React.InputHTMLAttributes<HTMLInputElement> {
    onCheckedChange?: (checked: boolean) => void
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
    ({ className, onCheckedChange, checked, disabled, ...props }, ref) => {
        const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
            onCheckedChange?.(e.target.checked)
            props.onChange?.(e)
        }

        return (
            <label
                className={cn(
                    'relative inline-flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center rounded-sm border border-primary ring-offset-background',
                    'focus-within:outline-none focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
                    checked && 'bg-primary text-primary-foreground',
                    disabled && 'cursor-not-allowed opacity-50',
                    className
                )}
            >
                <input
                    type="checkbox"
                    ref={ref}
                    checked={checked}
                    disabled={disabled}
                    className="sr-only"
                    onChange={handleChange}
                    {...props}
                />
                {checked && <Check className="h-4 w-4" />}
            </label>
        )
    }
)
Checkbox.displayName = 'Checkbox'

export { Checkbox }
