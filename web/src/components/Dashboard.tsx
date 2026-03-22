'use client'

import { motion, useReducedMotion } from 'framer-motion'
import { useCacheStats, useDocuments, useServiceHealth } from '@/hooks/useApi'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Loaders'
import { staggerContainer, staggerItem } from '@/lib/motion'
import { Activity, FileText, Gauge, Server } from 'lucide-react'
import type { Document } from '@/types/api'

export function Dashboard() {
  const { data: documents, isLoading: docsLoading } = useDocuments()
  const { data: cacheStats, isLoading: cacheLoading } = useCacheStats()
  const { data: health, isLoading: healthLoading } = useServiceHealth()
  const reducedMotion = useReducedMotion() ?? false

  const processingDocs = documents?.filter(d => d.status === 'processing').length || 0
  const completedDocs = documents?.filter(d => d.status === 'completed').length || 0

  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          System metrics and recent activity
        </p>
      </header>

      <motion.div
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
        initial="hidden"
        animate="visible"
        variants={staggerContainer(reducedMotion)}
      >
        <motion.div variants={staggerItem(reducedMotion)}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total documents
              </CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} aria-hidden />
            </CardHeader>
            <CardContent>
              {docsLoading ? (
                <Skeleton className="h-8 w-14" />
              ) : (
                <>
                  <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                    {documents?.length ?? 0}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    <span className="font-mono tabular-nums">{completedDocs}</span> completed
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Processing</CardTitle>
              <Activity className="h-4 w-4 text-amber-600 dark:text-amber-400" strokeWidth={1.75} aria-hidden />
            </CardHeader>
            <CardContent>
              {docsLoading ? (
                <Skeleton className="h-8 w-14" />
              ) : (
                <>
                  <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                    {processingDocs}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">In pipeline</p>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Cache hit rate
              </CardTitle>
              <Gauge className="h-4 w-4 text-primary" strokeWidth={1.75} aria-hidden />
            </CardHeader>
            <CardContent>
              {cacheLoading ? (
                <Skeleton className="h-8 w-14" />
              ) : (
                <>
                  <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                    {((cacheStats?.hit_rate || 0) * 100).toFixed(1)}%
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    <span className="font-mono tabular-nums">{cacheStats?.hits ?? 0}</span> hits
                  </p>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Gateway</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} aria-hidden />
            </CardHeader>
            <CardContent>
              {healthLoading ? (
                <Skeleton className="h-8 w-20" />
              ) : (
                <>
                  <Badge
                    variant={
                      health?.status === 'healthy'
                        ? 'success'
                        : health?.status === 'degraded'
                          ? 'warning'
                          : 'error'
                    }
                    className="mb-2"
                  >
                    {health?.status || 'unknown'}
                  </Badge>
                  <p className="text-xs text-muted-foreground">{health?.service || 'API Gateway'}</p>
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      <Card>
        <CardHeader>
          <CardTitle>Recent documents</CardTitle>
          <CardDescription>Latest files in the system</CardDescription>
        </CardHeader>
        <CardContent>
          {docsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : documents && documents.length > 0 ? (
            <motion.ul
              className="divide-y divide-border rounded-md border border-border"
              initial="hidden"
              animate="visible"
              variants={staggerContainer(reducedMotion)}
            >
              {documents.slice(0, 5).map((doc: Document) => (
                <motion.li
                  key={doc.doc_id}
                  variants={staggerItem(reducedMotion)}
                  className="flex flex-col gap-2 p-4 first:rounded-t-md last:rounded-b-md sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-medium leading-snug">{doc.filename}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      <span className="font-mono tabular-nums">{doc.pages}</span> pages ·{' '}
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge
                    variant={
                      doc.status === 'completed'
                        ? 'success'
                        : doc.status === 'processing'
                          ? 'warning'
                          : 'error'
                    }
                    className="w-fit shrink-0"
                  >
                    {doc.status}
                  </Badge>
                </motion.li>
              ))}
            </motion.ul>
          ) : (
            <p className="text-sm text-muted-foreground">No documents yet. Upload your first PDF.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
