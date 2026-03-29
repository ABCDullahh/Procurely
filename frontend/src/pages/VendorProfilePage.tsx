import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
    ArrowLeft,
    Building2,
    Globe,
    Mail,
    Phone,
    MapPin,
    Users,
    DollarSign,
    ExternalLink,
    Search,
    Sparkles,
    Target,
    CheckCircle,
    BookOpen,
    BarChart3,
    ShoppingCart,
    Star,
    TrendingDown,
    TrendingUp,
    Minus,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { vendorsApi, VendorDetail, VendorEvidence, VendorSource, VendorAsset } from '@/lib/vendors-api'

export default function VendorProfilePage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const vendorId = parseInt(id || '0', 10)

    const [activeTab, setActiveTab] = useState('overview')
    const [evidenceSearch, setEvidenceSearch] = useState('')

    // Fetch vendor
    const { data: vendor, isLoading: vendorLoading } = useQuery({
        queryKey: ['vendor', vendorId],
        queryFn: () => vendorsApi.get(vendorId),
        enabled: vendorId > 0,
    })

    // Fetch evidence
    const { data: evidenceData, isLoading: evidenceLoading } = useQuery({
        queryKey: ['vendor-evidence', vendorId],
        queryFn: () => vendorsApi.getEvidence(vendorId),
        enabled: vendorId > 0,
    })

    // Fetch sources
    const { data: sourcesData, isLoading: sourcesLoading } = useQuery({
        queryKey: ['vendor-sources', vendorId],
        queryFn: () => vendorsApi.getSources(vendorId),
        enabled: vendorId > 0,
    })

    // Fetch assets
    const { data: assetsData, isLoading: assetsLoading } = useQuery({
        queryKey: ['vendor-assets', vendorId],
        queryFn: () => vendorsApi.getAssets(vendorId),
        enabled: vendorId > 0,
    })

    // Filter evidence by search
    const filteredEvidence = (evidenceData?.evidence || []).filter(
        (e) =>
            !evidenceSearch ||
            e.field_name.toLowerCase().includes(evidenceSearch.toLowerCase()) ||
            e.field_value.toLowerCase().includes(evidenceSearch.toLowerCase())
    )

    if (vendorLoading) {
        return <VendorProfileSkeleton />
    }

    if (!vendor) {
        return (
            <div className="p-6">
                <Button variant="ghost" onClick={() => navigate(-1)}>
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back
                </Button>
                <div className="mt-8 text-center text-muted-foreground">
                    Vendor not found or you don't have access.
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <div className="border-b bg-card">
                <div className="container mx-auto px-4 py-6">
                    <Button variant="ghost" size="sm" className="mb-4" onClick={() => navigate(-1)}>
                        <ArrowLeft className="mr-2 h-4 w-4" /> Back
                    </Button>

                    <div className="flex items-start gap-6">
                        {/* Logo */}
                        {vendor.logo_url ? (
                            <img
                                src={vendor.logo_url}
                                alt={vendor.name}
                                className="h-20 w-20 rounded-xl object-contain bg-white border"
                            />
                        ) : (
                            <div className="h-20 w-20 rounded-xl bg-[#F3F0EB] flex items-center justify-center">
                                <Building2 className="h-10 w-10 text-[#6B6560]" />
                            </div>
                        )}

                        {/* Info */}
                        <div className="flex-1">
                            <div className="flex items-center gap-4">
                                <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">{vendor.name}</h1>
                                {vendor.website && (
                                    <a
                                        href={vendor.website}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-muted-foreground hover:text-primary"
                                    >
                                        <ExternalLink className="h-5 w-5" />
                                    </a>
                                )}
                            </div>
                            {vendor.industry && (
                                <p className="text-muted-foreground mt-1">{vendor.industry}</p>
                            )}
                            {vendor.description && (
                                <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                                    {vendor.description}
                                </p>
                            )}

                            {/* Scores */}
                            {vendor.metrics && (
                                <div className="flex flex-wrap gap-4 mt-4">
                                    <ScoreBadge label="Overall" score={vendor.metrics.overall_score} />
                                    <ScoreBadge label="Fit" score={vendor.metrics.fit_score} color="blue" />
                                    <ScoreBadge label="Trust" score={vendor.metrics.trust_score} color="purple" />
                                    <ScoreBadge label="Quality" score={vendor.metrics.quality_score} color="yellow" />
                                    {vendor.metrics.price_score > 0 && (
                                        <ScoreBadge label="Price" score={vendor.metrics.price_score} color="green" />
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="container mx-auto px-4 py-6">
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList>
                        <TabsTrigger value="overview">Overview</TabsTrigger>
                        <TabsTrigger value="evidence">Evidence</TabsTrigger>
                        <TabsTrigger value="sources">Sources</TabsTrigger>
                        <TabsTrigger value="assets">Assets</TabsTrigger>
                    </TabsList>

                    <TabsContent value="overview" className="mt-6">
                        <OverviewTab vendor={vendor} />
                    </TabsContent>

                    <TabsContent value="evidence" className="mt-6">
                        <div className="space-y-4">
                            {/* Search */}
                            <div className="relative max-w-sm">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    placeholder="Search evidence..."
                                    value={evidenceSearch}
                                    onChange={(e) => setEvidenceSearch(e.target.value)}
                                    className="pl-9"
                                />
                            </div>

                            {evidenceLoading ? (
                                <EvidenceSkeleton />
                            ) : (
                                <EvidenceTab evidence={filteredEvidence} />
                            )}
                        </div>
                    </TabsContent>

                    <TabsContent value="sources" className="mt-6">
                        {sourcesLoading ? (
                            <SourcesSkeleton />
                        ) : (
                            <SourcesTab sources={sourcesData?.sources || []} />
                        )}
                    </TabsContent>

                    <TabsContent value="assets" className="mt-6">
                        {assetsLoading ? (
                            <AssetsSkeleton />
                        ) : (
                            <AssetsTab assets={assetsData?.assets || []} />
                        )}
                    </TabsContent>
                </Tabs>
            </div>
        </div>
    )
}

function formatPrice(price: number | null | undefined, currency: string = 'IDR'): string {
    if (price == null) return '-'
    if (currency === 'IDR') {
        return `Rp ${price.toLocaleString('id-ID')}`
    }
    if (currency === 'USD') {
        return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
    }
    return `${currency} ${price.toLocaleString()}`
}

function OverviewTab({ vendor }: { vendor: VendorDetail }) {
    const structured = vendor.structured_data
    const shopping = vendor.shopping_data

    return (
        <div className="space-y-6">
            {/* Section 1: Summary */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-primary" />
                        Summary
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <InfoField label="Description" value={vendor.description} />
                        <InfoField label="Industry" value={vendor.industry} />
                        <InfoField label="Target Segment" value={structured?.target_segment} />
                        <InfoField label="Regions Served" value={structured?.regions_served} />
                    </div>
                </CardContent>
            </Card>

            {/* Section 2: Fit and Use Cases */}
            <Card>
                <CardHeader>
                    <CardTitle>Fit and Use Cases</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <h4 className="font-medium text-sm text-muted-foreground mb-2">Use Cases</h4>
                            {structured?.use_cases && structured.use_cases.length > 0 ? (
                                <ul className="list-disc list-inside space-y-1">
                                    {structured.use_cases.map((uc, i) => (
                                        <li key={i} className="text-sm">{uc}</li>
                                    ))}
                                </ul>
                            ) : (
                                <NotFound />
                            )}
                        </div>
                        <div>
                            <h4 className="font-medium text-sm text-muted-foreground mb-2">Key Features</h4>
                            {structured?.key_features && structured.key_features.length > 0 ? (
                                <ul className="list-disc list-inside space-y-1">
                                    {structured.key_features.map((f, i) => (
                                        <li key={i} className="text-sm">{f}</li>
                                    ))}
                                </ul>
                            ) : (
                                <NotFound />
                            )}
                        </div>
                        <div>
                            <h4 className="font-medium text-sm text-muted-foreground mb-2">Differentiators</h4>
                            {structured?.differentiators && structured.differentiators.length > 0 ? (
                                <ul className="list-disc list-inside space-y-1">
                                    {structured.differentiators.map((d, i) => (
                                        <li key={i} className="text-sm">{d}</li>
                                    ))}
                                </ul>
                            ) : (
                                <NotFound />
                            )}
                        </div>
                        <div>
                            <h4 className="font-medium text-sm text-muted-foreground mb-2">Limitations</h4>
                            {structured?.limitations && structured.limitations.length > 0 ? (
                                <ul className="list-disc list-inside space-y-1 text-amber-600">
                                    {structured.limitations.map((l, i) => (
                                        <li key={i} className="text-sm">{l}</li>
                                    ))}
                                </ul>
                            ) : (
                                <span className="text-sm text-muted-foreground">None noted</span>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Section 3: Pricing and Commercials */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <DollarSign className="h-5 w-5 text-primary" />
                        Pricing and Commercials
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <InfoField label="Pricing Model" value={vendor.pricing_model} />
                        <InfoField label="Pricing Details" value={vendor.pricing_details} />
                        <InfoField label="Contract Terms" value={structured?.contract_terms} />
                    </div>
                </CardContent>
            </Card>

            {/* Section 3b: Google Shopping Prices */}
            {shopping && shopping.products && shopping.products.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <ShoppingCart className="h-5 w-5 text-primary" />
                            Market Prices (Google Shopping)
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {/* Price Summary */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="p-4 bg-muted/50 rounded-lg text-center">
                                <p className="text-sm text-muted-foreground mb-1">Min Price</p>
                                <p className="text-xl font-bold text-green-600">
                                    {formatPrice(shopping.price_min)}
                                </p>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg text-center">
                                <p className="text-sm text-muted-foreground mb-1">Max Price</p>
                                <p className="text-xl font-bold text-red-500">
                                    {formatPrice(shopping.price_max)}
                                </p>
                            </div>
                            <div className="p-4 bg-muted/50 rounded-lg text-center">
                                <p className="text-sm text-muted-foreground mb-1">Average</p>
                                <p className="text-xl font-bold">
                                    {formatPrice(shopping.price_avg)}
                                </p>
                            </div>
                            {shopping.market_avg && (
                                <div className="p-4 bg-muted/50 rounded-lg text-center">
                                    <p className="text-sm text-muted-foreground mb-1">Market Avg</p>
                                    <p className="text-xl font-bold text-blue-600">
                                        {formatPrice(shopping.market_avg)}
                                    </p>
                                </div>
                            )}
                        </div>

                        {/* Price Competitiveness */}
                        {shopping.price_competitiveness != null && (
                            <div className="p-4 rounded-lg bg-muted/30 mb-6">
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        {shopping.price_competitiveness < 1 ? (
                                            <TrendingDown className="h-5 w-5 text-green-500" />
                                        ) : shopping.price_competitiveness > 1.1 ? (
                                            <TrendingUp className="h-5 w-5 text-red-500" />
                                        ) : (
                                            <Minus className="h-5 w-5 text-gray-500" />
                                        )}
                                        Price Competitiveness
                                    </span>
                                    <span className={`font-semibold ${
                                        shopping.price_competitiveness < 1
                                            ? 'text-green-600'
                                            : shopping.price_competitiveness > 1.1
                                            ? 'text-red-500'
                                            : 'text-muted-foreground'
                                    }`}>
                                        {shopping.price_competitiveness < 1
                                            ? 'Below market average'
                                            : shopping.price_competitiveness > 1.1
                                            ? 'Above market average'
                                            : 'At market average'}
                                        {' '}({(shopping.price_competitiveness * 100).toFixed(0)}%)
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Products Grid */}
                        <h4 className="font-medium text-sm text-muted-foreground mb-3">
                            Products Found ({shopping.products.length})
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {shopping.products.slice(0, 9).map((product, idx) => (
                                <a
                                    key={idx}
                                    href={product.link}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="border rounded-lg p-4 hover:border-primary/50 hover:bg-muted/30 transition-colors block"
                                >
                                    <div className="flex gap-3">
                                        {product.thumbnail && (
                                            <img
                                                src={product.thumbnail}
                                                alt={product.title}
                                                className="w-16 h-16 object-contain rounded bg-white border flex-shrink-0"
                                            />
                                        )}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm line-clamp-2 mb-1">
                                                {product.title}
                                            </p>
                                            <p className="text-lg font-bold text-[#1A1816]">
                                                {product.price != null
                                                    ? formatPrice(product.price, product.currency)
                                                    : product.price_raw}
                                            </p>
                                            {product.rating != null && (
                                                <div className="flex items-center gap-1 mt-1">
                                                    <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                                    <span className="text-xs text-muted-foreground">
                                                        {product.rating.toFixed(1)}
                                                        {product.reviews_count != null && (
                                                            <span> ({product.reviews_count} reviews)</span>
                                                        )}
                                                    </span>
                                                </div>
                                            )}
                                            <p className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                                                via {product.source}
                                                <ExternalLink className="h-3 w-3" />
                                            </p>
                                        </div>
                                    </div>
                                </a>
                            ))}
                        </div>

                        {/* Sources */}
                        {shopping.sources && shopping.sources.length > 0 && (
                            <div className="mt-4 pt-4 border-t">
                                <p className="text-xs text-muted-foreground">
                                    Data from: {shopping.sources.join(', ')}
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Section 4: Security and Compliance */}
            <Card>
                <CardHeader>
                    <CardTitle>Security and Compliance</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <InfoField label="Compliance" value={vendor.security_compliance} />
                        <InfoField label="Deployment" value={vendor.deployment} />
                        <InfoField label="Data Hosting" value={structured?.data_hosting} />
                        <InfoField
                            label="SSO/SAML"
                            value={structured?.sso_saml === true ? 'Supported' : structured?.sso_saml === false ? 'Not supported' : null}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Section 5: Company and Credibility */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5 text-primary" />
                        Company and Credibility
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <InfoFieldWithIcon icon={MapPin} label="Location" value={vendor.location ? `${vendor.location}${vendor.country ? `, ${vendor.country}` : ''}` : null} />
                        <InfoField label="Founded" value={vendor.founded_year?.toString()} />
                        <InfoField label="Employees" value={vendor.employee_count} />
                        <div>
                            <h4 className="font-medium text-sm text-muted-foreground mb-2">Notable Customers</h4>
                            {structured?.notable_customers && structured.notable_customers.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {structured.notable_customers.map((c, i) => (
                                        <Badge key={i} variant="secondary">{c}</Badge>
                                    ))}
                                </div>
                            ) : (
                                <NotFound />
                            )}
                        </div>
                    </div>
                    {/* Contact Info */}
                    <div className="border-t mt-4 pt-4">
                        <h4 className="font-medium text-sm text-muted-foreground mb-3">Contact Information</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <InfoFieldWithIcon icon={Globe} label="Website" value={vendor.website} isLink />
                            <InfoFieldWithIcon icon={Mail} label="Email" value={vendor.email} isEmail />
                            <InfoFieldWithIcon icon={Phone} label="Phone" value={vendor.phone} />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Section 6: Implementation and Support */}
            <Card>
                <CardHeader>
                    <CardTitle>Implementation and Support</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <InfoField label="Integrations" value={vendor.integrations} />
                        <InfoField label="Support Channels" value={structured?.support_channels} />
                        <InfoField label="Onboarding Time" value={structured?.onboarding_time} />
                    </div>
                </CardContent>
            </Card>

            {/* Research Quality Card */}
            {vendor.metrics && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-yellow-500" />
                            Research Quality
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <QualityMetricCard
                                icon={CheckCircle}
                                label="Completeness"
                                value={vendor.metrics.completeness_pct}
                                suffix="%"
                            />
                            <QualityMetricCard
                                icon={Target}
                                label="Confidence"
                                value={vendor.metrics.confidence_pct}
                                suffix="%"
                            />
                            <QualityMetricCard
                                icon={BookOpen}
                                label="Source Diversity"
                                value={vendor.metrics.source_diversity}
                                suffix=" unique"
                            />
                            <QualityMetricCard
                                icon={BarChart3}
                                label="Research Depth"
                                value={vendor.metrics.research_depth}
                                suffix={vendor.metrics.research_depth === 1 ? ' iteration' : ' iterations'}
                            />
                        </div>
                        {vendor.metrics.price_competitiveness != null && (
                            <div className="p-4 rounded-lg bg-muted/50 mb-6">
                                <div className="flex items-center justify-between">
                                    <span className="flex items-center gap-2 text-muted-foreground">
                                        <DollarSign className="h-4 w-4" />
                                        Price Competitiveness
                                    </span>
                                    <span className={`font-semibold ${
                                        vendor.metrics.price_competitiveness < 1
                                            ? 'text-green-600'
                                            : vendor.metrics.price_competitiveness > 1.1
                                            ? 'text-red-500'
                                            : 'text-muted-foreground'
                                    }`}>
                                        {vendor.metrics.price_competitiveness < 1
                                            ? 'Below market average'
                                            : vendor.metrics.price_competitiveness > 1.1
                                            ? 'Above market average'
                                            : 'At market average'}
                                        ({(vendor.metrics.price_competitiveness * 100).toFixed(0)}%)
                                    </span>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* Scoring Details Card */}
            {vendor.metrics && (
                <Card>
                    <CardHeader>
                        <CardTitle>Scoring Details</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <MetricCard
                                label="Must-Have Matched"
                                value={`${vendor.metrics.must_have_matched}/${vendor.metrics.must_have_total}`}
                            />
                            <MetricCard
                                label="Nice-to-Have Matched"
                                value={`${vendor.metrics.nice_to_have_matched}/${vendor.metrics.nice_to_have_total}`}
                            />
                            <MetricCard label="Sources" value={vendor.metrics.source_count} />
                            <MetricCard label="Evidence Points" value={vendor.metrics.evidence_count} />
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    )
}

function EvidenceTab({ evidence }: { evidence: VendorEvidence[] }) {
    if (evidence.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                <p className="mb-2">No evidence found for this vendor.</p>
                <p className="text-sm">Evidence is extracted from vendor source pages during the search process.</p>
            </div>
        )
    }

    // Group by category, fallback to field_name if no category
    const categoryOrder = ['summary', 'company', 'features', 'pricing', 'security', 'implementation', 'other']
    const grouped = evidence.reduce((acc, e) => {
        const cat = e.category || 'other'
        if (!acc[cat]) acc[cat] = []
        acc[cat].push(e)
        return acc
    }, {} as Record<string, VendorEvidence[]>)

    // Sort categories
    const sortedCategories = Object.keys(grouped).sort((a, b) => {
        const aIdx = categoryOrder.indexOf(a.toLowerCase())
        const bIdx = categoryOrder.indexOf(b.toLowerCase())
        return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx)
    })

    const categoryLabels: Record<string, string> = {
        summary: 'Summary',
        company: 'Company',
        features: 'Features',
        pricing: 'Pricing',
        security: 'Security',
        implementation: 'Implementation',
        other: 'Other'
    }

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 0.9) return 'bg-green-500'
        if (confidence >= 0.7) return 'bg-yellow-500'
        return 'bg-orange-500'
    }

    return (
        <div className="space-y-6">
            {sortedCategories.map((category) => (
                <Card key={category}>
                    <CardHeader className="pb-2">
                        <CardTitle className="text-lg capitalize flex items-center gap-2">
                            {categoryLabels[category] || category}
                            <Badge variant="secondary" className="text-xs">
                                {grouped[category].length} items
                            </Badge>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {grouped[category].map((item) => (
                                <div key={item.id} className="border rounded-lg p-4 bg-muted/30">
                                    <div className="flex items-start justify-between gap-2 mb-2">
                                        <p className="font-medium text-sm">
                                            {item.field_label || item.field_name.replace(/_/g, ' ')}
                                        </p>
                                        <div className={`h-2 w-2 rounded-full ${getConfidenceColor(item.confidence)}`} title={`${(item.confidence * 100).toFixed(0)}% confidence`} />
                                    </div>
                                    <p className="text-sm mb-2">{item.field_value}</p>
                                    {item.evidence_snippet && (
                                        <blockquote className="text-xs text-muted-foreground border-l-2 border-primary/30 pl-2 italic mb-2">
                                            "{item.evidence_snippet}"
                                        </blockquote>
                                    )}
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <Badge variant="outline" className="text-xs">
                                            {(item.confidence * 100).toFixed(0)}%
                                        </Badge>
                                        {item.evidence_url && (
                                            <a
                                                href={item.evidence_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs text-primary hover:underline flex items-center gap-1"
                                            >
                                                {item.source_title || 'Source'}
                                                <ExternalLink className="h-3 w-3" />
                                            </a>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}

function SourcesTab({ sources }: { sources: VendorSource[] }) {
    if (sources.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                <p className="mb-2">No sources available for this vendor.</p>
                <p className="text-sm">Sources are web pages from which vendor information was extracted.</p>
            </div>
        )
    }

    // Group by source_category
    const categoryOrder = ['OFFICIAL', 'PRICING', 'SECURITY', 'DOCS', 'REVIEWS', 'NEWS', 'OTHER']
    const grouped = sources.reduce((acc, s) => {
        const cat = s.source_category || 'OTHER'
        if (!acc[cat]) acc[cat] = []
        acc[cat].push(s)
        return acc
    }, {} as Record<string, VendorSource[]>)

    const categoryLabels: Record<string, string> = {
        OFFICIAL: 'Official Website',
        PRICING: 'Pricing Pages',
        SECURITY: 'Security and Compliance',
        DOCS: 'Documentation',
        REVIEWS: 'Reviews',
        NEWS: 'News and Blogs',
        OTHER: 'Other Sources'
    }

    // Sort categories
    const sortedCategories = Object.keys(grouped).sort((a, b) => {
        const aIdx = categoryOrder.indexOf(a)
        const bIdx = categoryOrder.indexOf(b)
        return (aIdx === -1 ? 999 : aIdx) - (bIdx === -1 ? 999 : bIdx)
    })

    return (
        <div className="space-y-6">
            {sortedCategories.map((category) => (
                <div key={category}>
                    <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                        {categoryLabels[category] || category}
                        <Badge variant="secondary" className="text-xs">
                            {grouped[category].length}
                        </Badge>
                    </h3>
                    <div className="space-y-3">
                        {grouped[category].map((source) => (
                            <Card key={source.id}>
                                <CardContent className="pt-4">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium">{source.page_title || 'Untitled page'}</p>
                                            <a
                                                href={source.source_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-sm text-primary hover:underline flex items-center gap-1 mt-1"
                                            >
                                                Open in new tab
                                                <ExternalLink className="h-3 w-3" />
                                            </a>
                                            {source.content_summary && (
                                                <p className="text-sm text-muted-foreground mt-2">
                                                    {source.content_summary}
                                                </p>
                                            )}
                                        </div>
                                        <div className="flex flex-col items-end gap-2">
                                            <Badge variant={source.fetch_status === 'SUCCESS' ? 'default' : 'destructive'}>
                                                {source.fetch_status}
                                            </Badge>
                                            <Badge variant="outline" className="text-xs">
                                                {source.source_type}
                                            </Badge>
                                        </div>
                                    </div>
                                    {source.fetched_at && (
                                        <p className="text-xs text-muted-foreground mt-2">
                                            Fetched: {new Date(source.fetched_at).toLocaleString()}
                                        </p>
                                    )}
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    )
}

function AssetsTab({ assets }: { assets: VendorAsset[] }) {
    if (assets.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                No assets available.
            </div>
        )
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {assets.map((asset) => (
                <Card key={asset.id}>
                    <CardContent className="pt-4">
                        <div className="aspect-square bg-white border rounded-lg flex items-center justify-center p-4">
                            <img
                                src={asset.asset_url}
                                alt={asset.asset_type}
                                className="max-h-full max-w-full object-contain"
                            />
                        </div>
                        <div className="mt-3">
                            <Badge variant="outline">{asset.asset_type}</Badge>
                            <p className="text-xs text-muted-foreground mt-1">
                                Priority: {asset.priority}
                            </p>
                            {asset.source_url && (
                                <a
                                    href={asset.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1 mt-1"
                                >
                                    Source <ExternalLink className="h-3 w-3" />
                                </a>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}

function ScoreBadge({
    label,
    score,
    color = 'green',
}: {
    label: string
    score?: number | null
    color?: 'green' | 'blue' | 'purple' | 'yellow'
}) {
    const colors = {
        green: 'bg-green-500',
        blue: 'bg-blue-500',
        purple: 'bg-purple-500',
        yellow: 'bg-yellow-500',
    }
    return (
        <div className="flex items-center gap-2">
            <div
                className={`h-8 w-8 rounded-full ${colors[color]} text-white flex items-center justify-center text-sm font-bold`}
            >
                {score != null ? score.toFixed(0) : '—'}
            </div>
            <span className="text-sm text-muted-foreground">{label}</span>
        </div>
    )
}

function NotFound() {
    return <span className="text-sm text-muted-foreground italic">Not found</span>
}

function InfoField({ label, value }: { label: string; value: string | null | undefined }) {
    return (
        <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="font-medium">{value || <NotFound />}</p>
        </div>
    )
}

function InfoFieldWithIcon({
    icon: Icon,
    label,
    value,
    isLink = false,
    isEmail = false,
}: {
    icon: React.ElementType
    label: string
    value: string | null | undefined
    isLink?: boolean
    isEmail?: boolean
}) {
    const renderValue = () => {
        if (!value) return <NotFound />
        if (isLink) {
            return (
                <a
                    href={value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                >
                    {value}
                </a>
            )
        }
        if (isEmail) {
            return (
                <a href={`mailto:${value}`} className="text-primary hover:underline">
                    {value}
                </a>
            )
        }
        return <span>{value}</span>
    }

    return (
        <div className="flex items-start gap-3">
            <Icon className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
                <p className="text-sm text-muted-foreground">{label}</p>
                <p className="font-medium">{renderValue()}</p>
            </div>
        </div>
    )
}
function MetricCard({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="text-center p-4 bg-muted rounded-lg">
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
        </div>
    )
}

function QualityMetricCard({
    icon: Icon,
    label,
    value,
    suffix = '',
}: {
    icon: React.ElementType
    label: string
    value: number | null | undefined
    suffix?: string
}) {
    const displayValue = value ?? 0
    const getColorClass = () => {
        if (typeof displayValue !== 'number') return 'text-muted-foreground'
        if (displayValue >= 80) return 'text-green-600'
        if (displayValue >= 60) return 'text-yellow-600'
        if (displayValue >= 40) return 'text-orange-500'
        return 'text-red-500'
    }

    return (
        <div className="p-4 bg-muted/50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{label}</span>
            </div>
            <p className={`text-2xl font-bold ${getColorClass()}`}>
                {displayValue.toFixed(0)}{suffix}
            </p>
        </div>
    )
}

function VendorProfileSkeleton() {
    return (
        <div className="min-h-screen bg-background">
            <div className="border-b bg-card">
                <div className="container mx-auto px-4 py-6">
                    <Skeleton className="h-8 w-24 mb-4" />
                    <div className="flex gap-6">
                        <Skeleton className="h-20 w-20 rounded-xl" />
                        <div className="flex-1">
                            <Skeleton className="h-8 w-64" />
                            <Skeleton className="h-4 w-32 mt-2" />
                            <Skeleton className="h-16 w-full mt-4" />
                        </div>
                    </div>
                </div>
            </div>
            <div className="container mx-auto px-4 py-6">
                <Skeleton className="h-10 w-96 mb-6" />
                <div className="grid grid-cols-2 gap-6">
                    <Skeleton className="h-64" />
                    <Skeleton className="h-64" />
                </div>
            </div>
        </div>
    )
}

function EvidenceSkeleton() {
    return (
        <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-40" />
            ))}
        </div>
    )
}

function SourcesSkeleton() {
    return (
        <div className="space-y-4">
            {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-24" />
            ))}
        </div>
    )
}

function AssetsSkeleton() {
    return (
        <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-40" />
            ))}
        </div>
    )
}
