/**
 * Admin API client for API key management
 */

import api from './api'

export interface ApiKeyResponse {
    provider: string
    masked_tail: string
    is_active: boolean
    default_model: string | null
    updated_at: string
    updated_by_email: string
}

export interface ApiKeyListResponse {
    keys: ApiKeyResponse[]
}

export interface ApiKeyTestResponse {
    ok: boolean
    message: string
    provider: string
    latency_ms: number | null
}

export interface AuditLogResponse {
    id: number
    actor_email: string
    action: string
    target_type: string
    target_id: string | null
    metadata_json: string | null
    created_at: string
}

export interface AuditLogListResponse {
    logs: AuditLogResponse[]
    total: number
    page: number
    page_size: number
}

export interface ProviderModel {
    id: string
    label: string
    supports: string[]
}

export interface ProviderModelsResponse {
    provider: string
    models: ProviderModel[]
    source: 'live' | 'curated'
    fetched_at: string
}

export type ApiKeyProvider = 'OPENAI' | 'GEMINI' | 'SEARCH_PROVIDER' | 'TAVILY' | 'FIRECRAWL' | 'SERPAPI'

export interface SetApiKeyPayload {
    value: string
    default_model?: string | null
}

// API Key endpoints
export const adminApi = {
    /**
     * List all configured API keys (masked values only)
     */
    listApiKeys: async (): Promise<ApiKeyListResponse> => {
        const response = await api.get<ApiKeyListResponse>('/admin/api-keys')
        return response.data
    },

    /**
     * Set or update an API key for a provider
     */
    setApiKey: async (provider: ApiKeyProvider, payload: SetApiKeyPayload): Promise<ApiKeyResponse> => {
        const response = await api.put<ApiKeyResponse>(
            `/admin/api-keys/${provider}`,
            payload
        )
        return response.data
    },

    /**
     * Rotate an API key (deactivates old, sets new)
     */
    rotateApiKey: async (provider: ApiKeyProvider, payload: SetApiKeyPayload): Promise<ApiKeyResponse> => {
        const response = await api.post<ApiKeyResponse>(
            `/admin/api-keys/${provider}/rotate`,
            payload
        )
        return response.data
    },

    /**
     * Test an API key connection
     */
    testApiKey: async (provider: ApiKeyProvider): Promise<ApiKeyTestResponse> => {
        const response = await api.post<ApiKeyTestResponse>(
            `/admin/api-keys/${provider}/test`
        )
        return response.data
    },

    /**
     * Delete (deactivate) an API key
     */
    deleteApiKey: async (provider: ApiKeyProvider): Promise<void> => {
        await api.delete(`/admin/api-keys/${provider}`)
    },

    /**
     * Fetch available models for a provider (live or curated)
     */
    fetchProviderModels: async (provider: ApiKeyProvider): Promise<ProviderModelsResponse> => {
        const response = await api.get<ProviderModelsResponse>(
            `/admin/api-keys/provider-models/${provider}`
        )
        return response.data
    },

    /**
     * List audit logs with filtering/pagination
     */
    listAuditLogs: async (params: {
        action?: string
        target_type?: string
        page?: number
        page_size?: number
    }): Promise<AuditLogListResponse> => {
        const response = await api.get<AuditLogListResponse>('/admin/audit-logs', {
            params
        })
        return response.data
    },

    /**
     * Get current search strategy setting
     */
    getSearchStrategy: async (): Promise<SearchStrategyResponse> => {
        const response = await api.get<SearchStrategyResponse>('/admin/settings/search-strategy')
        return response.data
    },

    /**
     * Update search strategy setting
     */
    setSearchStrategy: async (strategy: SearchStrategy): Promise<SearchStrategyResponse> => {
        const response = await api.put<SearchStrategyResponse>(
            '/admin/settings/search-strategy',
            { strategy }
        )
        return response.data
    },

    /**
     * Get complete AI configuration
     */
    getAIConfig: async (): Promise<AIConfigResponse> => {
        const response = await api.get<AIConfigResponse>('/admin/settings/ai-config')
        return response.data
    },

    /**
     * Update AI configuration
     */
    setAIConfig: async (config: AIConfigRequest): Promise<AIConfigResponse> => {
        const response = await api.put<AIConfigResponse>(
            '/admin/settings/ai-config',
            config
        )
        return response.data
    },
}

// Search strategy types
export type SearchStrategy = 'SERPER' | 'GEMINI_GROUNDING' | 'TAVILY'

export interface SearchStrategyResponse {
    strategy: SearchStrategy
    description: string
}

// LLM Provider type
export type LLMProvider = 'OPENAI' | 'GEMINI'

// AI Config types
export interface WebSearchConfig {
    provider: SearchStrategy
    gemini_model: string | null
    key_configured: boolean
}

export interface LLMConfig {
    provider: LLMProvider
    model: string
    key_configured: boolean
}

export interface AIConfigResponse {
    web_search: WebSearchConfig
    procurement_llm: LLMConfig
    copilot_llm: LLMConfig
    ai_search_llm: LLMConfig
    available_search_providers: Array<{
        value: string
        label: string
        requires_key: string
    }>
}

export interface AIConfigRequest {
    web_search_provider?: SearchStrategy
    web_search_gemini_model?: string
    procurement_provider?: LLMProvider
    procurement_model?: string
    copilot_provider?: LLMProvider
    copilot_model?: string
    ai_search_provider?: LLMProvider
    ai_search_model?: string
}

