/**
 * EmptyVendorsIcon - Illustration for no vendors found
 */

export function EmptyVendorsIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            <circle
                cx="24"
                cy="24"
                r="12"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <circle
                cx="24"
                cy="24"
                r="12"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <circle
                cx="40"
                cy="40"
                r="12"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <circle
                cx="40"
                cy="40"
                r="12"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <line
                x1="32"
                y1="28"
                x2="32"
                y2="36"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.6"
            />
        </svg>
    )
}

export default EmptyVendorsIcon
