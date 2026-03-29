/**
 * Dashboard Page - Real aggregated stats from API
 */

import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
    FileSearch,
    Users,
    TrendingUp,
    Activity,
    Plus,
    ArrowRight,
    XCircle,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from '@/components/ui'
import { dashboardApi, RecentRequest } from '@/lib/dashboard-api'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks'

const statusDotColors: Record<string, string> = {
    DRAFT: 'bg-gray-400',
    PENDING: 'bg-yellow-500',
    RUNNING: 'bg-blue-500 animate-pulse',
    COMPLETED: 'bg-green-500',
    FAILED: 'bg-red-500',
}

const statusBadgeColors: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-600',
    PENDING: 'bg-yellow-50 text-yellow-700',
    RUNNING: 'bg-blue-50 text-blue-700',
    COMPLETED: 'bg-green-50 text-green-700',
    FAILED: 'bg-red-50 text-red-700',
}

function StatCard({
    title,
    value,
    icon,
    trend,
    isLoading,
    iconBg = 'bg-[#F3F0EB]',
    iconColor = 'text-[#6B6560]',
}: {
    title: string
    value: number | string
    icon: React.ReactNode
    trend?: string
    isLoading?: boolean
    iconBg?: string
    iconColor?: string
}) {
    return (
        <Card>
            <CardContent className="p-5">
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-[#A09A93]">{title}</p>
                        {isLoading ? (
                            <Skeleton className="h-8 w-20 mt-2" />
                        ) : (
                            <p className="text-2xl font-display font-bold text-[#1A1816] mt-2">{value}</p>
                        )}
                        {trend && <p className="text-xs text-green-600 mt-1">{trend}</p>}
                    </div>
                    <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', iconBg, iconColor)}>
                        {icon}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}

function RecentRequestRow({ request, onClick }: { request: RecentRequest; onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-[#FAF9F7] transition-colors border-b border-[#F3F0EB] last:border-0 text-left"
        >
            <div className="flex items-center gap-3">
                <span
                    className={cn(
                        'w-[6px] h-[6px] rounded-full flex-shrink-0',
                        statusDotColors[request.status] || 'bg-gray-400'
                    )}
                />
                <div>
                    <p className="font-medium text-sm text-[#1A1816]">{request.title}</p>
                    <p className="text-xs text-[#A09A93]">{request.category}</p>
                </div>
            </div>
            <div className="flex items-center gap-3">
                {request.vendors_found > 0 && (
                    <span className="text-xs font-medium text-[#6B6560]">{request.vendors_found} vendors</span>
                )}
                <span className={cn(
                    'text-[10px] font-medium px-2 py-0.5 rounded-full',
                    statusBadgeColors[request.status] || 'bg-gray-100 text-gray-600'
                )}>
                    {request.status.toLowerCase()}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-[#A09A93]" />
            </div>
        </button>
    )
}

function EmptyDashboard() {
    const navigate = useNavigate()

    return (
        <Card>
            <CardContent className="py-16 text-center">
                <FileSearch className="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
                <h3 className="font-semibold text-lg mb-2">Welcome to Procurely!</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                    Start your first procurement search to discover and evaluate vendors for your needs.
                </p>
                <Button onClick={() => navigate('/requests/new')}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create First Request
                </Button>
            </CardContent>
        </Card>
    )
}

function DashboardSkeleton() {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i}>
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <Skeleton className="h-4 w-24 mb-2" />
                                    <Skeleton className="h-8 w-16" />
                                </div>
                                <Skeleton className="w-12 h-12 rounded-xl" />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
            <Card>
                <CardHeader>
                    <Skeleton className="h-6 w-40" />
                </CardHeader>
                <CardContent className="p-0">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center gap-4 p-4 border-b">
                            <Skeleton className="w-8 h-8 rounded-lg" />
                            <div className="flex-1">
                                <Skeleton className="h-4 w-48 mb-1" />
                                <Skeleton className="h-3 w-24" />
                            </div>
                        </div>
                    ))}
                </CardContent>
            </Card>
        </div>
    )
}

export function Dashboard() {
    const navigate = useNavigate()
    const { user } = useAuth()

    const { data, isLoading, error } = useQuery({
        queryKey: ['dashboard'],
        queryFn: dashboardApi.get,
    })

    const getGreeting = () => {
        const hour = new Date().getHours()
        if (hour < 12) return 'Good morning'
        if (hour < 17) return 'Good afternoon'
        return 'Good evening'
    }

    if (error) {
        return (
            <div className="p-6">
                <Card>
                    <CardContent className="py-12 text-center">
                        <XCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
                        <p className="text-lg font-medium">Failed to load dashboard</p>
                        <p className="text-sm text-muted-foreground mt-1">Please try again later</p>
                    </CardContent>
                </Card>
            </div>
        )
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">
                        {getGreeting()}, {user?.full_name?.split(' ')[0] || 'there'}
                    </h1>
                    <p className="text-sm text-[#A09A93] mt-1">
                        Here's an overview of your procurement activities
                    </p>
                </div>
                <Button onClick={() => navigate('/requests/new')} className="bg-[#1A1816] hover:bg-[#1A1816]/90 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    New Request
                </Button>
            </div>

            {isLoading ? (
                <DashboardSkeleton />
            ) : data?.total_requests === 0 ? (
                <EmptyDashboard />
            ) : (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-6"
                >
                    {/* Stats Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <StatCard
                            title="Total Requests"
                            value={data?.total_requests || 0}
                            icon={<FileSearch className="w-5 h-5" />}
                            iconBg="bg-blue-50"
                            iconColor="text-blue-600"
                        />
                        <StatCard
                            title="Vendors Found"
                            value={data?.total_vendors_found || 0}
                            icon={<Users className="w-5 h-5" />}
                            iconBg="bg-green-50"
                            iconColor="text-green-600"
                        />
                        <StatCard
                            title="Completed"
                            value={data?.requests_by_status?.COMPLETED || 0}
                            icon={<TrendingUp className="w-5 h-5" />}
                            iconBg="bg-purple-50"
                            iconColor="text-purple-600"
                        />
                        <StatCard
                            title="Active Runs"
                            value={data?.active_runs || 0}
                            icon={<Activity className="w-5 h-5" />}
                            iconBg="bg-amber-50"
                            iconColor="text-amber-600"
                        />
                    </div>

                    {/* Status Breakdown */}
                    {data?.requests_by_status && Object.keys(data.requests_by_status).length > 0 && (
                        <Card>
                            <CardHeader className="pb-3">
                                <CardTitle className="text-sm font-semibold text-[#1A1816]">Status Overview</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-2.5">
                                    {Object.entries(data.requests_by_status).map(([status, count]) => (
                                        <div
                                            key={status}
                                            className="flex items-center justify-between py-1"
                                        >
                                            <div className="flex items-center gap-2.5">
                                                <span className={cn(
                                                    'w-[6px] h-[6px] rounded-full',
                                                    statusDotColors[status] || 'bg-gray-400'
                                                )} />
                                                <span className="text-sm text-[#6B6560] capitalize">{status.toLowerCase()}</span>
                                            </div>
                                            <span className="text-sm font-semibold text-[#1A1816]">{count}</span>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    )}

                    {/* Recent Requests */}
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between pb-0">
                            <CardTitle className="text-sm font-semibold text-[#1A1816]">Recent Requests</CardTitle>
                            <Button variant="ghost" size="sm" className="text-[#A09A93] hover:text-[#1A1816] text-xs" onClick={() => navigate('/requests')}>
                                View All
                                <ArrowRight className="w-3.5 h-3.5 ml-1" />
                            </Button>
                        </CardHeader>
                        <CardContent className="p-0 mt-3">
                            {data?.recent_requests && data.recent_requests.length > 0 ? (
                                data.recent_requests.map((request) => (
                                    <RecentRequestRow
                                        key={request.id}
                                        request={request}
                                        onClick={() => navigate(`/requests/${request.id}`)}
                                    />
                                ))
                            ) : (
                                <div className="p-8 text-center text-muted-foreground">
                                    No requests yet. Create one to get started!
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </motion.div>
            )}
        </div>
    )
}

export default Dashboard
