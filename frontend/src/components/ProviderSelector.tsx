import { useState, useEffect } from 'react'
import { Checkbox } from '@/components/ui/checkbox'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Search, Globe, Zap, AlertCircle, Loader2 } from 'lucide-react'
import { providersApi, type DataProvider } from '@/lib/providers-api'

interface ProviderSelectorProps {
    selectedProviders: string[]
    onChange: (selected: string[]) => void
}

export function ProviderSelector({
    selectedProviders,
    onChange,
}: ProviderSelectorProps) {
    const [providers, setProviders] = useState<DataProvider[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        loadProviders()
    }, [])

    const loadProviders = async () => {
        try {
            setLoading(true)
            setError(null)
            const response = await providersApi.list()
            setProviders(response.providers)
        } catch (err) {
            setError('Failed to load providers')
            console.error('Failed to load providers:', err)
        } finally {
            setLoading(false)
        }
    }

    // Filter out disabled providers
    const enabledProviders = providers.filter(p => p.is_enabled)
    const searchProviders = enabledProviders.filter(p => p.provider_type === 'SEARCH')
    const scrapeProviders = enabledProviders.filter(p => p.provider_type === 'SCRAPE')
    const hybridProviders = enabledProviders.filter(p => p.provider_type === 'HYBRID')

    const toggleProvider = (name: string) => {
        if (selectedProviders.includes(name)) {
            onChange(selectedProviders.filter(p => p !== name))
        } else {
            onChange([...selectedProviders, name])
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading providers...</span>
            </div>
        )
    }

    if (error) {
        return (
            <div className="flex items-center justify-center py-8 text-destructive">
                <AlertCircle className="h-5 w-5 mr-2" />
                <span>{error}</span>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Search Providers */}
            <Card className="p-4">
                <div className="flex items-center gap-2 mb-4">
                    <Search className="h-5 w-5 text-primary" />
                    <h3 className="text-lg font-semibold">Web Search Providers</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                    Select search engines to discover vendor websites
                </p>
                <div className="space-y-3">
                    {searchProviders.map(provider => (
                        <ProviderCheckbox
                            key={provider.name}
                            provider={provider}
                            checked={selectedProviders.includes(provider.name)}
                            onToggle={() => toggleProvider(provider.name)}
                        />
                    ))}
                </div>
            </Card>

            {/* Scrape Providers */}
            <Card className="p-4">
                <div className="flex items-center gap-2 mb-4">
                    <Globe className="h-5 w-5 text-primary" />
                    <h3 className="text-lg font-semibold">Web Scraping Providers</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                    Select scrapers to extract content from websites
                </p>
                <div className="space-y-3">
                    {scrapeProviders.map(provider => (
                        <ProviderCheckbox
                            key={provider.name}
                            provider={provider}
                            checked={selectedProviders.includes(provider.name)}
                            onToggle={() => toggleProvider(provider.name)}
                        />
                    ))}
                </div>
            </Card>

            {/* Hybrid Providers (if any) */}
            {hybridProviders.length > 0 && (
                <Card className="p-4">
                    <div className="flex items-center gap-2 mb-4">
                        <Zap className="h-5 w-5 text-primary" />
                        <h3 className="text-lg font-semibold">Hybrid Providers</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">
                        All-in-one providers that can both search and scrape
                    </p>
                    <div className="space-y-3">
                        {hybridProviders.map(provider => (
                            <ProviderCheckbox
                                key={provider.name}
                                provider={provider}
                                checked={selectedProviders.includes(provider.name)}
                                onToggle={() => toggleProvider(provider.name)}
                            />
                        ))}
                    </div>
                </Card>
            )}

            {/* Summary */}
            <div className="bg-muted/50 rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                    <strong>Selected:</strong>{' '}
                    {selectedProviders.length === 0 ? (
                        <span className="text-amber-600">No providers selected</span>
                    ) : (
                        selectedProviders.join(', ')
                    )}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                    Multiple providers can run in parallel for richer data collection.
                </p>
            </div>
        </div>
    )
}

function ProviderCheckbox({
    provider,
    checked,
    onToggle,
}: {
    provider: DataProvider
    checked: boolean
    onToggle: () => void
}) {
    const disabled = provider.requires_api_key && !provider.is_configured

    return (
        <label
            className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors
                ${checked ? 'bg-primary/5 border-primary' : 'hover:bg-muted border-border'}
                ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
        >
            <Checkbox
                checked={checked}
                onCheckedChange={onToggle}
                disabled={disabled}
                className="mt-0.5"
            />
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium">{provider.display_name}</span>
                    {provider.is_free && (
                        <Badge variant="secondary" className="text-xs">
                            FREE
                        </Badge>
                    )}
                    {provider.is_default && (
                        <Badge variant="outline" className="text-xs">
                            Default
                        </Badge>
                    )}
                    {disabled && (
                        <Badge variant="destructive" className="text-xs">
                            API Key Required
                        </Badge>
                    )}
                </div>
                <p className="text-sm text-muted-foreground mt-0.5 line-clamp-2">
                    {provider.description}
                </p>
            </div>
        </label>
    )
}

export default ProviderSelector
