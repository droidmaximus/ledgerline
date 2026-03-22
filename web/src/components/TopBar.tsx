'use client'

import { Button } from '@/components/ui/Button'
import { Menu, TriangleIcon } from 'lucide-react'

type TopBarProps = {
  onMenuClick: () => void
  menuExpanded: boolean
}

export function TopBar({ onMenuClick, menuExpanded }: TopBarProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center gap-3 border-b border-border bg-card/95 px-4 backdrop-blur-md md:hidden">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="shrink-0"
        onClick={onMenuClick}
        aria-expanded={menuExpanded}
        aria-controls="mobile-navigation"
        aria-label="Open navigation menu"
      >
        <Menu className="h-5 w-5" strokeWidth={1.75} />
      </Button>
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <TriangleIcon className="h-4 w-4" strokeWidth={1.75} />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold leading-tight tracking-tight">Ledgerline</p>
          <p className="truncate text-[11px] text-muted-foreground">Financial intelligence</p>
        </div>
      </div>
    </header>
  )
}
