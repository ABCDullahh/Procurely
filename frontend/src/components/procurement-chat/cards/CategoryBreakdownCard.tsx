/**
 * CategoryBreakdownCard - Shows industry/category breakdown
 */

import { motion } from 'framer-motion'
import { PieChart } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface CategoryItem {
    name: string
    count: number
    percentage: number
    color?: string
}

interface CategoryBreakdownCardProps {
    title?: string
    categories: CategoryItem[]
    onCategoryClick?: (category: string) => void
    className?: string
}

const defaultColors = [
    'bg-crimson',
    'bg-blue-500',
    'bg-green-500',
    'bg-purple-500',
    'bg-amber-500',
    'bg-teal-500',
    'bg-pink-500',
    'bg-indigo-500',
]

export function CategoryBreakdownCard({
    title = 'Industry Breakdown',
    categories,
    onCategoryClick,
    className,
}: CategoryBreakdownCardProps) {
    if (!categories || categories.length === 0) return null

    const total = categories.reduce((sum, c) => sum + c.count, 0)

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
                    <PieChart className="w-4 h-4 text-crimson" />
                    <h3 className="font-semibold text-sm">{title}</h3>
                </div>
            </div>

            {/* Progress Bars */}
            <div className="p-4 space-y-3">
                {categories.map((category, index) => {
                    const colorClass = category.color || defaultColors[index % defaultColors.length]

                    return (
                        <motion.div
                            key={category.name}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className={cn(
                                'cursor-pointer hover:opacity-80 transition-opacity',
                                onCategoryClick && 'cursor-pointer'
                            )}
                            onClick={() => onCategoryClick?.(category.name)}
                        >
                            <div className="flex items-center justify-between mb-1">
                                <div className="flex items-center gap-2">
                                    <div className={cn('w-2 h-2 rounded-full', colorClass)} />
                                    <span className="text-sm font-medium truncate">
                                        {category.name}
                                    </span>
                                </div>
                                <span className="text-xs text-muted-foreground">
                                    {category.count} ({category.percentage}%)
                                </span>
                            </div>
                            <div className="h-2 bg-muted rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${category.percentage}%` }}
                                    transition={{ duration: 0.5, delay: index * 0.05 }}
                                    className={cn('h-full rounded-full', colorClass)}
                                />
                            </div>
                        </motion.div>
                    )
                })}
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t bg-muted/20">
                <p className="text-xs text-muted-foreground text-center">
                    Total: {total} vendors across {categories.length} industries
                </p>
            </div>
        </motion.div>
    )
}

export default CategoryBreakdownCard
