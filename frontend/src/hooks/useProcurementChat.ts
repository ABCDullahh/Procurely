/**
 * Hook for managing Procurement Chat state and interactions
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
    procurementChatApi,
    ChatMessage,
    ProcurementChatRequest,
    ProcurementChatResponse,
    ResearchStatusResponse,
    SearchProgressData,
} from '@/lib/procurement-chat-api'

interface UseProcurementChatOptions {
    runId?: number
    onVendorClick?: (vendorId: number) => void
    onCompareClick?: (vendorIds: number[]) => void
    onShortlistClick?: (vendorIds: number[]) => void
}

interface ChatSession {
    id: string
    name: string
    messages: ChatMessage[]
    context: Record<string, unknown>
    createdAt: Date
    updatedAt: Date
}

const STORAGE_KEY = 'procurement-chat-sessions'

function generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function generateMessageId(): string {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function formatSessionName(): string {
    const now = new Date()
    return `Chat ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function loadSessions(): ChatSession[] {
    try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored) {
            const sessions = JSON.parse(stored)
            return sessions.map((s: ChatSession) => ({
                ...s,
                createdAt: new Date(s.createdAt),
                updatedAt: new Date(s.updatedAt),
                messages: s.messages.map((m: ChatMessage) => ({
                    ...m,
                    timestamp: new Date(m.timestamp),
                })),
            }))
        }
    } catch (e) {
        console.error('Failed to load chat sessions:', e)
    }
    return []
}

function saveSessions(sessions: ChatSession[]): void {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
    } catch (e) {
        console.error('Failed to save chat sessions:', e)
    }
}

export function useProcurementChat(options: UseProcurementChatOptions = {}) {
    const { runId, onVendorClick, onCompareClick, onShortlistClick } = options

    // State
    const [sessions, setSessions] = useState<ChatSession[]>(() => loadSessions())
    const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
        const loaded = loadSessions()
        return loaded.length > 0 ? loaded[0].id : null
    })
    const [isTyping, setIsTyping] = useState(false)
    const [conversationId, setConversationId] = useState<string | null>(null)
    const [context, setContext] = useState<Record<string, unknown>>({})

    // Active research tracking
    const [activeResearchRunId, setActiveResearchRunId] = useState<number | null>(null)
    const [researchStatus, setResearchStatus] = useState<ResearchStatusResponse | null>(null)
    const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

    // Refs
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const inputRef = useRef<HTMLTextAreaElement>(null)

    // Get current session
    const currentSession = sessions.find(s => s.id === activeSessionId)
    const messages = currentSession?.messages || []

    // Save sessions on change
    useEffect(() => {
        saveSessions(sessions)
    }, [sessions])

    // Polling for research status
    const startPolling = useCallback((researchRunId: number) => {
        setActiveResearchRunId(researchRunId)

        // Poll every 2 seconds
        pollingIntervalRef.current = setInterval(async () => {
            try {
                const status = await procurementChatApi.getResearchStatus(researchRunId)
                setResearchStatus(status)

                // Update the last message in the session with partial vendors
                if (status.partial_vendors && status.partial_vendors.length > 0) {
                    setSessions(prev =>
                        prev.map(s => {
                            if (s.id !== activeSessionId) return s
                            const lastMsgIndex = s.messages.length - 1
                            if (lastMsgIndex < 0) return s
                            const lastMsg = s.messages[lastMsgIndex]
                            if (lastMsg.role !== 'assistant' || lastMsg.response_type !== 'deep_research') return s

                            const existingProgress = lastMsg.data?.progress
                            const updatedProgress: SearchProgressData = existingProgress
                                ? {
                                      ...existingProgress,
                                      progress_pct: status.progress_pct,
                                      vendors_found: status.vendors_found,
                                      current_step: status.current_step || 'processing',
                                  }
                                : {
                                      steps: [],
                                      current_step: status.current_step || 'processing',
                                      progress_pct: status.progress_pct,
                                      vendors_found: status.vendors_found,
                                      sources_searched: 0,
                                      estimated_time_remaining: null,
                                  }

                            const updatedMessages: ChatMessage[] = s.messages.map((m, i) =>
                                i === lastMsgIndex && m.data
                                    ? {
                                          ...m,
                                          data: {
                                              ...m.data,
                                              vendors: status.partial_vendors,
                                              progress: updatedProgress,
                                          },
                                      }
                                    : m
                            )

                            return {
                                ...s,
                                messages: updatedMessages,
                            }
                        })
                    )
                }

                // Stop polling if complete
                if (status.is_complete) {
                    stopPolling()

                    // If successful, update message to show final results
                    if (status.status === 'COMPLETED' && status.partial_vendors) {
                        setSessions(prev =>
                            prev.map(s => {
                                if (s.id !== activeSessionId) return s
                                const lastMsgIndex = s.messages.length - 1
                                if (lastMsgIndex < 0) return s
                                const lastMsg = s.messages[lastMsgIndex]
                                if (lastMsg.role !== 'assistant') return s

                                const updatedMessages: ChatMessage[] = s.messages.map((m, i) => {
                                    if (i !== lastMsgIndex || !m.data) return m
                                    return {
                                        ...m,
                                        response_type: 'vendors' as const,
                                        content: `Pencarian web selesai! Ditemukan **${status.vendors_found} vendor** yang sesuai.`,
                                        data: {
                                            ...m.data,
                                            response_type: 'vendors' as const,
                                            text_content: `Pencarian web selesai! Ditemukan **${status.vendors_found} vendor** yang sesuai.`,
                                            vendors: status.partial_vendors,
                                            progress: null,
                                            actions: [
                                                {
                                                    type: 'COMPARE_VENDORS' as const,
                                                    label: 'Bandingkan Top 3',
                                                    icon: 'git-compare',
                                                    variant: 'primary' as const,
                                                    payload: {
                                                        vendor_ids: status.partial_vendors?.slice(0, 3).map((v) => v.id) || [],
                                                    },
                                                },
                                                {
                                                    type: 'ADD_TO_SHORTLIST' as const,
                                                    label: 'Tambah ke Shortlist',
                                                    icon: 'bookmark-plus',
                                                    variant: 'secondary' as const,
                                                    payload: {},
                                                },
                                            ],
                                        },
                                    }
                                })

                                return {
                                    ...s,
                                    messages: updatedMessages,
                                }
                            })
                        )
                    } else if (status.status === 'FAILED') {
                        toast.error(`Research failed: ${status.error_message || 'Unknown error'}`)
                    }
                }
            } catch (err) {
                console.error('Failed to poll research status:', err)
            }
        }, 2000)
    }, [activeSessionId])

    const stopPolling = useCallback(() => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
        }
        setActiveResearchRunId(null)
        setResearchStatus(null)
    }, [])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current)
            }
        }
    }, [])

    // Scroll to bottom
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [])

    // Create new session
    const createSession = useCallback(() => {
        const newSession: ChatSession = {
            id: generateSessionId(),
            name: formatSessionName(),
            messages: [],
            context: {},
            createdAt: new Date(),
            updatedAt: new Date(),
        }
        setSessions(prev => [newSession, ...prev])
        setActiveSessionId(newSession.id)
        setConversationId(null)
        setContext({})
        return newSession.id
    }, [])

    // Switch session
    const switchSession = useCallback((sessionId: string) => {
        const session = sessions.find(s => s.id === sessionId)
        if (session) {
            setActiveSessionId(sessionId)
            setContext(session.context)
        }
    }, [sessions])

    // Delete session
    const deleteSession = useCallback((sessionId: string) => {
        setSessions(prev => {
            const filtered = prev.filter(s => s.id !== sessionId)
            if (activeSessionId === sessionId && filtered.length > 0) {
                setActiveSessionId(filtered[0].id)
            } else if (filtered.length === 0) {
                setActiveSessionId(null)
            }
            return filtered
        })
    }, [activeSessionId])

    // Clear messages in current session
    const clearMessages = useCallback(() => {
        if (activeSessionId) {
            setSessions(prev =>
                prev.map(s =>
                    s.id === activeSessionId
                        ? { ...s, messages: [], updatedAt: new Date() }
                        : s
                )
            )
            setConversationId(null)
        }
    }, [activeSessionId])

    // Add message to current session
    const addMessage = useCallback((message: ChatMessage) => {
        if (!activeSessionId) {
            const newId = createSession()
            setSessions(prev =>
                prev.map(s =>
                    s.id === newId
                        ? { ...s, messages: [message], updatedAt: new Date() }
                        : s
                )
            )
        } else {
            setSessions(prev =>
                prev.map(s =>
                    s.id === activeSessionId
                        ? { ...s, messages: [...s.messages, message], updatedAt: new Date() }
                        : s
                )
            )
        }
        setTimeout(scrollToBottom, 100)
    }, [activeSessionId, createSession, scrollToBottom])

    // Send message mutation
    const sendMutation = useMutation({
        mutationFn: (payload: ProcurementChatRequest) =>
            procurementChatApi.sendMessage(payload),
        onMutate: () => {
            setIsTyping(true)
        },
        onSuccess: (response: ProcurementChatResponse) => {
            setIsTyping(false)
            setConversationId(response.conversation_id)

            // Update context from response for next message
            if (response.context) {
                const newContext: Record<string, unknown> = {}
                if (response.context.category) newContext.category = response.context.category
                if (response.context.keywords?.length) newContext.keywords = response.context.keywords
                if (response.context.budget) newContext.budget = response.context.budget
                if (response.context.location) newContext.location = response.context.location
                if (response.context.requirements?.length) newContext.requirements = response.context.requirements

                setContext(prev => ({ ...prev, ...newContext }))

                // Update session context
                setSessions(prev =>
                    prev.map(s =>
                        s.id === activeSessionId
                            ? { ...s, context: { ...s.context, ...newContext } }
                            : s
                    )
                )
            }

            const assistantMessage: ChatMessage = {
                id: response.message_id,
                role: 'assistant',
                content: response.text_content,
                response_type: response.response_type,
                data: response,
                timestamp: new Date(response.timestamp),
            }
            addMessage(assistantMessage)

            // Start polling if deep_research response
            if (response.response_type === 'deep_research' && response.run_id) {
                startPolling(response.run_id)
            }
        },
        onError: (error: Error) => {
            setIsTyping(false)
            toast.error(`Failed to send message: ${error.message}`)
        },
    })

    // Send message
    const sendMessage = useCallback(
        async (text: string, mode?: ProcurementChatRequest['mode']) => {
            if (!text.trim()) return

            // Ensure we have a session
            let sessionId = activeSessionId
            if (!sessionId) {
                sessionId = createSession()
            }

            // Add user message
            const userMessage: ChatMessage = {
                id: generateMessageId(),
                role: 'user',
                content: text,
                timestamp: new Date(),
            }
            addMessage(userMessage)

            // Send to API
            const payload: ProcurementChatRequest = {
                message: text,
                conversation_id: conversationId || undefined,
                context,
                mode: mode || 'search',
                run_id: runId,
            }

            sendMutation.mutate(payload)
        },
        [activeSessionId, createSession, addMessage, conversationId, context, runId, sendMutation]
    )

    // Handle action click
    const handleAction = useCallback(async (action: ProcurementChatResponse['actions'][0]) => {
        switch (action.type) {
            case 'VIEW_VENDOR':
                if (action.payload.vendor_id && onVendorClick) {
                    onVendorClick(action.payload.vendor_id as number)
                }
                break
            case 'COMPARE_VENDORS':
                if (action.payload.vendor_ids && onCompareClick) {
                    onCompareClick(action.payload.vendor_ids as number[])
                }
                break
            case 'ADD_TO_SHORTLIST':
                if (action.payload.vendor_ids && onShortlistClick) {
                    onShortlistClick(action.payload.vendor_ids as number[])
                }
                break
            case 'START_SEARCH':
            case 'CREATE_REQUEST':
                // Navigate to new request page
                window.location.href = '/requests/new'
                break
            case 'START_DEEP_RESEARCH':
                // Start web research with provided context
                try {
                    const researchPayload = {
                        category: (action.payload.category as string) || 'Other',
                        keywords: (action.payload.keywords as string[]) || [],
                        location: action.payload.location as string | undefined,
                    }
                    const result = await procurementChatApi.startResearch(researchPayload)

                    // Add a message indicating research started
                    const researchMessage: ChatMessage = {
                        id: generateMessageId(),
                        role: 'assistant',
                        content: `🔍 **Memulai pencarian web...**\n\nMencari vendor untuk "${researchPayload.category}"...`,
                        response_type: 'deep_research',
                        data: {
                            message_id: generateMessageId(),
                            conversation_id: conversationId || '',
                            response_type: 'deep_research',
                            text_content: `🔍 **Memulai pencarian web...**\n\nMencari vendor untuk "${researchPayload.category}"...`,
                            vendors: null,
                            comparison: null,
                            progress: {
                                steps: [
                                    { id: 'init', label: 'Inisialisasi', status: 'completed', details: null },
                                    { id: 'search', label: 'Mencari di web', status: 'active', details: null },
                                    { id: 'extract', label: 'Mengekstrak vendor', status: 'pending', details: null },
                                    { id: 'score', label: 'Menilai vendor', status: 'pending', details: null },
                                ],
                                current_step: 'search',
                                progress_pct: 10,
                                vendors_found: 0,
                                sources_searched: 0,
                                estimated_time_remaining: null,
                            },
                            evidence: null,
                            chart_data: null,
                            filter_chips: [],
                            suggested_queries: [],
                            actions: [
                                {
                                    type: 'CANCEL_RESEARCH',
                                    label: 'Batalkan',
                                    icon: 'x',
                                    variant: 'outline',
                                    payload: { run_id: result.run_id },
                                },
                            ],
                            run_id: result.run_id,
                            request_id: result.request_id,
                            timestamp: new Date().toISOString(),
                            insights: null,
                            quick_stats: null,
                            categories: null,
                            pricing_overview: null,
                            context: null,
                        },
                        timestamp: new Date(),
                    }
                    addMessage(researchMessage)
                    startPolling(result.run_id)
                } catch (err) {
                    toast.error('Failed to start research')
                    console.error(err)
                }
                break
            case 'CANCEL_RESEARCH':
                // Cancel ongoing research
                if (action.payload.run_id) {
                    try {
                        await procurementChatApi.cancelResearch(action.payload.run_id as number)
                        stopPolling()
                        toast.success('Research cancelled')
                    } catch (err) {
                        toast.error('Failed to cancel research')
                        console.error(err)
                    }
                }
                break
            default:
                console.log('Unhandled action:', action)
        }
    }, [onVendorClick, onCompareClick, onShortlistClick, conversationId, addMessage, startPolling, stopPolling])

    // Handle filter chip click
    const handleFilterClick = useCallback((filter: { filter_type: string; filter_value: string }) => {
        const newContext = {
            ...context,
            [filter.filter_type]: filter.filter_value,
        }
        setContext(newContext)

        // Update session context
        setSessions(prev =>
            prev.map(s =>
                s.id === activeSessionId
                    ? { ...s, context: newContext }
                    : s
            )
        )

        // Send message with filter applied
        sendMessage(`Filter by ${filter.filter_type}: ${filter.filter_value}`, 'refine')
    }, [context, activeSessionId, sendMessage])

    // Handle suggested query click
    const handleSuggestedQueryClick = useCallback((query: string) => {
        sendMessage(query)
    }, [sendMessage])

    return {
        // State
        sessions,
        activeSessionId,
        currentSession,
        messages,
        isTyping,
        isLoading: sendMutation.isPending,
        conversationId,
        context,

        // Research state
        activeResearchRunId,
        researchStatus,
        isResearching: activeResearchRunId !== null,

        // Refs
        messagesEndRef,
        inputRef,

        // Actions
        sendMessage,
        createSession,
        switchSession,
        deleteSession,
        clearMessages,
        handleAction,
        handleFilterClick,
        handleSuggestedQueryClick,
        scrollToBottom,
        setContext,
        stopPolling,
    }
}
