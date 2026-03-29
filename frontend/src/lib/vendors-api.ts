/**
 * Vendors and Runs API client
 */

import api from './api'

export interface VendorMetrics {
    fit_score: number
    trust_score: number
    quality_score: number
    price_score: number
    overall_score: number
    must_have_matched: number
    must_have_total: number
    nice_to_have_matched: number
    nice_to_have_total: number
    source_count: number
    evidence_count: number
    // DeepResearch quality metrics
    completeness_pct: number
    confidence_pct: number
    source_diversity: number
    research_depth: number
    price_competitiveness: number | null
}

export interface VendorStructuredData {
    target_segment: string | null
    regions_served: string | null
    use_cases: string[] | null
    key_features: string[] | null
    differentiators: string[] | null
    limitations: string[] | null
    notable_customers: string[] | null
    support_channels: string | null
    onboarding_time: string | null
    contract_terms: string | null
    data_hosting: string | null
    sso_saml: boolean | null
}

export interface ShoppingProduct {
    title: string
    price: number | null
    price_raw: string
    currency: string
    source: string
    link: string
    thumbnail: string | null
    rating: number | null
    reviews_count: number | null
}

export interface VendorShoppingData {
    vendor_name: string | null
    products: ShoppingProduct[]
    price_min: number | null
    price_max: number | null
    price_avg: number | null
    market_avg: number | null
    price_competitiveness: number | null
    sources: string[]
}

export interface CategoryBenchmark {
    category: string | null
    price_min: number | null
    price_max: number | null
    price_avg: number | null
    price_median: number | null
    sample_size: number
    sources: string[]
}

export interface SearchRunShoppingData {
    category_benchmark: CategoryBenchmark | null
    market_avg: number | null
    total_products: number
    search_queries: string[]
}

export interface Vendor {
    id: number
    name: string
    website: string | null
    description: string | null
    location: string | null
    country: string | null
    industry: string | null
    founded_year: number | null
    employee_count: string | null
    email: string | null
    phone: string | null
    pricing_model: string | null
    pricing_details: string | null
    // New procurement fields
    security_compliance: string | null
    deployment: string | null
    integrations: string | null
    structured_data: VendorStructuredData | null
    // Shopping/pricing data from Google Shopping
    shopping_data: VendorShoppingData | null
    price_range_min: number | null
    price_range_max: number | null
    price_last_updated: string | null
    created_at: string
    updated_at: string
    logo_url: string | null
    metrics: VendorMetrics | null
}

export interface VendorListResponse {
    vendors: Vendor[]
    total: number
    page: number
    page_size: number
}

export interface VendorSource {
    id: number
    source_url: string
    source_type: string
    source_category: string | null
    page_title: string | null
    content_summary: string | null
    fetch_status: string
    fetched_at: string
}

export interface VendorEvidence {
    id: number
    field_name: string
    field_label: string | null
    field_value: string
    category: string | null
    evidence_url: string | null
    evidence_snippet: string | null
    source_title: string | null
    confidence: number
    extraction_method: string
    extracted_at: string
}

export interface VendorAsset {
    id: number
    asset_type: string
    asset_url: string
    source_url: string | null
    mime_type: string | null
    width: number | null
    height: number | null
    priority: number
    fetched_at: string | null
}

export interface SearchRunDetail {
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
    // DeepResearch tracking
    research_iterations: number
    quality_assessment: Record<string, unknown> | null
    shopping_data: SearchRunShoppingData | null
}

export const runsApi = {
    /**
     * Get search run by ID
     */
    get: async (runId: number): Promise<SearchRunDetail> => {
        const response = await api.get<SearchRunDetail>(`/runs/${runId}`)
        return response.data
    },

    /**
     * List vendors for a search run
     */
    listVendors: async (
        runId: number,
        params?: {
            page?: number
            page_size?: number
            sort_by?: 'overall_score' | 'name' | 'created_at'
            sort_order?: 'asc' | 'desc'
        }
    ): Promise<VendorListResponse> => {
        const response = await api.get<VendorListResponse>(`/runs/${runId}/vendors`, {
            params,
        })
        return response.data
    },
}

export const vendorsApi = {
    /**
     * Get vendor by ID
     */
    get: async (vendorId: number): Promise<VendorDetail> => {
        const response = await api.get<VendorDetail>(`/vendors/${vendorId}`)
        return response.data
    },

    /**
     * List vendors by run ID
     */
    listByRun: async (
        runId: number,
        params?: {
            page?: number
            page_size?: number
            sort_by?: string
            sort_order?: 'asc' | 'desc'
            q?: string
        }
    ): Promise<VendorListResponse> => {
        const response = await api.get<VendorListResponse>(`/runs/${runId}/vendors`, {
            params,
        })
        return response.data
    },

    /**
     * Get vendor evidence
     */
    getEvidence: async (vendorId: number): Promise<VendorEvidenceResponse> => {
        const response = await api.get(`/vendors/${vendorId}/evidence`)
        const data = response.data
        // Handle both { evidence: [...] } and raw array [...]
        return Array.isArray(data) ? { evidence: data } : data
    },

    /**
     * Get vendor sources
     */
    getSources: async (vendorId: number): Promise<VendorSourcesResponse> => {
        const response = await api.get(`/vendors/${vendorId}/sources`)
        const data = response.data
        // Handle both { sources: [...] } and raw array [...]
        return Array.isArray(data) ? { sources: data } : data
    },

    /**
     * Get vendor assets
     */
    getAssets: async (vendorId: number): Promise<VendorAssetsResponse> => {
        const response = await api.get(`/vendors/${vendorId}/assets`)
        const data = response.data
        // Handle both { assets: [...] } and raw array [...]
        return Array.isArray(data) ? { assets: data } : data
    },
}

// Response types
export interface VendorEvidenceResponse {
    evidence: VendorEvidence[]
}

export interface VendorSourcesResponse {
    sources: VendorSource[]
}

export interface VendorAssetsResponse {
    assets: VendorAsset[]
}

// Alias for compatibility
export type VendorDetail = Vendor
export type VendorListItem = Vendor
