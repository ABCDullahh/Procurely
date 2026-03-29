import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from './hooks'
import { ToastProvider } from './components/ui'
import { AppShell } from './layouts/AppShell'
import {
    Login,
    Dashboard,
    UIKit,
    AdminApiKeys,
    AdminAuditLogs,
    RequestsPage,
    NewRequestPage,
} from './pages'

// Lazy-loaded pages for code splitting
const LandingPage = lazy(() => import('./pages/LandingPage'))
const RequestDetailPage = lazy(() => import('./pages/RequestDetailPage'))
const VendorProfilePage = lazy(() => import('./pages/VendorProfilePage'))
const ShortlistsPage = lazy(() => import('./pages/ShortlistsPage'))
const ShortlistDetailPage = lazy(() => import('./pages/ShortlistDetailPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const ReportViewPage = lazy(() => import('./pages/ReportViewPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const ProcurementChatPage = lazy(() => import('./pages/ProcurementChatPage'))
const CommandPalette = lazy(() => import('./components/CommandPalette'))

// Route-level loading fallback
function RouteLoader() {
    return (
        <div className="min-h-screen flex items-center justify-center">
            <div className="space-y-4 text-center">
                <div className="h-8 w-8 mx-auto rounded-full border-2 border-primary border-t-transparent animate-spin" />
                <p className="text-sm text-muted-foreground">Loading...</p>
            </div>
        </div>
    )
}

// Root redirect based on auth status
function RootRoute() {
    const { isAuthenticated, isLoading } = useAuth()

    if (isLoading) {
        return <RouteLoader />
    }

    if (isAuthenticated) {
        return <Navigate to="/dashboard" replace />
    }

    return (
        <Suspense fallback={<RouteLoader />}>
            <LandingPage />
        </Suspense>
    )
}

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 1,
            refetchOnWindowFocus: false,
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <ToastProvider>
                    <BrowserRouter>
                        <Suspense fallback={<RouteLoader />}>
                            <Routes>
                                {/* Public routes */}
                                <Route path="/" element={<RootRoute />} />
                                <Route path="/login" element={<Login />} />
                                <Route path="/ui-kit" element={<UIKit />} />

                                {/* Protected routes with AppShell layout */}
                                <Route element={<AppShell />}>
                                    <Route path="/dashboard" element={<Dashboard />} />
                                    <Route path="/requests" element={<RequestsPage />} />
                                    <Route path="/requests/new" element={<NewRequestPage />} />
                                    <Route path="/requests/:id" element={<RequestDetailPage />} />
                                    <Route path="/vendors/:id" element={<VendorProfilePage />} />
                                    <Route path="/shortlists" element={<ShortlistsPage />} />
                                    <Route path="/shortlists/:id" element={<ShortlistDetailPage />} />
                                    <Route path="/reports" element={<ReportsPage />} />
                                    <Route path="/reports/:id" element={<ReportViewPage />} />
                                    <Route path="/ai-search" element={<ProcurementChatPage />} />

                                    {/* Admin routes */}
                                    <Route path="/admin" element={<AdminApiKeys />} />
                                    <Route path="/admin/api-keys" element={<AdminApiKeys />} />
                                    <Route path="/admin/audit-logs" element={<AdminAuditLogs />} />
                                </Route>

                                {/* 404 */}
                                <Route path="*" element={<NotFoundPage />} />
                            </Routes>
                            <CommandPalette />
                        </Suspense>
                    </BrowserRouter>
                </ToastProvider>
            </AuthProvider>
        </QueryClientProvider>
    )
}

export default App
