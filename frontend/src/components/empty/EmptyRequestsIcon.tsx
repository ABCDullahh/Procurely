/**
 * EmptyRequestsIcon - Illustration for empty requests state
 * Uses CSS vars for palette alignment, no heavy filters
 */

export function EmptyRequestsIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            {/* Paper */}
            <rect
                x="12"
                y="8"
                width="40"
                height="48"
                rx="4"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <rect
                x="12"
                y="8"
                width="40"
                height="48"
                rx="4"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            {/* Lines */}
            <line
                x1="20"
                y1="20"
                x2="44"
                y2="20"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <line
                x1="20"
                y1="28"
                x2="40"
                y2="28"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.6"
            />
            <line
                x1="20"
                y1="36"
                x2="36"
                y2="36"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
                opacity="0.4"
            />
            {/* Plus circle */}
            <circle
                cx="48"
                cy="48"
                r="12"
                fill="hsl(var(--background))"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <line
                x1="44"
                y1="48"
                x2="52"
                y2="48"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
            />
            <line
                x1="48"
                y1="44"
                x2="48"
                y2="52"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinecap="round"
            />
        </svg>
    )
}

export default EmptyRequestsIcon
