/**
 * VendorResultsTable - Card-based vendor display with score explanations
 *
 * Design: Editorial Luxury with crimson accents
 * Features:
 * - Responsive card grid (2 cols desktop, 1 mobile)
 * - Score pills with tooltip explanations
 * - Price range extraction (only numbers)
 * - Hide empty sections
 */

import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, ExternalLink, Eye, TrendingUp, Shield, Target, Sparkles, DollarSign, ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent } from '@/components/ui/card'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip'
import { vendorsApi, VendorListItem } from '@/lib/vendors-api'
import { cn } from '@/lib/utils'

interface VendorResultsTableProps {
    runId: number
    isRunning?: boolean
    onVendorClick?: (vendorId: number) => void
}

/**
 * Extract only numeric price range from pricing text
 * e.g., "Office chairs range from Rp 459.000 - Rp 6.399.000" => "Rp 459.000 - Rp 6.399.000"
 */
function extractPriceRange(text: string | null | undefined): string | null {
    if (!text) return null

    // Pattern untuk IDR/Rp format
    const idrPattern = /(?:Rp\.?\s*|IDR\s*)[\d.,]+(?:\s*(?:-|to|hingga|sampai)\s*(?:Rp\.?\s*|IDR\s*)[\d.,]+)?/gi
    const idrMatch = text.match(idrPattern)
    if (idrMatch) {
        return idrMatch[0].trim()
    }

    // Pattern untuk USD format
    const usdPattern = /\$[\d.,]+(?:\s*(?:-|to)\s*\$[\d.,]+)?/gi
    const usdMatch = text.match(usdPattern)
    if (usdMatch) {
        return usdMatch[0].trim()
    }

    // Pattern untuk angka dengan currency symbol apapun
    const genericPattern = /[\d.,]+\s*(?:juta|ribu|rb|k|m|million|thousand)?\s*(?:-|to|hingga|sampai)\s*[\d.,]+\s*(?:juta|ribu|rb|k|m|million|thousand)?/gi
    const genericMatch = text.match(genericPattern)
    if (genericMatch) {
        return genericMatch[0].trim()
    }

    return null
}

/**
 * Format price from min/max values
 */
function formatPriceFromRange(min: number | null, max: number | null): string | null {
    if (!min && !max) return null

    const formatPrice = (val: number) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            maximumFractionDigits: 0,
        }).format(val)
    }

    if (min && max) {
        return `${formatPrice(min)} - ${formatPrice(max)}`
    }
    return formatPrice(min || max!)
}

/**
 * Get score explanation based on score type and value
 */
function getScoreExplanation(type: 'overall' | 'fit' | 'trust' | 'quality', score: number | null, metrics?: VendorListItem['metrics']): { title: string; description: string; breakdown: string[] } {
    if (score == null) {
        return {
            title: 'No Data',
            description: 'Score not yet calculated',
            breakdown: []
        }
    }

    const level = score >= 75 ? 'high' : score >= 50 ? 'medium' : 'low'

    switch (type) {
        case 'overall':
            return {
                title: 'Overall Score',
                description: level === 'high'
                    ? 'Excellent vendor match based on all criteria'
                    : level === 'medium'
                    ? 'Moderate match - review details before deciding'
                    : 'Lower match - may need additional evaluation',
                breakdown: [
                    `Fit: ${metrics?.fit_score?.toFixed(0) ?? '—'}% weight`,
                    `Trust: ${metrics?.trust_score?.toFixed(0) ?? '—'}% weight`,
                    `Quality: ${metrics?.quality_score?.toFixed(0) ?? '—'}% weight`,
                    metrics?.price_score ? `Price: ${metrics.price_score.toFixed(0)}% weight` : '',
                ].filter(Boolean)
            }
        case 'fit':
            return {
                title: 'Fit Score',
                description: level === 'high'
                    ? 'Strong match with your requirements'
                    : level === 'medium'
                    ? 'Partial match with requirements'
                    : 'Limited match - may not meet key needs',
                breakdown: [
                    metrics?.must_have_matched !== undefined
                        ? `Must-haves: ${metrics.must_have_matched}/${metrics.must_have_total} matched`
                        : '',
                    metrics?.nice_to_have_matched !== undefined
                        ? `Nice-to-haves: ${metrics.nice_to_have_matched}/${metrics.nice_to_have_total} matched`
                        : '',
                ].filter(Boolean)
            }
        case 'trust':
            return {
                title: 'Trust Score',
                description: level === 'high'
                    ? 'High reliability - verified from multiple sources'
                    : level === 'medium'
                    ? 'Moderate reliability - some verification available'
                    : 'Limited verification - proceed with caution',
                breakdown: [
                    metrics?.source_count !== undefined ? `${metrics.source_count} sources verified` : '',
                    metrics?.evidence_count !== undefined ? `${metrics.evidence_count} evidence points` : '',
                    metrics?.source_diversity !== undefined ? `Source diversity: ${(metrics.source_diversity * 100).toFixed(0)}%` : '',
                ].filter(Boolean)
            }
        case 'quality':
            return {
                title: 'Research Quality',
                description: level === 'high'
                    ? 'Comprehensive research with high confidence'
                    : level === 'medium'
                    ? 'Good research depth with moderate confidence'
                    : 'Limited research data available',
                breakdown: [
                    metrics?.completeness_pct !== undefined ? `Data completeness: ${metrics.completeness_pct.toFixed(0)}%` : '',
                    metrics?.confidence_pct !== undefined ? `Confidence: ${metrics.confidence_pct.toFixed(0)}%` : '',
                    metrics?.research_depth !== undefined ? `Research depth: ${(metrics.research_depth * 100).toFixed(0)}%` : '',
                ].filter(Boolean)
            }
    }
}

/**
 * Score pill with tooltip explanation
 */
function ScorePill({
    type,
    score,
    metrics,
    icon: Icon
}: {
    type: 'overall' | 'fit' | 'trust' | 'quality'
    score: number | null | undefined
    metrics?: VendorListItem['metrics']
    icon: React.ElementType
}) {
    if (score == null) return null

    const explanation = getScoreExplanation(type, score, metrics)

    const colorClasses = {
        overall: score >= 75
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            : score >= 50
            ? 'bg-amber-50 text-amber-700 border border-amber-200'
            : 'bg-red-50 text-red-700 border border-red-200',
        fit: 'bg-blue-50 text-blue-700 border border-blue-200',
        trust: 'bg-purple-50 text-purple-700 border border-purple-200',
        quality: 'bg-teal-50 text-teal-700 border border-teal-200',
    }

    const labels = {
        overall: 'Overall',
        fit: 'Fit',
        trust: 'Trust',
        quality: 'Quality',
    }

    return (
        <TooltipProvider>
            <Tooltip delayDuration={200}>
                <TooltipTrigger asChild>
                    <div className={cn(
                        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium cursor-help transition-all',
                        colorClasses[type]
                    )}>
                        <Icon className="w-3.5 h-3.5" />
                        <span>{labels[type]}</span>
                        <span className="font-bold">{score.toFixed(0)}</span>
                    </div>
                </TooltipTrigger>
                <TooltipContent
                    side="top"
                    className="max-w-xs p-4 bg-white border shadow-xl rounded-xl"
                >
                    <div className="space-y-2">
                        <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4 text-primary" />
                            <span className="font-semibold text-sm">{explanation.title}</span>
                            <span className={cn(
                                'ml-auto text-xs px-2 py-0.5 rounded-full',
                                score >= 75 ? 'bg-emerald-100 text-emerald-700' :
                                score >= 50 ? 'bg-amber-100 text-amber-700' :
                                'bg-rose-100 text-rose-700'
                            )}>
                                {score.toFixed(0)}%
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground">
                            {explanation.description}
                        </p>
                        {explanation.breakdown.length > 0 && (
                            <div className="pt-2 border-t space-y-1">
                                {explanation.breakdown.map((item, i) => (
                                    <p key={i} className="text-xs text-muted-foreground flex items-center gap-1.5">
                                        <span className="w-1.5 h-1.5 rounded-full bg-primary/40" />
                                        {item}
                                    </p>
                                ))}
                            </div>
                        )}
                    </div>
                </TooltipContent>
            </Tooltip>
        </TooltipProvider>
    )
}

/**
 * Vendor logo with fallback initials
 */
function VendorLogo({ name, logoUrl }: { name: string; logoUrl?: string | null }) {
    const initials = name
        .split(' ')
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase()

    if (logoUrl) {
        return (
            <div className="relative">
                <img
                    src={logoUrl}
                    alt={name}
                    className="h-14 w-14 rounded-xl object-contain bg-white border border-[#ECE8E1]"
                    onError={(e) => {
                        e.currentTarget.style.display = 'none'
                        e.currentTarget.nextElementSibling?.classList.remove('hidden')
                    }}
                />
                <div className="hidden h-14 w-14 rounded-xl bg-[#1A1816] flex items-center justify-center text-white font-bold text-lg">
                    {initials}
                </div>
            </div>
        )
    }

    return (
        <div className="h-14 w-14 rounded-xl bg-[#1A1816] flex items-center justify-center text-white font-bold text-lg">
            {initials}
        </div>
    )
}

/**
 * Single vendor card
 */
function VendorCard({
    vendor,
    onQuickView,
    onNavigate
}: {
    vendor: VendorListItem
    onQuickView: () => void
    onNavigate: () => void
}) {
    // Get price display - prioritize extracted range, then formatted min/max
    const priceDisplay = extractPriceRange(vendor.pricing_details)
        || formatPriceFromRange(vendor.price_range_min, vendor.price_range_max)

    return (
        <Card className="group relative overflow-hidden hover:shadow-card-hover transition-all duration-200 border-[#ECE8E1]">

            <CardContent className="p-5">
                {/* Header: Logo + Name + Website */}
                <div className="flex items-start gap-4 mb-4">
                    <VendorLogo name={vendor.name} logoUrl={vendor.logo_url} />
                    <div className="flex-1 min-w-0">
                        <h3 className="font-display font-semibold text-lg text-[#1A1816] truncate">
                            {vendor.name}
                        </h3>
                        {vendor.website && (
                            <a
                                href={vendor.website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-sm text-[#A09A93] hover:text-[#1A1816] transition-colors mt-0.5"
                                onClick={(e) => e.stopPropagation()}
                            >
                                {(() => {
                                    try {
                                        return new URL(vendor.website).hostname.replace('www.', '')
                                    } catch {
                                        return vendor.website
                                    }
                                })()}
                                <ExternalLink className="h-3 w-3" />
                            </a>
                        )}
                        {vendor.industry && (
                            <div className="mt-2">
                                <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-[#F3F0EB] text-xs font-medium text-[#6B6560]">
                                    {vendor.industry}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Score Pills */}
                <div className="flex flex-wrap gap-2 mb-4">
                    <ScorePill
                        type="overall"
                        score={vendor.metrics?.overall_score}
                        metrics={vendor.metrics}
                        icon={TrendingUp}
                    />
                    <ScorePill
                        type="fit"
                        score={vendor.metrics?.fit_score}
                        metrics={vendor.metrics}
                        icon={Target}
                    />
                    <ScorePill
                        type="trust"
                        score={vendor.metrics?.trust_score}
                        metrics={vendor.metrics}
                        icon={Shield}
                    />
                    <ScorePill
                        type="quality"
                        score={vendor.metrics?.quality_score}
                        metrics={vendor.metrics}
                        icon={Sparkles}
                    />
                </div>

                {/* Price Display - Only show if we have actual numeric prices */}
                {priceDisplay && (
                    <div className="mb-4 p-3 rounded-lg bg-[#FAF9F7] border border-[#ECE8E1]">
                        <div className="flex items-center gap-2">
                            <DollarSign className="w-4 h-4 text-[#6B6560] flex-shrink-0" />
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="text-sm font-semibold text-[#1A1816]">
                                    {priceDisplay}
                                </span>
                                {vendor.pricing_model && vendor.pricing_model !== 'contact-sales' && (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-[#ECE8E1] text-xs font-medium text-[#6B6560]">
                                        ({vendor.pricing_model})
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* Actions */}
                <div className="flex gap-2 pt-3 border-t border-[#F3F0EB]">
                    <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 gap-2 hover:bg-[#FAF9F7] transition-colors"
                        onClick={(e) => {
                            e.stopPropagation()
                            onQuickView()
                        }}
                    >
                        <Eye className="h-4 w-4" />
                        Quick View
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        className="gap-2 hover:bg-[#FAF9F7] transition-colors"
                        onClick={(e) => {
                            e.stopPropagation()
                            onNavigate()
                        }}
                    >
                        <ExternalLink className="h-4 w-4" />
                    </Button>
                </div>
            </CardContent>
        </Card>
    )
}

/**
 * Loading skeleton for vendor cards
 */
function VendorCardSkeleton() {
    return (
        <Card className="overflow-hidden">
            <CardContent className="p-5">
                <div className="flex items-start gap-4 mb-4">
                    <Skeleton className="h-14 w-14 rounded-xl" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-5 w-3/4" />
                        <Skeleton className="h-4 w-1/2" />
                        <Skeleton className="h-6 w-20 rounded-lg" />
                    </div>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                    <Skeleton className="h-8 w-24 rounded-full" />
                    <Skeleton className="h-8 w-20 rounded-full" />
                    <Skeleton className="h-8 w-20 rounded-full" />
                    <Skeleton className="h-8 w-24 rounded-full" />
                </div>
                <Skeleton className="h-12 w-full rounded-xl mb-4" />
                <div className="flex gap-2 pt-3 border-t">
                    <Skeleton className="h-9 flex-1 rounded-md" />
                    <Skeleton className="h-9 w-9 rounded-md" />
                </div>
            </CardContent>
        </Card>
    )
}

export default function VendorResultsTable({
    runId,
    isRunning,
    onVendorClick,
}: VendorResultsTableProps) {
    const navigate = useNavigate()
    const [page, setPage] = useState(1)
    const [pageSize, setPageSize] = useState(10)
    const [sortBy, setSortBy] = useState('overall_score')
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
    const [searchQuery, setSearchQuery] = useState('')
    const [debouncedQuery, setDebouncedQuery] = useState('')

    // Debounce search
    const handleSearch = useCallback((value: string) => {
        setSearchQuery(value)
        const timer = setTimeout(() => {
            setDebouncedQuery(value)
            setPage(1)
        }, 300)
        return () => clearTimeout(timer)
    }, [])

    // Fetch vendors
    const { data, isLoading, isFetching } = useQuery({
        queryKey: ['run-vendors', runId, page, pageSize, sortBy, sortOrder, debouncedQuery],
        queryFn: () =>
            vendorsApi.listByRun(runId, {
                page,
                page_size: pageSize,
                sort_by: sortBy,
                sort_order: sortOrder,
                q: debouncedQuery || undefined,
            }),
        enabled: runId > 0,
        refetchInterval: isRunning ? 5000 : false,
    })

    const vendors = data?.vendors || []
    const total = data?.total || 0
    const totalPages = Math.ceil(total / pageSize)

    if (isLoading) {
        return (
            <div className="space-y-6">
                {/* Search skeleton */}
                <div className="flex items-center gap-4">
                    <Skeleton className="h-10 w-64" />
                    <Skeleton className="h-10 w-32" />
                    <Skeleton className="h-10 w-40 ml-auto" />
                </div>
                {/* Cards skeleton */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2, 3, 4].map((i) => (
                        <VendorCardSkeleton key={i} />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Search and filters */}
            <div className="flex flex-wrap items-center gap-4">
                <div className="relative flex-1 min-w-[200px] max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search vendors..."
                        value={searchQuery}
                        onChange={(e) => handleSearch(e.target.value)}
                        className="pl-9 bg-white"
                    />
                </div>

                <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setPage(1) }}>
                    <SelectTrigger className="w-40 bg-white">
                        <SelectValue placeholder="Sort by" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="overall_score">Overall Score</SelectItem>
                        <SelectItem value="fit_score">Fit Score</SelectItem>
                        <SelectItem value="trust_score">Trust Score</SelectItem>
                        <SelectItem value="quality_score">Quality Score</SelectItem>
                        <SelectItem value="name">Name</SelectItem>
                    </SelectContent>
                </Select>

                <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as 'asc' | 'desc')}>
                    <SelectTrigger className="w-32 bg-white">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="desc">Highest</SelectItem>
                        <SelectItem value="asc">Lowest</SelectItem>
                    </SelectContent>
                </Select>

                <Select value={String(pageSize)} onValueChange={(v) => { setPageSize(Number(v)); setPage(1) }}>
                    <SelectTrigger className="w-32 bg-white">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="6">6 / page</SelectItem>
                        <SelectItem value="10">10 / page</SelectItem>
                        <SelectItem value="20">20 / page</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Vendor cards grid */}
            {vendors.length === 0 ? (
                <div className="text-center py-16">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#F3F0EB] mb-4">
                        <Search className="w-8 h-8 text-[#A09A93]" />
                    </div>
                    <h3 className="text-lg font-semibold text-[#1A1816] mb-2">
                        {debouncedQuery ? 'No vendors match your search' : 'No vendors found yet'}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                        {debouncedQuery
                            ? 'Try adjusting your search terms'
                            : 'Vendors will appear here once the search completes'}
                    </p>
                </div>
            ) : (
                <>
                    {/* Results count */}
                    <div className="flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            Showing <span className="font-semibold text-foreground">{(page - 1) * pageSize + 1}</span> to{' '}
                            <span className="font-semibold text-foreground">{Math.min(page * pageSize, total)}</span> of{' '}
                            <span className="font-semibold text-foreground">{total}</span> vendors
                        </p>
                        {isFetching && (
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                Updating...
                            </div>
                        )}
                    </div>

                    {/* Cards grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {vendors.map((vendor) => (
                            <VendorCard
                                key={vendor.id}
                                vendor={vendor}
                                onQuickView={() => onVendorClick?.(vendor.id)}
                                onNavigate={() => navigate(`/vendors/${vendor.id}`)}
                            />
                        ))}
                    </div>

                    {/* Pagination */}
                    <div className="flex items-center justify-between pt-4">
                        <p className="text-sm text-muted-foreground">
                            Page {page} of {totalPages}
                        </p>
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={page === 1 || isFetching}
                                className="gap-1"
                            >
                                <ChevronLeft className="h-4 w-4" />
                                Previous
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                disabled={page >= totalPages || isFetching}
                                className="gap-1"
                            >
                                Next
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}
