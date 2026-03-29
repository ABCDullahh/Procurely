/**
 * VendorHighlightCard - Elegant vendor display card for chat
 */

import { motion } from 'framer-motion'
import {
    ExternalLink, MapPin, Users, Calendar,
    TrendingUp, Award, ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { VendorCardData } from '@/lib/procurement-chat-api'

interface VendorHighlightCardProps {
    vendor: VendorCardData
    rank?: number
    onViewClick?: (vendorId: number) => void
    onCompareClick?: (vendorId: number) => void
    isHighlighted?: boolean
    className?: string
}

function ScoreRing({ score, label, color }: { score: number; label: string; color: string }) {
    const circumference = 2 * Math.PI * 18
    const progress = (score / 100) * circumference

    return (
        <div className="flex flex-col items-center">
            <div className="relative w-12 h-12">
                <svg className="w-12 h-12 transform -rotate-90">
                    <circle
                        cx="24"
                        cy="24"
                        r="18"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="4"
                        className="text-muted/20"
                    />
                    <circle
                        cx="24"
                        cy="24"
                        r="18"
                        fill="none"
                        stroke={color}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={circumference - progress}
                        className="transition-all duration-500"
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-xs font-bold">{score}</span>
                </div>
            </div>
            <span className="text-[10px] text-muted-foreground mt-1">{label}</span>
        </div>
    )
}

function RankBadge({ rank }: { rank: number }) {
    const colors = {
        1: 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white',
        2: 'bg-gradient-to-br from-gray-300 to-gray-500 text-white',
        3: 'bg-gradient-to-br from-amber-600 to-amber-800 text-white',
    }
    const badges = ['', '1st', '2nd', '3rd']

    if (rank > 3) return null

    return (
        <div className={cn(
            'absolute -top-2 -left-2 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold shadow-lg z-10',
            colors[rank as keyof typeof colors]
        )}>
            {badges[rank]}
        </div>
    )
}

export function VendorHighlightCard({
    vendor,
    rank,
    onViewClick,
    onCompareClick,
    isHighlighted = false,
    className,
}: VendorHighlightCardProps) {
    const getScoreColor = (score: number | null) => {
        if (!score) return '#9ca3af'
        if (score >= 80) return '#22c55e'
        if (score >= 60) return '#eab308'
        return '#f97316'
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2 }}
            className={cn(
                'relative rounded-xl border bg-card shadow-sm overflow-hidden transition-all',
                isHighlighted && 'ring-2 ring-crimson/50 shadow-md',
                className
            )}
        >
            {rank && <RankBadge rank={rank} />}

            {/* Header with Logo */}
            <div className="p-4 border-b bg-gradient-to-r from-muted/30 to-transparent">
                <div className="flex items-start gap-3">
                    {/* Logo */}
                    <div className="w-14 h-14 rounded-xl overflow-hidden bg-white border flex-shrink-0 flex items-center justify-center">
                        {vendor.logo_url ? (
                            <img
                                src={vendor.logo_url}
                                alt={vendor.name}
                                className="w-full h-full object-contain p-1"
                            />
                        ) : (
                            <div className="w-full h-full bg-gradient-to-br from-crimson/80 to-crimson flex items-center justify-center">
                                <span className="text-white font-bold text-lg">
                                    {vendor.name.charAt(0)}
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-base truncate">
                            {vendor.name}
                        </h4>
                        {vendor.industry && (
                            <p className="text-xs text-muted-foreground">
                                {vendor.industry}
                            </p>
                        )}
                        <div className="flex items-center gap-3 mt-1">
                            {vendor.location && (
                                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                                    <MapPin className="w-3 h-3" />
                                    {vendor.location}
                                </span>
                            )}
                            {vendor.website && (
                                <a
                                    href={vendor.website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 text-xs text-crimson hover:underline"
                                >
                                    <ExternalLink className="w-3 h-3" />
                                    Website
                                </a>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Scores */}
            <div className="px-4 py-3 border-b">
                <div className="flex justify-around">
                    <ScoreRing
                        score={vendor.overall_score || 0}
                        label="Overall"
                        color={getScoreColor(vendor.overall_score)}
                    />
                    <ScoreRing
                        score={vendor.fit_score || 0}
                        label="Fit"
                        color={getScoreColor(vendor.fit_score)}
                    />
                    <ScoreRing
                        score={vendor.trust_score || 0}
                        label="Trust"
                        color={getScoreColor(vendor.trust_score)}
                    />
                </div>
            </div>

            {/* Quick Info */}
            <div className="px-4 py-3 space-y-2">
                {vendor.description && (
                    <p className="text-xs text-muted-foreground line-clamp-2">
                        {vendor.description}
                    </p>
                )}

                <div className="flex flex-wrap gap-2">
                    {vendor.pricing_model && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-700">
                            <TrendingUp className="w-3 h-3" />
                            {vendor.pricing_model}
                        </span>
                    )}
                    {vendor.employee_count && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-700">
                            <Users className="w-3 h-3" />
                            {vendor.employee_count}
                        </span>
                    )}
                    {vendor.founded_year && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-purple-50 text-purple-700">
                            <Calendar className="w-3 h-3" />
                            Est. {vendor.founded_year}
                        </span>
                    )}
                </div>

                {/* Criteria Badges */}
                {vendor.criteria_matched && vendor.criteria_matched.length > 0 && (
                    <div className="pt-2 border-t mt-2">
                        <div className="flex items-center gap-1 mb-1">
                            <Award className="w-3 h-3 text-green-600" />
                            <span className="text-[10px] font-medium text-green-700">
                                Matches {vendor.criteria_matched.length} criteria
                            </span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {vendor.criteria_matched.slice(0, 3).map((c, i) => (
                                <span
                                    key={i}
                                    className="px-1.5 py-0.5 rounded text-[10px] bg-green-100 text-green-800"
                                >
                                    {c}
                                </span>
                            ))}
                            {vendor.criteria_matched.length > 3 && (
                                <span className="text-[10px] text-muted-foreground">
                                    +{vendor.criteria_matched.length - 3} more
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Actions */}
            <div className="px-4 py-3 border-t bg-muted/20 flex gap-2">
                <Button
                    size="sm"
                    className="flex-1 bg-crimson hover:bg-crimson/90 text-white"
                    onClick={() => onViewClick?.(vendor.id)}
                >
                    View Details
                    <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
                {onCompareClick && (
                    <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onCompareClick(vendor.id)}
                    >
                        Compare
                    </Button>
                )}
            </div>
        </motion.div>
    )
}

export function VendorHighlightGrid({
    vendors,
    onViewClick,
    onCompareClick,
    className,
}: {
    vendors: VendorCardData[]
    onViewClick?: (vendorId: number) => void
    onCompareClick?: (vendorId: number) => void
    className?: string
}) {
    return (
        <div className={cn('grid gap-4 sm:grid-cols-2', className)}>
            {vendors.map((vendor, index) => (
                <VendorHighlightCard
                    key={vendor.id}
                    vendor={vendor}
                    rank={index < 3 ? index + 1 : undefined}
                    onViewClick={onViewClick}
                    onCompareClick={onCompareClick}
                    isHighlighted={index === 0}
                />
            ))}
        </div>
    )
}

export default VendorHighlightCard
