import { useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
    ArrowLeft,
    GripVertical,
    Trash2,
    ExternalLink,
    Building2,
    GitCompare,
    Save,
    X,
    Pencil,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { shortlistsApi, ShortlistItem } from '@/lib/shortlists-api'
import CompareMatrix from '@/components/CompareMatrix'

export default function ShortlistDetailPage() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const queryClient = useQueryClient()
    const shortlistId = parseInt(id || '0', 10)

    const [editingNotesId, setEditingNotesId] = useState<number | null>(null)
    const [editingNotesValue, setEditingNotesValue] = useState('')
    const [compareOpen, setCompareOpen] = useState(false)
    const [draggingId, setDraggingId] = useState<number | null>(null)

    // Fetch shortlist detail
    const { data: shortlist, isLoading, error } = useQuery({
        queryKey: ['shortlist', shortlistId],
        queryFn: () => shortlistsApi.get(shortlistId),
        enabled: shortlistId > 0,
    })

    // Remove vendor mutation
    const removeMutation = useMutation({
        mutationFn: (vendorId: number) =>
            shortlistsApi.removeVendor(shortlistId, vendorId),
        onSuccess: () => {
            toast.success('Vendor removed from shortlist')
            queryClient.invalidateQueries({ queryKey: ['shortlist', shortlistId] })
        },
        onError: (error: Error) => {
            toast.error('Failed to remove vendor: ' + error.message)
        },
    })

    // Update notes mutation
    const updateNotesMutation = useMutation({
        mutationFn: ({ vendorId, notes }: { vendorId: number; notes: string | null }) =>
            shortlistsApi.updateNotes(shortlistId, vendorId, notes),
        onSuccess: () => {
            toast.success('Notes saved')
            queryClient.invalidateQueries({ queryKey: ['shortlist', shortlistId] })
            setEditingNotesId(null)
        },
        onError: (error: Error) => {
            toast.error('Failed to save notes: ' + error.message)
        },
    })

    // Reorder mutation
    const reorderMutation = useMutation({
        mutationFn: (itemIds: number[]) => shortlistsApi.reorder(shortlistId, itemIds),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['shortlist', shortlistId] })
        },
        onError: (error: Error) => {
            toast.error('Failed to reorder: ' + error.message)
        },
    })

    const startEditNotes = (item: ShortlistItem) => {
        setEditingNotesId(item.vendor_id)
        setEditingNotesValue(item.notes || '')
    }

    const saveNotes = (vendorId: number) => {
        updateNotesMutation.mutate({ vendorId, notes: editingNotesValue || null })
    }

    const cancelEditNotes = () => {
        setEditingNotesId(null)
        setEditingNotesValue('')
    }

    // Simple drag and drop handlers
    const handleDragStart = useCallback((e: React.DragEvent, itemId: number) => {
        setDraggingId(itemId)
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', String(itemId))
    }, [])

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
    }, [])

    const handleDrop = useCallback(
        (e: React.DragEvent, targetItemId: number) => {
            e.preventDefault()
            const draggedId = parseInt(e.dataTransfer.getData('text/plain'), 10)
            if (draggedId === targetItemId || !shortlist) return

            const items = [...shortlist.items]
            const draggedIndex = items.findIndex((i) => i.id === draggedId)
            const targetIndex = items.findIndex((i) => i.id === targetItemId)

            if (draggedIndex === -1 || targetIndex === -1) return

            // Swap positions
            const [draggedItem] = items.splice(draggedIndex, 1)
            items.splice(targetIndex, 0, draggedItem)

            const newItemIds = items.map((i) => i.id)
            reorderMutation.mutate(newItemIds)
            setDraggingId(null)
        },
        [shortlist, reorderMutation]
    )

    const handleDragEnd = useCallback(() => {
        setDraggingId(null)
    }, [])

    if (isLoading) {
        return <ShortlistDetailSkeleton />
    }

    if (error || !shortlist) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Button variant="ghost" onClick={() => navigate('/shortlists')}>
                    <ArrowLeft className="mr-2 h-4 w-4" /> Back to Shortlists
                </Button>
                <div className="mt-8 text-center text-muted-foreground">
                    Shortlist not found or you don't have access.
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" asChild>
                        <Link to="/shortlists">
                            <ArrowLeft className="mr-2 h-4 w-4" /> Back
                        </Link>
                    </Button>
                    <div>
                        <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">{shortlist.name}</h1>
                        <p className="text-sm text-[#A09A93]">
                            {shortlist.items.length} vendors
                        </p>
                    </div>
                </div>
                {shortlist.items.length >= 2 && (
                    <Button onClick={() => setCompareOpen(true)}>
                        <GitCompare className="mr-2 h-4 w-4" />
                        Compare
                    </Button>
                )}
            </div>

            {/* Empty state */}
            {shortlist.items.length === 0 ? (
                <Card className="text-center py-16">
                    <CardContent>
                        <Building2 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">No vendors yet</h3>
                        <p className="text-muted-foreground">
                            Add vendors to this shortlist from the search results or vendor
                            profiles.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    {shortlist.items.map((item) => (
                        <Card
                            key={item.id}
                            draggable
                            onDragStart={(e) => handleDragStart(e, item.id)}
                            onDragOver={handleDragOver}
                            onDrop={(e) => handleDrop(e, item.id)}
                            onDragEnd={handleDragEnd}
                            className={`transition-all ${draggingId === item.id
                                ? 'opacity-50 ring-2 ring-primary'
                                : 'hover:shadow-md'
                                }`}
                        >
                            <CardContent className="pt-4">
                                <div className="flex items-start gap-4">
                                    {/* Drag handle */}
                                    <div className="cursor-grab active:cursor-grabbing pt-1">
                                        <GripVertical className="h-5 w-5 text-muted-foreground" />
                                    </div>

                                    {/* Vendor logo */}
                                    {item.vendor.logo_url ? (
                                        <img
                                            src={item.vendor.logo_url}
                                            alt={item.vendor.name}
                                            className="h-12 w-12 rounded-lg object-contain bg-white border"
                                        />
                                    ) : (
                                        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                                            <Building2 className="h-6 w-6 text-primary" />
                                        </div>
                                    )}

                                    {/* Vendor info */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h3 className="font-semibold">
                                                <Link
                                                    to={`/vendors/${item.vendor.id}`}
                                                    className="hover:text-primary"
                                                >
                                                    {item.vendor.name}
                                                </Link>
                                            </h3>
                                            {item.vendor.website && (
                                                <a
                                                    href={item.vendor.website}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="text-muted-foreground hover:text-primary"
                                                >
                                                    <ExternalLink className="h-4 w-4" />
                                                </a>
                                            )}
                                        </div>

                                        {/* Scores */}
                                        <div className="flex gap-2 mt-2">
                                            {item.vendor.overall_score != null && (
                                                <Badge variant="secondary">
                                                    Overall: {item.vendor.overall_score.toFixed(0)}
                                                </Badge>
                                            )}
                                            {item.vendor.fit_score != null && (
                                                <Badge variant="outline">
                                                    Fit: {item.vendor.fit_score.toFixed(0)}
                                                </Badge>
                                            )}
                                            {item.vendor.trust_score != null && (
                                                <Badge variant="outline">
                                                    Trust: {item.vendor.trust_score.toFixed(0)}
                                                </Badge>
                                            )}
                                        </div>

                                        {/* Notes */}
                                        <div className="mt-3">
                                            {editingNotesId === item.vendor_id ? (
                                                <div className="space-y-2">
                                                    <Textarea
                                                        value={editingNotesValue}
                                                        onChange={(e) =>
                                                            setEditingNotesValue(e.target.value)
                                                        }
                                                        placeholder="Add notes about this vendor..."
                                                        rows={2}
                                                    />
                                                    <div className="flex gap-2">
                                                        <Button
                                                            size="sm"
                                                            onClick={() => saveNotes(item.vendor_id)}
                                                            disabled={updateNotesMutation.isPending}
                                                        >
                                                            <Save className="mr-1 h-3 w-3" />
                                                            Save
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={cancelEditNotes}
                                                        >
                                                            <X className="mr-1 h-3 w-3" />
                                                            Cancel
                                                        </Button>
                                                    </div>
                                                </div>
                                            ) : (
                                                <div
                                                    className="group cursor-pointer p-2 -m-2 rounded hover:bg-muted/50"
                                                    onClick={() => startEditNotes(item)}
                                                >
                                                    {item.notes ? (
                                                        <p className="text-sm text-muted-foreground italic">
                                                            "{item.notes}"
                                                        </p>
                                                    ) : (
                                                        <p className="text-sm text-muted-foreground flex items-center gap-1">
                                                            <Pencil className="h-3 w-3" />
                                                            Add notes...
                                                        </p>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="text-destructive hover:text-destructive"
                                        onClick={() => removeMutation.mutate(item.vendor_id)}
                                        disabled={removeMutation.isPending}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Compare Matrix Modal */}
            {compareOpen && (
                <CompareMatrix
                    vendors={shortlist.items.map((i) => i.vendor)}
                    open={compareOpen}
                    onClose={() => setCompareOpen(false)}
                />
            )}
        </div>
    )
}

function ShortlistDetailSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex items-center gap-4 mb-8">
                <Skeleton className="h-8 w-20" />
                <div>
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-24 mt-2" />
                </div>
            </div>
            <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-32" />
                ))}
            </div>
        </div>
    )
}
