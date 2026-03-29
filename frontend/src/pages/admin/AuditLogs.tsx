/**
 * Admin Audit Logs Page
 * View and filter audit logs for admin actions
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { History, Filter, ChevronDown, Loader2 } from 'lucide-react'
import { Button, Card, CardContent, CardHeader, CardTitle, Input } from '@/components/ui'
import { adminApi, AuditLogResponse } from '@/lib/admin-api'
import { cn } from '@/lib/utils'

const actionLabels: Record<string, { label: string; color: string }> = {
    API_KEY_SET: { label: 'Key Set', color: 'bg-blue-500/10 text-blue-600' },
    API_KEY_ROTATE: { label: 'Key Rotated', color: 'bg-purple-500/10 text-purple-600' },
    API_KEY_TEST: { label: 'Key Tested', color: 'bg-green-500/10 text-green-600' },
    API_KEY_DELETE: { label: 'Key Deleted', color: 'bg-red-500/10 text-red-600' },
}

function LogRow({ log, onClick }: { log: AuditLogResponse; onClick: () => void }) {
    const actionInfo = actionLabels[log.action] ?? { label: log.action, color: 'bg-muted' }
    const metadata = log.metadata_json ? JSON.parse(log.metadata_json) : null

    return (
        <button
            onClick={onClick}
            className="w-full text-left p-4 hover:bg-muted/50 transition-colors border-b last:border-0"
        >
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                    <span className={cn('px-2 py-1 rounded text-xs font-medium', actionInfo.color)}>
                        {actionInfo.label}
                    </span>
                    <span className="font-medium truncate">{log.actor_email}</span>
                    {log.target_id && (
                        <span className="text-sm text-muted-foreground">→ {log.target_id}</span>
                    )}
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground shrink-0">
                    {metadata?.success !== undefined && (
                        <span className={metadata.success ? 'text-green-600' : 'text-red-600'}>
                            {metadata.success ? '✓' : '✗'}
                        </span>
                    )}
                    <span>{new Date(log.created_at).toLocaleString()}</span>
                    <ChevronDown className="w-4 h-4" />
                </div>
            </div>
        </button>
    )
}

function LogDetail({ log, onClose }: { log: AuditLogResponse; onClose: () => void }) {
    const metadata = log.metadata_json ? JSON.parse(log.metadata_json) : null

    return (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-lg">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <History className="w-5 h-5" />
                        Audit Log Detail
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <p className="text-muted-foreground">Action</p>
                            <p className="font-medium">{log.action}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground">Actor</p>
                            <p className="font-medium">{log.actor_email}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground">Target Type</p>
                            <p className="font-medium">{log.target_type}</p>
                        </div>
                        <div>
                            <p className="text-muted-foreground">Target ID</p>
                            <p className="font-medium">{log.target_id ?? '—'}</p>
                        </div>
                        <div className="col-span-2">
                            <p className="text-muted-foreground">Timestamp</p>
                            <p className="font-medium">{new Date(log.created_at).toLocaleString()}</p>
                        </div>
                    </div>

                    {metadata && (
                        <div>
                            <p className="text-muted-foreground text-sm mb-2">Metadata</p>
                            <pre className="text-xs bg-muted p-3 rounded-lg overflow-auto max-h-48">
                                {JSON.stringify(metadata, null, 2)}
                            </pre>
                        </div>
                    )}

                    <Button variant="outline" onClick={onClose} className="w-full">
                        Close
                    </Button>
                </CardContent>
            </Card>
        </div>
    )
}

export function AdminAuditLogs() {
    const [filter, setFilter] = useState('')
    const [selectedLog, setSelectedLog] = useState<AuditLogResponse | null>(null)
    const [page, setPage] = useState(1)

    const { data, isLoading } = useQuery({
        queryKey: ['admin', 'audit-logs', { page }],
        queryFn: () => adminApi.listAuditLogs({ page, page_size: 20 }),
    })

    const filteredLogs = data?.logs.filter(log =>
        filter === '' ||
        log.action.toLowerCase().includes(filter.toLowerCase()) ||
        log.actor_email.toLowerCase().includes(filter.toLowerCase()) ||
        log.target_id?.toLowerCase().includes(filter.toLowerCase())
    ) ?? []

    return (
        <div className="p-6 space-y-6">
            <div>
                <h1 className="text-2xl font-display font-bold">Audit Logs</h1>
                <p className="text-muted-foreground mt-1">
                    Track admin actions for security and compliance
                </p>
            </div>

            <div className="flex gap-3">
                <div className="relative flex-1">
                    <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Filter by action, user, or target..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="pl-10"
                    />
                </div>
            </div>

            <Card>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 animate-spin text-primary" />
                        </div>
                    ) : filteredLogs.length === 0 ? (
                        <div className="text-center py-12 text-muted-foreground">
                            <History className="w-12 h-12 mx-auto mb-4 opacity-30" />
                            <p>No audit logs found</p>
                        </div>
                    ) : (
                        filteredLogs.map(log => (
                            <LogRow
                                key={log.id}
                                log={log}
                                onClick={() => setSelectedLog(log)}
                            />
                        ))
                    )}
                </CardContent>
            </Card>

            {data && data.total > data.page_size && (
                <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                        Showing {((page - 1) * data.page_size) + 1} to {Math.min(page * data.page_size, data.total)} of {data.total}
                    </p>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={page === 1}
                            onClick={() => setPage(p => p - 1)}
                        >
                            Previous
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            disabled={page * data.page_size >= data.total}
                            onClick={() => setPage(p => p + 1)}
                        >
                            Next
                        </Button>
                    </div>
                </div>
            )}

            {selectedLog && (
                <LogDetail log={selectedLog} onClose={() => setSelectedLog(null)} />
            )}
        </div>
    )
}

export default AdminAuditLogs
