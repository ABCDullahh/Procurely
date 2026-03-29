/**
 * Procurement Requests Page
 * List and manage vendor search requests
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
    Plus,
    Search,
    MoreVertical,
    Play,
    Trash2,
    Loader2,
    FileSearch,
} from 'lucide-react'
import { motion } from 'framer-motion'
import {
    Button,
    Card,
    CardContent,
    Input,
} from '@/components/ui'
import { useToast } from '@/components/ui/toast'
import { requestsApi, ProcurementRequest, RequestStatus } from '@/lib/requests-api'
import { cn, formatDate } from '@/lib/utils'

const statusDotConfig: Record<RequestStatus, { label: string; dotColor: string; badgeColor: string }> = {
    DRAFT: { label: 'Draft', dotColor: 'bg-gray-400', badgeColor: 'bg-gray-100 text-gray-600' },
    PENDING: { label: 'Pending', dotColor: 'bg-yellow-500', badgeColor: 'bg-yellow-50 text-yellow-700' },
    RUNNING: { label: 'Running', dotColor: 'bg-blue-500 animate-pulse', badgeColor: 'bg-blue-50 text-blue-700' },
    COMPLETED: { label: 'Completed', dotColor: 'bg-green-500', badgeColor: 'bg-green-50 text-green-700' },
    FAILED: { label: 'Failed', dotColor: 'bg-red-500', badgeColor: 'bg-red-50 text-red-700' },
    CANCELLED: { label: 'Cancelled', dotColor: 'bg-gray-400', badgeColor: 'bg-gray-100 text-gray-600' },
}

function StatusBadge({ status }: { status: RequestStatus }) {
    const config = statusDotConfig[status]
    return (
        <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium', config.badgeColor)}>
            <span className={cn('w-[6px] h-[6px] rounded-full', config.dotColor)} />
            {config.label}
        </span>
    )
}

function RequestCard({
    request,
    onSubmit,
    onDelete,
}: {
    request: ProcurementRequest
    onSubmit: () => void
    onDelete: () => void
}) {
    const navigate = useNavigate()
    const [showMenu, setShowMenu] = useState(false)

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="group"
        >
            <Card className="transition-all duration-200 hover:shadow-card-hover cursor-pointer border-[#ECE8E1]">
                <CardContent className="p-5">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0" onClick={() => navigate(`/requests/${request.id}`)}>
                            <div className="flex items-center gap-2 mb-2">
                                <StatusBadge status={(request.latest_run_status || request.status) as RequestStatus} />
                                <span className="text-xs text-muted-foreground">
                                    {formatDate(request.updated_at)}
                                </span>
                            </div>
                            <h3 className="font-semibold text-[15px] mb-1 truncate text-[#1A1816]">{request.title}</h3>
                            <p className="text-sm text-[#A09A93] line-clamp-2 mb-3">
                                {request.description || 'No description'}
                            </p>
                            <div className="flex items-center gap-4 text-sm">
                                <span className="flex items-center gap-1 text-muted-foreground">
                                    <FileSearch className="w-4 h-4" />
                                    {request.category}
                                </span>
                                {request.vendors_found > 0 && (
                                    <span className="text-green-600">
                                        {request.vendors_found} vendors found
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="relative">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setShowMenu(!showMenu)
                                }}
                                className="p-2 rounded-lg hover:bg-muted transition-colors"
                            >
                                <MoreVertical className="w-4 h-4" />
                            </button>
                            {showMenu && (
                                <div
                                    className="absolute right-0 top-full mt-1 w-40 bg-popover border rounded-lg shadow-lg z-10 py-1"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    {request.status === 'DRAFT' && (
                                        <button
                                            onClick={() => {
                                                onSubmit()
                                                setShowMenu(false)
                                            }}
                                            className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
                                        >
                                            <Play className="w-4 h-4" />
                                            Start Search
                                        </button>
                                    )}
                                    <button
                                        onClick={() => {
                                            onDelete()
                                            setShowMenu(false)
                                        }}
                                        className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2 text-red-600"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                        Delete
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

export function RequestsPage() {
    const navigate = useNavigate()
    const { addToast } = useToast()
    const queryClient = useQueryClient()
    const [filter, setFilter] = useState('')
    const [statusFilter, setStatusFilter] = useState<RequestStatus | ''>('')

    // Fetch requests
    const { data, isLoading } = useQuery({
        queryKey: ['requests', { status: statusFilter || undefined }],
        queryFn: () => requestsApi.list({ status: statusFilter || undefined }),
    })

    // Submit request mutation
    const submitMutation = useMutation({
        mutationFn: requestsApi.submit,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['requests'] })
            addToast({
                type: 'success',
                title: 'Search Started',
                message: 'Your request has been submitted for processing.',
            })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to start search',
                message: error.message,
            })
        },
    })

    // Delete request mutation
    const deleteMutation = useMutation({
        mutationFn: requestsApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['requests'] })
            addToast({
                type: 'success',
                title: 'Request Deleted',
            })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to delete',
                message: error.message,
            })
        },
    })

    const filteredRequests = data?.requests.filter(
        (r) =>
            filter === '' ||
            r.title.toLowerCase().includes(filter.toLowerCase()) ||
            r.category.toLowerCase().includes(filter.toLowerCase())
    ) ?? []

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">Procurement Requests</h1>
                    <p className="text-sm text-[#A09A93] mt-1">
                        Create and manage vendor search requests
                    </p>
                </div>
                <Button onClick={() => navigate('/requests/new')} className="bg-[#1A1816] hover:bg-[#1A1816]/90 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    New Request
                </Button>
            </div>

            <div className="flex gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                        placeholder="Search requests..."
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value as RequestStatus | '')}
                    className="px-3 py-2 border border-[#ECE8E1] rounded-xl bg-white text-sm text-[#6B6560]"
                >
                    <option value="">All Statuses</option>
                    <option value="DRAFT">Draft</option>
                    <option value="PENDING">Pending</option>
                    <option value="RUNNING">Running</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="FAILED">Failed</option>
                </select>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            ) : filteredRequests.length === 0 ? (
                <Card>
                    <CardContent className="py-16 text-center">
                        <FileSearch className="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
                        <h3 className="font-semibold text-lg mb-2">No requests yet</h3>
                        <p className="text-muted-foreground mb-6">
                            Create your first procurement request to start finding vendors
                        </p>
                        <Button onClick={() => navigate('/requests/new')}>
                            <Plus className="w-4 h-4 mr-2" />
                            Create Request
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {filteredRequests.map((request) => (
                        <RequestCard
                            key={request.id}
                            request={request}
                            onSubmit={() => submitMutation.mutate(request.id)}
                            onDelete={() => deleteMutation.mutate(request.id)}
                        />
                    ))}
                </div>
            )}

            {data && data.total > data.page_size && (
                <div className="flex justify-center">
                    <p className="text-sm text-muted-foreground">
                        Showing {filteredRequests.length} of {data.total} requests
                    </p>
                </div>
            )}
        </div>
    )
}

export default RequestsPage
