/**
 * Copilot API client and types
 */

import { api } from './api'

// ====== Types ======

export interface Citation {
    vendor_id: number | null
    vendor_name: string | null
    source_url: string
    snippet: string
    field_name: string | null
}

export interface CopilotAction {
    type:
    | 'OPEN_VENDOR'
    | 'COMPARE_TOP'
    | 'CREATE_SHORTLIST'
    | 'EXPORT_REPORT'
    | 'OPEN_REPORTS'
    label: string
    payload: Record<string, unknown>
}

export interface ChatRequest {
    run_id: number
    message: string
    vendor_ids?: number[]
    mode?: 'ask' | 'insights'
}

export interface ChatResponse {
    answer: string
    citations: Citation[]
    suggested_actions: CopilotAction[]
}

export interface CopilotMessage {
    id: string
    role: 'user' | 'assistant'
    content: string
    citations?: Citation[]
    suggested_actions?: CopilotAction[]
    timestamp: Date
}

// ====== API Functions ======

export const copilotApi = {
    /**
     * Send a message to the copilot
     */
    chat: async (payload: ChatRequest): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/copilot/chat', payload)
        return response.data
    },
}
