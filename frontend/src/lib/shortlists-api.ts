/**
 * Shortlists API client for managing vendor shortlists.
 */

import api from './api'

// Types
export interface VendorInShortlist {
    id: number
    name: string
    website: string | null
    logo_url: string | null
    overall_score: number | null
    fit_score: number | null
    trust_score: number | null
}

export interface ShortlistItem {
    id: number
    shortlist_id: number
    vendor_id: number
    notes: string | null
    position: number
    created_at: string
    vendor: VendorInShortlist
}

export interface Shortlist {
    id: number
    name: string
    request_id: number | null
    created_by_user_id: number
    created_at: string
    updated_at: string
    item_count: number
}

export interface ShortlistDetail extends Shortlist {
    items: ShortlistItem[]
}

export interface ShortlistListResponse {
    shortlists: Shortlist[]
    total: number
}

export interface CreateShortlistRequest {
    name: string
    request_id?: number | null
}

export interface UpdateShortlistRequest {
    name: string
}

export interface AddVendorRequest {
    notes?: string | null
}

export interface UpdateNotesRequest {
    notes: string | null
}

export interface ReorderRequest {
    item_ids: number[]
}

// API client
export const shortlistsApi = {
    /**
     * List user's shortlists
     */
    list: async (requestId?: number): Promise<ShortlistListResponse> => {
        const params = requestId ? { request_id: requestId } : undefined
        const response = await api.get<ShortlistListResponse>('/shortlists', { params })
        return response.data
    },

    /**
     * Get shortlist detail with items
     */
    get: async (id: number): Promise<ShortlistDetail> => {
        const response = await api.get<ShortlistDetail>(`/shortlists/${id}`)
        return response.data
    },

    /**
     * Create a new shortlist
     */
    create: async (data: CreateShortlistRequest): Promise<Shortlist> => {
        const response = await api.post<Shortlist>('/shortlists', data)
        return response.data
    },

    /**
     * Update (rename) a shortlist
     */
    update: async (id: number, data: UpdateShortlistRequest): Promise<Shortlist> => {
        const response = await api.put<Shortlist>(`/shortlists/${id}`, data)
        return response.data
    },

    /**
     * Delete a shortlist
     */
    delete: async (id: number): Promise<void> => {
        await api.delete(`/shortlists/${id}`)
    },

    /**
     * Add a vendor to shortlist
     */
    addVendor: async (
        shortlistId: number,
        vendorId: number,
        data?: AddVendorRequest
    ): Promise<ShortlistItem> => {
        const response = await api.post<ShortlistItem>(
            `/shortlists/${shortlistId}/vendors/${vendorId}`,
            data || {}
        )
        return response.data
    },

    /**
     * Remove a vendor from shortlist
     */
    removeVendor: async (shortlistId: number, vendorId: number): Promise<void> => {
        await api.delete(`/shortlists/${shortlistId}/vendors/${vendorId}`)
    },

    /**
     * Reorder items in shortlist
     */
    reorder: async (id: number, itemIds: number[]): Promise<ShortlistDetail> => {
        const response = await api.put<ShortlistDetail>(
            `/shortlists/${id}/reorder`,
            { item_ids: itemIds }
        )
        return response.data
    },

    /**
     * Update notes for a vendor in shortlist
     */
    updateNotes: async (
        shortlistId: number,
        vendorId: number,
        notes: string | null
    ): Promise<ShortlistItem> => {
        const response = await api.put<ShortlistItem>(
            `/shortlists/${shortlistId}/vendors/${vendorId}/notes`,
            { notes }
        )
        return response.data
    },
}

export default shortlistsApi
