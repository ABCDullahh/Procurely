/**
 * FilterChips - Interactive filter suggestion chips
 */

import { motion } from 'framer-motion'
import {
    Flag,
    Globe,
    Shield,
    Lock,
    Headphones,
    Gift,
    MapPin,
    DollarSign,
    Users,
    Building2,
    Clock,
    Star,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { FilterChip } from '@/lib/procurement-chat-api'

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    flag: Flag,
    globe: Globe,
    shield: Shield,
    lock: Lock,
    headphones: Headphones,
    gift: Gift,
    'map-pin': MapPin,
    dollar: DollarSign,
    users: Users,
    building: Building2,
    clock: Clock,
    star: Star,
}

interface FilterChipsProps {
    chips: FilterChip[]
    onChipClick: (chip: FilterChip) => void
    activeFilters?: string[]
    className?: string
}

export function FilterChips({
    chips,
    onChipClick,
    activeFilters = [],
    className,
}: FilterChipsProps) {
    if (chips.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn('flex flex-wrap gap-2', className)}
        >
            {chips.map((chip, index) => {
                const Icon = chip.icon ? iconMap[chip.icon] || null : null
                const isActive = activeFilters.includes(chip.id)

                return (
                    <motion.button
                        key={chip.id}
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => onChipClick(chip)}
                        className={cn(
                            'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium',
                            'border transition-all duration-200',
                            'hover:scale-105 active:scale-95',
                            isActive
                                ? 'bg-primary text-primary-foreground border-primary'
                                : 'bg-card hover:bg-accent/50 border-border hover:border-primary/50'
                        )}
                    >
                        {Icon && <Icon className="w-3.5 h-3.5" />}
                        <span>{chip.label}</span>
                    </motion.button>
                )
            })}
        </motion.div>
    )
}

interface SuggestedQueriesProps {
    queries: Array<{ text: string; type: string }>
    onQueryClick: (text: string) => void
    className?: string
}

export function SuggestedQueries({
    queries,
    onQueryClick,
    className,
}: SuggestedQueriesProps) {
    if (queries.length === 0) return null

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'compare':
                return 'border-blue-500/30 bg-blue-500/5 hover:bg-blue-500/10 text-blue-700'
            case 'explain':
                return 'border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10 text-purple-700'
            case 'refine':
                return 'border-green-500/30 bg-green-500/5 hover:bg-green-500/10 text-green-700'
            case 'action':
                return 'border-orange-500/30 bg-orange-500/5 hover:bg-orange-500/10 text-orange-700'
            default:
                return 'border-border bg-card hover:bg-accent/50'
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn('space-y-2', className)}
        >
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Suggested
            </span>
            <div className="flex flex-wrap gap-2">
                {queries.map((query, index) => (
                    <motion.button
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => onQueryClick(query.text)}
                        className={cn(
                            'px-3 py-1.5 rounded-lg text-sm border transition-all duration-200',
                            'hover:scale-[1.02] active:scale-95',
                            getTypeColor(query.type)
                        )}
                    >
                        {query.text}
                    </motion.button>
                ))}
            </div>
        </motion.div>
    )
}
