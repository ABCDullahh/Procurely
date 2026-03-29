/**
 * Admin API Keys & Provider Settings Page
 * Manages provider enable/disable, default selection, and API key configuration
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
    Key, TestTube, RotateCcw, Eye, EyeOff, Loader2, RefreshCw,
    ChevronDown, Check, Settings2, Search, Globe, Bot
} from 'lucide-react'
import { motion } from 'framer-motion'
import { Button, Card, CardContent, CardHeader, CardTitle, Input, Label } from '@/components/ui'
import { useToast } from '@/components/ui/toast'
import { adminApi, ApiKeyResponse, ApiKeyListResponse, ApiKeyProvider, ProviderModel, SetApiKeyPayload } from '@/lib/admin-api'
import { providersApi, DataProvider } from '@/lib/providers-api'
import { ProviderSettingsRow } from '@/components/admin/ProviderSettingsRow'
import { cn } from '@/lib/utils'

interface LLMProviderInfo {
    id: ApiKeyProvider
    name: string
    description: string
    icon: string
}

const llmProviders: LLMProviderInfo[] = [
    {
        id: 'OPENAI',
        name: 'OpenAI',
        description: 'GPT-4, GPT-3.5 for AI-powered vendor analysis',
        icon: '',
    },
    {
        id: 'GEMINI',
        name: 'Google Gemini',
        description: 'Gemini Pro for alternative AI processing',
        icon: '',
    },
]

function ModelSelector({
    provider,
    selectedModel,
    onChange,
    existingKey,
}: {
    provider: ApiKeyProvider
    selectedModel: string
    onChange: (model: string) => void
    existingKey: boolean
}) {
    const { addToast } = useToast()
    const [models, setModels] = useState<ProviderModel[]>([])
    const [isFetching, setIsFetching] = useState(false)
    const [source, setSource] = useState<'live' | 'curated' | null>(null)
    const [fetchedAt, setFetchedAt] = useState<string | null>(null)
    const [isOpen, setIsOpen] = useState(false)
    const [filterText, setFilterText] = useState('')

    const fetchModels = async () => {
        if (!existingKey) {
            addToast({
                type: 'error',
                title: 'Key required',
                message: 'Please save an API key first to fetch models.',
            })
            return
        }

        setIsFetching(true)
        try {
            const response = await adminApi.fetchProviderModels(provider)
            setModels(response.models)
            setSource(response.source)
            setFetchedAt(response.fetched_at)
            if (response.models.length === 0) {
                addToast({
                    type: 'warning',
                    title: 'No models found',
                    message: 'Could not retrieve models. You can still type a model ID manually.',
                })
            }
        } catch {
            addToast({
                type: 'error',
                title: 'Failed to fetch models',
                message: 'Could not load models. You can still type a model ID manually.',
            })
        } finally {
            setIsFetching(false)
        }
    }

    const filteredModels = models.filter(m =>
        m.id.toLowerCase().includes(filterText.toLowerCase()) ||
        m.label.toLowerCase().includes(filterText.toLowerCase())
    )

    return (
        <div className="space-y-2">
            <div className="flex items-center justify-between">
                <Label htmlFor={`model-${provider}`}>Default Model</Label>
                <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={fetchModels}
                    disabled={isFetching}
                    className="h-7 text-xs gap-1.5"
                >
                    {isFetching ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                        <RefreshCw className="w-3 h-3" />
                    )}
                    Fetch models
                </Button>
            </div>

            <div className="relative">
                <div
                    className={cn(
                        'flex h-10 w-full items-center justify-between rounded-lg',
                        'border border-blush/50 bg-cream/50 px-3 py-2 text-sm cursor-pointer',
                        'shadow-sm hover:shadow-md hover:border-rose/40',
                        'transition-all duration-200',
                        isOpen && 'ring-2 ring-crimson/30 ring-offset-1'
                    )}
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <input
                        id={`model-${provider}`}
                        type="text"
                        value={selectedModel}
                        onChange={(e) => {
                            onChange(e.target.value)
                            setFilterText(e.target.value)
                        }}
                        onFocus={() => setIsOpen(true)}
                        placeholder="Type or select a model..."
                        className="flex-1 bg-transparent outline-none placeholder:text-muted-foreground"
                    />
                    <ChevronDown className={cn(
                        "h-4 w-4 text-crimson/60 transition-transform duration-200",
                        isOpen && "rotate-180"
                    )} />
                </div>

                {isOpen && (
                    <div
                        className={cn(
                            "absolute z-50 mt-1 w-full max-h-60 overflow-auto",
                            "rounded-lg border border-blush/40 bg-cream/95",
                            "shadow-lg shadow-crimson/5 backdrop-blur-sm",
                            "py-1"
                        )}
                    >
                        {filteredModels.length > 0 ? (
                            filteredModels.map((model) => (
                                <div
                                    key={model.id}
                                    className={cn(
                                        "flex items-center justify-between px-3 py-2 cursor-pointer",
                                        "transition-colors duration-150",
                                        "hover:bg-blush/30 hover:text-crimson",
                                        selectedModel === model.id && "bg-blush/20 text-crimson"
                                    )}
                                    onClick={() => {
                                        onChange(model.id)
                                        setFilterText('')
                                        setIsOpen(false)
                                    }}
                                >
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium">{model.label}</span>
                                        <span className="text-xs text-muted-foreground">{model.id}</span>
                                    </div>
                                    {selectedModel === model.id && (
                                        <Check className="h-4 w-4 text-crimson" />
                                    )}
                                </div>
                            ))
                        ) : models.length === 0 ? (
                            <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                                <p>No models loaded yet.</p>
                                <p className="text-xs mt-1">Click "Fetch models" or type an ID manually.</p>
                            </div>
                        ) : (
                            <div className="px-3 py-2 text-sm text-muted-foreground">
                                No matching models
                            </div>
                        )}
                    </div>
                )}
            </div>

            {source && (
                <p className="text-xs text-muted-foreground">
                    Source: {source}{fetchedAt && ` • Updated ${new Date(fetchedAt).toLocaleTimeString()}`}
                </p>
            )}
        </div>
    )
}

function LLMProviderCard({
    provider,
    keyData,
    onSave,
    onRotate,
    onTestKey,
}: {
    provider: LLMProviderInfo
    keyData: ApiKeyResponse | null
    onSave: (payload: SetApiKeyPayload) => void
    onRotate: (payload: SetApiKeyPayload) => void
    onTestKey: () => void
}) {
    const [isEditing, setIsEditing] = useState(false)
    const [keyValue, setKeyValue] = useState('')
    const [selectedModel, setSelectedModel] = useState(keyData?.default_model || '')
    const [showKey, setShowKey] = useState(false)
    const [isRotating, setIsRotating] = useState(false)
    const isConfigured = keyData !== null

    const handleSubmit = () => {
        const payload: SetApiKeyPayload = {
            value: keyValue.trim() || (isConfigured ? '' : ''),
            default_model: selectedModel || undefined,
        }

        if (!isConfigured && !keyValue.trim()) return

        if (isRotating) {
            if (!keyValue.trim()) return
            onRotate(payload)
        } else {
            if (!keyValue.trim() && !isConfigured) return
            onSave(payload)
        }

        setKeyValue('')
        setShowKey(false)
        setIsEditing(false)
        setIsRotating(false)
    }

    const handleCancel = () => {
        setKeyValue('')
        setSelectedModel(keyData?.default_model || '')
        setShowKey(false)
        setIsEditing(false)
        setIsRotating(false)
    }

    const canSave = () => {
        if (keyValue.trim()) return true
        if (isConfigured && selectedModel !== (keyData?.default_model || '')) return true
        return false
    }

    return (
        <Card className={cn(
            'transition-all duration-300',
            isConfigured ? 'border-green-500/30' : 'border-muted'
        )}>
            <CardContent className="py-4">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <span className="text-xl">{provider.icon}</span>
                        <div>
                            <h3 className="font-medium">{provider.name}</h3>
                            <p className="text-sm text-muted-foreground">{provider.description}</p>
                        </div>
                    </div>
                    <span className={cn(
                        'px-3 py-1 rounded-full text-xs font-medium',
                        isConfigured
                            ? 'bg-green-500/10 text-green-600'
                            : 'bg-muted text-muted-foreground'
                    )}>
                        {isConfigured ? 'Configured' : 'Not configured'}
                    </span>
                </div>

                {isConfigured && !isEditing && (
                    <div className="space-y-2 mb-4">
                        <div className="flex items-center justify-between py-2 px-3 bg-muted/50 rounded-lg">
                            <div className="flex items-center gap-2">
                                <Key className="w-4 h-4 text-muted-foreground" />
                                <span className="font-mono text-sm">{keyData.masked_tail}</span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                                Updated {new Date(keyData.updated_at).toLocaleDateString()}
                            </span>
                        </div>
                        {keyData.default_model && (
                            <div className="flex items-center gap-2 py-2 px-3 bg-blush/20 rounded-lg">
                                <Settings2 className="w-4 h-4 text-crimson/60" />
                                <span className="text-sm">Model: <span className="font-medium text-crimson">{keyData.default_model}</span></span>
                            </div>
                        )}
                    </div>
                )}

                {isEditing ? (
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor={`key-${provider.id}`}>
                                {isRotating ? 'New API Key' : isConfigured ? 'API Key (leave empty to keep existing)' : 'API Key'}
                            </Label>
                            <div className="relative">
                                <Input
                                    id={`key-${provider.id}`}
                                    type={showKey ? 'text' : 'password'}
                                    value={keyValue}
                                    onChange={(e) => setKeyValue(e.target.value)}
                                    placeholder={isConfigured && !isRotating ? 'Keep existing key...' : `Enter ${provider.name} API key...`}
                                    className="pr-10"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowKey(!showKey)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        <ModelSelector
                            provider={provider.id}
                            selectedModel={selectedModel}
                            onChange={setSelectedModel}
                            existingKey={isConfigured}
                        />

                        <div className="flex gap-2">
                            <Button
                                onClick={handleSubmit}
                                disabled={!canSave()}
                                className="flex-1 bg-crimson hover:bg-crimson/90 text-white"
                            >
                                {isRotating ? 'Rotate Key' : 'Save'}
                            </Button>
                            <Button variant="outline" onClick={handleCancel}>
                                Cancel
                            </Button>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-wrap gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsEditing(true)}
                        >
                            <Key className="w-4 h-4 mr-2" />
                            {isConfigured ? 'Update' : 'Set Key'}
                        </Button>
                        {isConfigured && (
                            <>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setIsRotating(true)
                                        setIsEditing(true)
                                    }}
                                >
                                    <RotateCcw className="w-4 h-4 mr-2" />
                                    Rotate
                                </Button>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={onTestKey}
                                >
                                    <TestTube className="w-4 h-4 mr-2" />
                                    Test
                                </Button>
                            </>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}

function ProviderSection({
    title,
    icon: Icon,
    providers,
    apiKeys,
}: {
    title: string
    icon: React.ComponentType<{ className?: string }>
    providers: DataProvider[]
    apiKeys: ApiKeyResponse[]
}) {
    const getApiKeyForProvider = (provider: DataProvider): ApiKeyResponse | null => {
        if (!provider.api_key_provider) return null
        return apiKeys.find(k => k.provider === provider.api_key_provider) ?? null
    }

    if (providers.length === 0) return null

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-3"
        >
            <div className="flex items-center gap-2 px-1">
                <Icon className="w-5 h-5 text-crimson" />
                <h2 className="text-lg font-display font-semibold">{title}</h2>
            </div>
            <div className="space-y-3">
                {providers.map((provider) => (
                    <ProviderSettingsRow
                        key={provider.name}
                        provider={provider}
                        apiKey={getApiKeyForProvider(provider)}
                    />
                ))}
            </div>
        </motion.div>
    )
}

export function AdminApiKeys() {
    const { addToast } = useToast()
    const queryClient = useQueryClient()
    const [testingProvider, setTestingProvider] = useState<ApiKeyProvider | null>(null)

    // Fetch API keys
    const { data: keysData, isLoading: keysLoading } = useQuery({
        queryKey: ['admin', 'api-keys'],
        queryFn: adminApi.listApiKeys,
    })

    // Fetch data providers
    const { data: providersData, isLoading: providersLoading } = useQuery({
        queryKey: ['providers'],
        queryFn: providersApi.list,
    })

    // Set key mutation
    const setKeyMutation = useMutation({
        mutationFn: ({ provider, payload }: { provider: ApiKeyProvider; payload: SetApiKeyPayload }) =>
            adminApi.setApiKey(provider, payload),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] })
            queryClient.invalidateQueries({ queryKey: ['providers'] })
            addToast({
                type: 'success',
                title: 'Settings Saved',
                message: `${data.provider} configuration updated.${data.default_model ? ` Model: ${data.default_model}` : ''}`,
            })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to save',
                message: error.message,
            })
        },
    })

    // Rotate key mutation
    const rotateKeyMutation = useMutation({
        mutationFn: ({ provider, payload }: { provider: ApiKeyProvider; payload: SetApiKeyPayload }) =>
            adminApi.rotateApiKey(provider, payload),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] })
            addToast({
                type: 'success',
                title: 'API Key Rotated',
                message: `Old ${data.provider} key has been deactivated. New key is now active.`,
            })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to rotate key',
                message: error.message,
            })
        },
    })

    // Test key mutation
    const testKeyMutation = useMutation({
        mutationFn: (provider: ApiKeyProvider) => adminApi.testApiKey(provider),
        onMutate: (provider) => setTestingProvider(provider),
        onSuccess: (result) => {
            setTestingProvider(null)
            if (result.ok) {
                addToast({
                    type: 'success',
                    title: 'Connection Successful',
                    message: `${result.message}${result.latency_ms ? ` (${result.latency_ms}ms)` : ''}`,
                })
            } else {
                addToast({
                    type: 'error',
                    title: 'Connection Failed',
                    message: result.message,
                })
            }
        },
        onError: (error: Error) => {
            setTestingProvider(null)
            addToast({
                type: 'error',
                title: 'Test Failed',
                message: error.message,
            })
        },
    })

    const getKeyForProvider = (providerId: ApiKeyProvider): ApiKeyResponse | null => {
        return keysData?.keys.find((k) => k.provider === providerId) ?? null
    }

    // Group providers by type
    const searchProviders = providersData?.providers.filter(p => p.provider_type === 'SEARCH') || []
    const scrapeProviders = providersData?.providers.filter(p => p.provider_type === 'SCRAPE') || []
    const hybridProviders = providersData?.providers.filter(p => p.provider_type === 'HYBRID') || []

    const isLoading = keysLoading || providersLoading

    if (isLoading) {
        return (
            <div className="p-6">
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            </div>
        )
    }

    return (
        <div className="p-6 space-y-8">
            <div>
                <h1 className="text-2xl font-display font-bold">Provider Settings</h1>
                <p className="text-muted-foreground mt-1">
                    Configure API keys, enable/disable providers, and set defaults for search and scraping.
                </p>
            </div>

            {/* LLM Providers Section */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="space-y-3"
            >
                <div className="flex items-center gap-2 px-1">
                    <Bot className="w-5 h-5 text-crimson" />
                    <h2 className="text-lg font-display font-semibold">LLM Providers</h2>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                    {llmProviders.map((provider) => (
                        <LLMProviderCard
                            key={provider.id}
                            provider={provider}
                            keyData={getKeyForProvider(provider.id)}
                            onSave={(payload) => setKeyMutation.mutate({ provider: provider.id, payload })}
                            onRotate={(payload) => rotateKeyMutation.mutate({ provider: provider.id, payload })}
                            onTestKey={() => testKeyMutation.mutate(provider.id)}
                        />
                    ))}
                </div>
            </motion.div>

            {/* Search Providers Section */}
            <ProviderSection
                title="Search Providers"
                icon={Search}
                providers={searchProviders}
                apiKeys={keysData?.keys || []}
            />

            {/* Scrape Providers Section */}
            <ProviderSection
                title="Scrape Providers"
                icon={Globe}
                providers={scrapeProviders}
                apiKeys={keysData?.keys || []}
            />

            {/* Hybrid Providers Section (if any) */}
            {hybridProviders.length > 0 && (
                <ProviderSection
                    title="Hybrid Providers"
                    icon={Settings2}
                    providers={hybridProviders}
                    apiKeys={keysData?.keys || []}
                />
            )}

            {/* AI Configuration Section */}
            <AIConfigSection keysData={keysData} />

            {testingProvider && (
                <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
                    <Card className="w-80">
                        <CardContent className="pt-6 text-center">
                            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary" />
                            <p className="font-medium">Testing {testingProvider} Connection...</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                Verifying API key is valid
                            </p>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}

/**
 * AI Configuration Section
 */
function AIConfigSection({ keysData }: { keysData: ApiKeyListResponse | undefined }) {
    const { addToast } = useToast()
    const queryClient = useQueryClient()

    const { data: aiConfig, isLoading } = useQuery({
        queryKey: ['admin', 'ai-config'],
        queryFn: adminApi.getAIConfig,
    })

    const [webSearchProvider, setWebSearchProvider] = useState<string>('')
    const [procProvider, setProcProvider] = useState<string>('')
    const [procModel, setProcModel] = useState<string>('')
    const [copilotProvider, setCopilotProvider] = useState<string>('')
    const [copilotModel, setCopilotModel] = useState<string>('')
    const [aiSearchProvider, setAiSearchProvider] = useState<string>('')
    const [aiSearchModel, setAiSearchModel] = useState<string>('')
    const [initialized, setInitialized] = useState(false)

    const isProviderKeyConfigured = (provider: string): boolean => {
        if (!keysData?.keys) return false
        return keysData.keys.some(k => k.provider === provider && k.is_active)
    }

    if (aiConfig && !initialized) {
        setWebSearchProvider(aiConfig.web_search.provider)
        setProcProvider(aiConfig.procurement_llm.provider)
        setProcModel(aiConfig.procurement_llm.model)
        setCopilotProvider(aiConfig.copilot_llm.provider)
        setCopilotModel(aiConfig.copilot_llm.model)
        setAiSearchProvider(aiConfig.ai_search_llm.provider)
        setAiSearchModel(aiConfig.ai_search_llm.model)
        setInitialized(true)
    }

    const saveMutation = useMutation({
        mutationFn: adminApi.setAIConfig,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'ai-config'] })
            addToast({
                type: 'success',
                title: 'AI Configuration Saved',
                message: 'Provider and model settings have been updated.',
            })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to save',
                message: error.message,
            })
        },
    })

    const handleSave = () => {
        saveMutation.mutate({
            web_search_provider: webSearchProvider as 'SERPER' | 'TAVILY' | 'GEMINI_GROUNDING',
            procurement_provider: procProvider as 'OPENAI' | 'GEMINI',
            procurement_model: procModel,
            copilot_provider: copilotProvider as 'OPENAI' | 'GEMINI',
            copilot_model: copilotModel,
            ai_search_provider: aiSearchProvider as 'OPENAI' | 'GEMINI',
            ai_search_model: aiSearchModel,
        })
    }

    if (isLoading) {
        return (
            <Card>
                <CardContent className="py-8 text-center">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                </CardContent>
            </Card>
        )
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
        >
            <Card>
                <CardHeader>
                    <div className="flex items-center gap-3">
                        <Settings2 className="w-6 h-6 text-crimson" />
                        <div>
                            <CardTitle>AI Configuration</CardTitle>
                            <p className="text-sm text-muted-foreground">
                                Configure which providers and models are used for search and AI features
                            </p>
                        </div>
                    </div>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Web Search Provider */}
                    <div className="space-y-3">
                        <Label className="text-base font-medium">Web Search Provider</Label>
                        <p className="text-xs text-muted-foreground">
                            Used by the procurement pipeline for web searches
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {['SERPER', 'TAVILY', 'GEMINI_GROUNDING'].map((opt) => (
                                <Button
                                    key={opt}
                                    variant={webSearchProvider === opt ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setWebSearchProvider(opt)}
                                    className={cn(
                                        webSearchProvider === opt && 'bg-crimson hover:bg-crimson/90'
                                    )}
                                >
                                    {opt === 'SERPER' && 'Serper'}
                                    {opt === 'TAVILY' && 'Tavily'}
                                    {opt === 'GEMINI_GROUNDING' && 'Gemini Grounding'}
                                </Button>
                            ))}
                        </div>
                        {aiConfig && !aiConfig.web_search.key_configured && (
                            <p className="text-xs text-amber-600">
                                Required API key not configured
                            </p>
                        )}
                    </div>

                    <hr className="border-blush/30" />

                    {/* Procurement LLM */}
                    <div className="space-y-3">
                        <Label className="text-base font-medium">Procurement Search LLM</Label>
                        <p className="text-xs text-muted-foreground">
                            AI model for vendor extraction, scoring, and analysis
                        </p>
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm">Provider</Label>
                                <div className="flex gap-2">
                                    <Button
                                        variant={procProvider === 'OPENAI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setProcProvider('OPENAI')}
                                        className={cn(
                                            procProvider === 'OPENAI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        OpenAI
                                    </Button>
                                    <Button
                                        variant={procProvider === 'GEMINI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setProcProvider('GEMINI')}
                                        className={cn(
                                            procProvider === 'GEMINI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        Gemini
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <ModelSelector
                                    provider={procProvider as ApiKeyProvider}
                                    selectedModel={procModel}
                                    onChange={setProcModel}
                                    existingKey={isProviderKeyConfigured(procProvider)}
                                />
                            </div>
                        </div>
                        {!isProviderKeyConfigured(procProvider) && (
                            <p className="text-xs text-amber-600">
                                {procProvider} API key not configured
                            </p>
                        )}
                    </div>

                    <hr className="border-blush/30" />

                    {/* Copilot LLM */}
                    <div className="space-y-3">
                        <Label className="text-base font-medium">Copilot LLM</Label>
                        <p className="text-xs text-muted-foreground">
                            AI model for Copilot Ask, Insights, and Actions
                        </p>
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm">Provider</Label>
                                <div className="flex gap-2">
                                    <Button
                                        variant={copilotProvider === 'OPENAI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setCopilotProvider('OPENAI')}
                                        className={cn(
                                            copilotProvider === 'OPENAI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        OpenAI
                                    </Button>
                                    <Button
                                        variant={copilotProvider === 'GEMINI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setCopilotProvider('GEMINI')}
                                        className={cn(
                                            copilotProvider === 'GEMINI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        Gemini
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <ModelSelector
                                    provider={copilotProvider as ApiKeyProvider}
                                    selectedModel={copilotModel}
                                    onChange={setCopilotModel}
                                    existingKey={isProviderKeyConfigured(copilotProvider)}
                                />
                            </div>
                        </div>
                        {!isProviderKeyConfigured(copilotProvider) && (
                            <p className="text-xs text-amber-600">
                                {copilotProvider} API key not configured
                            </p>
                        )}
                    </div>

                    <hr className="border-blush/30" />

                    {/* AI Search LLM */}
                    <div className="space-y-3">
                        <Label className="text-base font-medium">AI Search LLM</Label>
                        <p className="text-xs text-muted-foreground">
                            AI model untuk fitur AI Search (chat conversational vendor search)
                        </p>
                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label className="text-sm">Provider</Label>
                                <div className="flex gap-2">
                                    <Button
                                        variant={aiSearchProvider === 'OPENAI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setAiSearchProvider('OPENAI')}
                                        className={cn(
                                            aiSearchProvider === 'OPENAI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        OpenAI
                                    </Button>
                                    <Button
                                        variant={aiSearchProvider === 'GEMINI' ? 'default' : 'outline'}
                                        size="sm"
                                        onClick={() => setAiSearchProvider('GEMINI')}
                                        className={cn(
                                            aiSearchProvider === 'GEMINI' && 'bg-crimson hover:bg-crimson/90'
                                        )}
                                    >
                                        Gemini
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <ModelSelector
                                    provider={aiSearchProvider as ApiKeyProvider}
                                    selectedModel={aiSearchModel}
                                    onChange={setAiSearchModel}
                                    existingKey={isProviderKeyConfigured(aiSearchProvider)}
                                />
                            </div>
                        </div>
                        {!isProviderKeyConfigured(aiSearchProvider) && (
                            <p className="text-xs text-amber-600">
                                {aiSearchProvider} API key not configured
                            </p>
                        )}
                    </div>

                    {/* Save Button */}
                    <div className="pt-4">
                        <Button
                            onClick={handleSave}
                            disabled={saveMutation.isPending}
                            className="bg-crimson hover:bg-crimson/90 text-white"
                        >
                            {saveMutation.isPending ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                'Save AI Configuration'
                            )}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

export default AdminApiKeys
