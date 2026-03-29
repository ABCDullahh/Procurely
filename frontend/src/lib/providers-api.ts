import { api } from './api'

export interface DataProvider {
    name: string
    provider_type: 'SEARCH' | 'SCRAPE' | 'HYBRID'
    display_name: string
    description: string | null
    requires_api_key: boolean
    api_key_provider: string | null
    is_configured: boolean
    is_enabled: boolean
    is_default: boolean
    is_free: boolean
}

export interface ProvidersListResponse {
    providers: DataProvider[]
    search_providers: string[]
    scrape_providers: string[]
}

export interface ProviderDefaults {
    search: string[]
    scrape: string[]
}

export interface ProviderStatusResponse {
    provider: string
    status: 'AVAILABLE' | 'UNAVAILABLE' | 'NOT_CONFIGURED' | 'UNKNOWN'
    message: string | null
}

export interface UpdateProviderRequest {
    is_enabled?: boolean
    is_default?: boolean
}

export interface ResearchConfig {
    enabled: boolean
    max_iterations: number
    gap_threshold: number
    include_shopping: boolean
    region_bias: boolean
    location: string | null
}

export interface LocaleOption {
    code: string
    name: string
    country_code: string
    default: boolean
}

export interface LocalesResponse {
    locales: LocaleOption[]
    default: string
}

export interface ShoppingStatusResponse {
    provider: string
    is_configured: boolean
    is_enabled: boolean
    message: string
}

export const providersApi = {
    /**
     * List all available data providers
     */
    list: async (): Promise<ProvidersListResponse> => {
        const response = await api.get('/providers')
        return response.data
    },

    /**
     * Get default provider selection
     */
    getDefaults: async (): Promise<ProviderDefaults> => {
        const response = await api.get('/providers/defaults')
        return response.data
    },

    /**
     * Check status of a specific provider
     */
    checkStatus: async (providerName: string): Promise<ProviderStatusResponse> => {
        const response = await api.get(`/providers/${providerName}/status`)
        return response.data
    },

    /**
     * Update provider settings (enable/disable, set default)
     */
    update: async (providerName: string, request: UpdateProviderRequest): Promise<DataProvider> => {
        const response = await api.put(`/providers/${providerName}`, request)
        return response.data
    },

    /**
     * Get available locales for region-focused search
     */
    getLocales: async (): Promise<LocalesResponse> => {
        const response = await api.get('/providers/locales')
        return response.data
    },

    /**
     * Get current research configuration
     */
    getResearchConfig: async (): Promise<ResearchConfig> => {
        const response = await api.get('/providers/research-config')
        return response.data
    },

    /**
     * Update research configuration
     */
    updateResearchConfig: async (config: Partial<ResearchConfig>): Promise<ResearchConfig> => {
        const response = await api.put('/providers/research-config', config)
        return response.data
    },

    /**
     * Get shopping provider status
     */
    getShoppingStatus: async (): Promise<ShoppingStatusResponse> => {
        const response = await api.get('/providers/shopping/status')
        return response.data
    },
}

export default providersApi
