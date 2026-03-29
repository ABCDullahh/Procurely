import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import {
    Plus,
    List,
    Loader2,
    MoreHorizontal,
    Trash2,
    Pencil,
    BookmarkCheck,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog'
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { shortlistsApi, Shortlist } from '@/lib/shortlists-api'

export default function ShortlistsPage() {
    const [searchParams] = useSearchParams()
    const requestIdParam = searchParams.get('request_id')
    const requestId = requestIdParam ? parseInt(requestIdParam, 10) : undefined
    const queryClient = useQueryClient()

    const [createDialogOpen, setCreateDialogOpen] = useState(false)
    const [newShortlistName, setNewShortlistName] = useState('')
    const [renameDialogOpen, setRenameDialogOpen] = useState(false)
    const [editingShortlist, setEditingShortlist] = useState<Shortlist | null>(null)
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false)
    const [deletingShortlistId, setDeletingShortlistId] = useState<number | null>(null)

    // Fetch shortlists
    const { data, isLoading, error } = useQuery({
        queryKey: ['shortlists', requestId],
        queryFn: () => shortlistsApi.list(requestId),
    })

    // Create mutation
    const createMutation = useMutation({
        mutationFn: (name: string) =>
            shortlistsApi.create({ name, request_id: requestId }),
        onSuccess: () => {
            toast.success('Shortlist created!')
            queryClient.invalidateQueries({ queryKey: ['shortlists'] })
            setCreateDialogOpen(false)
            setNewShortlistName('')
        },
        onError: (error: Error) => {
            toast.error('Failed to create shortlist: ' + error.message)
        },
    })

    // Rename mutation
    const renameMutation = useMutation({
        mutationFn: ({ id, name }: { id: number; name: string }) =>
            shortlistsApi.update(id, { name }),
        onSuccess: () => {
            toast.success('Shortlist renamed!')
            queryClient.invalidateQueries({ queryKey: ['shortlists'] })
            setRenameDialogOpen(false)
            setEditingShortlist(null)
        },
        onError: (error: Error) => {
            toast.error('Failed to rename: ' + error.message)
        },
    })

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: (id: number) => shortlistsApi.delete(id),
        onSuccess: () => {
            toast.success('Shortlist deleted!')
            queryClient.invalidateQueries({ queryKey: ['shortlists'] })
            setDeleteConfirmOpen(false)
            setDeletingShortlistId(null)
        },
        onError: (error: Error) => {
            toast.error('Failed to delete: ' + error.message)
        },
    })

    const handleCreate = () => {
        if (!newShortlistName.trim()) return
        createMutation.mutate(newShortlistName.trim())
    }

    const handleRename = () => {
        if (!editingShortlist || !editingShortlist.name.trim()) return
        renameMutation.mutate({
            id: editingShortlist.id,
            name: editingShortlist.name.trim(),
        })
    }

    const handleDelete = () => {
        if (!deletingShortlistId) return
        deleteMutation.mutate(deletingShortlistId)
    }

    const openRenameDialog = (shortlist: Shortlist) => {
        setEditingShortlist({ ...shortlist })
        setRenameDialogOpen(true)
    }

    const openDeleteConfirm = (id: number) => {
        setDeletingShortlistId(id)
        setDeleteConfirmOpen(true)
    }

    if (isLoading) {
        return <ShortlistsPageSkeleton />
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center text-muted-foreground">
                    Failed to load shortlists. Please try again.
                </div>
            </div>
        )
    }

    const shortlists = data?.shortlists || []

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-display font-bold tracking-tight text-[#1A1816]">Shortlists</h1>
                    <p className="text-sm text-[#A09A93] mt-1">
                        Organize and compare your favorite vendors
                    </p>
                </div>
                <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            Create Shortlist
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Create Shortlist</DialogTitle>
                            <DialogDescription>
                                Give your shortlist a name to get started.
                            </DialogDescription>
                        </DialogHeader>
                        <Input
                            placeholder="Shortlist name"
                            value={newShortlistName}
                            onChange={(e) => setNewShortlistName(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                        />
                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => setCreateDialogOpen(false)}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleCreate}
                                disabled={
                                    createMutation.isPending || !newShortlistName.trim()
                                }
                            >
                                {createMutation.isPending && (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                )}
                                Create
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            {/* Empty state */}
            {shortlists.length === 0 ? (
                <Card className="text-center py-16">
                    <CardContent>
                        <BookmarkCheck className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-semibold mb-2">
                            No shortlists yet
                        </h3>
                        <p className="text-muted-foreground mb-6">
                            Create your first shortlist to start organizing vendors.
                        </p>
                        <Button onClick={() => setCreateDialogOpen(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Create Shortlist
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {shortlists.map((shortlist) => (
                        <Card key={shortlist.id} className="hover:shadow-md transition-shadow">
                            <CardHeader className="flex flex-row items-center justify-between pb-2">
                                <CardTitle className="text-base">{shortlist.name}</CardTitle>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="sm">
                                            <MoreHorizontal className="h-4 w-4" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end">
                                        <DropdownMenuItem
                                            onClick={() => openRenameDialog(shortlist)}
                                        >
                                            <Pencil className="mr-2 h-4 w-4" />
                                            Rename
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            className="text-destructive"
                                            onClick={() => openDeleteConfirm(shortlist.id)}
                                        >
                                            <Trash2 className="mr-2 h-4 w-4" />
                                            Delete
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                                    <List className="h-4 w-4" />
                                    <span>{shortlist.item_count} vendors</span>
                                </div>
                                <Button variant="outline" size="sm" asChild>
                                    <Link to={`/shortlists/${shortlist.id}`}>
                                        View Shortlist
                                    </Link>
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}

            {/* Rename Dialog */}
            <Dialog open={renameDialogOpen} onOpenChange={setRenameDialogOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Rename Shortlist</DialogTitle>
                    </DialogHeader>
                    <Input
                        value={editingShortlist?.name || ''}
                        onChange={(e) =>
                            setEditingShortlist(
                                editingShortlist
                                    ? { ...editingShortlist, name: e.target.value }
                                    : null
                            )
                        }
                        onKeyDown={(e) => e.key === 'Enter' && handleRename()}
                    />
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setRenameDialogOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            onClick={handleRename}
                            disabled={
                                renameMutation.isPending ||
                                !editingShortlist?.name.trim()
                            }
                        >
                            {renameMutation.isPending && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            Save
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Delete Confirm Dialog */}
            <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Shortlist</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete this shortlist? This action
                            cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button
                            variant="outline"
                            onClick={() => setDeleteConfirmOpen(false)}
                        >
                            Cancel
                        </Button>
                        <Button
                            variant="destructive"
                            onClick={handleDelete}
                            disabled={deleteMutation.isPending}
                        >
                            {deleteMutation.isPending && (
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            )}
                            Delete
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    )
}

function ShortlistsPageSkeleton() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <Skeleton className="h-8 w-48" />
                    <Skeleton className="h-4 w-64 mt-2" />
                </div>
                <Skeleton className="h-10 w-40" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-32" />
                ))}
            </div>
        </div>
    )
}
