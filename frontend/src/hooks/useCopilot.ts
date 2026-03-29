/**
 * useCopilot - Hook for managing copilot chat with multi-session support
 * Sessions are persisted per Procurement Request (requestId)
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
    copilotApi,
    CopilotMessage,
    Citation,
    CopilotAction,
} from '@/lib/copilot-api'

// Session types
export interface ChatSession {
    id: string
    name: string
    createdAt: string
    messages: CopilotMessage[]
}

interface SessionStore {
    activeSessionId: string
    sessions: ChatSession[]
}

interface UseCopilotOptions {
    runId: number
    requestId: number
}

interface UseCopilotReturn {
    // Messages for current session
    messages: CopilotMessage[]
    isLoading: boolean
    error: string | null
    latestCitations: Citation[]
    latestActions: CopilotAction[]
    sendMessage: (message: string, mode?: 'ask' | 'insights') => void
    clearMessages: () => void

    // Scroll controls
    isNearBottom: boolean
    scrollToBottom: () => void
    messagesContainerRef: React.RefObject<HTMLDivElement>

    // Session management
    sessions: ChatSession[]
    activeSessionId: string
    createSession: () => void
    switchSession: (sessionId: string) => void
    deleteSession: (sessionId: string) => void
}

function generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

function generateSessionName(): string {
    const now = new Date()
    return `Chat ${now.toLocaleDateString()} ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

// Storage key for all sessions per request
function getStorageKey(requestId: number): string {
    return `copilot-sessions:${requestId}`
}

// Load session store from localStorage
function loadSessionStore(requestId: number): SessionStore {
    try {
        const stored = localStorage.getItem(getStorageKey(requestId))
        if (stored) {
            const parsed = JSON.parse(stored)
            // Ensure sessions exist and have proper structure
            if (parsed.sessions && Array.isArray(parsed.sessions)) {
                return {
                    activeSessionId: parsed.activeSessionId || parsed.sessions[0]?.id || '',
                    sessions: parsed.sessions.map((s: ChatSession) => ({
                        ...s,
                        messages: s.messages.map(m => ({
                            ...m,
                            timestamp: new Date(m.timestamp)
                        }))
                    }))
                }
            }
        }
    } catch (e) {
        console.warn('Failed to load session store:', e)
    }

    // Create default session if none exists
    const defaultSession: ChatSession = {
        id: generateId(),
        name: generateSessionName(),
        createdAt: new Date().toISOString(),
        messages: []
    }
    return {
        activeSessionId: defaultSession.id,
        sessions: [defaultSession]
    }
}

// Save session store to localStorage
function saveSessionStore(requestId: number, store: SessionStore): void {
    try {
        localStorage.setItem(getStorageKey(requestId), JSON.stringify(store))
    } catch (e) {
        console.warn('Failed to save session store:', e)
    }
}

// Sanitize answer content
function sanitizeAnswer(content: string): string {
    if (!content) return 'No response available.'

    const trimmed = content.trim()
    if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        try {
            const parsed = JSON.parse(trimmed)
            if (typeof parsed.answer === 'string') {
                return parsed.answer
            }
            return content
        } catch {
            return content
        }
    }

    const jsonMatch = content.match(/```(?:json)?\s*([\s\S]*?)```/)
    if (jsonMatch) {
        try {
            const parsed = JSON.parse(jsonMatch[1].trim())
            if (typeof parsed.answer === 'string') {
                return parsed.answer
            }
        } catch {
            // Not valid JSON in code block
        }
    }

    return content
}

export function useCopilot({ runId, requestId }: UseCopilotOptions): UseCopilotReturn {
    // Load session store
    const [sessionStore, setSessionStore] = useState<SessionStore>(() => loadSessionStore(requestId))
    const [error, setError] = useState<string | null>(null)
    const [latestCitations, setLatestCitations] = useState<Citation[]>([])
    const [latestActions, setLatestActions] = useState<CopilotAction[]>([])
    const [isNearBottom, setIsNearBottom] = useState(true)

    const messagesContainerRef = useRef<HTMLDivElement>(null)

    // Get current session
    const currentSession = sessionStore.sessions.find(s => s.id === sessionStore.activeSessionId)
    const messages = currentSession?.messages || []

    // Sync to localStorage on session store change
    useEffect(() => {
        saveSessionStore(requestId, sessionStore)
    }, [requestId, sessionStore])

    // Reload when requestId changes
    useEffect(() => {
        setSessionStore(loadSessionStore(requestId))
        setLatestCitations([])
        setLatestActions([])
        setError(null)
    }, [requestId])

    // Scroll detection
    useEffect(() => {
        const container = messagesContainerRef.current
        if (!container) return

        const handleScroll = () => {
            const { scrollTop, scrollHeight, clientHeight } = container
            const distanceFromBottom = scrollHeight - scrollTop - clientHeight
            setIsNearBottom(distanceFromBottom < 100)
        }

        container.addEventListener('scroll', handleScroll)
        return () => container.removeEventListener('scroll', handleScroll)
    }, [])

    const scrollToBottom = useCallback(() => {
        const container = messagesContainerRef.current
        if (container) {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' })
        }
    }, [])

    // Auto-scroll on new messages
    useEffect(() => {
        if (isNearBottom) {
            scrollToBottom()
        }
    }, [messages, isNearBottom, scrollToBottom])

    // Update messages in current session
    const updateMessages = useCallback((updater: (msgs: CopilotMessage[]) => CopilotMessage[]) => {
        setSessionStore(prev => ({
            ...prev,
            sessions: prev.sessions.map(s =>
                s.id === prev.activeSessionId
                    ? { ...s, messages: updater(s.messages) }
                    : s
            )
        }))
    }, [])

    const chatMutation = useMutation({
        mutationFn: copilotApi.chat,
        onSuccess: (response) => {
            const assistantMessage: CopilotMessage = {
                id: generateId(),
                role: 'assistant',
                content: sanitizeAnswer(response.answer),
                citations: response.citations,
                suggested_actions: response.suggested_actions,
                timestamp: new Date(),
            }
            updateMessages(prev => [...prev, assistantMessage])
            setLatestCitations(response.citations)
            setLatestActions(response.suggested_actions)
            setError(null)
        },
        onError: (err: Error) => {
            setError(err.message || 'Failed to get response')
            const errorMessage: CopilotMessage = {
                id: generateId(),
                role: 'assistant',
                content: `Sorry, I encountered an error: ${err.message}`,
                timestamp: new Date(),
            }
            updateMessages(prev => [...prev, errorMessage])
        },
    })

    const sendMessage = useCallback((message: string, mode: 'ask' | 'insights' = 'ask') => {
        const userMessage: CopilotMessage = {
            id: generateId(),
            role: 'user',
            content: message,
            timestamp: new Date(),
        }
        updateMessages(prev => [...prev, userMessage])

        chatMutation.mutate({
            run_id: runId,
            message,
            mode,
        })
    }, [runId, chatMutation, updateMessages])

    const clearMessages = useCallback(() => {
        updateMessages(() => [])
        setLatestCitations([])
        setLatestActions([])
        setError(null)
    }, [updateMessages])

    // Session management
    const createSession = useCallback(() => {
        const newSession: ChatSession = {
            id: generateId(),
            name: generateSessionName(),
            createdAt: new Date().toISOString(),
            messages: []
        }
        setSessionStore(prev => ({
            activeSessionId: newSession.id,
            sessions: [newSession, ...prev.sessions]
        }))
        setLatestCitations([])
        setLatestActions([])
    }, [])

    const switchSession = useCallback((sessionId: string) => {
        setSessionStore(prev => ({
            ...prev,
            activeSessionId: sessionId
        }))
        setLatestCitations([])
        setLatestActions([])
    }, [])

    const deleteSession = useCallback((sessionId: string) => {
        setSessionStore(prev => {
            const filtered = prev.sessions.filter(s => s.id !== sessionId)
            // If deleting active session, switch to first remaining or create new
            if (filtered.length === 0) {
                const newSession: ChatSession = {
                    id: generateId(),
                    name: generateSessionName(),
                    createdAt: new Date().toISOString(),
                    messages: []
                }
                return { activeSessionId: newSession.id, sessions: [newSession] }
            }
            const newActiveId = prev.activeSessionId === sessionId
                ? filtered[0].id
                : prev.activeSessionId
            return { activeSessionId: newActiveId, sessions: filtered }
        })
    }, [])

    return {
        messages,
        isLoading: chatMutation.isPending,
        error,
        latestCitations,
        latestActions,
        sendMessage,
        clearMessages,
        isNearBottom,
        scrollToBottom,
        messagesContainerRef,
        sessions: sessionStore.sessions,
        activeSessionId: sessionStore.activeSessionId,
        createSession,
        switchSession,
        deleteSession,
    }
}
