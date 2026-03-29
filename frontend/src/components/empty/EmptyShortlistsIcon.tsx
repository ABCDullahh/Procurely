/**
 * EmptyShortlistsIcon - Illustration for no shortlists
 */

export function EmptyShortlistsIcon({ className = 'w-12 h-12' }: { className?: string }) {
    return (
        <svg viewBox="0 0 64 64" className={className} fill="none">
            <polygon
                points="32,8 38,24 56,26 42,38 46,56 32,46 18,56 22,38 8,26 26,24"
                fill="hsl(var(--blush))"
                opacity="0.5"
            />
            <polygon
                points="32,8 38,24 56,26 42,38 46,56 32,46 18,56 22,38 8,26 26,24"
                stroke="hsl(var(--primary))"
                strokeWidth="2"
                strokeLinejoin="round"
            />
        </svg>
    )
}

export default EmptyShortlistsIcon
