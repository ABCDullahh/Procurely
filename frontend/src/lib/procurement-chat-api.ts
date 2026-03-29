/**
 * Procurement Chat API client and types
 */

import { api } from './api'

// ====== Types ======

export interface VendorCardData {
    id: number
    name: string
    website: string | null
    logo_url: string | null
    industry: string | null
    location: string | null
    country: string | null
    description: string | null
    overall_score: number | null
    fit_score: number | null
    trust_score: number | null
    pricing_model: string | null
    pricing_details: string | null
    employee_count: string | null
    founded_year: number | null
    criteria_matched: string[]
    criteria_partial: string[]
    criteria_missing: string[]
}

export interface ComparisonRow {
    metric: string
    values: Record<string, unknown>
    best_vendor_id: number | null
}

export interface ComparisonData {
    vendors: VendorCardData[]
    rows: ComparisonRow[]
}

export interface FilterChip {
    id: string
    label: string
    icon: string | null
    filter_type: string
    filter_value: string
}

export interface SearchProgressStep {
    id: string
    label: string
    status: 'pending' | 'active' | 'completed' | 'failed'
    details: string | null
}

export interface SearchProgressData {
    steps: SearchProgressStep[]
    current_step: string
    progress_pct: number
    vendors_found: number
    sources_searched: number
    estimated_time_remaining: string | null
}

export interface EvidenceItem {
    vendor_id: number
    vendor_name: string
    field: string
    value: string
    snippet: string
    source_url: string
    confidence: number
}

// Enhanced card data types
export interface InsightData {
    type: 'recommendation' | 'trend' | 'warning' | 'highlight'
    title: string
    description: string
    action?: string
}

export interface StatData {
    label: string
    value: string | number
    change?: string
    changeType?: 'positive' | 'negative' | 'neutral'
    icon?: string
}

export interface CategoryData {
    name: string
    count: number
    percentage: number
    color?: string
}

export interface PricingData {
    vendor_name: string
    vendor_id: number
    pricing_model: string
    pricing_details?: string
    has_free_tier: boolean
    starting_price?: string
}

export interface SuggestedQuery {
    text: string
    type: 'refine' | 'compare' | 'explain' | 'action'
}

export interface ConversationContext {
    category: string | null
    keywords: string[]
    budget: string | null
    location: string | null
    requirements: string[]
}

export interface ChatAction {
    type:
        | 'VIEW_VENDOR'
        | 'ADD_TO_SHORTLIST'
        | 'COMPARE_VENDORS'
        | 'EXPORT_CSV'
        | 'GENERATE_REPORT'
        | 'APPLY_FILTER'
        | 'START_SEARCH'
        | 'REFINE_SEARCH'
        | 'CREATE_REQUEST'
        | 'START_DEEP_RESEARCH'  // Trigger web search
        | 'CANCEL_RESEARCH'  // Cancel ongoing research
    label: string
    payload: Record<string, unknown>
    variant: 'primary' | 'secondary' | 'outline' | 'ghost'
    icon: string | null
}

// Research types
export interface StartResearchRequest {
    category: string
    keywords: string[]
    location?: string
    budget_max?: number
    conversation_id?: string
}

export interface ResearchStatusResponse {
    request_id: number
    run_id: number
    status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'
    current_step: string | null
    progress_pct: number
    vendors_found: number
    partial_vendors: VendorCardData[] | null
    error_message: string | null
    is_complete: boolean
}

export type ResponseType =
    | 'text'
    | 'vendors'
    | 'comparison'
    | 'progress'
    | 'evidence'
    | 'criteria_builder'
    | 'chart'
    | 'gathering_info'
    | 'deep_research'  // DeepResearch in progress
    | 'error'

export interface ProcurementChatRequest {
    message: string
    conversation_id?: string
    context?: Record<string, unknown>
    mode?: 'search' | 'refine' | 'compare' | 'explain' | 'create'
    run_id?: number
    vendor_ids?: number[]
}

export interface ProcurementChatResponse {
    message_id: string
    conversation_id: string
    response_type: ResponseType
    text_content: string
    vendors: VendorCardData[] | null
    comparison: ComparisonData | null
    progress: SearchProgressData | null
    evidence: EvidenceItem[] | null
    chart_data: Record<string, unknown> | null
    filter_chips: FilterChip[]
    suggested_queries: SuggestedQuery[]
    actions: ChatAction[]
    run_id: number | null
    request_id: number | null
    timestamp: string
    // Enhanced data for professional cards
    insights: InsightData[] | null
    quick_stats: StatData[] | null
    categories: CategoryData[] | null
    pricing_overview: PricingData[] | null
    // Conversation context for follow-up messages
    context: ConversationContext | null
}

export interface ChatMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    response_type?: ResponseType
    data?: ProcurementChatResponse
    timestamp: Date
}

// ====== API Functions ======

export const procurementChatApi = {
    /**
     * Send a message to the procurement chat assistant
     */
    sendMessage: async (payload: ProcurementChatRequest): Promise<ProcurementChatResponse> => {
        const response = await api.post<ProcurementChatResponse>('/procurement-chat/message', payload)
        return response.data
    },

    /**
     * Start a DeepResearch from chat
     */
    startResearch: async (payload: StartResearchRequest): Promise<ResearchStatusResponse> => {
        const response = await api.post<ResearchStatusResponse>('/procurement-chat/research/start', payload)
        return response.data
    },

    /**
     * Get research status (poll for updates)
     */
    getResearchStatus: async (runId: number): Promise<ResearchStatusResponse> => {
        const response = await api.get<ResearchStatusResponse>(`/procurement-chat/research/${runId}/status`)
        return response.data
    },

    /**
     * Cancel ongoing research
     */
    cancelResearch: async (runId: number): Promise<{ success: boolean; message: string }> => {
        const response = await api.post<{ success: boolean; message: string }>(`/procurement-chat/research/${runId}/cancel`)
        return response.data
    },
}
