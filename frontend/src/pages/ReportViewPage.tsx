/**
 * ReportViewPage - Full-page report viewer
 * Displays report HTML in an isolated iframe with actions
 */

import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Download, Trash2, Loader2, FileText, AlertTriangle } from 'lucide-react'
import { Button, Card, CardContent } from '@/components/ui'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { useToast } from '@/components/ui/toast'
import { analyticsApi, ReportDetail } from '@/lib/analytics-api'

export function ReportViewPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const { addToast } = useToast()
    const queryClient = useQueryClient()
    const [showDeleteDialog, setShowDeleteDialog] = useState(false)

    const reportId = parseInt(id || '0', 10)

    // Fetch report
    const { data: report, isLoading, error } = useQuery<ReportDetail>({
        queryKey: ['report', reportId],
        queryFn: () => analyticsApi.getReport(reportId),
        enabled: reportId > 0,
    })

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: () => analyticsApi.deleteReport(reportId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reports'] })
            addToast({
                type: 'success',
                title: 'Report deleted',
                message: 'The report has been permanently removed.',
            })
            navigate('/reports')
        },
        onError: (err: Error) => {
            addToast({
                type: 'error',
                title: 'Delete failed',
                message: err.message,
            })
        },
    })

    const handleDownload = () => {
        if (!report?.html_content) return
        const blob = new Blob([report.html_content], { type: 'text/html' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report-${reportId}.html`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        addToast({
            type: 'success',
            title: 'Downloaded',
            message: 'Report saved as HTML file.',
        })
    }

    if (isLoading) {
        return (
            <div className="p-6 flex items-center justify-center min-h-[60vh]">
                <div className="text-center space-y-4">
                    <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto" />
                    <p className="text-muted-foreground">Loading report...</p>
                </div>
            </div>
        )
    }

    if (error || !report) {
        return (
            <div className="p-6">
                <Card className="max-w-lg mx-auto">
                    <CardContent className="pt-6 text-center space-y-4">
                        <AlertTriangle className="w-12 h-12 text-destructive mx-auto" />
                        <h2 className="text-xl font-semibold">Report not found</h2>
                        <p className="text-muted-foreground">
                            The report may have been deleted or you don't have access.
                        </p>
                        <Button asChild>
                            <Link to="/reports">← Back to Reports</Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10">
                <div className="flex items-center justify-between p-4">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" asChild>
                            <Link to="/reports">
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                Back
                            </Link>
                        </Button>
                        <div className="flex items-center gap-2">
                            <FileText className="w-5 h-5 text-crimson" />
                            <div>
                                <h1 className="font-semibold">Report #{report.id}</h1>
                                <p className="text-xs text-muted-foreground">
                                    Generated {new Date(report.created_at).toLocaleDateString()} at{' '}
                                    {new Date(report.created_at).toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={handleDownload}>
                            <Download className="w-4 h-4 mr-2" />
                            Download HTML
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setShowDeleteDialog(true)}
                        >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                        </Button>
                    </div>
                </div>
            </div>

            {/* Report content in iframe */}
            <div className="flex-1 p-4 bg-muted/30">
                {report.html_content ? (
                    <iframe
                        srcDoc={report.html_content}
                        className="w-full h-full min-h-[70vh] rounded-lg border bg-white shadow-lg"
                        title={`Report ${report.id}`}
                        sandbox="allow-same-origin"
                    />
                ) : (
                    <Card className="max-w-lg mx-auto mt-12">
                        <CardContent className="pt-6 text-center">
                            <p className="text-muted-foreground">No content available for this report.</p>
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Delete confirmation dialog */}
            <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Report?</DialogTitle>
                        <DialogDescription>
                            This action cannot be undone. The report will be permanently removed.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={() => deleteMutation.mutate()}
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

export default ReportViewPage
