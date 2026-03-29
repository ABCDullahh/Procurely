/**
 * Provider Settings Row Component
 * Shows provider info with enable/disable, default selection, and API key management
 */

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Eye, EyeOff, TestTube, Loader2, Check, X } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button, Card, CardContent, Input } from '@/components/ui'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/components/ui/toast'
import { DataProvider } from '@/lib/providers-api'
import { providersApi } from '@/lib/providers-api'
import { adminApi, ApiKeyResponse, ApiKeyProvider, SetApiKeyPayload } from '@/lib/admin-api'
import { cn } from '@/lib/utils'

interface ProviderSettingsRowProps {
    provider: DataProvider
    apiKey: ApiKeyResponse | null
    onApiKeySaved?: () => void
}

export function ProviderSettingsRow({ provider, apiKey, onApiKeySaved }: ProviderSettingsRowProps) {
    const { addToast } = useToast()
    const queryClient = useQueryClient()
    const [keyValue, setKeyValue] = useState('')
    const [showKey, setShowKey] = useState(false)
    const [isEditing, setIsEditing] = useState(false)
    const [isTesting, setIsTesting] = useState(false)

    const isConfigured = provider.requires_api_key ? provider.is_configured : true

    // Update provider mutation (enable/disable, default)
    const updateMutation = useMutation({
        mutationFn: ({ isEnabled, isDefault }: { isEnabled?: boolean; isDefault?: boolean }) =>
            providersApi.update(provider.name, { is_enabled: isEnabled, is_default: isDefault }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['providers'] })
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Update Failed',
                message: error.message,
            })
        },
    })

    // Set API key mutation
    const setKeyMutation = useMutation({
        mutationFn: (payload: SetApiKeyPayload) => {
            const keyProvider = provider.api_key_provider as ApiKeyProvider
            return adminApi.setApiKey(keyProvider, payload)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin', 'api-keys'] })
            queryClient.invalidateQueries({ queryKey: ['providers'] })
            setKeyValue('')
            setIsEditing(false)
            onApiKeySaved?.()
            addToast({
                type: 'success',
                title: 'API Key Saved',
                message: `${provider.display_name} API key configured successfully.`,
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

    // Test API key mutation
    const testKeyMutation = useMutation({
        mutationFn: () => {
            const keyProvider = provider.api_key_provider as ApiKeyProvider
            return adminApi.testApiKey(keyProvider)
        },
        onMutate: () => setIsTesting(true),
        onSettled: () => setIsTesting(false),
        onSuccess: (result) => {
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
            addToast({
                type: 'error',
                title: 'Test Failed',
                message: error.message,
            })
        },
    })

    const handleEnableChange = (checked: boolean) => {
        updateMutation.mutate({ isEnabled: checked })
    }

    const handleDefaultChange = (checked: boolean) => {
        updateMutation.mutate({ isDefault: checked })
    }

    const handleSaveKey = () => {
        if (!keyValue.trim()) return
        setKeyMutation.mutate({ value: keyValue.trim() })
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
        >
            <Card className={cn(
                'transition-all duration-200',
                isConfigured && provider.is_enabled ? 'border-green-500/30' : 'border-muted/50'
            )}>
                <CardContent className="py-4">
                    <div className="flex flex-col gap-4">
                        {/* Header Row */}
                        <div className="flex items-start justify-between gap-4">
                            {/* Provider Info */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                    <h3 className="font-medium text-foreground">{provider.display_name}</h3>
                                    {provider.is_free && (
                                        <span className="px-2 py-0.5 text-xs font-medium bg-green-500/10 text-green-600 rounded">
                                            FREE
                                        </span>
                                    )}
                                    {/* Status Badge */}
                                    {provider.requires_api_key && (
                                        <span className={cn(
                                            'flex items-center gap-1 px-2 py-0.5 text-xs rounded',
                                            isConfigured
                                                ? 'bg-green-500/10 text-green-600'
                                                : 'bg-amber-500/10 text-amber-600'
                                        )}>
                                            {isConfigured ? (
                                                <><Check className="w-3 h-3" /> Configured</>
                                            ) : (
                                                <><X className="w-3 h-3" /> Not Configured</>
                                            )}
                                        </span>
                                    )}
                                </div>
                                <p className="text-sm text-muted-foreground mt-1">{provider.description}</p>
                            </div>

                            {/* Checkboxes */}
                            <div className="flex items-center gap-4 shrink-0">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <Checkbox
                                        checked={provider.is_enabled}
                                        onCheckedChange={handleEnableChange}
                                        disabled={updateMutation.isPending || (!isConfigured && provider.requires_api_key)}
                                    />
                                    <span className="text-sm">Enabled</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <Checkbox
                                        checked={provider.is_default}
                                        onCheckedChange={handleDefaultChange}
                                        disabled={updateMutation.isPending || !provider.is_enabled}
                                    />
                                    <span className="text-sm">Default</span>
                                </label>
                            </div>
                        </div>

                        {/* API Key Section */}
                        {provider.requires_api_key && (
                            <div className="flex items-center gap-3 pt-2 border-t border-muted/30">
                                {isEditing ? (
                                    <>
                                        <div className="relative flex-1 max-w-md">
                                            <Input
                                                type={showKey ? 'text' : 'password'}
                                                value={keyValue}
                                                onChange={(e) => setKeyValue(e.target.value)}
                                                placeholder={`Enter ${provider.display_name} API key...`}
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
                                        <Button
                                            size="sm"
                                            onClick={handleSaveKey}
                                            disabled={!keyValue.trim() || setKeyMutation.isPending}
                                            className="bg-crimson hover:bg-crimson/90 text-white"
                                        >
                                            {setKeyMutation.isPending ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                'Save'
                                            )}
                                        </Button>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => {
                                                setIsEditing(false)
                                                setKeyValue('')
                                            }}
                                        >
                                            Cancel
                                        </Button>
                                    </>
                                ) : (
                                    <>
                                        {apiKey ? (
                                            <div className="flex items-center gap-3">
                                                <span className="font-mono text-sm text-muted-foreground">
                                                    ••••••••{apiKey.masked_tail}
                                                </span>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => setIsEditing(true)}
                                                >
                                                    Update
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => testKeyMutation.mutate()}
                                                    disabled={isTesting}
                                                >
                                                    {isTesting ? (
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                    ) : (
                                                        <><TestTube className="w-4 h-4 mr-1" /> Test</>
                                                    )}
                                                </Button>
                                            </div>
                                        ) : (
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => setIsEditing(true)}
                                            >
                                                Set API Key
                                            </Button>
                                        )}
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    )
}

export default ProviderSettingsRow
