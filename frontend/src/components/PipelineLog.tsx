/**
 * PipelineLog - Beautiful pipeline progress visualization
 * Shows detailed step-by-step progress of the search pipeline
 */

import { motion, AnimatePresence } from 'framer-motion'
import {
    CheckCircle2,
    Circle,
    Loader2,
    XCircle,
    Sparkles,
    Search,
    Globe,
    FileText,
    Users,
    Calculator,
    ImageIcon,
    Database,
    AlertTriangle,
    ChevronDown,
    ChevronUp,
    Clock,
    Cpu,
    Info,
    AlertCircle,
} from 'lucide-react'
import { useState, useMemo } from 'react'
import { cn } from '@/lib/utils'
import { SearchRun, TokenUsageEntry } from '@/lib/requests-api'

interface PipelineLogProps {
    run: SearchRun
    className?: string
}

// Steps that use LLM and should show token usage
const LLM_STEPS = ['EXPAND', 'EXPAND_INDONESIA', 'EXTRACT', 'GAP_ANALYSIS', 'QUALITY_ASSESS']

// Pipeline step definitions with icons and descriptions
const PIPELINE_STEPS = [
    {
        id: 'INIT',
        label: 'Initialize',
        description: 'Setting up pipeline and validating request',
        icon: Sparkles,
        progress: 5,
    },
    {
        id: 'EXPAND',
        label: 'Expand Queries',
        description: 'Generating search queries with Indonesia focus',
        icon: Search,
        progress: 10,
    },
    {
        id: 'SEARCH',
        label: 'Web Search',
        description: 'Searching across multiple providers (Serper, Tavily)',
        icon: Globe,
        progress: 25,
    },
    {
        id: 'FETCH',
        label: 'Fetch Content',
        description: 'Scraping pages with Jina Reader & Crawl4AI',
        icon: FileText,
        progress: 40,
    },
    {
        id: 'EXTRACT',
        label: 'Extract Vendors',
        description: 'Using AI to extract vendor information from pages',
        icon: Users,
        progress: 60,
    },
    {
        id: 'DEDUP',
        label: 'Deduplicate',
        description: 'Merging duplicate vendors from multiple sources',
        icon: Database,
        progress: 70,
    },
    {
        id: 'SCORE',
        label: 'Score & Rank',
        description: 'Calculating fit, trust, and quality scores',
        icon: Calculator,
        progress: 80,
    },
    {
        id: 'LOGO',
        label: 'Fetch Logos',
        description: 'Retrieving company logos from Clearbit & Logo.dev',
        icon: ImageIcon,
        progress: 90,
    },
    {
        id: 'SAVE',
        label: 'Save Results',
        description: 'Persisting vendors and evidence to database',
        icon: Database,
        progress: 95,
    },
    {
        id: 'DONE',
        label: 'Complete',
        description: 'Pipeline finished successfully',
        icon: CheckCircle2,
        progress: 100,
    },
]

function getStepStatus(stepId: string, currentStep: string | null, runStatus: string): 'completed' | 'current' | 'pending' | 'failed' {
    if (runStatus === 'FAILED') {
        const currentIndex = PIPELINE_STEPS.findIndex(s => s.id === currentStep)
        const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === stepId)
        if (stepIndex < currentIndex) return 'completed'
        if (stepIndex === currentIndex) return 'failed'
        return 'pending'
    }

    if (runStatus === 'COMPLETED' || currentStep === 'DONE') {
        return 'completed'
    }

    const currentIndex = PIPELINE_STEPS.findIndex(s => s.id === currentStep)
    const stepIndex = PIPELINE_STEPS.findIndex(s => s.id === stepId)

    if (stepIndex < currentIndex) return 'completed'
    if (stepIndex === currentIndex) return 'current'
    return 'pending'
}

function StepIcon({ status, icon: Icon }: { status: 'completed' | 'current' | 'pending' | 'failed'; icon: React.ElementType }) {
    if (status === 'completed') {
        return (
            <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="w-8 h-8 rounded-full bg-green-50 border border-green-200 flex items-center justify-center"
            >
                <CheckCircle2 className="w-4 h-4 text-green-600" />
            </motion.div>
        )
    }

    if (status === 'current') {
        return (
            <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ repeat: Infinity, duration: 1.5 }}
                className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center"
            >
                <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
            </motion.div>
        )
    }

    if (status === 'failed') {
        return (
            <div className="w-8 h-8 rounded-full bg-red-50 border border-red-200 flex items-center justify-center">
                <XCircle className="w-4 h-4 text-red-600" />
            </div>
        )
    }

    return (
        <div className="w-8 h-8 rounded-full bg-[#F3F0EB] border border-[#ECE8E1] flex items-center justify-center">
            <Icon className="w-4 h-4 text-[#A09A93]" />
        </div>
    )
}

function TimelineConnector({ status }: { status: 'completed' | 'current' | 'pending' | 'failed' }) {
    return (
        <div className="absolute left-4 top-8 bottom-0 w-[2px] -translate-x-1/2">
            <div
                className={cn(
                    'w-full h-full',
                    status === 'completed' && 'bg-green-200',
                    status === 'current' && 'bg-gradient-to-b from-green-200 to-[#ECE8E1]',
                    status === 'failed' && 'bg-gradient-to-b from-green-200 to-red-200',
                    status === 'pending' && 'bg-[#ECE8E1]'
                )}
            />
        </div>
    )
}

// Token usage display component
function TokenUsageDisplay({ usage }: { usage: TokenUsageEntry }) {
    return (
        <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1 text-cyan-600">
                <Cpu className="w-3 h-3" />
                <span>{usage.total_tokens.toLocaleString()} tokens</span>
            </div>
            <div className="text-muted-foreground">
                (↓{usage.prompt_tokens.toLocaleString()} / ↑{usage.completion_tokens.toLocaleString()})
            </div>
            {usage.model && (
                <div className="text-muted-foreground/70 text-[10px] px-1.5 py-0.5 bg-muted/50 rounded">
                    {usage.model}
                </div>
            )}
        </div>
    )
}

// Format log level icon
function LogLevelIcon({ level }: { level: string }) {
    switch (level) {
        case 'error':
            return <AlertTriangle className="w-3 h-3 text-red-500" />
        case 'warning':
            return <AlertCircle className="w-3 h-3 text-yellow-500" />
        case 'info':
            return <Info className="w-3 h-3 text-blue-500" />
        default:
            return <Circle className="w-2 h-2 text-muted-foreground" />
    }
}

export default function PipelineLog({ run, className }: PipelineLogProps) {
    const [expanded, setExpanded] = useState(true)
    const [showDetailedLogs, setShowDetailedLogs] = useState(false)

    const isActive = run.status === 'RUNNING' || run.status === 'QUEUED'
    const isFailed = run.status === 'FAILED'
    const isCompleted = run.status === 'COMPLETED'

    // Calculate duration
    const startTime = run.started_at ? new Date(run.started_at) : null
    const endTime = run.completed_at ? new Date(run.completed_at) : null
    const duration = startTime && endTime
        ? Math.round((endTime.getTime() - startTime.getTime()) / 1000)
        : null

    // Get total token usage
    const totalTokens = useMemo(() => {
        if (!run.token_usage) return 0
        return Object.values(run.token_usage).reduce((sum, u) => sum + (u.total_tokens || 0), 0)
    }, [run.token_usage])

    // Get token usage for a step
    const getStepTokens = (stepId: string): TokenUsageEntry | null => {
        if (!run.token_usage) return null
        return run.token_usage[stepId] || null
    }

    return (
        <div className={cn('rounded-xl border border-[#ECE8E1] bg-white overflow-hidden', className)}>
            {/* Header */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full px-4 py-3 flex items-center justify-between bg-[#FAF9F7] hover:bg-[#F3F0EB] transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className={cn(
                        'w-[6px] h-[6px] rounded-full',
                        isActive && 'bg-blue-500 animate-pulse',
                        isCompleted && 'bg-green-500',
                        isFailed && 'bg-red-500'
                    )} />
                    <span className="font-medium text-sm">Pipeline Log</span>
                    {duration && (
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {duration}s
                        </span>
                    )}
                    {totalTokens > 0 && (
                        <span className="text-xs text-cyan-600 flex items-center gap-1">
                            <Cpu className="w-3 h-3" />
                            {totalTokens.toLocaleString()}
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                        {run.progress_pct}%
                    </span>
                    {expanded ? (
                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                </div>
            </button>

            {/* Steps Timeline */}
            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 space-y-0">
                            {PIPELINE_STEPS.map((step, index) => {
                                const status = getStepStatus(step.id, run.current_step, run.status)
                                const isLast = index === PIPELINE_STEPS.length - 1

                                return (
                                    <div key={step.id} className="relative">
                                        {/* Connector line */}
                                        {!isLast && <TimelineConnector status={status} />}

                                        {/* Step content */}
                                        <div className="flex gap-4 pb-4">
                                            <StepIcon status={status} icon={step.icon} />
                                            <div className="flex-1 pt-1">
                                                <div className="flex items-center gap-2">
                                                    <span className={cn(
                                                        'font-medium text-sm',
                                                        status === 'completed' && 'text-foreground',
                                                        status === 'current' && 'text-primary',
                                                        status === 'failed' && 'text-red-500',
                                                        status === 'pending' && 'text-muted-foreground'
                                                    )}>
                                                        {step.label}
                                                    </span>
                                                    {status === 'current' && (
                                                        <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">
                                                            In Progress
                                                        </span>
                                                    )}
                                                    {status === 'completed' && step.id !== 'DONE' && (
                                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                                                    )}
                                                </div>
                                                <p className={cn(
                                                    'text-xs mt-0.5',
                                                    status === 'pending' ? 'text-muted-foreground/50' : 'text-muted-foreground'
                                                )}>
                                                    {step.description}
                                                </p>

                                                {/* Show token usage for LLM steps */}
                                                {(status === 'completed' || status === 'current') && LLM_STEPS.includes(step.id) && (() => {
                                                    const tokens = getStepTokens(step.id)
                                                    if (tokens && tokens.total_tokens > 0) {
                                                        return (
                                                            <motion.div
                                                                initial={{ opacity: 0 }}
                                                                animate={{ opacity: 1 }}
                                                                className="mt-1"
                                                            >
                                                                <TokenUsageDisplay usage={tokens} />
                                                            </motion.div>
                                                        )
                                                    }
                                                    return null
                                                })()}

                                                {/* Show extra info for current step */}
                                                {status === 'current' && (
                                                    <motion.div
                                                        initial={{ opacity: 0, y: -5 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        className="mt-2 p-2 rounded-lg bg-primary/5 border border-primary/10"
                                                    >
                                                        <div className="flex items-center gap-4 text-xs">
                                                            <div>
                                                                <span className="text-muted-foreground">Vendors: </span>
                                                                <span className="font-medium">{run.vendors_found}</span>
                                                            </div>
                                                            <div>
                                                                <span className="text-muted-foreground">Sources: </span>
                                                                <span className="font-medium">{run.sources_searched}</span>
                                                            </div>
                                                        </div>
                                                    </motion.div>
                                                )}

                                                {/* Show error for failed step */}
                                                {status === 'failed' && run.error_message && (
                                                    <motion.div
                                                        initial={{ opacity: 0, y: -5 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        className="mt-2 p-2 rounded-lg bg-red-500/5 border border-red-500/20"
                                                    >
                                                        <div className="flex items-start gap-2 text-xs text-red-600">
                                                            <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                                                            <span className="line-clamp-3">{run.error_message}</span>
                                                        </div>
                                                    </motion.div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>

                        {/* Footer stats */}
                        {isCompleted && (
                            <div className="px-4 pb-4">
                                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                                    <div className="flex items-center gap-2 text-sm text-emerald-700">
                                        <CheckCircle2 className="w-4 h-4" />
                                        <span className="font-medium">
                                            Pipeline completed successfully
                                        </span>
                                    </div>
                                    <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                                        <div>
                                            <span>Vendors found: </span>
                                            <span className="font-medium text-foreground">{run.vendors_found}</span>
                                        </div>
                                        <div>
                                            <span>Sources searched: </span>
                                            <span className="font-medium text-foreground">{run.sources_searched}</span>
                                        </div>
                                        {duration && (
                                            <div>
                                                <span>Duration: </span>
                                                <span className="font-medium text-foreground">{duration}s</span>
                                            </div>
                                        )}
                                        {totalTokens > 0 && (
                                            <div className="flex items-center gap-1 text-cyan-600">
                                                <Cpu className="w-3 h-3" />
                                                <span className="font-medium">{totalTokens.toLocaleString()}</span>
                                                <span className="text-muted-foreground">total tokens</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Detailed Logs Section */}
                        {run.pipeline_logs && run.pipeline_logs.length > 0 && (
                            <div className="px-4 pb-4">
                                <button
                                    onClick={() => setShowDetailedLogs(!showDetailedLogs)}
                                    className="w-full flex items-center justify-between p-2 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors text-sm"
                                >
                                    <span className="text-muted-foreground flex items-center gap-2">
                                        <FileText className="w-4 h-4" />
                                        Detailed Logs ({run.pipeline_logs.length} entries)
                                    </span>
                                    {showDetailedLogs ? (
                                        <ChevronUp className="w-4 h-4 text-muted-foreground" />
                                    ) : (
                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                    )}
                                </button>

                                <AnimatePresence>
                                    {showDetailedLogs && (
                                        <motion.div
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: 'auto', opacity: 1 }}
                                            exit={{ height: 0, opacity: 0 }}
                                            transition={{ duration: 0.2 }}
                                            className="overflow-hidden"
                                        >
                                            <div className="mt-2 max-h-64 overflow-y-auto rounded-lg border bg-muted/20">
                                                <div className="divide-y divide-border/50">
                                                    {run.pipeline_logs.map((log, idx) => (
                                                        <div
                                                            key={idx}
                                                            className={cn(
                                                                'px-3 py-2 text-xs font-mono',
                                                                log.level === 'error' && 'bg-red-500/5',
                                                                log.level === 'warning' && 'bg-yellow-500/5'
                                                            )}
                                                        >
                                                            <div className="flex items-start gap-2">
                                                                <LogLevelIcon level={log.level} />
                                                                <span className="text-muted-foreground/70 flex-shrink-0 w-20">
                                                                    [{log.step}]
                                                                </span>
                                                                <span className={cn(
                                                                    log.level === 'error' && 'text-red-600',
                                                                    log.level === 'warning' && 'text-yellow-600'
                                                                )}>
                                                                    {log.message}
                                                                </span>
                                                            </div>
                                                            {log.data && Object.keys(log.data).length > 0 && (
                                                                <div className="mt-1 ml-6 pl-2 border-l border-muted-foreground/20 text-muted-foreground/70">
                                                                    {Object.entries(log.data).map(([key, value]) => (
                                                                        <div key={key}>
                                                                            <span className="text-muted-foreground">{key}: </span>
                                                                            <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}
