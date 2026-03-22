'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from '@/components/ui/Dialog'
import {
  LayoutGrid,
  Upload,
  Search,
  BarChart3,
  Network,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'

export const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutGrid,
    description: 'System metrics and recent activity',
  },
  {
    name: 'Ingestion',
    href: '/ingestion',
    icon: Upload,
    description: 'Upload and manage documents',
  },
  {
    name: 'Tree Explorer',
    href: '/tree-explorer',
    icon: Network,
    description: 'Navigate document structure',
  },
  {
    name: 'Agentic Query',
    href: '/query',
    icon: Search,
    description: 'Stream queries with reasoning',
  },
  {
    name: 'Observability',
    href: '/observability',
    icon: BarChart3,
    description: 'LLM evaluation and system health',
  },
] as const

type SidebarProps = {
  collapsed: boolean
  onCollapsedChange: (collapsed: boolean) => void
  mobileOpen: boolean
  onMobileOpenChange: (open: boolean) => void
}

function NavLinks({
  collapsed,
  onNavigate,
  layoutIdPrefix,
}: {
  collapsed: boolean
  onNavigate?: () => void
  layoutIdPrefix: string
}) {
  const pathname = usePathname()
  const reduceMotion = useReducedMotion()

  return (
    <nav className="space-y-1 p-4" aria-label="Main">
      {navigationItems.map((item) => {
        const Icon = item.icon
        const isActive = pathname === item.href
        return (
          <Link key={item.href} href={item.href} onClick={onNavigate} className="block">
            <div
              className={cn(
                'relative flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {!reduceMotion && isActive && (
                <motion.span
                  layoutId={`${layoutIdPrefix}-nav-active`}
                  className="absolute inset-0 rounded-md bg-primary/10"
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              {reduceMotion && isActive && (
                <span className="absolute inset-0 rounded-md bg-primary/10" />
              )}
              <Icon
                size={20}
                className="relative z-10 flex-shrink-0"
                strokeWidth={1.75}
                aria-hidden
              />
              {!collapsed && (
                <div className="relative z-10 flex-1">
                  <div>{item.name}</div>
                </div>
              )}
            </div>
            {!collapsed && isActive && (
              <div className="ml-2 mt-1 border-l-2 border-primary pl-2 text-xs text-muted-foreground">
                {item.description}
              </div>
            )}
          </Link>
        )
      })}
    </nav>
  )
}

export function Sidebar({
  collapsed,
  onCollapsedChange,
  mobileOpen,
  onMobileOpenChange,
}: SidebarProps) {
  return (
    <>
      <Dialog open={mobileOpen} onOpenChange={onMobileOpenChange}>
        <DialogContent
          id="mobile-navigation"
          className="w-[min(100%,19rem)] max-w-[100vw] border-r p-0"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <DialogTitle className="sr-only">Navigation</DialogTitle>
          <div className="flex shrink-0 items-center gap-2 border-b border-border px-4 py-4 pr-12">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Network className="h-5 w-5" strokeWidth={1.75} />
            </div>
            <div>
              <p className="text-sm font-semibold">Ledgerline</p>
              <p className="text-xs text-muted-foreground">Financial intelligence</p>
            </div>
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto">
            <NavLinks
              collapsed={false}
              onNavigate={() => onMobileOpenChange(false)}
              layoutIdPrefix="mobile"
            />
          </div>
          <div className="mt-auto shrink-0 border-t border-border p-4">
            <p className="text-xs font-medium text-muted-foreground">Status</p>
            <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-emerald-500/30" />
              Operational
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <aside
        className={cn(
          'fixed left-0 top-0 z-30 hidden h-screen flex-col border-r border-border bg-card transition-[width] duration-300 ease-out md:flex',
          collapsed ? 'w-20' : 'w-64'
        )}
        aria-label="Sidebar"
      >
        <div
          className={cn(
            'flex border-b border-border p-4',
            collapsed ? 'flex-col items-center gap-3' : 'items-center justify-between gap-2'
          )}
        >
          {!collapsed ? (
            <div className="flex min-w-0 flex-1 items-center gap-2">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <Network className="h-5 w-5" strokeWidth={1.75} />
              </div>
              <div className="min-w-0">
                <h1 className="truncate text-sm font-semibold tracking-tight">Ledgerline</h1>
                <p className="truncate text-[11px] text-muted-foreground">Financial intelligence</p>
              </div>
            </div>
          ) : (
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Network className="h-5 w-5" strokeWidth={1.75} />
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="shrink-0"
            onClick={() => onCollapsedChange(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="h-[18px] w-[18px]" strokeWidth={1.75} />
            ) : (
              <ChevronLeft className="h-[18px] w-[18px]" strokeWidth={1.75} />
            )}
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <NavLinks collapsed={collapsed} layoutIdPrefix="desktop" />
        </div>

        {!collapsed && (
          <div className="border-t border-border p-4">
            <p className="text-xs font-medium text-muted-foreground">Status</p>
            <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-emerald-500/30" />
              Operational
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
