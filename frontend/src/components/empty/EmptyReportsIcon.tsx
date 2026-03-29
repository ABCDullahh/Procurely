/**
 * EmptyReportsIcon - Illustration for no reports
 */

export function EmptyReportsIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            {/* Back paper */}
            <rect
                x="8"
                y="12"
                width="32"
                height="40"
                rx="3"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <rect
                x="8"
                y="12"
                width="32"
                height="40"
                rx="3"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            {/* Front paper */}
            <rect
                x="24"
                y="20"
                width="32"
                height="40"
                rx="3"
                fill="hsl(var(--background))"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <line
                x1="32"
                y1="32"
                x2="48"
                y2="32"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <line
                x1="32"
                y1="40"
                x2="44"
                y2="40"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.6"
            />
            <line
                x1="32"
                y1="48"
                x2="40"
                y2="48"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.4"
            />
        </svg>
    )
}

export default EmptyReportsIcon
