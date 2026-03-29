/**
 * SearchProgress - Real-time search pipeline progress display
 */

import { motion } from 'framer-motion'
import {
    Search,
    Globe,
    FileText,
    Sparkles,
    Filter,
    BarChart3,
    Image,
    Save,
    CheckCircle2,
    Loader2,
    XCircle,
    Clock,
    Users,
    FileSearch,
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'
import type { SearchProgressData, SearchProgressStep } from '@/lib/procurement-chat-api'

const stepIcons: Record<string, React.ComponentType<{ className?: string }>> = {
    expand: Sparkles,
    search: Search,
    fetch: Globe,
    extract: FileText,
    dedup: Filter,
    score: BarChart3,
    logo: Image,
    save: Save,
    done: CheckCircle2,
}

interface SearchProgressProps {
    data: SearchProgressData
    className?: string
}

function StepItem({ step, isLast }: { step: SearchProgressStep; isLast: boolean }) {
    const Icon = stepIcons[step.id] || Clock

    const getStatusStyles = () => {
        switch (step.status) {
            case 'completed':
                return {
                    icon: 'bg-green-500 text-white',
                    line: 'bg-green-500',
                    text: 'text-green-700',
                }
            case 'active':
                return {
                    icon: 'bg-primary text-primary-foreground animate-pulse',
                    line: 'bg-gradient-to-b from-primary to-border',
                    text: 'text-primary font-medium',
                }
            case 'failed':
                return {
                    icon: 'bg-red-500 text-white',
                    line: 'bg-red-500',
                    text: 'text-red-700',
                }
            default:
                return {
                    icon: 'bg-muted text-muted-foreground',
                    line: 'bg-border',
                    text: 'text-muted-foreground',
                }
        }
    }

    const styles = getStatusStyles()

    return (
        <div className="flex items-start gap-3">
            {/* Icon */}
            <div className="flex flex-col items-center">
                <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center',
                        styles.icon
                    )}
                >
                    {step.status === 'active' ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : step.status === 'failed' ? (
                        <XCircle className="w-4 h-4" />
                    ) : step.status === 'completed' ? (
                        <CheckCircle2 className="w-4 h-4" />
                    ) : (
                        <Icon className="w-4 h-4" />
                    )}
                </motion.div>
                {!isLast && (
                    <div className={cn('w-0.5 h-8 mt-1', styles.line)} />
                )}
            </div>

            {/* Label */}
            <div className="pt-1">
                <span className={cn('text-sm', styles.text)}>
                    {step.label}
                </span>
                {step.details && (
                    <p className="text-xs text-muted-foreground mt-0.5">
                        {step.details}
                    </p>
                )}
            </div>
        </div>
    )
}

export function SearchProgress({ data, className }: SearchProgressProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn('rounded-xl border bg-card p-4', className)}
        >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <FileSearch className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                        <h3 className="font-medium text-sm">Searching vendors...</h3>
                        <p className="text-xs text-muted-foreground">
                            {data.progress_pct}% complete
                        </p>
                    </div>
                </div>
                {data.estimated_time_remaining && (
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        {data.estimated_time_remaining}
                    </div>
                )}
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
                <Progress value={data.progress_pct} className="h-2" />
            </div>

            {/* Stats */}
            <div className="flex gap-4 mb-4 text-sm">
                <div className="flex items-center gap-1.5">
                    <Users className="w-4 h-4 text-green-500" />
                    <span className="font-medium">{data.vendors_found}</span>
                    <span className="text-muted-foreground">vendors</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <Globe className="w-4 h-4 text-blue-500" />
                    <span className="font-medium">{data.sources_searched}</span>
                    <span className="text-muted-foreground">sources</span>
                </div>
            </div>

            {/* Steps */}
            <div className="space-y-0">
                {data.steps.map((step, index) => (
                    <StepItem
                        key={step.id}
                        step={step}
                        isLast={index === data.steps.length - 1}
                    />
                ))}
            </div>
        </motion.div>
    )
}

export function CompactSearchProgress({ data }: { data: SearchProgressData }) {
    const activeStep = data.steps.find(s => s.status === 'active')
    const completedCount = data.steps.filter(s => s.status === 'completed').length

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border bg-card p-3"
        >
            <div className="flex items-center gap-3">
                <div className="relative">
                    <Loader2 className="w-5 h-5 text-primary animate-spin" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between text-sm">
                        <span className="font-medium truncate">
                            {activeStep?.label || 'Processing...'}
                        </span>
                        <span className="text-muted-foreground text-xs">
                            {data.progress_pct}%
                        </span>
                    </div>
                    <Progress value={data.progress_pct} className="h-1.5 mt-1" />
                    <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                        <span>{data.vendors_found} vendors</span>
                        <span>{data.sources_searched} sources</span>
                        <span>{completedCount}/{data.steps.length} steps</span>
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
