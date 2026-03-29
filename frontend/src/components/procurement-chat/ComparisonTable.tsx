/**
 * ComparisonTable - Side-by-side vendor comparison for chat
 */

import { motion } from 'framer-motion'
import { Download, ExternalLink, Crown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area'
import { cn } from '@/lib/utils'
import type { ComparisonData } from '@/lib/procurement-chat-api'

interface ComparisonTableProps {
    data: ComparisonData
    onExportCSV?: () => void
    onVendorClick?: (vendorId: number) => void
    className?: string
}

function VendorLogo({ name, logoUrl }: { name: string; logoUrl: string | null }) {
    if (logoUrl) {
        return (
            <img
                src={logoUrl}
                alt={`${name} logo`}
                className="w-10 h-10 rounded-lg object-contain bg-white border"
                onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none'
                }}
            />
        )
    }

    const initials = name
        .split(' ')
        .slice(0, 2)
        .map(w => w[0])
        .join('')
        .toUpperCase()

    const colors = [
        'from-blue-500 to-blue-600',
        'from-purple-500 to-purple-600',
        'from-green-500 to-green-600',
        'from-orange-500 to-orange-600',
    ]
    const colorIndex = name.charCodeAt(0) % colors.length

    return (
        <div
            className={cn(
                'w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm bg-gradient-to-br',
                colors[colorIndex]
            )}
        >
            {initials}
        </div>
    )
}

function ScoreCell({ value, isBest }: { value: unknown; isBest: boolean }) {
    if (value === null || value === undefined) {
        return <span className="text-muted-foreground">-</span>
    }

    const numValue = typeof value === 'number' ? value : null

    if (numValue !== null) {
        const getScoreColor = (score: number) => {
            if (score >= 80) return 'text-green-600'
            if (score >= 60) return 'text-yellow-600'
            return 'text-red-600'
        }

        return (
            <div className={cn('flex items-center gap-1', isBest && 'font-bold')}>
                <span className={cn('text-lg', getScoreColor(numValue))}>
                    {Math.round(numValue)}
                </span>
                {isBest && <Crown className="w-4 h-4 text-yellow-500" />}
            </div>
        )
    }

    return <span className="text-sm">{String(value)}</span>
}

export function ComparisonTable({
    data,
    onExportCSV,
    onVendorClick,
    className,
}: ComparisonTableProps) {
    const { vendors, rows } = data

    if (vendors.length === 0) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                No vendors to compare
            </div>
        )
    }

    const handleExportCSV = () => {
        // Generate CSV content
        const headers = ['Metric', ...vendors.map(v => v.name)]
        const csvRows = rows.map(row => {
            const values = vendors.map(v => {
                const val = row.values[String(v.id)]
                return val !== null && val !== undefined ? String(val) : ''
            })
            return [row.metric, ...values]
        })

        const csvContent = [headers, ...csvRows]
            .map(row => row.map(cell => `"${cell}"`).join(','))
            .join('\n')

        // Download
        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `vendor-comparison-${Date.now()}.csv`
        a.click()
        URL.revokeObjectURL(url)

        onExportCSV?.()
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn('rounded-xl border bg-card overflow-hidden', className)}
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
                <h3 className="font-semibold">Vendor Comparison</h3>
                <Button size="sm" variant="outline" onClick={handleExportCSV}>
                    <Download className="w-4 h-4 mr-1" />
                    Export CSV
                </Button>
            </div>

            {/* Table */}
            <ScrollArea className="w-full">
                <div className="min-w-max">
                    <table className="w-full">
                        {/* Vendor Headers */}
                        <thead>
                            <tr className="border-b">
                                <th className="w-40 p-3 text-left font-medium text-muted-foreground bg-muted/20 sticky left-0">
                                    Metric
                                </th>
                                {vendors.map((vendor, index) => (
                                    <th
                                        key={vendor.id}
                                        className={cn(
                                            'p-3 text-center min-w-[140px]',
                                            index === 0 && 'bg-primary/5'
                                        )}
                                    >
                                        <div
                                            className="flex flex-col items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
                                            onClick={() => onVendorClick?.(vendor.id)}
                                        >
                                            <VendorLogo name={vendor.name} logoUrl={vendor.logo_url} />
                                            <div className="flex items-center gap-1">
                                                <span className="font-medium text-sm">{vendor.name}</span>
                                                {vendor.website && (
                                                    <ExternalLink className="w-3 h-3 text-muted-foreground" />
                                                )}
                                            </div>
                                            {index === 0 && (
                                                <Badge variant="default" className="text-[10px]">
                                                    <Crown className="w-3 h-3 mr-1" />
                                                    Top Pick
                                                </Badge>
                                            )}
                                        </div>
                                    </th>
                                ))}
                            </tr>
                        </thead>

                        {/* Data Rows */}
                        <tbody>
                            {rows.map((row, rowIndex) => (
                                <tr
                                    key={row.metric}
                                    className={cn(
                                        'border-b last:border-b-0',
                                        rowIndex % 2 === 0 && 'bg-muted/10'
                                    )}
                                >
                                    <td className="p-3 font-medium text-sm text-muted-foreground bg-muted/20 sticky left-0">
                                        {row.metric}
                                    </td>
                                    {vendors.map((vendor, index) => {
                                        const value = row.values[String(vendor.id)]
                                        const isBest = row.best_vendor_id === vendor.id

                                        return (
                                            <td
                                                key={vendor.id}
                                                className={cn(
                                                    'p-3 text-center',
                                                    index === 0 && 'bg-primary/5',
                                                    isBest && 'bg-green-500/10'
                                                )}
                                            >
                                                <ScoreCell value={value} isBest={isBest} />
                                            </td>
                                        )
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <ScrollBar orientation="horizontal" />
            </ScrollArea>
        </motion.div>
    )
}

export function CompactComparisonTable({
    data,
    onVendorClick,
}: {
    data: ComparisonData
    onVendorClick?: (vendorId: number) => void
}) {
    const { vendors, rows } = data

    // Only show score rows for compact view
    const scoreRows = rows.filter(r =>
        r.metric.toLowerCase().includes('score')
    )

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border bg-card overflow-hidden"
        >
            <div className="grid gap-px bg-border" style={{ gridTemplateColumns: `auto repeat(${vendors.length}, 1fr)` }}>
                {/* Header row */}
                <div className="bg-muted/50 p-2 text-xs font-medium text-muted-foreground">
                    Vendor
                </div>
                {vendors.map((vendor) => (
                    <div
                        key={vendor.id}
                        className="bg-card p-2 text-center cursor-pointer hover:bg-accent/50 transition-colors"
                        onClick={() => onVendorClick?.(vendor.id)}
                    >
                        <span className="font-medium text-sm truncate block">{vendor.name}</span>
                    </div>
                ))}

                {/* Score rows */}
                {scoreRows.map((row) => (
                    <>
                        <div key={`${row.metric}-label`} className="bg-muted/50 p-2 text-xs font-medium text-muted-foreground">
                            {row.metric}
                        </div>
                        {vendors.map((vendor) => {
                            const value = row.values[String(vendor.id)]
                            const isBest = row.best_vendor_id === vendor.id
                            const numValue = typeof value === 'number' ? value : null

                            return (
                                <div
                                    key={`${row.metric}-${vendor.id}`}
                                    className={cn(
                                        'bg-card p-2 text-center',
                                        isBest && 'bg-green-500/10'
                                    )}
                                >
                                    {numValue !== null ? (
                                        <span className={cn(
                                            'font-bold',
                                            numValue >= 80 ? 'text-green-600' :
                                            numValue >= 60 ? 'text-yellow-600' : 'text-red-600'
                                        )}>
                                            {Math.round(numValue)}
                                        </span>
                                    ) : (
                                        <span className="text-muted-foreground">-</span>
                                    )}
                                </div>
                            )
                        })}
                    </>
                ))}
            </div>
        </motion.div>
    )
}
