/**
 * InsightsCard - Displays key procurement insights in an elegant card
 */

import { motion } from 'framer-motion'
import { Lightbulb, TrendingUp, AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Insight {
    type: 'recommendation' | 'trend' | 'warning' | 'highlight'
    title: string
    description: string
    action?: string
}

interface InsightsCardProps {
    title?: string
    insights: Insight[]
    onActionClick?: (action: string) => void
    className?: string
}

const iconMap = {
    recommendation: Lightbulb,
    trend: TrendingUp,
    warning: AlertTriangle,
    highlight: CheckCircle2,
}

const colorMap = {
    recommendation: 'text-blue-600 bg-blue-50',
    trend: 'text-purple-600 bg-purple-50',
    warning: 'text-amber-600 bg-amber-50',
    highlight: 'text-green-600 bg-green-50',
}

export function InsightsCard({
    title = 'Key Insights',
    insights,
    onActionClick,
    className,
}: InsightsCardProps) {
    if (!insights || insights.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                'rounded-xl border bg-card shadow-sm overflow-hidden',
                className
            )}
        >
            {/* Header */}
            <div className="px-4 py-3 border-b bg-muted/30">
                <div className="flex items-center gap-2">
                    <Lightbulb className="w-4 h-4 text-crimson" />
                    <h3 className="font-semibold text-sm">{title}</h3>
                </div>
            </div>

            {/* Insights List */}
            <div className="divide-y">
                {insights.map((insight, index) => {
                    const Icon = iconMap[insight.type]
                    const colorClass = colorMap[insight.type]

                    return (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 hover:bg-muted/20 transition-colors"
                        >
                            <div className="flex gap-3">
                                <div className={cn(
                                    'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                                    colorClass
                                )}>
                                    <Icon className="w-4 h-4" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="font-medium text-sm mb-1">
                                        {insight.title}
                                    </h4>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        {insight.description}
                                    </p>
                                    {insight.action && (
                                        <button
                                            onClick={() => onActionClick?.(insight.action!)}
                                            className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-crimson hover:text-crimson/80 transition-colors"
                                        >
                                            {insight.action}
                                            <ArrowRight className="w-3 h-3" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    )
                })}
            </div>
        </motion.div>
    )
}

export default InsightsCard
