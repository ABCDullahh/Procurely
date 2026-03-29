/**
 * EmptySearchIcon - Illustration for "ready to search" state
 */

export function EmptySearchIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            <circle
                cx="32"
                cy="32"
                r="24"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <circle
                cx="32"
                cy="32"
                r="24"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <polygon points="28,22 28,42 44,32" fill="hsl(var(--primary))" />
        </svg>
    )
}

export default EmptySearchIcon
