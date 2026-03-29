/**
 * ProcurementChat - Main chat interface component
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Send,
    Plus,
    Trash2,
    History,
    MessageSquare,
    Search,
    ArrowDown,
    MoreVertical,
    X,
    Scale,
    Shield,
    DollarSign,
    Target,
    BarChart3,
    Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { useProcurementChat } from '@/hooks/useProcurementChat'
import { ChatMessage, TypingIndicator } from './ChatMessage'
import type { ChatAction, FilterChip } from '@/lib/procurement-chat-api'

interface ProcurementChatProps {
    runId?: number
    className?: string
    onVendorClick?: (vendorId: number) => void
    onClose?: () => void
}

const EXAMPLE_QUERIES = [
    { text: "Cari vendor CRM untuk enterprise", icon: "search" },
    { text: "Bandingkan top 3 vendor cloud hosting", icon: "compare" },
    { text: "Vendor dengan SOC 2 certification", icon: "shield" },
    { text: "Pricing breakdown untuk kategori SaaS", icon: "dollar" },
    { text: "Rekomendasi vendor berdasarkan budget", icon: "target" },
    { text: "Analisis industri software HR", icon: "chart" },
]

export function ProcurementChat({
    runId,
    className,
    onVendorClick,
    onClose,
}: ProcurementChatProps) {
    const [inputValue, setInputValue] = useState('')
    const [showScrollButton, setShowScrollButton] = useState(false)
    const textareaRef = useRef<HTMLTextAreaElement>(null)
    const scrollAreaRef = useRef<HTMLDivElement>(null)

    const {
        sessions,
        activeSessionId,
        messages,
        isTyping,
        isLoading,
        sendMessage,
        createSession,
        switchSession,
        deleteSession,
        clearMessages,
        handleAction,
        handleFilterClick,
        handleSuggestedQueryClick,
        messagesEndRef,
        scrollToBottom,
    } = useProcurementChat({
        runId,
        onVendorClick,
    })

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto'
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
        }
    }, [inputValue])

    // Check scroll position
    const handleScroll = useCallback((event: React.UIEvent<HTMLDivElement>) => {
        const target = event.target as HTMLDivElement
        const isNearBottom = target.scrollHeight - target.scrollTop - target.clientHeight < 100
        setShowScrollButton(!isNearBottom)
    }, [])

    // Handle send
    const handleSend = useCallback(() => {
        if (inputValue.trim() && !isLoading) {
            sendMessage(inputValue)
            setInputValue('')
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto'
            }
        }
    }, [inputValue, isLoading, sendMessage])

    // Handle key press
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
            }
        },
        [handleSend]
    )

    // Handle example query click
    const handleExampleClick = (query: string) => {
        sendMessage(query)
    }

    // Handle action from message
    const onActionClick = useCallback((action: ChatAction) => {
        handleAction(action)
    }, [handleAction])

    // Handle filter click
    const onFilterClickHandler = useCallback((chip: FilterChip) => {
        handleFilterClick(chip)
    }, [handleFilterClick])

    return (
        <div className={cn('flex flex-col h-full bg-background', className)}>
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b bg-card">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Search className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                        <h2 className="font-semibold">AI Search</h2>
                        <p className="text-xs text-muted-foreground">
                            {isTyping ? 'Mengetik...' : 'Siap membantu'}
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {/* Session dropdown */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <History className="w-4 h-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                                Chat History
                            </div>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={createSession}>
                                <Plus className="w-4 h-4 mr-2" />
                                New Chat
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {sessions.slice(0, 5).map((session) => (
                                <DropdownMenuItem
                                    key={session.id}
                                    onClick={() => switchSession(session.id)}
                                    className={cn(
                                        session.id === activeSessionId && 'bg-accent'
                                    )}
                                >
                                    <MessageSquare className="w-4 h-4 mr-2" />
                                    <span className="truncate flex-1">{session.name}</span>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            deleteSession(session.id)
                                        }}
                                        className="ml-2 text-muted-foreground hover:text-destructive"
                                    >
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </DropdownMenuItem>
                            ))}
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* More options */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <MoreVertical className="w-4 h-4" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={clearMessages}>
                                <Trash2 className="w-4 h-4 mr-2" />
                                Clear Chat
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>

                    {/* Close button */}
                    {onClose && (
                        <Button variant="ghost" size="icon" onClick={onClose}>
                            <X className="w-4 h-4" />
                        </Button>
                    )}
                </div>
            </div>

            {/* Messages */}
            <ScrollArea
                ref={scrollAreaRef}
                className="flex-1 px-4"
                onScroll={handleScroll}
            >
                <div className="py-4 space-y-4">
                    {/* Welcome message if no messages */}
                    {messages.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-6"
                        >
                            {/* Welcome card */}
                            <div className="rounded-2xl bg-muted/50 border p-6">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                                        <Search className="w-6 h-6 text-primary" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-lg">
                                            AI Search Assistant
                                        </h3>
                                        <p className="text-sm text-muted-foreground">
                                            Pencarian vendor dengan AI
                                        </p>
                                    </div>
                                </div>
                                <div className="text-sm space-y-2">
                                    <p>Saya dapat membantu Anda:</p>
                                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                                        <li><strong>Mencari</strong> vendor di berbagai kategori</li>
                                        <li><strong>Membandingkan</strong> vendor side-by-side</li>
                                        <li><strong>Menganalisis</strong> pricing dan fitur</li>
                                        <li><strong>Membuat shortlist</strong> vendor terpilih</li>
                                    </ul>
                                </div>
                            </div>

                            {/* Example queries */}
                            <div className="space-y-3">
                                <div className="flex items-center gap-2">
                                    <Sparkles className="w-4 h-4 text-crimson" />
                                    <p className="text-sm font-medium">
                                        Coba tanyakan
                                    </p>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                    {EXAMPLE_QUERIES.map((query, i) => {
                                        const iconMap: Record<string, React.ReactNode> = {
                                            search: <Search className="w-4 h-4" />,
                                            compare: <Scale className="w-4 h-4" />,
                                            shield: <Shield className="w-4 h-4" />,
                                            dollar: <DollarSign className="w-4 h-4" />,
                                            target: <Target className="w-4 h-4" />,
                                            chart: <BarChart3 className="w-4 h-4" />,
                                        }
                                        return (
                                            <motion.button
                                                key={i}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: i * 0.05 }}
                                                onClick={() => handleExampleClick(query.text)}
                                                className="flex items-center gap-3 px-4 py-3 rounded-xl border bg-card hover:bg-crimson/5 hover:border-crimson/30 transition-all text-left text-sm group"
                                            >
                                                <div className="w-8 h-8 rounded-lg bg-muted group-hover:bg-crimson/10 flex items-center justify-center text-muted-foreground group-hover:text-crimson transition-colors">
                                                    {iconMap[query.icon]}
                                                </div>
                                                <span className="flex-1">{query.text}</span>
                                            </motion.button>
                                        )
                                    })}
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {/* Messages */}
                    <AnimatePresence initial={false}>
                        {messages.map((message) => (
                            <ChatMessage
                                key={message.id}
                                message={message}
                                onVendorClick={onVendorClick}
                                onFilterClick={onFilterClickHandler}
                                onSuggestedQueryClick={handleSuggestedQueryClick}
                                onActionClick={onActionClick}
                            />
                        ))}
                    </AnimatePresence>

                    {/* Typing indicator */}
                    {isTyping && <TypingIndicator />}

                    {/* Scroll anchor */}
                    <div ref={messagesEndRef} />
                </div>
            </ScrollArea>

            {/* Scroll to bottom button */}
            <AnimatePresence>
                {showScrollButton && (
                    <motion.button
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        onClick={scrollToBottom}
                        className="absolute bottom-24 right-6 w-10 h-10 rounded-full bg-primary text-primary-foreground shadow-lg flex items-center justify-center hover:bg-primary/90 transition-colors"
                    >
                        <ArrowDown className="w-5 h-5" />
                    </motion.button>
                )}
            </AnimatePresence>

            {/* Input */}
            <div className="p-4 border-t bg-card">
                <div className="flex items-end gap-2">
                    <div className="flex-1 relative">
                        <textarea
                            ref={textareaRef}
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Tanyakan sesuatu..."
                            rows={1}
                            disabled={isLoading}
                            className={cn(
                                'w-full resize-none rounded-xl border bg-background px-4 py-3 pr-12',
                                'focus:outline-none focus:ring-2 focus:ring-primary/50',
                                'placeholder:text-muted-foreground',
                                'disabled:opacity-50 disabled:cursor-not-allowed',
                                'min-h-[48px] max-h-[200px]'
                            )}
                        />
                        <Button
                            size="icon"
                            disabled={!inputValue.trim() || isLoading}
                            onClick={handleSend}
                            className="absolute right-2 bottom-2 rounded-lg h-8 w-8"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
                <p className="text-[10px] text-muted-foreground text-center mt-2">
                    Tekan Enter untuk kirim, Shift+Enter untuk baris baru
                </p>
            </div>
        </div>
    )
}

export default ProcurementChat
