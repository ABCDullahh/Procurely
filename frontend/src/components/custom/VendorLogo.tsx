import { cn, getInitials, stringToColor } from '@/lib/utils'

interface VendorLogoProps {
    name: string
    logoUrl?: string | null
    size?: 'sm' | 'md' | 'lg' | 'xl'
    className?: string
}

const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-base',
    xl: 'w-20 h-20 text-xl',
}

/**
 * VendorLogo - Displays vendor logo with fallback to gradient initials avatar
 */
export function VendorLogo({ name, logoUrl, size = 'md', className }: VendorLogoProps) {
    const initials = getInitials(name)
    const bgColor = stringToColor(name)

    if (logoUrl) {
        return (
            <div
                className={cn(
                    'rounded-xl overflow-hidden flex items-center justify-center bg-muted',
                    sizeClasses[size],
                    className
                )}
            >
                <img
                    src={logoUrl}
                    alt={`${name} logo`}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                        // Fallback to initials on error
                        const target = e.target as HTMLImageElement
                        target.style.display = 'none'
                    }}
                />
            </div>
        )
    }

    return (
        <div
            className={cn(
                'rounded-xl flex items-center justify-center font-semibold text-white shadow-sm',
                sizeClasses[size],
                className
            )}
            style={{ background: `linear-gradient(135deg, ${bgColor}, ${bgColor}dd)` }}
        >
            {initials}
        </div>
    )
}
