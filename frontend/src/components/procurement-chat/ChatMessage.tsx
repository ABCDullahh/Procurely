/**
 * ChatMessage - Renders chat messages with rich content
 */

import { motion } from 'framer-motion'
import { User, MessageSquare, ExternalLink, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { VendorMiniList } from './VendorCard'
import { ComparisonTable, CompactComparisonTable } from './ComparisonTable'
import { SearchProgress, CompactSearchProgress } from './SearchProgress'
import { FilterChips, SuggestedQueries } from './FilterChips'
import {
    InsightsCard,
    QuickStatsCard,
    VendorHighlightGrid,
    CategoryBreakdownCard,
    PricingOverviewCard,
} from './cards'
import { LiveSearchProgress } from './LiveSearchProgress'
import type {
    ChatMessage as ChatMessageType,
    ProcurementChatResponse,
    FilterChip,
    ChatAction,
} from '@/lib/procurement-chat-api'

interface ChatMessageProps {
    message: ChatMessageType
    onVendorClick?: (vendorId: number) => void
    onFilterClick?: (chip: FilterChip) => void
    onSuggestedQueryClick?: (text: string) => void
    onActionClick?: (action: ChatAction) => void
    isCompact?: boolean
}

// Simple markdown-like formatting
function formatText(text: string): React.ReactNode {
    if (!text) return null

    const lines = text.split('\n')
    const elements: React.ReactNode[] = []
    let listItems: string[] = []

    const processInlineFormatting = (line: string): React.ReactNode => {
        // Bold
        const parts = line.split(/(\*\*[^*]+\*\*)/g)
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i}>{part.slice(2, -2)}</strong>
            }
            return part
        })
    }

    const flushList = () => {
        if (listItems.length > 0) {
            elements.push(
                <ul key={`list-${elements.length}`} className="list-disc list-inside space-y-1 my-2">
                    {listItems.map((item, i) => (
                        <li key={i}>{processInlineFormatting(item)}</li>
                    ))}
                </ul>
            )
            listItems = []
        }
    }

    lines.forEach((line, i) => {
        // Headers
        if (line.startsWith('## ')) {
            flushList()
            elements.push(
                <h2 key={i} className="text-lg font-semibold mt-4 mb-2">
                    {processInlineFormatting(line.slice(3))}
                </h2>
            )
            return
        }

        if (line.startsWith('### ')) {
            flushList()
            elements.push(
                <h3 key={i} className="text-base font-medium mt-3 mb-1">
                    {processInlineFormatting(line.slice(4))}
                </h3>
            )
            return
        }

        // List items
        if (line.match(/^[-•*]\s/)) {
            listItems.push(line.slice(2))
            return
        }

        // Numbered lists
        if (line.match(/^\d+\.\s/)) {
            flushList()
            elements.push(
                <div key={i} className="my-1">
                    {processInlineFormatting(line)}
                </div>
            )
            return
        }

        // Empty line
        if (line.trim() === '') {
            flushList()
            elements.push(<br key={i} />)
            return
        }

        // Regular paragraph
        flushList()
        elements.push(
            <p key={i} className="my-1">
                {processInlineFormatting(line)}
            </p>
        )
    })

    flushList()

    return <div className="space-y-0">{elements}</div>
}

function ActionButtons({
    actions,
    onActionClick,
}: {
    actions: ChatAction[]
    onActionClick?: (action: ChatAction) => void
}) {
    if (actions.length === 0) return null

    const getVariantClass = (variant: string) => {
        switch (variant) {
            case 'primary':
                return 'bg-primary text-primary-foreground hover:bg-primary/90'
            case 'outline':
                return 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
            case 'ghost':
                return 'hover:bg-accent hover:text-accent-foreground'
            default:
                return 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-wrap gap-2 mt-3"
        >
            {actions.map((action, i) => (
                <Button
                    key={i}
                    size="sm"
                    className={cn('gap-1.5', getVariantClass(action.variant))}
                    onClick={() => onActionClick?.(action)}
                >
                    {action.label}
                </Button>
            ))}
        </motion.div>
    )
}

function EvidenceList({
    evidence,
}: {
    evidence: NonNullable<ProcurementChatResponse['evidence']>
}) {
    return (
        <div className="space-y-3 mt-3">
            {evidence.map((item, i) => (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="rounded-lg border bg-card p-3"
                >
                    <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                            <span className="font-medium text-sm">{item.vendor_name}</span>
                            <span className="mx-2 text-muted-foreground">·</span>
                            <span className="text-sm text-muted-foreground capitalize">
                                {item.field.replace(/_/g, ' ')}
                            </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs">
                            <div
                                className={cn(
                                    'w-2 h-2 rounded-full',
                                    item.confidence >= 0.9
                                        ? 'bg-green-500'
                                        : item.confidence >= 0.7
                                        ? 'bg-yellow-500'
                                        : 'bg-orange-500'
                                )}
                            />
                            <span className="text-muted-foreground">
                                {Math.round(item.confidence * 100)}%
                            </span>
                        </div>
                    </div>
                    <p className="text-sm font-medium mb-1">{item.value}</p>
                    {item.snippet && (
                        <p className="text-xs text-muted-foreground italic border-l-2 border-muted pl-2">
                            "{item.snippet}"
                        </p>
                    )}
                    {item.source_url && (
                        <a
                            href={item.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-primary hover:underline mt-2"
                        >
                            <ExternalLink className="w-3 h-3" />
                            Source
                        </a>
                    )}
                </motion.div>
            ))}
        </div>
    )
}

export function ChatMessage({
    message,
    onVendorClick,
    onFilterClick,
    onSuggestedQueryClick,
    onActionClick,
    isCompact = false,
}: ChatMessageProps) {
    const [copied, setCopied] = useState(false)
    const isUser = message.role === 'user'
    const data = message.data

    const handleCopy = async () => {
        await navigator.clipboard.writeText(message.content)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                'flex gap-3',
                isUser ? 'flex-row-reverse' : 'flex-row'
            )}
        >
            {/* Avatar */}
            <div
                className={cn(
                    'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
                    isUser
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-primary/10 text-primary'
                )}
            >
                {isUser ? (
                    <User className="w-4 h-4" />
                ) : (
                    <MessageSquare className="w-4 h-4" />
                )}
            </div>

            {/* Message Content */}
            <div
                className={cn(
                    'flex-1 max-w-[85%]',
                    isUser && 'flex flex-col items-end'
                )}
            >
                {/* Bubble */}
                <div
                    className={cn(
                        'rounded-2xl px-4 py-3',
                        isUser
                            ? 'bg-primary text-primary-foreground rounded-tr-sm'
                            : 'bg-muted rounded-tl-sm'
                    )}
                >
                    {/* Text content */}
                    <div className={cn('text-sm', isUser && 'text-right')}>
                        {formatText(message.content)}
                    </div>

                    {/* Copy button for assistant */}
                    {!isUser && (
                        <button
                            onClick={handleCopy}
                            className="mt-2 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
                        >
                            {copied ? (
                                <>
                                    <Check className="w-3 h-3" /> Copied
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3 h-3" /> Copy
                                </>
                            )}
                        </button>
                    )}
                </div>

                {/* Rich content for assistant messages */}
                {!isUser && data && (
                    <div className="mt-3 w-full space-y-4">
                        {/* Quick Stats - Show first if available */}
                        {data.quick_stats && data.quick_stats.length > 0 && (
                            <QuickStatsCard
                                stats={data.quick_stats}
                                columns={data.quick_stats.length <= 4 ? data.quick_stats.length as 2 | 3 | 4 : 4}
                            />
                        )}

                        {/* Insights - Key recommendations */}
                        {data.insights && data.insights.length > 0 && (
                            <InsightsCard
                                insights={data.insights}
                                onActionClick={onSuggestedQueryClick}
                            />
                        )}

                        {/* Vendors - Use enhanced cards for better display */}
                        {data.response_type === 'vendors' && data.vendors && (
                            isCompact ? (
                                <VendorMiniList
                                    vendors={data.vendors}
                                    onViewClick={onVendorClick}
                                />
                            ) : (
                                <VendorHighlightGrid
                                    vendors={data.vendors.slice(0, 4)}
                                    onViewClick={onVendorClick}
                                />
                            )
                        )}

                        {/* Comparison */}
                        {data.response_type === 'comparison' && data.comparison && (
                            isCompact ? (
                                <CompactComparisonTable
                                    data={data.comparison}
                                    onVendorClick={onVendorClick}
                                />
                            ) : (
                                <ComparisonTable
                                    data={data.comparison}
                                    onVendorClick={onVendorClick}
                                />
                            )
                        )}

                        {/* Progress */}
                        {data.response_type === 'progress' && data.progress && (
                            isCompact ? (
                                <CompactSearchProgress data={data.progress} />
                            ) : (
                                <SearchProgress data={data.progress} />
                            )
                        )}

                        {/* DeepResearch in progress */}
                        {data.response_type === 'deep_research' && data.progress && (
                            <LiveSearchProgress
                                progress={data.progress}
                                vendors={data.vendors}
                                onCancel={
                                    data.actions?.find((a) => a.type === 'CANCEL_RESEARCH')
                                        ? () => {
                                              const cancelAction = data.actions?.find(
                                                  (a) => a.type === 'CANCEL_RESEARCH'
                                              )
                                              if (cancelAction) {
                                                  onActionClick?.(cancelAction)
                                              }
                                          }
                                        : undefined
                                }
                            />
                        )}

                        {/* Evidence */}
                        {data.response_type === 'evidence' && data.evidence && (
                            <EvidenceList evidence={data.evidence} />
                        )}

                        {/* Category Breakdown */}
                        {data.categories && data.categories.length > 0 && (
                            <CategoryBreakdownCard
                                categories={data.categories}
                                onCategoryClick={onSuggestedQueryClick}
                            />
                        )}

                        {/* Pricing Overview */}
                        {data.pricing_overview && data.pricing_overview.length > 0 && (
                            <PricingOverviewCard
                                pricingData={data.pricing_overview}
                                onVendorClick={onVendorClick}
                            />
                        )}

                        {/* Filter chips */}
                        {data.filter_chips && data.filter_chips.length > 0 && (
                            <div className="mt-4">
                                <FilterChips
                                    chips={data.filter_chips}
                                    onChipClick={(chip) => onFilterClick?.(chip)}
                                />
                            </div>
                        )}

                        {/* Suggested queries */}
                        {data.suggested_queries && data.suggested_queries.length > 0 && (
                            <div className="mt-4">
                                <SuggestedQueries
                                    queries={data.suggested_queries}
                                    onQueryClick={(text) => onSuggestedQueryClick?.(text)}
                                />
                            </div>
                        )}

                        {/* Actions */}
                        {data.actions && data.actions.length > 0 && (
                            <ActionButtons
                                actions={data.actions}
                                onActionClick={onActionClick}
                            />
                        )}
                    </div>
                )}

                {/* Timestamp */}
                <div className={cn(
                    'text-[10px] text-muted-foreground mt-1',
                    isUser && 'text-right'
                )}>
                    {new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                    })}
                </div>
            </div>
        </motion.div>
    )
}

export function TypingIndicator() {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
        >
            <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                <MessageSquare className="w-4 h-4" />
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
                <div className="flex gap-1.5">
                    {[0, 1, 2].map((i) => (
                        <motion.div
                            key={i}
                            className="w-2 h-2 rounded-full bg-muted-foreground/50"
                            animate={{ y: [0, -6, 0] }}
                            transition={{
                                duration: 0.6,
                                repeat: Infinity,
                                delay: i * 0.15,
                            }}
                        />
                    ))}
                </div>
            </div>
        </motion.div>
    )
}
