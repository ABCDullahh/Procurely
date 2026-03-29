/**
 * CompareMatrix component for side-by-side vendor comparison.
 */

import { Building2, Download } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface VendorInComparison {
    id: number
    name: string
    website: string | null
    logo_url: string | null
    overall_score: number | null
    fit_score: number | null
    trust_score: number | null
}

interface CompareMatrixProps {
    vendors: VendorInComparison[]
    open: boolean
    onClose: () => void
}

interface ComparisonRow {
    label: string
    getValue: (vendor: VendorInComparison) => string | number | null
    isBestHigher?: boolean // true = higher is better
    format?: 'number' | 'score' | 'text'
}

const comparisonRows: ComparisonRow[] = [
    {
        label: 'Overall Score',
        getValue: (v) => v.overall_score,
        isBestHigher: true,
        format: 'score',
    },
    {
        label: 'Fit Score',
        getValue: (v) => v.fit_score,
        isBestHigher: true,
        format: 'score',
    },
    {
        label: 'Trust Score',
        getValue: (v) => v.trust_score,
        isBestHigher: true,
        format: 'score',
    },
    {
        label: 'Website',
        getValue: (v) => v.website,
        format: 'text',
    },
]

export default function CompareMatrix({ vendors, open, onClose }: CompareMatrixProps) {
    // Find best values for highlighting
    const getBestValue = (row: ComparisonRow): number | null => {
        const values = vendors
            .map((v) => row.getValue(v))
            .filter((v): v is number => typeof v === 'number')

        if (values.length === 0) return null
        return row.isBestHigher ? Math.max(...values) : Math.min(...values)
    }

    // Export to CSV
    const handleExportCSV = () => {
        const headers = ['Metric', ...vendors.map((v) => v.name)]
        const rows = comparisonRows.map((row) => [
            row.label,
            ...vendors.map((v) => {
                const val = row.getValue(v)
                return val != null ? String(val) : '-'
            }),
        ])

        const csvContent = [headers, ...rows].map((r) => r.join(',')).join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'vendor-comparison.csv'
        a.click()
        URL.revokeObjectURL(url)
    }

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl max-h-[90vh]">
                <DialogHeader>
                    <div className="flex items-center justify-between">
                        <DialogTitle>Compare Vendors</DialogTitle>
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="sm" onClick={handleExportCSV}>
                                <Download className="mr-2 h-4 w-4" />
                                Export CSV
                            </Button>
                        </div>
                    </div>
                </DialogHeader>

                <ScrollArea className="h-[calc(90vh-150px)]">
                    <div className="min-w-max">
                        {/* Header row with vendor info */}
                        <div className="grid gap-4" style={{
                            gridTemplateColumns: `150px repeat(${vendors.length}, minmax(150px, 1fr))`
                        }}>
                            <div className="font-medium text-muted-foreground p-3 bg-muted rounded-lg">
                                Vendor
                            </div>
                            {vendors.map((vendor) => (
                                <div
                                    key={vendor.id}
                                    className="p-3 bg-muted rounded-lg text-center"
                                >
                                    {vendor.logo_url ? (
                                        <img
                                            src={vendor.logo_url}
                                            alt={vendor.name}
                                            className="h-10 w-10 rounded mx-auto object-contain bg-white border"
                                        />
                                    ) : (
                                        <div className="h-10 w-10 rounded mx-auto bg-primary/10 flex items-center justify-center">
                                            <Building2 className="h-5 w-5 text-primary" />
                                        </div>
                                    )}
                                    <p className="font-semibold mt-2 text-sm truncate">
                                        {vendor.name}
                                    </p>
                                </div>
                            ))}
                        </div>

                        {/* Comparison rows */}
                        <div className="mt-4 space-y-2">
                            {comparisonRows.map((row) => {
                                const bestValue = getBestValue(row)

                                return (
                                    <div
                                        key={row.label}
                                        className="grid gap-4 items-center"
                                        style={{
                                            gridTemplateColumns: `150px repeat(${vendors.length}, minmax(150px, 1fr))`
                                        }}
                                    >
                                        <div className="font-medium text-sm p-3">
                                            {row.label}
                                        </div>
                                        {vendors.map((vendor) => {
                                            const value = row.getValue(vendor)
                                            const isBest =
                                                row.isBestHigher &&
                                                typeof value === 'number' &&
                                                value === bestValue

                                            return (
                                                <div
                                                    key={vendor.id}
                                                    className={`p-3 rounded-lg text-center ${isBest
                                                        ? 'bg-green-50 border border-green-200'
                                                        : 'bg-muted/50'
                                                        }`}
                                                >
                                                    {row.format === 'score' &&
                                                        typeof value === 'number' ? (
                                                        <Badge
                                                            variant={isBest ? 'default' : 'secondary'}
                                                            className={
                                                                isBest
                                                                    ? 'bg-green-500'
                                                                    : ''
                                                            }
                                                        >
                                                            {value.toFixed(0)}
                                                        </Badge>
                                                    ) : row.format === 'text' && value ? (
                                                        <a
                                                            href={String(value)}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-primary hover:underline text-sm truncate block"
                                                        >
                                                            {String(value).replace(/^https?:\/\//, '')}
                                                        </a>
                                                    ) : (
                                                        <span className="text-muted-foreground text-sm">
                                                            {value != null ? String(value) : '-'}
                                                        </span>
                                                    )}
                                                </div>
                                            )
                                        })}
                                    </div>
                                )
                            })}
                        </div>
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    )
}
