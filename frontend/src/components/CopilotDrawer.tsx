/**
 * CopilotDrawer - AI-powered assistant drawer with Ask/Insights/Actions tabs
 * Now supports multiple chat sessions with session picker
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
    Send,
    Loader2,
    ExternalLink,
    Lightbulb,
    Zap,
    FileText,
    Users,
    Scale,
    ListChecks,
    Trash2,
    Plus,
    ChevronDown,
    MessageSquare,
    Check,
    HelpCircle,
} from 'lucide-react'

import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

import { useCopilot } from '@/hooks/useCopilot'
import { analyticsApi, AnalyticsData } from '@/lib/analytics-api'
import { shortlistsApi } from '@/lib/shortlists-api'
import { CopilotAction, Citation } from '@/lib/copilot-api'

interface CopilotDrawerProps {
    open: boolean
    onClose: () => void
    runId: number
    requestId: number
    runStatus: string
}

export default function CopilotDrawer({
    open,
    onClose,
    runId,
    requestId,
    runStatus,
}: CopilotDrawerProps) {
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const [inputValue, setInputValue] = useState('')
    const [sessionDropdownOpen, setSessionDropdownOpen] = useState(false)

    const {
        messages,
        isLoading,
        latestCitations,
        latestActions,
        sendMessage,
        clearMessages,
        isNearBottom,
        scrollToBottom,
        messagesContainerRef,
        sessions,
        activeSessionId,
        createSession,
        switchSession,
        deleteSession,
    } = useCopilot({ runId, requestId })

    const [showClearConfirm, setShowClearConfirm] = useState(false)
    const activeSession = sessions.find(s => s.id === activeSessionId)

    const handleClearChat = () => {
        clearMessages()
        setShowClearConfirm(false)
        toast.success('Chat cleared')
    }

    const handleNewChat = () => {
        createSession()
        setSessionDropdownOpen(false)
        toast.success('New chat started')
    }

    const handleSwitchSession = (sessionId: string) => {
        switchSession(sessionId)
        setSessionDropdownOpen(false)
    }

    const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        deleteSession(sessionId)
        toast.success('Chat deleted')
    }

    const isCompleted = runStatus === 'COMPLETED'

    // Fetch analytics for Insights tab
    const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
        queryKey: ['run-analytics', runId],
        queryFn: () => analyticsApi.getRunAnalytics(runId),
        enabled: open && isCompleted,
    })

    // Export report mutation
    const exportMutation = useMutation({
        mutationFn: () => analyticsApi.exportRunReport(runId),
        onSuccess: () => {
            toast.success('Report generated!')
            queryClient.invalidateQueries({ queryKey: ['reports'] })
        },
        onError: () => {
            toast.error('Failed to generate report')
        },
    })

    // Create shortlist mutation
    const createShortlistMutation = useMutation({
        mutationFn: async (vendorIds: number[]) => {
            const shortlist = await shortlistsApi.create({
                name: `Copilot Shortlist ${new Date().toLocaleDateString()}`,
            })
            for (const vendorId of vendorIds) {
                await shortlistsApi.addVendor(shortlist.id, vendorId)
            }
            return shortlist
        },
        onSuccess: (shortlist) => {
            toast.success('Shortlist created!')
            navigate(`/shortlists/${shortlist.id}`)
        },
        onError: () => {
            toast.error('Failed to create shortlist')
        },
    })

    const handleSend = () => {
        if (!inputValue.trim() || isLoading) return
        sendMessage(inputValue.trim())
        setInputValue('')
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    const handleGenerateInsights = () => {
        sendMessage('Summarize the top vendors and key tradeoffs.', 'insights')
    }

    const handleAction = (action: CopilotAction) => {
        switch (action.type) {
            case 'OPEN_VENDOR':
                if (action.payload.vendor_id) {
                    navigate(`/vendors/${action.payload.vendor_id}`)
                    onClose()
                }
                break
            case 'OPEN_REPORTS':
                navigate('/reports')
                onClose()
                break
            case 'EXPORT_REPORT':
                exportMutation.mutate()
                break
            case 'CREATE_SHORTLIST':
                if (action.payload.vendor_ids) {
                    const ids = action.payload.vendor_ids as number[]
                    createShortlistMutation.mutate(ids)
                } else if (analyticsData?.top_vendors) {
                    const topIds = analyticsData.top_vendors.slice(0, 5).map((v) => v.id)
                    createShortlistMutation.mutate(topIds)
                }
                break
            case 'COMPARE_TOP':
                if (analyticsData?.top_vendors) {
                    const topIds = analyticsData.top_vendors.slice(0, 5).map((v) => v.id)
                    createShortlistMutation.mutate(topIds)
                }
                break
        }
    }

    return (
        <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
            <SheetContent className="w-[400px] sm:w-[540px] flex flex-col p-0 h-full">
                <SheetHeader className="px-6 py-4 border-b shrink-0">
                    <SheetTitle className="flex items-center gap-2">
                        <HelpCircle className="h-5 w-5 text-primary" />
                        Procurement Copilot
                    </SheetTitle>
                </SheetHeader>

                <Tabs defaultValue="ask" className="flex-1 flex flex-col min-h-0">
                    <TabsList className="mx-6 mt-2 shrink-0">
                        <TabsTrigger value="ask" className="flex-1">
                            <Send className="h-4 w-4 mr-2" />
                            Ask
                        </TabsTrigger>
                        <TabsTrigger value="insights" className="flex-1">
                            <Lightbulb className="h-4 w-4 mr-2" />
                            Insights
                        </TabsTrigger>
                        <TabsTrigger value="actions" className="flex-1">
                            <Zap className="h-4 w-4 mr-2" />
                            Actions
                        </TabsTrigger>
                    </TabsList>

                    {/* Ask Tab */}
                    <TabsContent value="ask" className="flex-1 flex flex-col m-0 min-h-0">
                        {/* Session Selector */}
                        <div className="px-4 py-2 border-b flex items-center justify-between shrink-0 bg-muted/30">
                            <div className="relative">
                                <button
                                    onClick={() => setSessionDropdownOpen(!sessionDropdownOpen)}
                                    className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                                >
                                    <MessageSquare className="h-4 w-4" />
                                    <span className="max-w-[180px] truncate">
                                        {activeSession?.name || 'Chat'}
                                    </span>
                                    <ChevronDown className="h-3 w-3" />
                                </button>

                                {sessionDropdownOpen && (
                                    <>
                                        <div
                                            className="fixed inset-0 z-40"
                                            onClick={() => setSessionDropdownOpen(false)}
                                        />
                                        <div className="absolute left-0 top-8 z-50 w-64 bg-popover border rounded-lg shadow-lg py-1">
                                            <div className="max-h-48 overflow-y-auto">
                                                {sessions.map((session) => (
                                                    <div
                                                        key={session.id}
                                                        onClick={() => handleSwitchSession(session.id)}
                                                        className="flex items-center justify-between px-3 py-2 hover:bg-muted cursor-pointer group"
                                                    >
                                                        <div className="flex items-center gap-2 min-w-0">
                                                            {session.id === activeSessionId && (
                                                                <Check className="h-3 w-3 text-primary shrink-0" />
                                                            )}
                                                            <span className="text-sm truncate">
                                                                {session.name}
                                                            </span>
                                                        </div>
                                                        {sessions.length > 1 && (
                                                            <button
                                                                onClick={(e) => handleDeleteSession(session.id, e)}
                                                                className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                                                            >
                                                                <Trash2 className="h-3 w-3" />
                                                            </button>
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="border-t mt-1 pt-1">
                                                <button
                                                    onClick={handleNewChat}
                                                    className="flex items-center gap-2 px-3 py-2 w-full text-sm text-primary hover:bg-muted"
                                                >
                                                    <Plus className="h-4 w-4" />
                                                    New Chat
                                                </button>
                                            </div>
                                        </div>
                                    </>
                                )}
                            </div>
                            <Button
                                size="sm"
                                variant="ghost"
                                onClick={handleNewChat}
                                className="h-7 px-2"
                            >
                                <Plus className="h-4 w-4" />
                            </Button>
                        </div>

                        {/* Messages Container - scrollable area */}
                        <div
                            ref={messagesContainerRef}
                            className="flex-1 overflow-y-auto px-6 py-4 min-h-0"
                        >
                            <div className="space-y-4">
                                {messages.length === 0 ? (
                                    <div className="text-center text-muted-foreground py-8">
                                        <HelpCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>Ask me anything about your vendor search!</p>
                                        <p className="text-sm mt-2">
                                            Try: "Who is the best fit?" or "Compare top 3"
                                        </p>
                                    </div>
                                ) : (
                                    messages.map((msg) => (
                                        <MessageBubble
                                            key={msg.id}
                                            message={msg}
                                            citations={msg.citations}
                                        />
                                    ))
                                )}
                                {isLoading && (
                                    <div className="flex gap-2 items-center text-muted-foreground">
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        <span className="text-sm">Thinking...</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Jump to Latest */}
                        {!isNearBottom && messages.length > 0 && (
                            <button
                                onClick={scrollToBottom}
                                className="absolute bottom-24 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-xs px-3 py-1.5 rounded-full shadow-lg hover:bg-primary/90 transition-all z-10"
                            >
                                ↓ Jump to latest
                            </button>
                        )}

                        {/* Input Area - fixed at bottom */}
                        <div className="p-4 border-t space-y-2 shrink-0 bg-background">
                            <div className="flex gap-2">
                                <Input
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Ask about vendors..."
                                    disabled={isLoading}
                                />
                                <Button
                                    onClick={handleSend}
                                    disabled={!inputValue.trim() || isLoading}
                                    size="icon"
                                >
                                    <Send className="h-4 w-4" />
                                </Button>
                            </div>
                            {messages.length > 0 && (
                                <div className="flex justify-end">
                                    {showClearConfirm ? (
                                        <div className="flex items-center gap-2 text-sm">
                                            <span className="text-muted-foreground">Clear?</span>
                                            <Button size="sm" variant="destructive" onClick={handleClearChat}>
                                                Yes
                                            </Button>
                                            <Button size="sm" variant="outline" onClick={() => setShowClearConfirm(false)}>
                                                No
                                            </Button>
                                        </div>
                                    ) : (
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            className="text-muted-foreground hover:text-destructive"
                                            onClick={() => setShowClearConfirm(true)}
                                        >
                                            <Trash2 className="h-3 w-3 mr-1" />
                                            Clear
                                        </Button>
                                    )}
                                </div>
                            )}
                        </div>
                    </TabsContent>

                    {/* Insights Tab */}
                    <TabsContent value="insights" className="flex-1 m-0 min-h-0">
                        <div className="h-full overflow-y-auto px-6 py-4">
                            {!isCompleted ? (
                                <div className="text-center text-muted-foreground py-8">
                                    <Lightbulb className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                    <p>Insights available after search completes</p>
                                </div>
                            ) : analyticsLoading ? (
                                <div className="flex justify-center py-8">
                                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                </div>
                            ) : analyticsData ? (
                                <InsightsPanel
                                    data={analyticsData}
                                    onGenerateAI={handleGenerateInsights}
                                    isGenerating={isLoading}
                                />
                            ) : null}
                        </div>
                    </TabsContent>

                    {/* Actions Tab */}
                    <TabsContent value="actions" className="flex-1 m-0 min-h-0">
                        <div className="h-full overflow-y-auto px-6 py-4">
                            <div className="space-y-4">
                                {latestActions.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="font-medium text-sm">Suggested Actions</h4>
                                        {latestActions.map((action, idx) => (
                                            <ActionButton
                                                key={idx}
                                                action={action}
                                                onClick={() => handleAction(action)}
                                            />
                                        ))}
                                    </div>
                                )}

                                <div className="space-y-2">
                                    <h4 className="font-medium text-sm">Quick Actions</h4>
                                    <ActionButton
                                        action={{
                                            type: 'EXPORT_REPORT',
                                            label: 'Generate Report',
                                            payload: {},
                                        }}
                                        onClick={() => handleAction({ type: 'EXPORT_REPORT', label: '', payload: {} })}
                                        loading={exportMutation.isPending}
                                    />
                                    <ActionButton
                                        action={{
                                            type: 'OPEN_REPORTS',
                                            label: 'View All Reports',
                                            payload: {},
                                        }}
                                        onClick={() => handleAction({ type: 'OPEN_REPORTS', label: '', payload: {} })}
                                    />
                                    {analyticsData && (
                                        <ActionButton
                                            action={{
                                                type: 'CREATE_SHORTLIST',
                                                label: 'Create Shortlist from Top 5',
                                                payload: {},
                                            }}
                                            onClick={() => handleAction({ type: 'CREATE_SHORTLIST', label: '', payload: {} })}
                                            loading={createShortlistMutation.isPending}
                                        />
                                    )}
                                </div>

                                {latestCitations.length > 0 && (
                                    <div className="space-y-2">
                                        <h4 className="font-medium text-sm">Recent Citations</h4>
                                        {latestCitations.map((citation, idx) => (
                                            <CitationCard key={idx} citation={citation} />
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </TabsContent>
                </Tabs>
            </SheetContent>
        </Sheet>
    )
}

// Helper Components

interface MessageBubbleProps {
    message: { role: string; content: string }
    citations?: Citation[]
}

function MessageBubble({ message, citations }: MessageBubbleProps) {
    const isUser = message.role === 'user'

    const renderContent = (content: string) => {
        if (isUser) return <span>{content}</span>

        const lines = content.split('\n')
        return (
            <div className="space-y-2">
                {lines.map((line, idx) => {
                    if (!line.trim()) return <div key={idx} className="h-2" />
                    if (line.startsWith('### ')) {
                        return <h4 key={idx} className="font-semibold text-sm mt-2">{line.slice(4)}</h4>
                    }
                    if (line.startsWith('## ')) {
                        return <h3 key={idx} className="font-bold text-sm mt-2">{line.slice(3)}</h3>
                    }
                    if (line.startsWith('- ') || line.startsWith('• ') || line.startsWith('* ')) {
                        return (
                            <div key={idx} className="flex gap-2 pl-2">
                                <span className="text-primary">•</span>
                                <span>{formatInlineMarkdown(line.slice(2))}</span>
                            </div>
                        )
                    }
                    const numberedMatch = line.match(/^(\d+)\.\s+(.+)/)
                    if (numberedMatch) {
                        return (
                            <div key={idx} className="flex gap-2 pl-2">
                                <span className="text-primary font-medium">{numberedMatch[1]}.</span>
                                <span>{formatInlineMarkdown(numberedMatch[2])}</span>
                            </div>
                        )
                    }
                    return <p key={idx}>{formatInlineMarkdown(line)}</p>
                })}
            </div>
        )
    }

    const formatInlineMarkdown = (text: string): React.ReactNode => {
        const parts = text.split(/(\*\*[^*]+\*\*)/g)
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i}>{part.slice(2, -2)}</strong>
            }
            return <span key={i}>{part}</span>
        })
    }

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-lg px-4 py-2 ${isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                <div className="text-sm">{renderContent(message.content)}</div>
                {citations && citations.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/20 space-y-1">
                        <p className="text-xs font-medium opacity-80">Sources:</p>
                        {citations.slice(0, 3).map((c, i) => (
                            <a
                                key={i}
                                href={c.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1 text-xs opacity-80 hover:opacity-100"
                            >
                                <ExternalLink className="h-3 w-3" />
                                {c.vendor_name || 'Source'}
                            </a>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

interface InsightsPanelProps {
    data: AnalyticsData
    onGenerateAI: () => void
    isGenerating: boolean
}

function InsightsPanel({ data, onGenerateAI, isGenerating }: InsightsPanelProps) {
    const { totals, distributions, top_vendors } = data

    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
                <Card>
                    <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                            <Users className="h-4 w-4 text-primary" />
                            <div>
                                <p className="text-lg font-bold">{totals.vendors_count}</p>
                                <p className="text-xs text-muted-foreground">Vendors</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-3">
                        <div className="flex items-center gap-2">
                            <Scale className="h-4 w-4 text-primary" />
                            <div>
                                <p className="text-lg font-bold">
                                    {distributions.average_scores.avg_overall?.toFixed(0) || 'N/A'}
                                </p>
                                <p className="text-xs text-muted-foreground">Avg Score</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {distributions.vendors_by_location.length > 0 && (
                <div>
                    <p className="text-sm font-medium mb-1">Top Location</p>
                    <p className="text-sm text-muted-foreground">
                        {distributions.vendors_by_location[0].location} ({distributions.vendors_by_location[0].count})
                    </p>
                </div>
            )}

            {top_vendors.length > 0 && (
                <div>
                    <p className="text-sm font-medium mb-2">Top 3 Vendors</p>
                    <div className="space-y-2">
                        {top_vendors.slice(0, 3).map((v, i) => (
                            <div key={v.id} className="flex items-center justify-between p-2 rounded bg-muted/50">
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-bold text-primary">#{i + 1}</span>
                                    <span className="text-sm">{v.name}</span>
                                </div>
                                <span className="text-sm font-medium">{v.overall_score?.toFixed(0)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <Button onClick={onGenerateAI} disabled={isGenerating} className="w-full" variant="outline">
                {isGenerating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <ListChecks className="h-4 w-4 mr-2" />}
                Generate AI Insights
            </Button>
        </div>
    )
}

interface ActionButtonProps {
    action: CopilotAction
    onClick: () => void
    loading?: boolean
}

function ActionButton({ action, onClick, loading }: ActionButtonProps) {
    const icons: Record<string, React.ReactNode> = {
        OPEN_VENDOR: <Users className="h-4 w-4" />,
        COMPARE_TOP: <Scale className="h-4 w-4" />,
        CREATE_SHORTLIST: <Users className="h-4 w-4" />,
        EXPORT_REPORT: <FileText className="h-4 w-4" />,
        OPEN_REPORTS: <FileText className="h-4 w-4" />,
    }

    return (
        <Button variant="outline" className="w-full justify-start" onClick={onClick} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <span className="mr-2">{icons[action.type]}</span>}
            {action.label}
        </Button>
    )
}

function CitationCard({ citation }: { citation: Citation }) {
    return (
        <Card>
            <CardContent className="p-3">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{citation.vendor_name || 'Unknown'}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">{citation.snippet}</p>
                    </div>
                    <a href={citation.source_url} target="_blank" rel="noopener noreferrer" className="flex-shrink-0">
                        <ExternalLink className="h-4 w-4 text-muted-foreground hover:text-primary" />
                    </a>
                </div>
            </CardContent>
        </Card>
    )
}
