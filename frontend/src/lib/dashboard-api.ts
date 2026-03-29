/**
 * Dashboard API client
 */

import api from './api'

export interface RecentRequest {
    id: number
    title: string
    status: string
    category: string
    vendors_found: number
    updated_at: string
}

export interface DashboardData {
    total_requests: number
    requests_by_status: Record<string, number>
    total_vendors_found: number
    recent_requests: RecentRequest[]
    active_runs: number
}

export const dashboardApi = {
    /**
     * Get aggregated dashboard stats
     */
    get: async (): Promise<DashboardData> => {
        const response = await api.get<DashboardData>('/dashboard')
        return response.data
    },
}
