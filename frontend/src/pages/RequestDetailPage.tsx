import { useState, useCallback, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
    ArrowLeft,
    Play,
    RefreshCw,
    MapPin,
    DollarSign,
    Clock,
    CheckCircle2,
    XCircle,
    Loader2,
    Tag,
    ListChecks,
    FileText,
    Bot,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { requestsApi, SearchRun } from '@/lib/requests-api'
import { analyticsApi } from '@/lib/analytics-api'
import VendorResultsTable from '@/components/VendorResultsTable'
import VendorQuickView from '@/components/VendorQuickView'
import AnalyticsWidgets from '@/components/AnalyticsWidgets'
import CopilotDrawer from '@/components/CopilotDrawer'
import PipelineLog from '@/components/PipelineLog'
import { useDynamicPolling } from '@/hooks/usePolling'

export default function RequestDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const requestId = parseInt(id || '0', 10)

    const [selectedVendorId, setSelectedVendorId] = useState<number | null>(null)
    const [latestRunId, setLatestRunId] = useState<number | null>(null)
    const [copilotOpen, setCopilotOpen] = useState(false)

    // Fetch request
    const {
        data: request,
        isLoading: requestLoading,
        error: requestError,
    } = useQuery({
        queryKey: ['request', requestId],
        queryFn: () => requestsApi.get(requestId),
        enabled: requestId > 0,
    })

    // Fetch runs for this request
    const { data: runs } = useQuery({
        queryKey: ['request-runs', requestId],
        queryFn: () => requestsApi.listRuns(requestId),
        enabled: requestId > 0,
    })

    // Set latest run ID when runs data changes
    useEffect(() => {
        if (runs && runs.length > 0) {
            setLatestRunId(runs[0].id)
        }
    }, [runs])

    const latestRun = runs?.[0]
    const isRunning = latestRun?.status === 'RUNNING' || latestRun?.status === 'QUEUED'

    // Poll run status when running
    const { data: polledRun } = useDynamicPolling(
        useCallback(() => requestsApi.getRun(latestRunId!), [latestRunId]),
        {
            activeIntervalMs: 2000,
            idleIntervalMs: 30000,
            isActive: isRunning,
            enabled: !!latestRunId,
        }
    )

    const currentRun = polledRun || latestRun
    const isCompleted = currentRun?.status === 'COMPLETED'

    // Fetch analytics when run is completed
    const { data: analyticsData, isLoading: analyticsLoading } = useQuery({
        queryKey: ['run-analytics', currentRun?.id],
        queryFn: () => analyticsApi.getRunAnalytics(currentRun!.id),
        enabled: !!currentRun && isCompleted,
    })

    // Submit mutation
    const submitMutation = useMutation({
        mutationFn: () => requestsApi.submit(requestId),
        onSuccess: () => {
            toast.success('Search started!')
            queryClient.invalidateQueries({ queryKey: ['request-runs', requestId] })
            queryClient.invalidateQueries({ queryKey: ['request', requestId] })
        },
        onError: (error: Error) => {
            toast.error('Failed to start search: ' + error.message)
        },
    })

    // Export report mutation
    const exportMutation = useMutation({
        mutationFn: () => analyticsApi.exportRunReport(currentRun!.id),
        onSuccess: (report) => {
            toast.success('Report generated!')
            queryClient.invalidateQueries({ queryKey: ['reports'] })
            // Navigate to the full-page report view
            navigate(`/reports/${report.id}`)
        },
        onError: (error: Error) => {
            toast.error('Failed to generate report: ' + error.message)
        },
    })

    const handleStartSearch = () => {
        submitMutation.mutate()
    }

    const handleRetry = () => {
        submitMutation.mutate()
    }

    if (requestLoading) {
        return <RequestDetailSkeleton />
    }

    if (requestError || !request) {
        return (
            <div className="p-6">
                <Button variant="ghost" onClick={() => navigate('/requests')}>
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Requests
                </Button>
                <div className="mt-8 text-center text-muted-foreground">
                    Request not found or you don't have access.
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="border-b border-[#ECE8E1] bg-white">
                <div className="container mx-auto px-4 py-6">
                    <div className="flex items-center gap-4 mb-4">
                        <Button variant="ghost" size="sm" className="text-[#6B6560] hover:text-[#1A1816]" asChild>
                            <Link to="/requests">
                                <ArrowLeft className="mr-2 h-4 w-4" /> Back
                            </Link>
                        </Button>
                        <StatusBadge status={currentRun?.status || request.status} />
                        <div className="flex-1" />
                        {currentRun && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setCopilotOpen(true)}
                            >
                                <Bot className="mr-2 h-4 w-4" />
                                Copilot
                            </Button>
                        )}
                    </div>
                    <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">{request.title}</h1>
                    {request.description && (
                        <p className="text-sm text-[#6B6560] mt-2">{request.description}</p>
                    )}
                </div>
            </div>

            <div className="container mx-auto px-4 py-6 space-y-6">
                {/* Request Info Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {request.category && (
                        <InfoCard icon={Tag} label="Category" value={request.category} />
                    )}
                    {request.location && (
                        <InfoCard icon={MapPin} label="Location" value={request.location} />
                    )}
                    {(request.budget_min || request.budget_max) && (
                        <InfoCard
                            icon={DollarSign}
                            label="Budget"
                            value={formatBudget(request.budget_min, request.budget_max)}
                        />
                    )}
                    {request.timeline && (
                        <InfoCard icon={Clock} label="Timeline" value={request.timeline} />
                    )}
                </div>

                {/* Criteria */}
                {(request.must_have_criteria?.length || request.nice_to_have_criteria?.length) && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-[#1A1816]">
                                <ListChecks className="h-4 w-4 text-[#6B6560]" /> Requirements
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {request.must_have_criteria && request.must_have_criteria.length > 0 && (
                                <div>
                                    <h4 className="font-medium text-sm text-muted-foreground mb-2">
                                        Must Have
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {request.must_have_criteria.map((c, i) => (
                                            <Badge key={i} variant="default">
                                                {c}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                            {request.nice_to_have_criteria && request.nice_to_have_criteria.length > 0 && (
                                <div>
                                    <h4 className="font-medium text-sm text-muted-foreground mb-2">
                                        Nice to Have
                                    </h4>
                                    <div className="flex flex-wrap gap-2">
                                        {request.nice_to_have_criteria.map((c, i) => (
                                            <Badge key={i} variant="secondary">
                                                {c}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Run Status / Action */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="text-sm font-semibold text-[#1A1816]">Search Status</CardTitle>
                        {request.status === 'DRAFT' && (
                            <Button
                                onClick={handleStartSearch}
                                disabled={submitMutation.isPending}
                            >
                                {submitMutation.isPending ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    <Play className="mr-2 h-4 w-4" />
                                )}
                                Start Search
                            </Button>
                        )}
                    </CardHeader>
                    <CardContent>
                        {!currentRun ? (
                            <div className="text-center py-8 text-muted-foreground">
                                No search has been started yet.
                                {request.status === 'DRAFT' && (
                                    <p className="mt-2">Click "Start Search" to begin finding vendors.</p>
                                )}
                            </div>
                        ) : (
                            <RunStatusCard run={currentRun} onRetry={handleRetry} />
                        )}
                    </CardContent>
                </Card>

                {/* Pipeline Log */}
                {currentRun && (
                    <PipelineLog run={currentRun} />
                )}

                {/* Vendor Results */}
                {currentRun && currentRun.status !== 'QUEUED' && (
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm font-semibold text-[#1A1816]">
                                Vendor Results
                                {currentRun.vendors_found > 0 && (
                                    <span className="ml-2 text-muted-foreground font-normal">
                                        ({currentRun.vendors_found} found)
                                    </span>
                                )}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <VendorResultsTable
                                runId={currentRun.id}
                                isRunning={isRunning}
                                onVendorClick={setSelectedVendorId}
                            />
                        </CardContent>
                    </Card>
                )}

                {/* Analytics Section - Only show when completed */}
                {isCompleted && currentRun && (
                    <>
                        <Card>
                            <CardHeader className="flex flex-row items-center justify-between">
                                <CardTitle className="text-sm font-semibold text-[#1A1816]">Analytics</CardTitle>
                                <Button
                                    onClick={() => exportMutation.mutate()}
                                    disabled={exportMutation.isPending}
                                    variant="outline"
                                >
                                    {exportMutation.isPending ? (
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    ) : (
                                        <FileText className="mr-2 h-4 w-4" />
                                    )}
                                    Generate Report
                                </Button>
                            </CardHeader>
                            <CardContent>
                                <AnalyticsWidgets
                                    data={analyticsData}
                                    isLoading={analyticsLoading}
                                />
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>

            {/* Quick View Drawer */}
            <VendorQuickView
                vendorId={selectedVendorId}
                open={!!selectedVendorId}
                onClose={() => setSelectedVendorId(null)}
            />

            {/* Copilot Drawer */}
            {currentRun && (
                <CopilotDrawer
                    open={copilotOpen}
                    onClose={() => setCopilotOpen(false)}
                    runId={currentRun.id}
                    requestId={requestId}
                    runStatus={currentRun.status}
                />
            )}
        </div>
    )
}

function StatusBadge({ status }: { status: string }) {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
        DRAFT: 'outline',
        PENDING: 'secondary',
        RUNNING: 'default',
        COMPLETED: 'default',
        FAILED: 'destructive',
        CANCELLED: 'secondary',
    }
    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>
}

function InfoCard({
    icon: Icon,
    label,
    value,
}: {
    icon: React.ElementType
    label: string
    value: string
}) {
    return (
        <Card>
            <CardContent className="pt-4">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-[#F3F0EB] rounded-lg">
                        <Icon className="h-4 w-4 text-[#6B6560]" />
                    </div>
                    <div>
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-[#A09A93]">{label}</p>
                        <p className="font-medium text-[#1A1816]">{value}</p>
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function RunStatusCard({
    run,
    onRetry,
}: {
    run: SearchRun
    onRetry: () => void
}) {
    const stepLabels: Record<string, string> = {
        INIT: 'Initializing',
        EXPAND: 'Expanding queries',
        SEARCH: 'Searching web',
        FETCH: 'Fetching pages',
        EXTRACT: 'Extracting vendors',
        DEDUP: 'Deduplicating',
        SCORE: 'Scoring vendors',
        LOGO: 'Fetching logos',
        SAVE: 'Saving results',
        DONE: 'Completed',
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {run.status === 'COMPLETED' && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                    {run.status === 'FAILED' && <XCircle className="h-5 w-5 text-red-500" />}
                    {(run.status === 'RUNNING' || run.status === 'QUEUED') && (
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                    )}
                    <div>
                        <p className="font-medium">{run.status}</p>
                        {run.current_step && (
                            <p className="text-sm text-muted-foreground">
                                {stepLabels[run.current_step] || run.current_step}
                            </p>
                        )}
                    </div>
                </div>
                {run.status === 'FAILED' && (
                    <Button variant="outline" size="sm" onClick={onRetry}>
                        <RefreshCw className="mr-2 h-4 w-4" /> Retry
                    </Button>
                )}
            </div>

            {(run.status === 'RUNNING' || run.status === 'QUEUED') && (
                <Progress value={run.progress_pct} className="h-2" />
            )}

            {run.error_message && (
                <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                    {run.error_message}
                </div>
            )}

            <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                    <span className="text-muted-foreground">Vendors found:</span>
                    <span className="ml-2 font-medium">{run.vendors_found}</span>
                </div>
                <div>
                    <span className="text-muted-foreground">Sources searched:</span>
                    <span className="ml-2 font-medium">{run.sources_searched}</span>
                </div>
            </div>
        </div>
    )
}

function RequestDetailSkeleton() {
    return (
        <div className="min-h-screen bg-background">
            <div className="border-b bg-card">
                <div className="container mx-auto px-4 py-6">
                    <Skeleton className="h-8 w-32 mb-4" />
                    <Skeleton className="h-8 w-64" />
                    <Skeleton className="h-4 w-96 mt-2" />
                </div>
            </div>
            <div className="container mx-auto px-4 py-6 space-y-6">
                <div className="grid grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <Skeleton key={i} className="h-20" />
                    ))}
                </div>
                <Skeleton className="h-48" />
                <Skeleton className="h-96" />
            </div>
        </div>
    )
}

function formatBudget(min: number | null, max: number | null): string {
    if (min && max) return `$${min.toLocaleString()} - $${max.toLocaleString()}`
    if (min) return `From $${min.toLocaleString()}`
    if (max) return `Up to $${max.toLocaleString()}`
    return 'Not specified'
}
