/**
 * Analytics & Reports API client
 */

import { api } from './api'

// ====== Types ======

export interface LocationDistribution {
    location: string
    count: number
}

export interface IndustryDistribution {
    industry: string
    count: number
}

export interface ScoreBucket {
    range: string
    count: number
}

export interface TopVendor {
    id: number
    name: string
    website: string | null
    overall_score: number | null
    fit_score: number | null
    trust_score: number | null
    location: string | null
    industry: string | null
}

export interface RunSummary {
    status: string
    started_at: string | null
    completed_at: string | null
    duration_sec: number | null
}

export interface Totals {
    vendors_count: number
    sources_count: number
}

export interface AverageScores {
    avg_fit: number | null
    avg_trust: number | null
    avg_overall: number | null
}

export interface Distributions {
    vendors_by_location: LocationDistribution[]
    vendors_by_industry: IndustryDistribution[]
    score_distribution: ScoreBucket[]
    average_scores: AverageScores
}

export interface PricingDataItem {
    name: string
    price_min: number | null
    price_max: number | null
    pricing_model: string | null
}

export interface CriteriaDataItem {
    name: string
    must_have_matched: number
    must_have_total: number
    nice_to_have_matched: number
    nice_to_have_total: number
    quality_score: number
    completeness_pct: number
    confidence_pct: number
}

export interface ScoreBreakdown {
    avg_fit: number
    avg_trust: number
    avg_quality: number
    avg_overall: number
}

export interface AnalyticsData {
    run_summary: RunSummary
    totals: Totals
    distributions: Distributions
    top_vendors: TopVendor[]
    pricing_data?: PricingDataItem[]
    criteria_matching?: CriteriaDataItem[]
    score_breakdown?: ScoreBreakdown
}

export interface Report {
    id: number
    run_id: number
    format: string
    status: string
    created_at: string
}

export interface ReportDetail extends Report {
    html_content: string | null
}

export interface ReportListResponse {
    reports: Report[]
    total: number
}

// ====== API Functions ======

export const analyticsApi = {
    /**
     * Get analytics for a search run
     */
    getRunAnalytics: async (runId: number): Promise<AnalyticsData> => {
        const response = await api.get<AnalyticsData>(`/runs/${runId}/analytics`)
        return response.data
    },

    /**
     * Export run as HTML report
     */
    exportRunReport: async (runId: number): Promise<Report> => {
        const response = await api.post<Report>(`/runs/${runId}/export`)
        return response.data
    },

    /**
     * List all reports for current user
     */
    listReports: async (): Promise<ReportListResponse> => {
        const response = await api.get<ReportListResponse>('/reports')
        return response.data
    },

    /**
     * Get report details including HTML content
     */
    getReport: async (reportId: number): Promise<ReportDetail> => {
        const response = await api.get<ReportDetail>(`/reports/${reportId}`)
        return response.data
    },

    /**
     * Delete a report
     */
    deleteReport: async (reportId: number): Promise<void> => {
        await api.delete(`/reports/${reportId}`)
    },
}
