/**
 * New Request Page - Simplified Single-Page Form
 * Creates a procurement request with minimal required fields.
 * Keywords are auto-generated from title/description.
 */

import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowLeft, Loader2, Search, X, Sparkles, MapPin, Wallet, AlertTriangle, Info } from 'lucide-react'
import { Button, Card, CardContent, Input, Label } from '@/components/ui'
import { useToast } from '@/components/ui/toast'
import { requestsApi, CreateRequestData } from '@/lib/requests-api'
import { authApi } from '@/lib/api'
import { cn } from '@/lib/utils'

const CATEGORIES = [
    { id: 'furniture', label: 'Furniture', icon: '🪑' },
    { id: 'software', label: 'Software', icon: '💻' },
    { id: 'cloud', label: 'Cloud Services', icon: '☁️' },
    { id: 'consulting', label: 'Consulting', icon: '💼' },
    { id: 'marketing', label: 'Marketing', icon: '📣' },
    { id: 'it', label: 'IT Infrastructure', icon: '🖥️' },
    { id: 'professional', label: 'Professional Services', icon: '👔' },
    { id: 'manufacturing', label: 'Manufacturing', icon: '🏭' },
    { id: 'logistics', label: 'Logistics', icon: '🚚' },
    { id: 'other', label: 'Other', icon: '📦' },
]

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value)

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay)
        return () => clearTimeout(timer)
    }, [value, delay])

    return debouncedValue
}

export function NewRequestPage() {
    const navigate = useNavigate()
    const { addToast } = useToast()

    // Tier info query
    const { data: tierInfo } = useQuery({
        queryKey: ['tier-info'],
        queryFn: () => authApi.tierInfo(),
        staleTime: 10000,
    })

    const isFreeTier = tierInfo?.tier === 'free'
    const canSearch = tierInfo?.can_search ?? true
    const searchesRemaining = tierInfo ? (tierInfo.searches_limit === -1 ? -1 : Math.max(0, tierInfo.searches_limit - tierInfo.searches_used)) : -1

    // Form state - simplified
    const [title, setTitle] = useState('')
    const [description, setDescription] = useState('')
    const [category, setCategory] = useState('')
    const [location, setLocation] = useState('')
    const [budgetMax, setBudgetMax] = useState<number | undefined>(undefined)
    const [keywords, setKeywords] = useState<string[]>([])
    const [keywordInput, setKeywordInput] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    // Debounced values for keyword generation
    const debouncedTitle = useDebounce(title, 500)
    const debouncedDescription = useDebounce(description, 500)
    const debouncedCategory = useDebounce(category, 500)

    // Auto-generate keywords when title/description/category changes
    const { data: suggestedKeywords, isLoading: isGeneratingKeywords } = useQuery({
        queryKey: ['generate-keywords', debouncedTitle, debouncedDescription, debouncedCategory],
        queryFn: () => requestsApi.generateKeywords({
            title: debouncedTitle,
            description: debouncedDescription || undefined,
            category: debouncedCategory,
        }),
        enabled: debouncedTitle.length >= 5 && debouncedCategory.length > 0,
        staleTime: 30000,
    })

    // Update keywords when suggestions arrive (only if user hasn't modified)
    useEffect(() => {
        if (suggestedKeywords?.keywords && keywords.length === 0) {
            setKeywords(suggestedKeywords.keywords)
        }
    }, [suggestedKeywords, keywords.length])

    const addKeyword = useCallback(() => {
        const trimmed = keywordInput.trim()
        if (trimmed && !keywords.includes(trimmed)) {
            setKeywords(prev => [...prev, trimmed])
            setKeywordInput('')
        }
    }, [keywordInput, keywords])

    const removeKeyword = useCallback((index: number) => {
        setKeywords(prev => prev.filter((_, i) => i !== index))
    }, [])

    // Create mutation
    const createMutation = useMutation({
        mutationFn: (data: CreateRequestData) => requestsApi.create(data),
        onSuccess: async (newRequest) => {
            // Immediately submit the request to start search
            try {
                await requestsApi.submit(newRequest.id)
                addToast({
                    type: 'success',
                    title: 'Search Started',
                    message: 'Searching for vendors matching your requirements...',
                })
                navigate(`/requests/${newRequest.id}`)
            } catch (err) {
                // If submit fails, still navigate to the request
                addToast({
                    type: 'success',
                    title: 'Request Created',
                    message: 'Your request was created. You can start the search from the details page.',
                })
                navigate(`/requests/${newRequest.id}`)
            }
        },
        onError: (error: Error) => {
            addToast({
                type: 'error',
                title: 'Failed to create request',
                message: error.message,
            })
            setIsSubmitting(false)
        },
    })

    const handleSubmit = async () => {
        if (!title.trim() || !category) {
            addToast({
                type: 'error',
                title: 'Missing required fields',
                message: 'Please provide a title and select a category.',
            })
            return
        }

        setIsSubmitting(true)

        // Submit with auto-generated keywords if none provided
        createMutation.mutate({
            title: title.trim(),
            description: description.trim() || undefined,
            category,
            keywords: keywords.length > 0 ? keywords : undefined,
            auto_generate_keywords: keywords.length === 0,
            location: location.trim() || undefined,
            budget_max: budgetMax,
            // Smart defaults applied by backend
        })
    }

    const canSubmit = title.trim().length > 0 && category.length > 0 && canSearch

    return (
        <div className="min-h-screen bg-background">
            <div className="max-w-2xl mx-auto p-6">
                {/* Header */}
                <button
                    onClick={() => navigate('/requests')}
                    className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Requests
                </button>

                <div className="mb-8">
                    <h1 className="text-3xl font-display font-bold tracking-tight text-[#1A1816]">Find Vendors</h1>
                    <p className="text-sm text-[#A09A93] mt-2">
                        Tell us what you're looking for and we'll find the best vendors.
                    </p>
                </div>

                <Card className="border-[#ECE8E1]">
                    <CardContent className="p-6 space-y-6">
                        {/* Title */}
                        <div className="space-y-2">
                            <Label htmlFor="title" className="text-base font-medium">
                                What are you looking for? <span className="text-red-500">*</span>
                            </Label>
                            <Input
                                id="title"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="e.g., Office desks for new Jakarta office"
                                className="text-lg py-3"
                            />
                        </div>

                        {/* Description */}
                        <div className="space-y-2">
                            <Label htmlFor="description" className="text-base font-medium">
                                Additional details <span className="text-muted-foreground">(optional)</span>
                            </Label>
                            <textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe specific requirements, quantities, features..."
                                className="w-full px-3 py-2 border border-[#ECE8E1] rounded-xl bg-background resize-none h-24 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                            />
                        </div>

                        {/* Category */}
                        <div className="space-y-3">
                            <Label className="text-base font-medium">
                                Category <span className="text-red-500">*</span>
                            </Label>
                            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                                {CATEGORIES.map((cat) => (
                                    <button
                                        key={cat.id}
                                        type="button"
                                        onClick={() => setCategory(cat.label)}
                                        className={cn(
                                            'px-3 py-2 border rounded-xl text-sm transition-all flex flex-col items-center gap-1',
                                            category === cat.label
                                                ? 'border-crimson-600 bg-crimson-50 text-crimson-600 ring-1 ring-crimson-200'
                                                : 'border-[#ECE8E1] hover:bg-[#F3F0EB] text-[#6B6560]'
                                        )}
                                    >
                                        <span className="text-lg">{cat.icon}</span>
                                        <span className="text-xs">{cat.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Location & Budget - Side by side */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="location" className="flex items-center gap-2">
                                    <MapPin className="w-4 h-4 text-muted-foreground" />
                                    Location <span className="text-muted-foreground text-xs">(optional)</span>
                                </Label>
                                <Input
                                    id="location"
                                    value={location}
                                    onChange={(e) => setLocation(e.target.value)}
                                    placeholder="e.g., Jakarta, Indonesia"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="budget" className="flex items-center gap-2">
                                    <Wallet className="w-4 h-4 text-muted-foreground" />
                                    Max Budget <span className="text-muted-foreground text-xs">(optional)</span>
                                </Label>
                                <div className="relative">
                                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                        Rp
                                    </span>
                                    <Input
                                        id="budget"
                                        type="number"
                                        value={budgetMax || ''}
                                        onChange={(e) => setBudgetMax(e.target.value ? parseInt(e.target.value) : undefined)}
                                        placeholder="500.000.000"
                                        className="pl-10"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Keywords */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label className="flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-yellow-500" />
                                    Search Keywords
                                </Label>
                                {isGeneratingKeywords && (
                                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                                        <Loader2 className="w-3 h-3 animate-spin" />
                                        Generating...
                                    </span>
                                )}
                            </div>
                            <div className="flex gap-2">
                                <Input
                                    value={keywordInput}
                                    onChange={(e) => setKeywordInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault()
                                            addKeyword()
                                        }
                                    }}
                                    placeholder="Add keyword and press Enter"
                                    className="flex-1"
                                />
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={addKeyword}
                                    disabled={!keywordInput.trim()}
                                >
                                    Add
                                </Button>
                            </div>
                            {keywords.length > 0 ? (
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {keywords.map((kw, i) => (
                                        <span
                                            key={i}
                                            className="px-3 py-1 bg-[#F3F0EB] text-[#1A1816] rounded-full text-sm flex items-center gap-2 group border border-[#ECE8E1]"
                                        >
                                            {kw}
                                            <button
                                                onClick={() => removeKeyword(i)}
                                                className="hover:text-red-500 opacity-50 group-hover:opacity-100"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-muted-foreground">
                                    Keywords will be auto-generated from your title and description
                                </p>
                            )}
                        </div>

                        {/* Submit */}
                        <div className="pt-4 border-t border-[#F3F0EB]">
                            {/* Free tier: no searches remaining */}
                            {isFreeTier && !canSearch && (
                                <div className="mb-4 p-4 rounded-xl border border-amber-200 bg-amber-50 flex items-start gap-3">
                                    <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-medium text-amber-800">
                                            You've used your free search
                                        </p>
                                        <p className="text-xs text-amber-700 mt-1">
                                            Free tier allows 1 search only.{' '}
                                            <a
                                                href="mailto:faizal2jz@gmail.com"
                                                className="underline font-medium hover:text-amber-900"
                                            >
                                                Contact us
                                            </a>
                                            {' '}for unlimited access.
                                        </p>
                                    </div>
                                </div>
                            )}

                            {/* Free tier: 1 search remaining */}
                            {isFreeTier && canSearch && searchesRemaining === 1 && (
                                <div className="mb-4 p-3 rounded-xl border border-blue-200 bg-blue-50 flex items-center gap-2.5">
                                    <Info className="w-4 h-4 text-blue-600 flex-shrink-0" />
                                    <p className="text-xs text-blue-700">
                                        <span className="font-semibold">1 free search remaining.</span> Make it count!
                                    </p>
                                </div>
                            )}

                            <Button
                                size="lg"
                                className="w-full bg-[#1A1816] hover:bg-[#1A1816]/90 text-white"
                                onClick={handleSubmit}
                                disabled={!canSubmit || isSubmitting}
                            >
                                {isSubmitting ? (
                                    <>
                                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                        Starting Search...
                                    </>
                                ) : (
                                    <>
                                        <Search className="w-5 h-5 mr-2" />
                                        Find Vendors
                                    </>
                                )}
                            </Button>
                            <p className="text-xs text-center text-muted-foreground mt-3">
                                We'll search multiple sources and present the best matches
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}

export default NewRequestPage
