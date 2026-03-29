/**
 * LiveSearchProgress - Animated progress display for DeepResearch in chat
 */

import { SearchProgressData, VendorCardData } from '@/lib/procurement-chat-api'
import { cn } from '@/lib/utils'
import { Check, Loader2, Search, FileText, BarChart3, AlertCircle } from 'lucide-react'
import { Progress } from '@/components/ui/progress'

interface LiveSearchProgressProps {
    progress: SearchProgressData | null
    vendors?: VendorCardData[] | null
    onCancel?: () => void
}

const STEP_ICONS: Record<string, React.ElementType> = {
    init: Check,
    search: Search,
    extract: FileText,
    score: BarChart3,
    done: Check,
}

export function LiveSearchProgress({ progress, vendors, onCancel }: LiveSearchProgressProps) {
    if (!progress) return null

    return (
        <div className="space-y-4">
            {/* Animated progress bar */}
            <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                        {progress.current_step === 'search' && 'Mencari vendor di web...'}
                        {progress.current_step === 'extract' && 'Mengekstrak informasi vendor...'}
                        {progress.current_step === 'score' && 'Menilai kualitas vendor...'}
                        {progress.current_step === 'done' && 'Selesai!'}
                        {!['search', 'extract', 'score', 'done'].includes(progress.current_step) && 'Memproses...'}
                    </span>
                    <span className="font-medium">{progress.progress_pct}%</span>
                </div>
                <Progress value={progress.progress_pct} className="h-2" />
            </div>

            {/* Steps */}
            <div className="flex items-center gap-1 py-2">
                {progress.steps.map((step, i) => {
                    const Icon = STEP_ICONS[step.id] || Loader2
                    const isActive = step.status === 'active'
                    const isCompleted = step.status === 'completed'
                    const isFailed = step.status === 'failed'

                    return (
                        <div key={step.id} className="flex items-center">
                            <div
                                className={cn(
                                    'flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                                    isCompleted && 'bg-emerald-100 text-emerald-700',
                                    isActive && 'bg-primary/10 text-primary animate-pulse',
                                    isFailed && 'bg-red-100 text-red-700',
                                    !isCompleted && !isActive && !isFailed && 'bg-muted text-muted-foreground'
                                )}
                            >
                                {isActive ? (
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                ) : isFailed ? (
                                    <AlertCircle className="w-3 h-3" />
                                ) : (
                                    <Icon className="w-3 h-3" />
                                )}
                                <span className="hidden sm:inline">{step.label}</span>
                            </div>
                            {i < progress.steps.length - 1 && (
                                <div
                                    className={cn(
                                        'w-4 h-0.5 mx-1',
                                        isCompleted ? 'bg-emerald-400' : 'bg-muted'
                                    )}
                                />
                            )}
                        </div>
                    )
                })}
            </div>

            {/* Stats */}
            <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-muted-foreground">Vendor ditemukan:</span>
                    <span className="font-semibold">{progress.vendors_found}</span>
                </div>
                {progress.sources_searched > 0 && (
                    <div className="flex items-center gap-2">
                        <span className="text-muted-foreground">Sumber:</span>
                        <span className="font-semibold">{progress.sources_searched}</span>
                    </div>
                )}
            </div>

            {/* Partial vendors preview */}
            {vendors && vendors.length > 0 && (
                <div className="pt-4 border-t">
                    <h4 className="text-sm font-medium text-muted-foreground mb-2">
                        Vendor yang ditemukan sejauh ini:
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {vendors.slice(0, 4).map((vendor) => (
                            <div
                                key={vendor.id}
                                className="flex items-center gap-3 p-2 rounded-lg bg-muted/50 animate-fade-in"
                            >
                                {vendor.logo_url ? (
                                    <img
                                        src={vendor.logo_url}
                                        alt={vendor.name}
                                        className="w-8 h-8 rounded object-contain bg-white"
                                    />
                                ) : (
                                    <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                                        <span className="text-xs font-bold text-primary">
                                            {vendor.name.substring(0, 2).toUpperCase()}
                                        </span>
                                    </div>
                                )}
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">{vendor.name}</p>
                                    <p className="text-xs text-muted-foreground truncate">
                                        {vendor.industry || vendor.location || 'Loading...'}
                                    </p>
                                </div>
                                {vendor.overall_score && (
                                    <div className="text-xs font-semibold text-emerald-600">
                                        {vendor.overall_score.toFixed(0)}%
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                    {vendors.length > 4 && (
                        <p className="text-xs text-muted-foreground mt-2 text-center">
                            +{vendors.length - 4} vendor lainnya...
                        </p>
                    )}
                </div>
            )}

            {/* Cancel button */}
            {onCancel && (
                <div className="pt-2">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 transition-colors"
                    >
                        Batalkan Pencarian
                    </button>
                </div>
            )}
        </div>
    )
}

export default LiveSearchProgress
