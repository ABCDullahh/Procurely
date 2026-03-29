/**
 * CommandPalette - Global command palette (Cmd+K / Ctrl+K)
 */

import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Command } from 'cmdk'
import {
    Home,
    FileText,
    Star,
    BarChart3,
    MessageSquare,
    Plus,
    Search,
    Clock,
    ArrowRight,
    Scale,
    Key,
    History,
} from 'lucide-react'

import { Dialog, DialogContent } from '@/components/ui/dialog'
import { useAuth } from '@/hooks'

interface CommandItem {
    id: string
    label: string
    icon: React.ComponentType<{ className?: string }>
    action: () => void
    group: string
    keywords?: string[]
}

const RECENT_COMMANDS_KEY = 'procurely-recent-commands'
const MAX_RECENT = 5

export default function CommandPalette() {
    const [open, setOpen] = useState(false)
    const [search, setSearch] = useState('')
    const [recentIds, setRecentIds] = useState<string[]>([])
    const navigate = useNavigate()
    const location = useLocation()
    const { user } = useAuth()
    const isAdmin = user?.role === 'admin'

    // Check if we're on a request detail page
    const requestMatch = location.pathname.match(/^\/requests\/(\d+)$/)
    const hasActiveRun = !!requestMatch

    // Load recent commands
    useEffect(() => {
        try {
            const stored = localStorage.getItem(RECENT_COMMANDS_KEY)
            if (stored) {
                setRecentIds(JSON.parse(stored))
            }
        } catch {
            // ignore
        }
    }, [])

    // Save recent command
    const saveRecent = useCallback((id: string) => {
        setRecentIds((prev) => {
            const updated = [id, ...prev.filter((i) => i !== id)].slice(0, MAX_RECENT)
            localStorage.setItem(RECENT_COMMANDS_KEY, JSON.stringify(updated))
            return updated
        })
    }, [])

    // Command handler
    const runCommand = useCallback(
        (cmd: CommandItem) => {
            saveRecent(cmd.id)
            setOpen(false)
            setSearch('')
            cmd.action()
        },
        [saveRecent]
    )

    // Define all commands
    const allCommands: CommandItem[] = [
        // Navigation
        {
            id: 'nav-dashboard',
            label: 'Go to Dashboard',
            icon: Home,
            action: () => navigate('/'),
            group: 'Navigate',
            keywords: ['home', 'overview'],
        },
        {
            id: 'nav-requests',
            label: 'Go to Requests',
            icon: FileText,
            action: () => navigate('/requests'),
            group: 'Navigate',
            keywords: ['procurement', 'search'],
        },
        {
            id: 'nav-shortlists',
            label: 'Go to Shortlists',
            icon: Star,
            action: () => navigate('/shortlists'),
            group: 'Navigate',
            keywords: ['favorites', 'saved'],
        },
        {
            id: 'nav-reports',
            label: 'Go to Reports',
            icon: BarChart3,
            action: () => navigate('/reports'),
            group: 'Navigate',
            keywords: ['export', 'analytics'],
        },
        ...(isAdmin
            ? [
                {
                    id: 'nav-admin-keys',
                    label: 'Admin: API Keys',
                    icon: Key,
                    action: () => navigate('/admin/api-keys'),
                    group: 'Navigate',
                    keywords: ['settings', 'configuration'],
                },
                {
                    id: 'nav-admin-logs',
                    label: 'Admin: Audit Logs',
                    icon: History,
                    action: () => navigate('/admin/audit-logs'),
                    group: 'Navigate',
                    keywords: ['activity', 'history'],
                },
            ]
            : []),
        // Quick actions
        {
            id: 'action-new-request',
            label: 'New Request',
            icon: Plus,
            action: () => navigate('/requests/new'),
            group: 'Actions',
            keywords: ['create', 'add', 'start'],
        },
        // Contextual (only on request detail)
        ...(hasActiveRun
            ? [
                {
                    id: 'ctx-copilot',
                    label: 'Open Copilot',
                    icon: MessageSquare,
                    action: () => {
                        // Trigger copilot via custom event
                        window.dispatchEvent(new CustomEvent('open-copilot'))
                    },
                    group: 'This Request',
                    keywords: ['ai', 'chat', 'ask'],
                },
                {
                    id: 'ctx-report',
                    label: 'Generate Report',
                    icon: FileText,
                    action: () => {
                        window.dispatchEvent(new CustomEvent('generate-report'))
                    },
                    group: 'This Request',
                    keywords: ['export', 'pdf'],
                },
                {
                    id: 'ctx-shortlist',
                    label: 'Create Shortlist',
                    icon: Star,
                    action: () => {
                        window.dispatchEvent(new CustomEvent('create-shortlist'))
                    },
                    group: 'This Request',
                    keywords: ['save', 'favorites'],
                },
                {
                    id: 'ctx-compare',
                    label: 'Compare Top Vendors',
                    icon: Scale,
                    action: () => {
                        window.dispatchEvent(new CustomEvent('compare-vendors'))
                    },
                    group: 'This Request',
                    keywords: ['side by side'],
                },
            ]
            : []),
    ]

    // Keyboard shortcut
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault()
                setOpen((o) => !o)
            }
        }
        document.addEventListener('keydown', handleKeyDown)
        return () => document.removeEventListener('keydown', handleKeyDown)
    }, [])

    // Group commands
    const groups = Array.from(new Set(allCommands.map((c) => c.group)))
    const recentCommands = recentIds
        .map((id) => allCommands.find((c) => c.id === id))
        .filter(Boolean) as CommandItem[]

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogContent className="p-0 max-w-lg overflow-hidden">
                <Command
                    className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground"
                    loop
                >
                    <div className="flex items-center border-b px-3">
                        <Search className="h-4 w-4 text-muted-foreground mr-2" />
                        <Command.Input
                            value={search}
                            onValueChange={setSearch}
                            placeholder="Type a command or search..."
                            className="flex h-12 w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
                        />
                        <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                            ESC
                        </kbd>
                    </div>
                    <Command.List className="max-h-[300px] overflow-y-auto px-2 py-2">
                        <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
                            No results found.
                        </Command.Empty>

                        {/* Recent */}
                        {recentCommands.length > 0 && !search && (
                            <Command.Group heading="Recent">
                                {recentCommands.map((cmd) => (
                                    <Command.Item
                                        key={`recent-${cmd.id}`}
                                        value={cmd.label}
                                        onSelect={() => runCommand(cmd)}
                                        className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer aria-selected:bg-accent"
                                    >
                                        <Clock className="h-4 w-4 text-muted-foreground" />
                                        <span>{cmd.label}</span>
                                    </Command.Item>
                                ))}
                            </Command.Group>
                        )}

                        {/* Grouped commands */}
                        {groups.map((group) => {
                            const items = allCommands.filter((c) => c.group === group)
                            return (
                                <Command.Group key={group} heading={group}>
                                    {items.map((cmd) => (
                                        <Command.Item
                                            key={cmd.id}
                                            value={`${cmd.label} ${cmd.keywords?.join(' ') || ''}`}
                                            onSelect={() => runCommand(cmd)}
                                            className="flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer aria-selected:bg-accent"
                                        >
                                            <cmd.icon className="h-4 w-4 text-muted-foreground" />
                                            <span>{cmd.label}</span>
                                            <ArrowRight className="ml-auto h-3 w-3 text-muted-foreground opacity-0 group-aria-selected:opacity-100" />
                                        </Command.Item>
                                    ))}
                                </Command.Group>
                            )
                        })}
                    </Command.List>
                    <div className="border-t px-3 py-2 text-xs text-muted-foreground flex items-center gap-4">
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">↑↓</kbd>
                            navigate
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">↵</kbd>
                            select
                        </span>
                        <span className="flex items-center gap-1">
                            <kbd className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px]">esc</kbd>
                            close
                        </span>
                    </div>
                </Command>
            </DialogContent>
        </Dialog>
    )
}
