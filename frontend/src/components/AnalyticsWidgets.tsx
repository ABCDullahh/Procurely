/**
 * AnalyticsWidgets - Dashboard-style visualizations for run analytics
 */

import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell,

} from 'recharts'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
    AnalyticsData,
    LocationDistribution,
    IndustryDistribution,
    ScoreBucket,
} from '@/lib/analytics-api'
import { Users, Globe, TrendingUp, Clock } from 'lucide-react'

interface AnalyticsWidgetsProps {
    data: AnalyticsData | undefined
    isLoading: boolean
}

// Color palette for charts
const COLORS = [
    '#6366f1', // indigo
    '#8b5cf6', // violet
    '#a855f7', // purple
    '#ec4899', // pink
    '#f43f5e', // rose
    '#f97316', // orange
    '#eab308', // yellow
    '#22c55e', // green
    '#14b8a6', // teal
    '#06b6d4', // cyan
]

function KPICard({
    title,
    value,
    icon: Icon,
    subtitle,
    iconBg,
    iconColor,
}: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    subtitle?: string
    iconBg?: string
    iconColor?: string
}) {
    return (
        <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
            <div className="flex items-center gap-4">
                <div className={`p-3 rounded-xl ${iconBg || 'bg-[#F3F0EB]'}`}>
                    <Icon className={`h-5 w-5 ${iconColor || 'text-[#6B6560]'}`} />
                </div>
                <div>
                    <p className="text-2xl font-display font-bold text-[#1A1816]">{value}</p>
                    <p className="text-sm text-[#A09A93]">{title}</p>
                    {subtitle && (
                        <p className="text-xs text-muted-foreground">{subtitle}</p>
                    )}
                </div>
            </div>
        </div>
    )
}

function ScoreBar({ label, value, color }: { label: string; value?: number; color: string }) {
    const v = value || 0
    const colorMap: Record<string, string> = {
        blue: 'bg-blue-500',
        purple: 'bg-purple-500',
        teal: 'bg-teal-500',
        emerald: 'bg-emerald-500',
    }
    return (
        <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-[#6B6560] w-14">{label}</span>
            <div className="flex-1 h-2 bg-[#F3F0EB] rounded-full overflow-hidden">
                <div
                    className={`h-full ${colorMap[color]} rounded-full transition-all`}
                    style={{ width: `${v}%` }}
                />
            </div>
            <span className="text-xs font-semibold text-[#1A1816] w-8 text-right">{v.toFixed(0)}</span>
        </div>
    )
}

function LocationChart({ data }: { data: LocationDistribution[] }) {
    if (data.length === 0) {
        return (
            <div className="h-40 flex items-center justify-center text-muted-foreground">
                No location data available
            </div>
        )
    }

    const maxCount = Math.max(...data.map(d => d.count), 1)

    return (
        <div className="space-y-3">
            {data.slice(0, 6).map((item, index) => (
                <div key={item.location} className="flex items-center gap-3">
                    <span className="text-xs text-[#6B6560] w-28 shrink-0 truncate text-right" title={item.location}>
                        {item.location}
                    </span>
                    <div className="flex-1 h-6 bg-[#F3F0EB] rounded-lg overflow-hidden relative">
                        <div
                            className="h-full rounded-lg transition-all"
                            style={{
                                width: `${(item.count / maxCount) * 100}%`,
                                backgroundColor: COLORS[index % COLORS.length],
                                minWidth: '24px',
                            }}
                        />
                        <span className="absolute inset-y-0 right-2 flex items-center text-[11px] font-semibold text-[#1A1816]">
                            {item.count}
                        </span>
                    </div>
                </div>
            ))}
            {data.length > 6 && (
                <p className="text-[11px] text-[#A09A93] text-center">+{data.length - 6} more locations</p>
            )}
        </div>
    )
}

function IndustryChart({ data }: { data: IndustryDistribution[] }) {
    if (data.length === 0) {
        return (
            <div className="h-40 flex items-center justify-center text-muted-foreground">
                No industry data available
            </div>
        )
    }

    const total = data.reduce((sum, d) => sum + d.count, 0)

    return (
        <div className="flex items-start gap-6">
            {/* Donut Chart */}
            <div className="shrink-0">
                <ResponsiveContainer width={140} height={140}>
                    <PieChart>
                        <Pie
                            data={data.slice(0, 6)}
                            dataKey="count"
                            nameKey="industry"
                            cx="50%"
                            cy="50%"
                            innerRadius={38}
                            outerRadius={62}
                            paddingAngle={2}
                            strokeWidth={0}
                        >
                            {data.slice(0, 6).map((_, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex-1 space-y-2 pt-1">
                {data.slice(0, 6).map((item, index) => {
                    const pct = total > 0 ? (item.count / total) * 100 : 0
                    return (
                        <div key={item.industry} className="flex items-center gap-2">
                            <div
                                className="w-2 h-2 rounded-full shrink-0"
                                style={{ backgroundColor: COLORS[index % COLORS.length] }}
                            />
                            <span className="text-[11px] text-[#1A1816] flex-1 min-w-0 truncate" title={item.industry}>
                                {item.industry}
                            </span>
                            <span className="text-[11px] font-medium text-[#6B6560] shrink-0">
                                {pct.toFixed(0)}%
                            </span>
                        </div>
                    )
                })}
                {data.length > 6 && (
                    <p className="text-[10px] text-[#A09A93]">+{data.length - 6} more</p>
                )}
            </div>
        </div>
    )
}

function ScoreDistributionChart({ data }: { data: ScoreBucket[] }) {
    if (data.every((d) => d.count === 0)) {
        return (
            <div className="h-64 flex items-center justify-center text-muted-foreground">
                No score data available
            </div>
        )
    }

    return (
        <ResponsiveContainer width="100%" height={250}>
            <BarChart data={data}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip
                    contentStyle={{
                        backgroundColor: 'hsl(var(--background))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '8px',
                    }}
                />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    )
}

export default function AnalyticsWidgets({
    data,
    isLoading,
}: AnalyticsWidgetsProps) {
    if (isLoading) {
        return <AnalyticsWidgetsSkeleton />
    }

    if (!data) {
        return (
            <div className="text-center text-muted-foreground py-8">
                No analytics data available
            </div>
        )
    }

    const { run_summary, totals, distributions, top_vendors } = data

    // Format duration
    let durationStr = 'N/A'
    if (run_summary.duration_sec != null) {
        const mins = Math.floor(run_summary.duration_sec / 60)
        const secs = run_summary.duration_sec % 60
        durationStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
    }

    return (
        <div className="space-y-6">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KPICard
                    title="Vendors Found"
                    value={totals.vendors_count}
                    icon={Users}
                    iconBg="bg-red-50"
                    iconColor="text-red-600"
                />
                <KPICard
                    title="Sources Scanned"
                    value={totals.sources_count}
                    icon={Globe}
                    iconBg="bg-blue-50"
                    iconColor="text-blue-600"
                />
                <KPICard
                    title="Avg. Score"
                    value={
                        distributions.average_scores.avg_overall?.toFixed(1) ?? 'N/A'
                    }
                    icon={TrendingUp}
                    iconBg="bg-emerald-50"
                    iconColor="text-emerald-600"
                />
                <KPICard
                    title="Duration"
                    value={durationStr}
                    icon={Clock}
                    iconBg="bg-amber-50"
                    iconColor="text-amber-600"
                />
            </div>

            {/* Score Breakdown */}
            {data.score_breakdown && (
                <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
                    <h3 className="text-sm font-semibold text-[#1A1816] mb-4">Score Breakdown</h3>
                    <div className="space-y-3">
                        <ScoreBar label="Fit" value={data.score_breakdown?.avg_fit} color="blue" />
                        <ScoreBar label="Trust" value={data.score_breakdown?.avg_trust} color="purple" />
                        <ScoreBar label="Quality" value={data.score_breakdown?.avg_quality} color="teal" />
                        <ScoreBar label="Overall" value={data.score_breakdown?.avg_overall} color="emerald" />
                    </div>
                </div>
            )}

            {/* Charts Row */}
            <div className="grid md:grid-cols-2 gap-6">
                <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
                    <h3 className="text-sm font-semibold text-[#1A1816] mb-4">Vendors by Location</h3>
                    <LocationChart data={distributions.vendors_by_location} />
                </div>

                <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
                    <h3 className="text-sm font-semibold text-[#1A1816] mb-4">Vendors by Industry</h3>
                    <IndustryChart data={distributions.vendors_by_industry} />
                </div>
            </div>

            {/* Score Distribution */}
            <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
                <h3 className="text-sm font-semibold text-[#1A1816] mb-4">Score Distribution</h3>
                <ScoreDistributionChart data={distributions.score_distribution} />
            </div>

            {/* Top Vendors */}
            {top_vendors.length > 0 && (
                <div className="rounded-xl border border-[#ECE8E1] bg-white p-5">
                    <h3 className="text-sm font-semibold text-[#1A1816] mb-4">Top Vendors</h3>
                    <div className="space-y-3">
                        {top_vendors.map((vendor, idx) => (
                            <div
                                key={vendor.id}
                                className="flex items-center justify-between p-3 rounded-lg bg-[#F9F7F4]"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-lg font-bold text-[#6366f1] w-6">
                                        #{idx + 1}
                                    </span>
                                    <div>
                                        <p className="font-medium text-[#1A1816]">{vendor.name}</p>
                                        <p className="text-xs text-[#A09A93]">
                                            {vendor.location ?? 'Unknown'} •{' '}
                                            {vendor.industry ?? 'Unknown'}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-[#6366f1]">
                                        {vendor.overall_score?.toFixed(0) ?? '-'}
                                    </p>
                                    <p className="text-xs text-[#A09A93]">
                                        Fit: {vendor.fit_score?.toFixed(0) ?? '-'} / Trust:{' '}
                                        {vendor.trust_score?.toFixed(0) ?? '-'}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

function AnalyticsWidgetsSkeleton() {
    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                    <Card key={i}>
                        <CardContent className="pt-6">
                            <Skeleton className="h-16" />
                        </CardContent>
                    </Card>
                ))}
            </div>
            <div className="grid md:grid-cols-2 gap-6">
                <Card>
                    <CardHeader>
                        <Skeleton className="h-5 w-40" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton className="h-64" />
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <Skeleton className="h-5 w-40" />
                    </CardHeader>
                    <CardContent>
                        <Skeleton className="h-64" />
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
