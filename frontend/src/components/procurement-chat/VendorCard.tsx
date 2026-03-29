/**
 * VendorCard - Rich vendor card for chat display
 */

import { motion } from 'framer-motion'
import {
    ExternalLink,
    MapPin,
    Users,
    DollarSign,
    CheckCircle2,
    AlertCircle,
    XCircle,
    Bookmark,
    GitCompare,
    Eye,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { VendorCardData } from '@/lib/procurement-chat-api'

// Extract numeric price range from pricing_details text
function extractPriceRange(pricingDetails: string | null | undefined): string | null {
    if (!pricingDetails) return null

    // Pattern untuk mendeteksi harga dalam berbagai format
    const pricePatterns = [
        // IDR format: Rp 1.000.000 atau Rp1000000
        /Rp\.?\s*[\d.,]+/gi,
        // USD format: $100 atau USD 100
        /\$[\d.,]+|USD\s*[\d.,]+/gi,
        // Generic dengan currency: 100,000 IDR
        /[\d.,]+\s*(?:IDR|USD|EUR)/gi,
    ]

    const prices: string[] = []

    for (const pattern of pricePatterns) {
        const matches = pricingDetails.match(pattern)
        if (matches) {
            prices.push(...matches)
        }
    }

    if (prices.length === 0) return null

    // Clean up dan return
    const cleanPrices = prices.map(p => p.trim()).filter(Boolean)
    if (cleanPrices.length === 1) {
        return cleanPrices[0]
    } else if (cleanPrices.length >= 2) {
        return `${cleanPrices[0]} - ${cleanPrices[cleanPrices.length - 1]}`
    }

    return null
}

interface VendorCardProps {
    vendor: VendorCardData
    rank?: number
    onViewClick?: (vendorId: number) => void
    onShortlistClick?: (vendorId: number) => void
    onCompareClick?: (vendorId: number) => void
    compact?: boolean
    className?: string
}

function ScoreBadge({ score, label }: { score: number | null; label: string }) {
    if (score === null) return null

    const getColor = (s: number) => {
        if (s >= 80) return 'bg-green-500/10 text-green-600 border-green-500/20'
        if (s >= 60) return 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20'
        return 'bg-red-500/10 text-red-600 border-red-500/20'
    }

    return (
        <div className={cn('flex flex-col items-center p-2 rounded-lg border', getColor(score))}>
            <span className="text-lg font-bold">{Math.round(score)}</span>
            <span className="text-[10px] uppercase tracking-wide opacity-80">{label}</span>
        </div>
    )
}

function VendorLogo({ name, logoUrl, size = 'md' }: { name: string; logoUrl: string | null; size?: 'sm' | 'md' | 'lg' }) {
    const sizeClasses = {
        sm: 'w-10 h-10',
        md: 'w-14 h-14',
        lg: 'w-20 h-20',
    }

    if (logoUrl) {
        return (
            <img
                src={logoUrl}
                alt={`${name} logo`}
                className={cn(sizeClasses[size], 'rounded-lg object-contain bg-white border')}
                onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                }}
            />
        )
    }

    // Generate initials
    const initials = name
        .split(' ')
        .slice(0, 2)
        .map(w => w[0])
        .join('')
        .toUpperCase()

    // Generate consistent color from name
    const colors = [
        'from-blue-500 to-blue-600',
        'from-purple-500 to-purple-600',
        'from-green-500 to-green-600',
        'from-orange-500 to-orange-600',
        'from-pink-500 to-pink-600',
        'from-cyan-500 to-cyan-600',
    ]
    const colorIndex = name.charCodeAt(0) % colors.length

    return (
        <div
            className={cn(
                sizeClasses[size],
                'rounded-lg flex items-center justify-center text-white font-bold bg-gradient-to-br',
                colors[colorIndex]
            )}
        >
            {size === 'sm' ? initials[0] : initials}
        </div>
    )
}

export function VendorCard({
    vendor,
    rank,
    onViewClick,
    onShortlistClick,
    onCompareClick,
    compact = false,
    className,
}: VendorCardProps) {
    const rankBadge = rank ? (
        <div className="absolute -top-2 -left-2 z-10">
            <div className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold shadow-lg',
                rank === 1 ? 'bg-gradient-to-br from-yellow-400 to-yellow-600' :
                rank === 2 ? 'bg-gradient-to-br from-gray-300 to-gray-500' :
                rank === 3 ? 'bg-gradient-to-br from-orange-400 to-orange-600' :
                'bg-gradient-to-br from-primary/80 to-primary'
            )}>
                {rank <= 3 ? ['', '1', '2', '3'][rank] : rank}
            </div>
        </div>
    ) : null

    if (compact) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn(
                    'relative flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors cursor-pointer',
                    className
                )}
                onClick={() => onViewClick?.(vendor.id)}
            >
                {rankBadge}
                <VendorLogo name={vendor.name} logoUrl={vendor.logo_url} size="sm" />
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <span className="font-medium truncate">{vendor.name}</span>
                        {vendor.website && (
                            <ExternalLink className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                        )}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                        {vendor.industry || vendor.location || 'N/A'}
                    </div>
                </div>
                {vendor.overall_score && (
                    <Badge variant="secondary" className="ml-auto">
                        {Math.round(vendor.overall_score)}
                    </Badge>
                )}
            </motion.div>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                'relative rounded-xl border bg-card overflow-hidden shadow-sm hover:shadow-md transition-shadow',
                className
            )}
        >
            {rankBadge}

            {/* Header */}
            <div className="p-4 pb-3">
                <div className="flex items-start gap-4">
                    <VendorLogo name={vendor.name} logoUrl={vendor.logo_url} size="md" />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-lg truncate">{vendor.name}</h3>
                            {vendor.website && (
                                <a
                                    href={vendor.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-muted-foreground hover:text-primary"
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <ExternalLink className="w-4 h-4" />
                                </a>
                            )}
                        </div>
                        {vendor.industry && (
                            <p className="text-sm text-muted-foreground">{vendor.industry}</p>
                        )}
                        {vendor.description && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                {vendor.description}
                            </p>
                        )}
                    </div>
                </div>
            </div>

            {/* Scores */}
            <div className="px-4 pb-3">
                <div className="flex gap-2">
                    <ScoreBadge score={vendor.overall_score} label="Overall" />
                    <ScoreBadge score={vendor.fit_score} label="Fit" />
                    <ScoreBadge score={vendor.trust_score} label="Trust" />
                </div>
            </div>

            {/* Criteria Match */}
            {(vendor.criteria_matched.length > 0 || vendor.criteria_partial.length > 0 || vendor.criteria_missing.length > 0) && (
                <div className="px-4 pb-3 space-y-2">
                    {vendor.criteria_matched.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {vendor.criteria_matched.slice(0, 3).map((c, i) => (
                                <Badge key={i} variant="outline" className="bg-green-500/10 text-green-700 border-green-500/30 text-xs">
                                    <CheckCircle2 className="w-3 h-3 mr-1" />
                                    {c}
                                </Badge>
                            ))}
                        </div>
                    )}
                    {vendor.criteria_partial.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {vendor.criteria_partial.slice(0, 2).map((c, i) => (
                                <Badge key={i} variant="outline" className="bg-yellow-500/10 text-yellow-700 border-yellow-500/30 text-xs">
                                    <AlertCircle className="w-3 h-3 mr-1" />
                                    {c}
                                </Badge>
                            ))}
                        </div>
                    )}
                    {vendor.criteria_missing.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                            {vendor.criteria_missing.slice(0, 2).map((c, i) => (
                                <Badge key={i} variant="outline" className="bg-red-500/10 text-red-700 border-red-500/30 text-xs">
                                    <XCircle className="w-3 h-3 mr-1" />
                                    {c}
                                </Badge>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Price Display - Only show if we have actual numeric prices */}
            {(() => {
                const priceDisplay = extractPriceRange(vendor.pricing_details)
                // Only show price section if we have actual numeric prices
                // Don't show just "one-time" or "contact-sales" without a price
                if (priceDisplay) {
                    return (
                        <div className="px-4 pb-3">
                            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200/50">
                                <DollarSign className="w-4 h-4 text-amber-600 flex-shrink-0" />
                                <div className="flex flex-wrap items-center gap-2">
                                    <span className="text-sm font-semibold text-amber-700">
                                        {priceDisplay}
                                    </span>
                                    {vendor.pricing_model && vendor.pricing_model !== 'contact-sales' && (
                                        <span className="text-xs text-amber-600">
                                            ({vendor.pricing_model})
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    )
                }
                return null
            })()}

            {/* Quick Stats */}
            <div className="px-4 pb-3 flex flex-wrap gap-3 text-sm text-muted-foreground">
                {vendor.employee_count && (
                    <div className="flex items-center gap-1">
                        <Users className="w-4 h-4" />
                        <span>{vendor.employee_count}</span>
                    </div>
                )}
                {(vendor.location || vendor.country) && (
                    <div className="flex items-center gap-1">
                        <MapPin className="w-4 h-4" />
                        <span>{vendor.location || vendor.country}</span>
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="px-4 pb-4 flex gap-2">
                <Button
                    size="sm"
                    variant="default"
                    className="flex-1"
                    onClick={() => onViewClick?.(vendor.id)}
                >
                    <Eye className="w-4 h-4 mr-1" />
                    View Details
                </Button>
                <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onShortlistClick?.(vendor.id)}
                >
                    <Bookmark className="w-4 h-4" />
                </Button>
                <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onCompareClick?.(vendor.id)}
                >
                    <GitCompare className="w-4 h-4" />
                </Button>
            </div>
        </motion.div>
    )
}

export function VendorCardGrid({
    vendors,
    onViewClick,
    onShortlistClick,
    onCompareClick,
}: {
    vendors: VendorCardData[]
    onViewClick?: (vendorId: number) => void
    onShortlistClick?: (vendorId: number) => void
    onCompareClick?: (vendorId: number) => void
}) {
    return (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            {vendors.map((vendor, index) => (
                <VendorCard
                    key={vendor.id}
                    vendor={vendor}
                    rank={index + 1}
                    onViewClick={onViewClick}
                    onShortlistClick={onShortlistClick}
                    onCompareClick={onCompareClick}
                />
            ))}
        </div>
    )
}

export function VendorMiniList({
    vendors,
    onViewClick,
}: {
    vendors: VendorCardData[]
    onViewClick?: (vendorId: number) => void
}) {
    return (
        <div className="space-y-2">
            {vendors.map((vendor, index) => (
                <VendorCard
                    key={vendor.id}
                    vendor={vendor}
                    rank={index + 1}
                    onViewClick={onViewClick}
                    compact
                />
            ))}
        </div>
    )
}
