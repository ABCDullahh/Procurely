import { cn, getScoreColor } from '@/lib/utils'
import { Info } from 'lucide-react'

interface ScorePillProps {
    label: string
    score: number
    maxScore?: number
    showTooltip?: boolean
    tooltipText?: string
    className?: string
}

/**
 * ScorePill - Displays a score with color-coded badge
 */
export function ScorePill({
    label,
    score,
    maxScore = 100,
    showTooltip = true,
    tooltipText,
    className,
}: ScorePillProps) {
    const percentage = Math.round((score / maxScore) * 100)
    const colorClass = getScoreColor(percentage)

    return (
        <div className={cn('inline-flex items-center gap-2', className)}>
            <span className="text-xs text-muted-foreground font-medium">{label}</span>
            <div
                className={cn(
                    'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold',
                    colorClass
                )}
                title={tooltipText}
            >
                <span>{percentage}%</span>
                {showTooltip && tooltipText && (
                    <Info className="w-3 h-3 opacity-60" />
                )}
            </div>
        </div>
    )
}
