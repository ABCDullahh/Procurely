import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { X, ExternalLink, Copy, Building2, Mail, Phone, Globe, Sparkles, Target, CheckCircle, BookOpen, DollarSign, ShoppingCart, Star, MapPin, Shield, FileText, Link2, AlertCircle } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from '@/components/ui/sheet'
import { vendorsApi, VendorDetail, VendorEvidence, VendorSource } from '@/lib/vendors-api'

interface VendorQuickViewProps {
    vendorId: number | null
    open: boolean
    onClose: () => void
}

export default function VendorQuickView({
    vendorId,
    open,
    onClose,
}: VendorQuickViewProps) {
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState('overview')

    const { data: vendor, isLoading: vendorLoading } = useQuery({
        queryKey: ['vendor', vendorId],
        queryFn: () => vendorsApi.get(vendorId!),
        enabled: !!vendorId && open,
    })

    const { data: evidenceData, isLoading: evidenceLoading } = useQuery({
        queryKey: ['vendor-evidence', vendorId],
        queryFn: () => vendorsApi.getEvidence(vendorId!),
        enabled: !!vendorId && open && activeTab === 'evidence',
    })

    const { data: sourcesData, isLoading: sourcesLoading } = useQuery({
        queryKey: ['vendor-sources', vendorId],
        queryFn: () => vendorsApi.getSources(vendorId!),
        enabled: !!vendorId && open && activeTab === 'sources',
    })

    const handleCopySummary = () => {
        if (!vendor) return
        const parts = [
            vendor.name,
            vendor.website || '',
            vendor.description || '',
            vendor.pricing_details ? `Pricing: ${vendor.pricing_details}` : '',
            vendor.phone ? `Phone: ${vendor.phone}` : '',
            vendor.email ? `Email: ${vendor.email}` : '',
            vendor.location ? `Location: ${vendor.location}` : '',
        ].filter(Boolean)
        navigator.clipboard.writeText(parts.join('\n'))
        toast.success('Vendor info copied to clipboard')
    }

    const evidenceCount = evidenceData?.evidence?.length || 0
    const sourcesCount = sourcesData?.sources?.length || 0

    return (
        <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
            <SheetContent className="w-[480px] sm:w-[560px] p-0 flex flex-col overflow-hidden">
                {/* Header */}
                <SheetHeader className="px-6 pt-6 pb-4 border-b shrink-0">
                    <div className="flex items-start gap-3">
                        {vendor?.logo_url ? (
                            <img src={vendor.logo_url} alt={vendor.name}
                                className="h-12 w-12 rounded-xl object-contain bg-white border shadow-sm" />
                        ) : (
                            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center border">
                                <Building2 className="h-5 w-5 text-primary" />
                            </div>
                        )}
                        <div className="flex-1 min-w-0">
                            <SheetTitle className="text-left text-lg">{vendor?.name || 'Loading...'}</SheetTitle>
                            <SheetDescription className="text-left">
                                {vendor?.industry || 'Vendor details'}
                            </SheetDescription>
                        </div>
                        <Button variant="ghost" size="icon" onClick={onClose} className="shrink-0 -mt-1">
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                </SheetHeader>

                {/* Tabs */}
                <div className="px-6 pt-4 shrink-0">
                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList className="grid w-full grid-cols-3 h-9">
                            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
                            <TabsTrigger value="evidence" className="text-xs">
                                Evidence {evidenceCount > 0 && <Badge variant="secondary" className="ml-1 h-4 px-1 text-[10px]">{evidenceCount}</Badge>}
                            </TabsTrigger>
                            <TabsTrigger value="sources" className="text-xs">
                                Sources {sourcesCount > 0 && <Badge variant="secondary" className="ml-1 h-4 px-1 text-[10px]">{sourcesCount}</Badge>}
                            </TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>

                {/* Content */}
                <ScrollArea className="flex-1 min-h-0 overflow-x-hidden">
                    <div className="px-6 py-4 overflow-hidden">
                        {activeTab === 'overview' && (
                            vendorLoading ? <OverviewSkeleton /> : vendor ? <OverviewTab vendor={vendor} /> : null
                        )}
                        {activeTab === 'evidence' && (
                            evidenceLoading ? <EvidenceSkeleton /> : <EvidenceTab evidence={evidenceData?.evidence || []} />
                        )}
                        {activeTab === 'sources' && (
                            sourcesLoading ? <SourcesSkeleton /> : <SourcesTab sources={sourcesData?.sources || []} />
                        )}
                    </div>
                </ScrollArea>

                {/* Footer Actions */}
                <div className="px-6 py-3 border-t bg-muted/30 flex gap-2 shrink-0">
                    <Button onClick={() => { navigate(`/vendors/${vendorId}`); onClose() }} className="flex-1 h-9" size="sm">
                        <ExternalLink className="mr-2 h-3.5 w-3.5" />
                        Open Profile
                    </Button>
                    <Button variant="outline" onClick={handleCopySummary} size="sm" className="h-9">
                        <Copy className="mr-2 h-3.5 w-3.5" />
                        Copy
                    </Button>
                </div>
            </SheetContent>
        </Sheet>
    )
}

/* ============================== */
/*         OVERVIEW TAB           */
/* ============================== */

function OverviewTab({ vendor }: { vendor: VendorDetail }) {
    return (
        <div className="space-y-5">
            {/* Score Cards */}
            {vendor.metrics && (
                <div className="grid grid-cols-3 gap-3">
                    <ScoreCircle label="Overall" score={vendor.metrics.overall_score} color="emerald" />
                    <ScoreCircle label="Fit" score={vendor.metrics.fit_score} color="blue" />
                    <ScoreCircle label="Trust" score={vendor.metrics.trust_score} color="purple" />
                </div>
            )}

            {/* Score Explanation */}
            {vendor.metrics && (
                <div className="rounded-lg border bg-muted/20 p-3">
                    <p className="text-[11px] text-muted-foreground leading-relaxed">
                        <span className="font-medium text-foreground">Score breakdown:</span>{' '}
                        Fit ({vendor.metrics.fit_score?.toFixed(0) || 0}) × 45% + Trust ({vendor.metrics.trust_score?.toFixed(0) || 0}) × 30% + Quality ({vendor.metrics.quality_score?.toFixed(0) || 0}) × 25% = <span className="font-semibold text-foreground">{vendor.metrics.overall_score?.toFixed(0) || 0}</span>
                    </p>
                </div>
            )}

            {/* Price Range */}
            {vendor.pricing_details && (
                <div className="rounded-lg border p-3 bg-emerald-50/50">
                    <div className="flex items-center gap-2 mb-1.5">
                        <DollarSign className="h-4 w-4 text-emerald-600" />
                        <h4 className="text-sm font-medium">Pricing</h4>
                    </div>
                    <p className="text-sm font-semibold text-emerald-700 break-words">
                        {vendor.pricing_details}
                    </p>
                    {vendor.pricing_model && (
                        <Badge variant="outline" className="mt-2 text-[10px] capitalize">{vendor.pricing_model}</Badge>
                    )}
                </div>
            )}

            {/* Research Quality */}
            {vendor.metrics && (
                <div className="rounded-lg border p-3 space-y-2.5">
                    <div className="flex items-center gap-2">
                        <Sparkles className="h-4 w-4 text-amber-500" />
                        <h4 className="text-sm font-medium">Research Quality</h4>
                    </div>
                    <div className="grid grid-cols-2 gap-2.5">
                        <MiniStat icon={CheckCircle} label="Completeness" value={`${(vendor.metrics.completeness_pct || 0).toFixed(0)}%`}
                            color={getQualityColor(vendor.metrics.completeness_pct)} />
                        <MiniStat icon={Target} label="Confidence" value={`${(vendor.metrics.confidence_pct || 0).toFixed(0)}%`}
                            color={getQualityColor(vendor.metrics.confidence_pct)} />
                        <MiniStat icon={BookOpen} label="Sources" value={`${vendor.metrics.source_diversity || 0} unique`} color="text-blue-600" />
                        <MiniStat icon={Shield} label="Evidence" value={`${vendor.metrics.evidence_count || 0} points`} color="text-purple-600" />
                    </div>
                </div>
            )}

            {/* About */}
            {vendor.description && (
                <div>
                    <h4 className="text-sm font-medium mb-1.5">About</h4>
                    <p className="text-sm text-muted-foreground leading-relaxed">{vendor.description}</p>
                </div>
            )}

            {/* Contact */}
            <div className="space-y-2">
                {vendor.website && (
                    <ContactRow icon={Globe} label="Website">
                        <a href={vendor.website} target="_blank" rel="noopener noreferrer"
                            className="text-primary hover:underline text-sm flex items-center gap-1 truncate">
                            {vendor.website.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '')}
                            <ExternalLink className="h-3 w-3 shrink-0" />
                        </a>
                    </ContactRow>
                )}
                {vendor.email && (
                    <ContactRow icon={Mail} label="Email">
                        <a href={`mailto:${vendor.email}`} className="text-primary hover:underline text-sm">{vendor.email}</a>
                    </ContactRow>
                )}
                {vendor.phone && (
                    <ContactRow icon={Phone} label="Phone">
                        <a href={`tel:${vendor.phone}`} className="text-sm font-medium">{vendor.phone}</a>
                    </ContactRow>
                )}
                {vendor.location && (
                    <ContactRow icon={MapPin} label="Location">
                        <span className="text-sm">{vendor.location}{vendor.country ? `, ${vendor.country}` : ''}</span>
                    </ContactRow>
                )}
            </div>

            {/* Shopping Data */}
            {vendor.shopping_data && vendor.shopping_data.products && vendor.shopping_data.products.length > 0 && (
                <div className="rounded-lg border p-3 bg-blue-50/50 space-y-2">
                    <div className="flex items-center gap-2">
                        <ShoppingCart className="h-4 w-4 text-blue-600" />
                        <h4 className="text-sm font-medium">Market Prices</h4>
                    </div>
                    {vendor.shopping_data.products.slice(0, 3).map((p, i) => (
                        <a key={i} href={p.link} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 text-sm">
                            {p.thumbnail && <img src={p.thumbnail} alt="" className="w-8 h-8 rounded object-cover" />}
                            <div className="flex-1 min-w-0">
                                <p className="truncate text-xs">{p.title}</p>
                                <span className="font-semibold text-blue-600 text-xs">{p.price_raw}</span>
                            </div>
                            {p.rating && (
                                <div className="flex items-center gap-0.5 text-xs text-muted-foreground">
                                    <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
                                    {p.rating}
                                </div>
                            )}
                        </a>
                    ))}
                </div>
            )}
        </div>
    )
}

/* ============================== */
/*         EVIDENCE TAB           */
/* ============================== */

function EvidenceTab({ evidence }: { evidence: VendorEvidence[] }) {
    if (evidence.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <AlertCircle className="h-8 w-8 mb-2 opacity-30" />
                <p className="text-sm">No evidence collected yet.</p>
            </div>
        )
    }

    // Group by field, deduplicate values, limit per group
    const grouped = evidence.reduce((acc, e) => {
        const key = e.field_name
        if (!acc[key]) acc[key] = []
        // Avoid duplicate values
        if (!acc[key].some(x => x.field_value === e.field_value)) {
            acc[key].push(e)
        }
        return acc
    }, {} as Record<string, VendorEvidence[]>)

    // Priority order for fields
    const fieldOrder = ['pricing_details', 'pricing_model', 'name', 'description', 'location', 'country',
        'email', 'phone', 'website', 'key_features', 'security_compliance', 'deployment',
        'contract_terms', 'founded_year', 'employee_count', 'industry']

    const sortedFields = Object.keys(grouped).sort((a, b) => {
        const ia = fieldOrder.indexOf(a)
        const ib = fieldOrder.indexOf(b)
        return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib)
    })

    return (
        <div className="space-y-3">
            <p className="text-xs text-muted-foreground">{evidence.length} evidence points across {sortedFields.length} fields</p>
            {sortedFields.map((field) => {
                const items = grouped[field].slice(0, 3) // Max 3 per field
                const remaining = grouped[field].length - 3
                return (
                    <div key={field} className="rounded-lg border p-3 overflow-hidden">
                        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
                            {field.replace(/_/g, ' ')}
                        </h4>
                        <div className="space-y-2 overflow-hidden">
                            {items.map((item) => (
                                <div key={item.id} className="text-sm border-b border-dashed border-border/50 pb-2 last:border-0 last:pb-0 overflow-hidden">
                                    <p className="font-medium text-foreground leading-snug break-words overflow-wrap-anywhere" style={{overflowWrap: 'anywhere', wordBreak: 'break-word'}}>
                                        {item.field_value}
                                    </p>
                                    {item.evidence_snippet && (
                                        <p className="text-[11px] text-muted-foreground mt-1 italic leading-relaxed overflow-hidden" style={{overflowWrap: 'anywhere', wordBreak: 'break-word'}}>
                                            &ldquo;{item.evidence_snippet}&rdquo;
                                        </p>
                                    )}
                                    <div className="flex items-center gap-1.5 mt-1.5">
                                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                            item.confidence >= 0.8 ? 'bg-emerald-100 text-emerald-700' :
                                            item.confidence >= 0.6 ? 'bg-amber-100 text-amber-700' :
                                            'bg-red-100 text-red-700'
                                        }`}>
                                            {(item.confidence * 100).toFixed(0)}%
                                        </span>
                                        <span className="text-[10px] text-muted-foreground">{item.extraction_method}</span>
                                    </div>
                                </div>
                            ))}
                            {remaining > 0 && (
                                <p className="text-[11px] text-muted-foreground">+{remaining} more</p>
                            )}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

/* ============================== */
/*         SOURCES TAB            */
/* ============================== */

function SourcesTab({ sources }: { sources: VendorSource[] }) {
    if (sources.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <Link2 className="h-8 w-8 mb-2 opacity-30" />
                <p className="text-sm">No sources available.</p>
            </div>
        )
    }

    return (
        <div className="space-y-2.5">
            <p className="text-xs text-muted-foreground">{sources.length} source{sources.length !== 1 ? 's' : ''} found</p>
            {sources.map((source) => (
                <a key={source.id} href={source.source_url} target="_blank" rel="noopener noreferrer"
                    className="block rounded-lg border p-3 hover:border-primary/30 hover:bg-muted/30 transition-colors group">
                    <div className="flex items-start gap-3">
                        <div className="mt-0.5 h-8 w-8 rounded-lg bg-muted flex items-center justify-center shrink-0">
                            <FileText className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium break-words group-hover:text-primary transition-colors">
                                {source.page_title || 'Untitled page'}
                            </p>
                            <p className="text-[11px] text-muted-foreground break-all mt-0.5">
                                {source.source_url}
                            </p>
                            <div className="flex items-center gap-2 mt-1.5">
                                <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${
                                    source.fetch_status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-700' :
                                    'bg-red-100 text-red-700'
                                }`}>
                                    {source.fetch_status}
                                </span>
                                {source.source_type && (
                                    <Badge variant="outline" className="text-[10px] h-4 px-1">{source.source_type}</Badge>
                                )}
                                {source.fetched_at && (
                                    <span className="text-[10px] text-muted-foreground">
                                        {new Date(source.fetched_at).toLocaleDateString()}
                                    </span>
                                )}
                            </div>
                        </div>
                        <ExternalLink className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-1" />
                    </div>
                </a>
            ))}
        </div>
    )
}

/* ============================== */
/*         SHARED COMPONENTS      */
/* ============================== */

function ScoreCircle({ label, score, color }: { label: string; score?: number | null; color: string }) {
    const val = score != null ? score.toFixed(0) : '—'
    const colorMap: Record<string, string> = {
        emerald: 'from-emerald-500 to-emerald-600 shadow-emerald-200',
        blue: 'from-blue-500 to-blue-600 shadow-blue-200',
        purple: 'from-purple-500 to-purple-600 shadow-purple-200',
    }
    return (
        <div className="text-center">
            <div className={`mx-auto h-14 w-14 rounded-2xl bg-gradient-to-br ${colorMap[color]} text-white flex items-center justify-center text-lg font-bold shadow-lg`}>
                {val}
            </div>
            <p className="text-xs text-muted-foreground mt-1.5 font-medium">{label}</p>
        </div>
    )
}

function MiniStat({ icon: Icon, label, value, color }: { icon: React.ElementType; label: string; value: string; color: string }) {
    return (
        <div className="flex items-center gap-2 p-2 rounded-md bg-muted/30">
            <Icon className={`h-3.5 w-3.5 ${color} shrink-0`} />
            <div className="min-w-0">
                <p className="text-[10px] text-muted-foreground truncate">{label}</p>
                <p className={`text-xs font-semibold ${color}`}>{value}</p>
            </div>
        </div>
    )
}

function ContactRow({ icon: Icon, label, children }: { icon: React.ElementType; label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center gap-3 py-1.5">
            <div className="h-7 w-7 rounded-lg bg-muted flex items-center justify-center shrink-0">
                <Icon className="h-3.5 w-3.5 text-muted-foreground" />
            </div>
            <div className="flex-1 min-w-0">
                <p className="text-[10px] text-muted-foreground">{label}</p>
                {children}
            </div>
        </div>
    )
}

function getQualityColor(value?: number | null): string {
    const v = value || 0
    if (v >= 80) return 'text-emerald-600'
    if (v >= 60) return 'text-amber-600'
    if (v >= 40) return 'text-orange-500'
    return 'text-red-500'
}

function OverviewSkeleton() {
    return (
        <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">{[1,2,3].map(i => <Skeleton key={i} className="h-20 rounded-2xl" />)}</div>
            <Skeleton className="h-16 rounded-lg" />
            <Skeleton className="h-24 rounded-lg" />
            <Skeleton className="h-32 rounded-lg" />
        </div>
    )
}

function EvidenceSkeleton() {
    return <div className="space-y-3">{[1,2,3,4].map(i => <Skeleton key={i} className="h-20 rounded-lg" />)}</div>
}

function SourcesSkeleton() {
    return <div className="space-y-2.5">{[1,2,3].map(i => <Skeleton key={i} className="h-16 rounded-lg" />)}</div>
}
