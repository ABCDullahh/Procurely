/**
 * EmptyStates - Themed empty states composing illustration components
 */

import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'

import {
    EmptyRequestsIcon,
    EmptySearchIcon,
    EmptyVendorsIcon,
    EmptyReportsIcon,
    EmptyShortlistsIcon,
    EmptyAnalyticsIcon,
} from '@/components/empty'

interface EmptyStateProps {
    icon?: ReactNode
    title: string
    description: string
    action?: {
        label: string
        href?: string
        onClick?: () => void
    }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            {icon && (
                <div className="w-24 h-24 mb-6 rounded-2xl bg-[#F3F0EB] flex items-center justify-center">
                    {icon}
                </div>
            )}
            <h3 className="font-display text-xl font-semibold mb-2 text-[#1A1816]">{title}</h3>
            <p className="text-[#A09A93] max-w-sm mb-6 text-sm">{description}</p>
            {action && (
                action.href ? (
                    <Button asChild>
                        <Link to={action.href}>
                            {action.label}
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                    </Button>
                ) : (
                    <Button onClick={action.onClick}>
                        {action.label}
                        <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                )
            )}
        </div>
    )
}

// === Specific Empty States (using refactored icons) ===

export function EmptyRequests() {
    return (
        <EmptyState
            icon={<EmptyRequestsIcon />}
            title="No requests yet"
            description="Create your first procurement request to start discovering vendors."
            action={{ label: "Create Request", href: "/requests/new" }}
        />
    )
}

export function EmptyRunNotStarted({ onStartSearch }: { onStartSearch?: () => void }) {
    return (
        <EmptyState
            icon={<EmptySearchIcon />}
            title="Ready to search"
            description="Run the AI search to discover and score vendors matching your criteria."
            action={{ label: "Start Search", onClick: onStartSearch }}
        />
    )
}

export function EmptyVendors() {
    return (
        <EmptyState
            icon={<EmptyVendorsIcon />}
            title="No vendors found"
            description="The search didn't find any vendors matching your criteria. Try adjusting your requirements."
        />
    )
}

export function EmptyReports({ onGenerate }: { onGenerate?: () => void }) {
    return (
        <EmptyState
            icon={<EmptyReportsIcon />}
            title="No reports yet"
            description="Generate a report from a completed vendor search to share with stakeholders."
            action={onGenerate ? { label: "Go to Requests", href: "/requests" } : undefined}
        />
    )
}

export function EmptyShortlists() {
    return (
        <EmptyState
            icon={<EmptyShortlistsIcon />}
            title="No shortlists yet"
            description="Create a shortlist to save and compare your favorite vendors."
            action={{ label: "Browse Requests", href: "/requests" }}
        />
    )
}

export function EmptyAnalytics() {
    return (
        <EmptyState
            icon={<EmptyAnalyticsIcon />}
            title="Analytics unavailable"
            description="Complete a vendor search to see analytics and insights."
        />
    )
}

// Utility wrapper for loading states
export function EmptyOrLoading({
    isLoading,
    isEmpty,
    loadingComponent,
    emptyComponent,
    children,
}: {
    isLoading: boolean
    isEmpty: boolean
    loadingComponent: ReactNode
    emptyComponent: ReactNode
    children: ReactNode
}) {
    if (isLoading) return <>{loadingComponent}</>
    if (isEmpty) return <>{emptyComponent}</>
    return <>{children}</>
}
