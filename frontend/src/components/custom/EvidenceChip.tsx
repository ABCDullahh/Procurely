import { cn } from '@/lib/utils'
import { Globe, Building2, ShoppingBag, FileCheck } from 'lucide-react'

type SourceType = 'official' | 'directory' | 'marketplace' | 'document' | 'other'

interface EvidenceChipProps {
    sourceType: SourceType
    url?: string
    className?: string
}

const sourceConfig: Record<SourceType, { label: string; icon: typeof Globe; color: string }> = {
    official: {
        label: 'Official',
        icon: Globe,
        color: 'bg-blue-100 text-blue-700',
    },
    directory: {
        label: 'Directory',
        icon: Building2,
        color: 'bg-purple-100 text-purple-700',
    },
    marketplace: {
        label: 'Marketplace',
        icon: ShoppingBag,
        color: 'bg-orange-100 text-orange-700',
    },
    document: {
        label: 'Document',
        icon: FileCheck,
        color: 'bg-green-100 text-green-700',
    },
    other: {
        label: 'Other',
        icon: Globe,
        color: 'bg-gray-100 text-gray-700',
    },
}

/**
 * EvidenceChip - Shows the source type of evidence with icon
 */
export function EvidenceChip({ sourceType, url, className }: EvidenceChipProps) {
    const config = sourceConfig[sourceType] || sourceConfig.other
    const Icon = config.icon

    const chip = (
        <span
            className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                config.color,
                className
            )}
        >
            <Icon className="w-3 h-3" />
            {config.label}
        </span>
    )

    if (url) {
        return (
            <a href={url} target="_blank" rel="noopener noreferrer" className="hover:opacity-80">
                {chip}
            </a>
        )
    }

    return chip
}
