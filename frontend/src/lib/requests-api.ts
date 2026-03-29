/**
 * Procurement Requests API client
 */

import api from './api'

export type RequestStatus = 'DRAFT' | 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'

export interface ProcurementRequest {
    id: number
    title: string
    description: string | null
    category: string
    keywords: string[]
    location: string | null
    budget_min: number | null
    budget_max: number | null
    timeline: string | null
    must_have_criteria: string[] | null
    nice_to_have_criteria: string[] | null
    selected_providers: string[] | null
    locale: string
    country_code: string
    region_bias: boolean
    research_config: ResearchConfigInput | null
    status: RequestStatus
    created_by_email: string
    created_at: string
    updated_at: string
    latest_run_status: string | null
    vendors_found: number
}

export interface ProcurementRequestListResponse {
    requests: ProcurementRequest[]
    total: number
    page: number
    page_size: number
}

export interface ResearchConfigInput {
    max_iterations: number
    gap_threshold: number
    include_shopping: boolean
}

export interface CreateRequestData {
    title: string
    description?: string
    category: string
    keywords?: string[]  // Now optional - auto-generated if not provided
    auto_generate_keywords?: boolean  // Auto-generate keywords if not provided
    location?: string
    budget_min?: number
    budget_max?: number
    timeline?: string
    must_have_criteria?: string[]
    nice_to_have_criteria?: string[]
    selected_providers?: string[]
    // Indonesia focus settings
    locale?: string
    country_code?: string
    region_bias?: boolean
    research_config?: ResearchConfigInput
}

export interface KeywordGenerationRequest {
    title: string
    description?: string
    category: string
}

export interface KeywordGenerationResponse {
    keywords: string[]
}

export interface UpdateRequestData extends Partial<CreateRequestData> {
    status?: RequestStatus
}

export interface PipelineLogEntry {
    timestamp: string
    step: string
    level: 'info' | 'warning' | 'error' | 'debug'
    message: string
    data?: Record<string, unknown>
}

export interface TokenUsageEntry {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
    calls: number
    model: string
}

export interface SearchRun {
    id: number
    request_id: number
    status: string
    current_step: string | null
    progress_pct: number
    vendors_found: number
    sources_searched: number
    error_message: string | null
    started_at: string | null
    completed_at: string | null
    created_at: string
    // Pipeline logging and token tracking
    pipeline_logs?: PipelineLogEntry[] | null
    token_usage?: Record<string, TokenUsageEntry> | null
}

export const requestsApi = {
    /**
     * Generate keywords from title and description using LLM
     */
    generateKeywords: async (data: KeywordGenerationRequest): Promise<KeywordGenerationResponse> => {
        const response = await api.post<KeywordGenerationResponse>('/requests/generate-keywords', data)
        return response.data
    },

    /**
     * List procurement requests with pagination
     */
    list: async (params?: {
        status?: RequestStatus
        page?: number
        page_size?: number
    }): Promise<ProcurementRequestListResponse> => {
        const response = await api.get<ProcurementRequestListResponse>('/requests', {
            params,
        })
        return response.data
    },

    /**
     * Get a single procurement request
     */
    get: async (id: number): Promise<ProcurementRequest> => {
        const response = await api.get<ProcurementRequest>(`/requests/${id}`)
        return response.data
    },

    /**
     * Create a new procurement request
     */
    create: async (data: CreateRequestData): Promise<ProcurementRequest> => {
        const response = await api.post<ProcurementRequest>('/requests', data)
        return response.data
    },

    /**
     * Update a procurement request
     */
    update: async (id: number, data: UpdateRequestData): Promise<ProcurementRequest> => {
        const response = await api.put<ProcurementRequest>(`/requests/${id}`, data)
        return response.data
    },

    /**
     * Delete a procurement request
     */
    delete: async (id: number): Promise<void> => {
        await api.delete(`/requests/${id}`)
    },

    /**
     * Submit a draft request to start the search pipeline
     */
    submit: async (id: number): Promise<ProcurementRequest> => {
        const response = await api.post<ProcurementRequest>(`/requests/${id}/submit`)
        return response.data
    },

    /**
     * List all search runs for a request
     */
    listRuns: async (id: number): Promise<SearchRun[]> => {
        const response = await api.get<SearchRun[]>(`/requests/${id}/runs`)
        return response.data
    },

    /**
     * Get a specific search run by ID
     */
    getRun: async (runId: number): Promise<SearchRun> => {
        const response = await api.get<SearchRun>(`/runs/${runId}`)
        return response.data
    },

    /**
     * Cancel an active search run
     */
    cancelRun: async (runId: number): Promise<SearchRun> => {
        const response = await api.post<SearchRun>(`/runs/${runId}/cancel`)
        return response.data
    },
}
