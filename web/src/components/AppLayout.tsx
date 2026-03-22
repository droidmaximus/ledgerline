'use client'

import { useState } from 'react'
import { usePathname } from 'next/navigation'
import { MotionConfig, motion, useReducedMotion } from 'framer-motion'
import { Sidebar } from '@/components/Sidebar'
import { TopBar } from '@/components/TopBar'
import { cn } from '@/lib/utils'
import { pageVariants } from '@/lib/motion'

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const pathname = usePathname()
  const reducedMotion = useReducedMotion() ?? false

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen bg-background">
        <TopBar
          onMenuClick={() => setMobileNavOpen(true)}
          menuExpanded={mobileNavOpen}
        />
        <Sidebar
          collapsed={collapsed}
          onCollapsedChange={setCollapsed}
          mobileOpen={mobileNavOpen}
          onMobileOpenChange={setMobileNavOpen}
        />
        <main
          className={cn(
            'min-h-screen overflow-auto pt-14 transition-[margin] duration-300 ease-out md:pt-0',
            collapsed ? 'md:ml-20' : 'md:ml-64'
          )}
        >
          <motion.div
            key={pathname}
            className="mx-auto max-w-7xl px-4 py-6 sm:px-6 md:px-8 md:py-8"
            initial="hidden"
            animate="visible"
            variants={pageVariants(reducedMotion)}
          >
            {children}
          </motion.div>
        </main>
      </div>
    </MotionConfig>
  )
}
