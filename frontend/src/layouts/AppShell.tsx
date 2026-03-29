import { useState } from 'react'
import { Link, useLocation, Outlet, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
    LayoutDashboard,
    FileSearch,
    Settings,
    LogOut,
    ChevronRight,
    Star,
    FileText,
    Search,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/hooks'
import { Button } from '@/components/ui'

interface NavItem {
    label: string
    icon: typeof LayoutDashboard
    href: string
    badge?: number
}

// Grouped navigation
const overviewItems: NavItem[] = [
    { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
]

const procurementItems: NavItem[] = [
    { label: 'AI Search', icon: Search, href: '/ai-search' },
    { label: 'Requests', icon: FileSearch, href: '/requests' },
    { label: 'Shortlists', icon: Star, href: '/shortlists' },
    { label: 'Reports', icon: FileText, href: '/reports' },
]

const systemItems: NavItem[] = [
    { label: 'Admin', icon: Settings, href: '/admin' },
]

function NavLink({ item, collapsed }: { item: NavItem; collapsed: boolean }) {
    const location = useLocation()
    const isActive = location.pathname === item.href ||
        (item.href !== '/' && location.pathname.startsWith(item.href))

    return (
        <Link
            to={item.href}
            className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 text-sm',
                'hover:bg-[#ECE8E1]/60',
                isActive && 'bg-crimson-50 text-crimson-600 font-medium',
                !isActive && 'text-[#6B6560]',
                collapsed && 'justify-center px-2'
            )}
        >
            <item.icon className={cn('w-[18px] h-[18px] flex-shrink-0', isActive && 'text-crimson-600')} />
            {!collapsed && (
                <>
                    <span className="flex-1">{item.label}</span>
                    {item.badge && (
                        <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-crimson-100 text-crimson-600 rounded-full min-w-[20px] text-center">
                            {item.badge}
                        </span>
                    )}
                </>
            )}
        </Link>
    )
}

function NavGroup({ label, items, collapsed }: { label: string; items: NavItem[]; collapsed: boolean }) {
    return (
        <div className="space-y-0.5">
            {!collapsed && (
                <p className="px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-[#A09A93]">
                    {label}
                </p>
            )}
            {items.map((item) => (
                <NavLink key={item.href} item={item} collapsed={collapsed} />
            ))}
        </div>
    )
}

export function AppShell() {
    const { user, isAuthenticated, isAdmin, logout } = useAuth()
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

    // Redirect to login if not authenticated
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return (
        <div className="min-h-screen bg-background">
            {/* Sidebar */}
            <aside
                className={cn(
                    'fixed left-0 top-0 z-40 h-screen border-r border-[#ECE8E1] bg-[#FAF9F7] transition-all duration-300',
                    sidebarCollapsed ? 'w-[70px]' : 'w-60'
                )}
            >
                <div className="flex h-full flex-col">
                    {/* Logo */}
                    <div className={cn(
                        'flex items-center gap-2.5 border-b border-[#ECE8E1] px-4 h-14',
                        sidebarCollapsed && 'justify-center px-2'
                    )}>
                        <div className="w-7 h-7 rounded-lg bg-crimson-600 flex items-center justify-center flex-shrink-0">
                            <FileSearch className="w-3.5 h-3.5 text-white" />
                        </div>
                        {!sidebarCollapsed && (
                            <span className="font-display font-bold text-[15px] text-[#1A1816]">Procurely</span>
                        )}
                    </div>

                    {/* Navigation */}
                    <nav className="flex-1 overflow-y-auto p-3 space-y-4">
                        <NavGroup label="Overview" items={overviewItems} collapsed={sidebarCollapsed} />
                        <NavGroup label="Procurement" items={procurementItems} collapsed={sidebarCollapsed} />

                        {isAdmin && (
                            <NavGroup label="System" items={systemItems} collapsed={sidebarCollapsed} />
                        )}
                    </nav>

                    {/* Collapse button */}
                    <button
                        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                        className={cn(
                            'absolute -right-3 top-20 w-6 h-6 rounded-full border border-[#ECE8E1] bg-white',
                            'flex items-center justify-center shadow-sm hover:bg-[#FAF9F7] transition-colors'
                        )}
                    >
                        <ChevronRight
                            className={cn(
                                'w-3.5 h-3.5 text-[#6B6560] transition-transform',
                                sidebarCollapsed ? '' : 'rotate-180'
                            )}
                        />
                    </button>

                    {/* User section */}
                    <div className={cn(
                        'border-t border-[#ECE8E1] p-3',
                        sidebarCollapsed && 'flex flex-col items-center'
                    )}>
                        {!sidebarCollapsed && user && (
                            <div className="flex items-center gap-2.5 mb-3 px-2">
                                <div className="w-8 h-8 rounded-full bg-crimson-600 flex items-center justify-center text-white text-xs font-semibold flex-shrink-0">
                                    {user.email[0].toUpperCase()}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1.5">
                                        <p className="text-sm font-medium truncate text-[#1A1816]">{user.full_name || user.email}</p>
                                        {user.tier === 'free' && (
                                            <span className="inline-flex items-center px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide bg-[#ECE8E1] text-[#6B6560] rounded">
                                                Free
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-[11px] text-[#A09A93] truncate">{user.role}</p>
                                </div>
                            </div>
                        )}

                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={logout}
                            className="h-8 w-8 text-[#6B6560] hover:text-destructive"
                        >
                            <LogOut className="w-4 h-4" />
                        </Button>
                    </div>
                </div>
            </aside>

            {/* Main content */}
            <main
                className={cn(
                    'transition-all duration-300',
                    sidebarCollapsed ? 'ml-[70px]' : 'ml-60'
                )}
            >
                <div className="min-h-screen">
                    <AnimatePresence mode="wait">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Outlet />
                        </motion.div>
                    </AnimatePresence>
                </div>
            </main>
        </div>
    )
}
