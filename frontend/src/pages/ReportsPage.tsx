/**
 * ReportsPage - List and view generated reports
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format } from 'date-fns'
import { FileText, Download, Eye, Loader2, Trash2, ExternalLink } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast'
import { analyticsApi, Report, ReportDetail } from '@/lib/analytics-api'

export default function ReportsPage() {
    const navigate = useNavigate()
    const { addToast } = useToast()
    const queryClient = useQueryClient()
    const [viewingReportId, setViewingReportId] = useState<number | null>(null)
    const [deletingReportId, setDeletingReportId] = useState<number | null>(null)

    // Fetch reports list
    const { data, isLoading, error } = useQuery({
        queryKey: ['reports'],
        queryFn: analyticsApi.listReports,
    })

    // Fetch report detail when viewing
    const { data: reportDetail, isLoading: loadingDetail } = useQuery({
        queryKey: ['report', viewingReportId],
        queryFn: () => analyticsApi.getReport(viewingReportId!),
        enabled: viewingReportId !== null,
    })

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: (reportId: number) => analyticsApi.deleteReport(reportId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reports'] })
            addToast({
                type: 'success',
                title: 'Report deleted',
                message: 'The report has been permanently removed.',
            })
            setDeletingReportId(null)
        },
        onError: (err: Error) => {
            addToast({
                type: 'error',
                title: 'Delete failed',
                message: err.message,
            })
        },
    })

    const handleDownload = (report: ReportDetail) => {
        if (!report.html_content) return

        const blob = new Blob([report.html_content], { type: 'text/html' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report-${report.id}.html`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
    }

    const handleViewFullPage = (reportId: number) => {
        navigate(`/reports/${reportId}`)
    }

    if (isLoading) {
        return <ReportsPageSkeleton />
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center text-destructive">
                    Failed to load reports. Please try again.
                </div>
            </div>
        )
    }

    const reports = data?.reports || []

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">Reports</h1>
                <p className="text-sm text-[#A09A93] mt-1">
                    View and download generated vendor search reports
                </p>
            </div>

            {/* Empty state */}
            {reports.length === 0 ? (
                <Card className="text-center py-16">
                    <CardContent>
                        <FileText className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No reports yet</h3>
                        <p className="text-muted-foreground max-w-sm mx-auto">
                            Reports are generated from completed search runs. Complete a
                            search to generate your first report.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-4">
                    {reports.map((report) => (
                        <ReportCard
                            key={report.id}
                            report={report}
                            onViewPreview={() => setViewingReportId(report.id)}
                            onViewFullPage={() => handleViewFullPage(report.id)}
                            onDelete={() => setDeletingReportId(report.id)}
                        />
                    ))}
                </div>
            )}

            {/* Report Viewer Dialog (Quick Preview) */}
            <Dialog
                open={viewingReportId !== null}
                onOpenChange={(open) => !open && setViewingReportId(null)}
            >
                <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                    <DialogHeader>
                        <DialogTitle className="flex items-center justify-between">
                            <span>Report Preview</span>
                            <div className="flex gap-2">
                                {reportDetail && (
                                    <>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleViewFullPage(reportDetail.id)}
                                        >
                                            <ExternalLink className="h-4 w-4 mr-2" />
                                            Full Page
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDownload(reportDetail)}
                                        >
                                            <Download className="h-4 w-4 mr-2" />
                                            Download
                                        </Button>
                                    </>
                                )}
                            </div>
                        </DialogTitle>
                    </DialogHeader>
                    <div className="flex-1 overflow-auto border rounded-lg bg-white">
                        {loadingDetail ? (
                            <div className="flex items-center justify-center p-8">
                                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            </div>
                        ) : reportDetail?.html_content ? (
                            <iframe
                                srcDoc={reportDetail.html_content}
                                className="w-full h-[600px] border-0"
                                title="Report Preview"
                                sandbox="allow-same-origin"
                            />
                        ) : (
                            <div className="flex items-center justify-center p-8 text-muted-foreground">
                                Report content not available
                            </div>
                        )}
                    </div>
                </DialogContent>
            </Dialog>

            {/* Delete Confirmation Dialog */}
            <Dialog
                open={deletingReportId !== null}
                onOpenChange={(open) => !open && setDeletingReportId(null)}
            >
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Report?</DialogTitle>
                        <DialogDescription>
                            This action cannot be undone. The report will be permanently removed.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setDeletingReportId(null)}>
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={() => deletingReportId && deleteMutation.mutate(deletingReportId)}
                            disabled={deleteMutation.isPending}
                        >
                            {deleteMutation.isPending ? (
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            ) : (
                                <Trash2 className="w-4 h-4 mr-2" />
                            )}
                            Delete
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}

interface ReportCardProps {
    report: Report
    onViewPreview: () => void
    onViewFullPage: () => void
    onDelete: () => void
}

function ReportCard({ report, onViewPreview, onViewFullPage, onDelete }: ReportCardProps) {
    return (
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={onViewFullPage}>
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-primary/10">
                            <FileText className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                            <CardTitle className="text-base">
                                Report #{report.id}
                            </CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Run #{report.run_id} • {report.format}
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-sm text-muted-foreground">
                            {format(new Date(report.created_at), 'MMM d, yyyy h:mm a')}
                        </p>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex gap-2 justify-end" onClick={(e) => e.stopPropagation()}>
                    <Button variant="outline" size="sm" onClick={onViewPreview}>
                        <Eye className="h-4 w-4 mr-2" />
                        Preview
                    </Button>
                    <Button variant="outline" size="sm" onClick={onViewFullPage}>
                        <ExternalLink className="h-4 w-4 mr-2" />
                        View
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={onDelete}
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

function ReportsPageSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-4 w-64 mt-2" />
            </div>
            <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-28" />
                ))}
            </div>
        </div>
    )
}
