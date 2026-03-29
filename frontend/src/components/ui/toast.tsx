/**
 * Toast notification system
 */

import { useState, useCallback, createContext, useContext, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
    id: string
    type: ToastType
    title: string
    message?: string
    duration?: number
}

interface ToastContextType {
    toasts: Toast[]
    addToast: (toast: Omit<Toast, 'id'>) => void
    removeToast: (id: string) => void
}

const ToastContext = createContext<ToastContextType | null>(null)

export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within ToastProvider')
    }
    return context
}

const ToastIcon = ({ type }: { type: ToastType }) => {
    switch (type) {
        case 'success':
            return <CheckCircle className="w-5 h-5 text-green-500" />
        case 'error':
            return <AlertCircle className="w-5 h-5 text-red-500" />
        case 'warning':
            return <AlertTriangle className="w-5 h-5 text-yellow-500" />
        case 'info':
            return <Info className="w-5 h-5 text-blue-500" />
    }
}

function ToastItem({ toast, onRemove }: { toast: Toast; onRemove: () => void }) {
    return (
        <motion.div
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 100, opacity: 0 }}
            className={cn(
                'flex items-start gap-3 p-4 rounded-xl shadow-lg border',
                'bg-card text-foreground min-w-[300px] max-w-[400px]',
            )}
        >
            <ToastIcon type={toast.type} />
            <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{toast.title}</p>
                {toast.message && (
                    <p className="text-sm text-muted-foreground mt-1">{toast.message}</p>
                )}
            </div>
            <button
                onClick={onRemove}
                className="text-muted-foreground hover:text-foreground transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </motion.div>
    )
}

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([])

    const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
        const id = Math.random().toString(36).slice(2)
        const newToast = { ...toast, id }
        setToasts(prev => [...prev, newToast])

        const duration = toast.duration ?? 5000
        if (duration > 0) {
            setTimeout(() => {
                setToasts(prev => prev.filter(t => t.id !== id))
            }, duration)
        }
    }, [])

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id))
    }, [])

    return (
        <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
            {children}
            <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
                <AnimatePresence>
                    {toasts.map(toast => (
                        <ToastItem
                            key={toast.id}
                            toast={toast}
                            onRemove={() => removeToast(toast.id)}
                        />
                    ))}
                </AnimatePresence>
            </div>
        </ToastContext.Provider>
    )
}
