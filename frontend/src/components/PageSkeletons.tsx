/**
 * PageSkeletons - Skeleton loaders for all major pages
 * Editorial warm theme with shimmer effect
 */

import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader } from '@/components/ui/card'

// Dashboard Skeleton
export function DashboardSkeleton() {
    return (
        <div className="p-6 space-y-6 animate-fade-in">
            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <Card key={i}>
                        <CardContent className="p-4">
                            <Skeleton className="h-4 w-20 mb-2" />
                            <Skeleton className="h-8 w-16" />
                        </CardContent>
                    </Card>
                ))}
            </div>
            {/* Recent activity */}
            <Card>
                <CardHeader>
                    <Skeleton className="h-5 w-32" />
                </CardHeader>
                <CardContent className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="flex items-center gap-3">
                            <Skeleton className="h-10 w-10 rounded-full" />
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

// Requests List Skeleton
export function RequestsListSkeleton() {
    return (
        <div className="p-6 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-40" />
                <Skeleton className="h-10 w-32 rounded-md" />
            </div>
            <div className="grid gap-4">
                {[...Array(6)].map((_, i) => (
                    <Card key={i}>
                        <CardContent className="p-4 flex items-center gap-4">
                            <div className="flex-1">
                                <Skeleton className="h-5 w-64 mb-2" />
                                <Skeleton className="h-4 w-48" />
                            </div>
                            <Skeleton className="h-6 w-20 rounded-full" />
                            <Skeleton className="h-4 w-24" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}

// Request Detail Skeleton
export function RequestDetailSkeleton() {
    return (
        <div className="min-h-screen animate-fade-in">
            {/* Header */}
            <div className="border-b bg-card p-6">
                <div className="container max-w-6xl">
                    <div className="flex items-center gap-4 mb-4">
                        <Skeleton className="h-8 w-20" />
                        <Skeleton className="h-6 w-24 rounded-full" />
                    </div>
                    <Skeleton className="h-8 w-96 mb-2" />
                    <Skeleton className="h-4 w-64" />
                </div>
            </div>
            {/* Content */}
            <div className="container max-w-6xl p-6 space-y-6">
                {/* Run status */}
                <Card>
                    <CardContent className="p-4 flex items-center gap-4">
                        <Skeleton className="h-12 w-12 rounded-full" />
                        <div className="flex-1">
                            <Skeleton className="h-5 w-32 mb-2" />
                            <Skeleton className="h-2 w-full rounded-full" />
                        </div>
                        <Skeleton className="h-10 w-28 rounded-md" />
                    </CardContent>
                </Card>
                {/* Vendors table */}
                <Card>
                    <CardHeader>
                        <Skeleton className="h-5 w-24" />
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-3">
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="flex items-center gap-4 py-3 border-b last:border-0">
                                    <Skeleton className="h-10 w-10 rounded" />
                                    <div className="flex-1">
                                        <Skeleton className="h-4 w-40 mb-1" />
                                        <Skeleton className="h-3 w-24" />
                                    </div>
                                    <Skeleton className="h-8 w-16 rounded" />
                                    <Skeleton className="h-8 w-16 rounded" />
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

// Vendor Profile Skeleton
export function VendorProfileSkeleton() {
    return (
        <div className="min-h-screen animate-fade-in">
            <div className="border-b bg-card p-6">
                <div className="container max-w-5xl flex items-center gap-4">
                    <Skeleton className="h-16 w-16 rounded-xl" />
                    <div>
                        <Skeleton className="h-7 w-48 mb-2" />
                        <Skeleton className="h-4 w-32" />
                    </div>
                </div>
            </div>
            <div className="container max-w-5xl p-6 space-y-6">
                <div className="grid md:grid-cols-3 gap-4">
                    {[...Array(3)].map((_, i) => (
                        <Card key={i}>
                            <CardContent className="p-4">
                                <Skeleton className="h-4 w-20 mb-2" />
                                <Skeleton className="h-6 w-24" />
                            </CardContent>
                        </Card>
                    ))}
                </div>
                <Card>
                    <CardContent className="p-6">
                        <Skeleton className="h-5 w-32 mb-4" />
                        <div className="space-y-3">
                            {[...Array(4)].map((_, i) => (
                                <Skeleton key={i} className="h-4 w-full" />
                            ))}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

// Shortlists Page Skeleton
export function ShortlistsSkeleton() {
    return (
        <div className="p-6 space-y-4 animate-fade-in">
            <div className="flex items-center justify-between">
                <Skeleton className="h-8 w-32" />
                <Skeleton className="h-10 w-36 rounded-md" />
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                    <Card key={i}>
                        <CardContent className="p-4">
                            <Skeleton className="h-5 w-40 mb-2" />
                            <Skeleton className="h-4 w-24 mb-4" />
                            <div className="flex gap-2">
                                <Skeleton className="h-8 w-8 rounded-full" />
                                <Skeleton className="h-8 w-8 rounded-full" />
                                <Skeleton className="h-8 w-8 rounded-full" />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}

// Reports Page Skeleton
export function ReportsSkeleton() {
    return (
        <div className="p-6 space-y-4 animate-fade-in">
            <Skeleton className="h-8 w-28" />
            <div className="grid gap-4">
                {[...Array(4)].map((_, i) => (
                    <Card key={i}>
                        <CardContent className="p-4 flex items-center gap-4">
                            <Skeleton className="h-10 w-10 rounded" />
                            <div className="flex-1">
                                <Skeleton className="h-4 w-48 mb-1" />
                                <Skeleton className="h-3 w-32" />
                            </div>
                            <Skeleton className="h-8 w-20 rounded-md" />
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}

// Copilot Drawer Skeleton
export function CopilotSkeleton() {
    return (
        <div className="p-4 space-y-4 animate-fade-in">
            <div className="flex items-start gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-1/2" />
                </div>
            </div>
            <div className="flex gap-2">
                <Skeleton className="h-8 w-24 rounded-md" />
                <Skeleton className="h-8 w-28 rounded-md" />
            </div>
        </div>
    )
}

// Compare Matrix Skeleton  
export function CompareMatrixSkeleton() {
    return (
        <div className="p-4 animate-fade-in">
            <div className="flex gap-4 mb-4">
                {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} className="h-32 w-40 rounded-lg" />
                ))}
            </div>
            <div className="space-y-2">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="flex gap-4">
                        <Skeleton className="h-10 w-24" />
                        {[...Array(3)].map((_, j) => (
                            <Skeleton key={j} className="h-10 w-40" />
                        ))}
                    </div>
                ))}
            </div>
        </div>
    )
}

// Vendor Quick View Skeleton
export function VendorQuickViewSkeleton() {
    return (
        <div className="p-6 space-y-4 animate-fade-in">
            <div className="flex items-center gap-4">
                <Skeleton className="h-12 w-12 rounded-lg" />
                <div>
                    <Skeleton className="h-5 w-40 mb-1" />
                    <Skeleton className="h-4 w-28" />
                </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
                <Skeleton className="h-16 rounded-lg" />
                <Skeleton className="h-16 rounded-lg" />
                <Skeleton className="h-16 rounded-lg" />
            </div>
            <Skeleton className="h-32 w-full rounded-lg" />
        </div>
    )
}
