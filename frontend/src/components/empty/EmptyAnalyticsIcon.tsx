/**
 * EmptyAnalyticsIcon - Illustration for analytics unavailable
 */

export function EmptyAnalyticsIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            {/* Bar 1 */}
            <rect
                x="8"
                y="32"
                width="12"
                height="24"
                rx="2"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <rect
                x="8"
                y="32"
                width="12"
                height="24"
                rx="2"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            {/* Bar 2 */}
            <rect
                x="26"
                y="20"
                width="12"
                height="36"
                rx="2"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <rect
                x="26"
                y="20"
                width="12"
                height="36"
                rx="2"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            {/* Bar 3 */}
            <rect
                x="44"
                y="8"
                width="12"
                height="48"
                rx="2"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <rect
                x="44"
                y="8"
                width="12"
                height="48"
                rx="2"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            {/* Question */}
            <circle
                cx="50"
                cy="16"
                r="6"
                fill="hsl(var(--background))"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
            />
            <text
                x="50"
                y="19"
                textAnchor="middle"
                fontSize="8"
                fill="hsl(var(--primary))"
            >
                ?
            </text>
        </svg>
    )
}

export default EmptyAnalyticsIcon
