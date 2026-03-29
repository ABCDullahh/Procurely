/**
 * QuickStatsCard - Displays search statistics in a clean grid
 */

import { motion } from 'framer-motion'
import {
    Building2, Globe, DollarSign, Users, Star, MapPin,
    TrendingUp, Shield, Clock, Zap, CheckCircle, Target
} from 'lucide-react'
import { cn } from '@/lib/utils'

export interface StatItem {
    label: string
    value: string | number
    change?: string
    changeType?: 'positive' | 'negative' | 'neutral'
    icon?: string
}

interface QuickStatsCardProps {
    title?: string
    stats: StatItem[]
    columns?: 2 | 3 | 4
    className?: string
}

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    building: Building2,
    globe: Globe,
    dollar: DollarSign,
    users: Users,
    star: Star,
    location: MapPin,
    trending: TrendingUp,
    shield: Shield,
    clock: Clock,
    zap: Zap,
    check: CheckCircle,
    target: Target,
}

export function QuickStatsCard({
    title = 'Quick Stats',
    stats,
    columns = 3,
    className,
}: QuickStatsCardProps) {
    if (!stats || stats.length === 0) return null

    const gridCols = {
        2: 'grid-cols-2',
        3: 'grid-cols-3',
        4: 'grid-cols-2 sm:grid-cols-4',
    }

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
                <h3 className="font-semibold text-sm">{title}</h3>
            </div>

            {/* Stats Grid */}
            <div className={cn('grid divide-x divide-y', gridCols[columns])}>
                {stats.map((stat, index) => {
                    const Icon = stat.icon ? iconMap[stat.icon] : null

                    return (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: index * 0.03 }}
                            className="p-4 text-center hover:bg-muted/20 transition-colors"
                        >
                            {Icon && (
                                <div className="flex justify-center mb-2">
                                    <div className="w-8 h-8 rounded-lg bg-crimson/10 flex items-center justify-center">
                                        <Icon className="w-4 h-4 text-crimson" />
                                    </div>
                                </div>
                            )}
                            <div className="text-2xl font-bold text-foreground">
                                {stat.value}
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                {stat.label}
                            </div>
                            {stat.change && (
                                <div className={cn(
                                    'text-xs font-medium mt-1',
                                    stat.changeType === 'positive' && 'text-green-600',
                                    stat.changeType === 'negative' && 'text-red-600',
                                    stat.changeType === 'neutral' && 'text-muted-foreground'
                                )}>
                                    {stat.change}
                                </div>
                            )}
                        </motion.div>
                    )
                })}
            </div>
        </motion.div>
    )
}

export default QuickStatsCard
