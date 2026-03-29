/**
 * PricingOverviewCard - Shows pricing model overview
 */

import { motion } from 'framer-motion'
import { DollarSign, Check, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface PricingItem {
    vendor_name: string
    vendor_id: number
    pricing_model: string
    pricing_details?: string
    has_free_tier: boolean
    starting_price?: string
}

interface PricingOverviewCardProps {
    title?: string
    pricingData: PricingItem[]
    onVendorClick?: (vendorId: number) => void
    className?: string
}

const modelColors: Record<string, string> = {
    'subscription': 'bg-blue-100 text-blue-700',
    'per-user': 'bg-purple-100 text-purple-700',
    'usage-based': 'bg-green-100 text-green-700',
    'one-time': 'bg-amber-100 text-amber-700',
    'freemium': 'bg-emerald-100 text-emerald-700',
    'enterprise': 'bg-crimson/10 text-crimson',
    'custom': 'bg-gray-100 text-gray-700',
}

function getModelColor(model: string): string {
    const lowerModel = model.toLowerCase()
    for (const [key, value] of Object.entries(modelColors)) {
        if (lowerModel.includes(key)) return value
    }
    return 'bg-muted text-muted-foreground'
}

export function PricingOverviewCard({
    title = 'Pricing Overview',
    pricingData,
    onVendorClick,
    className,
}: PricingOverviewCardProps) {
    if (!pricingData || pricingData.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                'rounded-xl border bg-card shadow-sm overflow-hidden',
                className
            )}
        >
            {/* Header */}
            <div className="px-4 py-3 border-b bg-muted/30">
                <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-crimson" />
                    <h3 className="font-semibold text-sm">{title}</h3>
                </div>
            </div>

            {/* Pricing List */}
            <div className="divide-y">
                {pricingData.map((item, index) => (
                    <motion.div
                        key={item.vendor_id}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        className={cn(
                            'p-4 hover:bg-muted/20 transition-colors',
                            onVendorClick && 'cursor-pointer'
                        )}
                        onClick={() => onVendorClick?.(item.vendor_id)}
                    >
                        <div className="flex items-start justify-between gap-3">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <h4 className="font-medium text-sm truncate">
                                        {item.vendor_name}
                                    </h4>
                                    {item.has_free_tier && (
                                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] bg-green-100 text-green-700">
                                            <Check className="w-2.5 h-2.5" />
                                            Free Tier
                                        </span>
                                    )}
                                </div>
                                {item.pricing_details && (
                                    <p className="text-xs text-muted-foreground line-clamp-1">
                                        {item.pricing_details}
                                    </p>
                                )}
                            </div>
                            <div className="text-right flex-shrink-0">
                                <span className={cn(
                                    'inline-block px-2 py-1 rounded-full text-xs font-medium',
                                    getModelColor(item.pricing_model)
                                )}>
                                    {item.pricing_model}
                                </span>
                                {item.starting_price && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                        From {item.starting_price}
                                    </p>
                                )}
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>

            {/* Footer Tip */}
            <div className="px-4 py-2 border-t bg-muted/20 flex items-start gap-2">
                <Info className="w-3 h-3 text-muted-foreground mt-0.5 flex-shrink-0" />
                <p className="text-[10px] text-muted-foreground">
                    Pricing may vary based on features, volume, and contract terms. Contact vendors for detailed quotes.
                </p>
            </div>
        </motion.div>
    )
}

export default PricingOverviewCard
