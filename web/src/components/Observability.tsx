'use client'

import { useMemo } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { useEvaluationMetrics, useRecentEvaluations } from '@/hooks/useApi'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts'
import { Skeleton } from '@/components/ui/Loaders'
import { staggerContainer, staggerItem } from '@/lib/motion'
import { Target, Percent, ListOrdered, Bot } from 'lucide-react'

const CHART_ACCENT = '#0d9488'
const CHART_GRID = '#e2e8f0'

export function Observability() {
  const { data: metrics, isLoading: metricsLoading, isError: metricsError } = useEvaluationMetrics()
  const { data: evaluations, isLoading: evalsLoading, isError: evalsError } = useRecentEvaluations(25)
  const reducedMotion = useReducedMotion() ?? false

  const avgAccuracy = (metrics?.average_score || 0).toFixed(1)
  const avgHallucination = (metrics?.hallucination_rate || 0).toFixed(1)
  const totalEvaluated = metrics?.total_evaluated || 0

  const scoreHistory = useMemo(() => {
    if (!evaluations?.length) return []
    const sorted = [...evaluations].sort((a, b) => {
      const ta = a.timestamp ? new Date(a.timestamp).getTime() : 0
      const tb = b.timestamp ? new Date(b.timestamp).getTime() : 0
      return ta - tb
    })
    return sorted.map((e, i) => ({
      index: i + 1,
      tooltipTime: e.timestamp
        ? new Date(e.timestamp).toLocaleString()
        : `Evaluation ${i + 1}`,
      score: Number(e.score),
    }))
  }, [evaluations])

  const criteriaData = useMemo(() => {
    const cs = metrics?.criteria_scores
    const rows: {
      key: string
      short: string
      raw: number
      max: number
      pct: number
    }[] = [
      {
        key: 'factual',
        short: 'Factual',
        raw: cs?.factual_accuracy ?? 0,
        max: 3,
        pct: 0,
      },
      {
        key: 'complete',
        short: 'Complete',
        raw: cs?.completeness ?? 0,
        max: 3,
        pct: 0,
      },
      {
        key: 'citation',
        short: 'Citation',
        raw: cs?.citation_quality ?? 0,
        max: 2,
        pct: 0,
      },
      {
        key: 'relevance',
        short: 'Relevance',
        raw: cs?.relevance ?? 0,
        max: 2,
        pct: 0,
      },
    ]
    return rows.map((r) => ({
      ...r,
      pct: r.max > 0 ? Math.min(100, Math.round((r.raw / r.max) * 1000) / 10) : 0,
    }))
  }, [metrics?.criteria_scores])

  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Observability</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          LLM-as-judge metrics and evaluation history
        </p>
      </header>

      {(metricsError || evalsError) && (
        <div className="rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-950 dark:text-amber-100">
          Evaluation data failed to load. Ensure the evaluation service is running and the API gateway is restarted
          (proxies <code className="rounded bg-amber-100/80 px-1 dark:bg-amber-900/50">/evaluation/*</code>).
        </div>
      )}

      <motion.div
        className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
        initial="hidden"
        animate="visible"
        variants={staggerContainer(reducedMotion)}
      >
        <motion.div variants={staggerItem(reducedMotion)}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg. accuracy</CardTitle>
            <Target className="h-4 w-4 text-primary" strokeWidth={1.75} aria-hidden />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <>
                <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                  {avgAccuracy}/10
                </p>
                <p
                  className={`text-xs ${
                    (metrics?.average_score || 0) >= 8.5
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-yellow-600 dark:text-yellow-400'
                  }`}
                >
                  {(metrics?.average_score || 0) >= 8.5 ? '✓' : '⚠'} Target: {'>'}8.5
                </p>
              </>
            )}
          </CardContent>
        </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Hallucination rate</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} aria-hidden />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <>
                <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                  {avgHallucination}%
                </p>
                <p
                  className={`text-xs ${
                    (metrics?.hallucination_rate || 0) < 5
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {(metrics?.hallucination_rate || 0) < 5 ? '✓' : '✗'} Target: {'<'}5%
                </p>
              </>
            )}
          </CardContent>
        </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Evaluated</CardTitle>
            <ListOrdered className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} aria-hidden />
          </CardHeader>
          <CardContent>
            {metricsLoading ? (
              <Skeleton className="h-8 w-12" />
            ) : (
              <>
                <p className="font-mono text-2xl font-semibold tabular-nums tracking-tight">
                  {totalEvaluated}
                </p>
                <p className="text-xs text-muted-foreground">Queries assessed</p>
              </>
            )}
          </CardContent>
        </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Judge</CardTitle>
            <Bot className="h-4 w-4 text-primary" strokeWidth={1.75} aria-hidden />
          </CardHeader>
          <CardContent>
            <p className="text-sm font-semibold">Claude (Haiku)</p>
            <p className="text-xs text-muted-foreground">LLM-as-judge</p>
          </CardContent>
        </Card>
        </motion.div>
      </motion.div>

      <div className="grid min-w-0 gap-6 lg:grid-cols-2">
        <Card className="min-w-0 overflow-hidden">
          <CardHeader>
            <CardTitle className="text-lg">Score history</CardTitle>
            <CardDescription>
              Total score per evaluation (0–10), oldest → newest. Aggregate average:{' '}
              {metricsLoading ? '…' : `${avgAccuracy}/10`}
            </CardDescription>
          </CardHeader>
          <CardContent className="min-w-0 pt-0">
            {evalsLoading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : scoreHistory.length === 0 ? (
              <div className="flex h-[300px] items-center justify-center text-sm text-slate-500 dark:text-slate-400">
                No evaluation history yet. Complete queries to plot scores here.
              </div>
            ) : (
              <div className="h-[300px] w-full min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={scoreHistory} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
                    <XAxis
                      dataKey="index"
                      tick={{ fontSize: 11 }}
                      label={{ value: 'Evaluation #', position: 'insideBottom', offset: -4, fontSize: 11 }}
                    />
                    <YAxis domain={[0, 10]} width={40} tickCount={6} />
                    <Tooltip
                      formatter={(value: number) => [`${value.toFixed(1)} / 10`, 'Total score']}
                      labelFormatter={(_, payload) =>
                        payload?.[0]?.payload?.tooltipTime ?? 'Evaluation'
                      }
                    />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke={CHART_ACCENT}
                      strokeWidth={2}
                      dot={{ r: 3, fill: CHART_ACCENT }}
                      name="Total score"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="min-w-0 overflow-hidden">
          <CardHeader>
            <CardTitle className="text-lg">Criteria averages</CardTitle>
            <CardDescription>
              Mean raw score vs rubric max (Factual &amp; Complete: /3, Citation &amp; Relevance: /2), shown
              as % of maximum
            </CardDescription>
          </CardHeader>
          <CardContent className="min-w-0 pt-0">
            {metricsLoading ? (
              <Skeleton className="h-[300px] w-full" />
            ) : (
              <div className="h-[300px] w-full min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={criteriaData} margin={{ top: 8, right: 12, left: 4, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
                    <XAxis dataKey="short" interval={0} tick={{ fontSize: 11 }} />
                    <YAxis
                      domain={[0, 100]}
                      width={44}
                      tickFormatter={(v) => `${v}%`}
                      label={{
                        value: '% of rubric max',
                        angle: -90,
                        position: 'insideLeft',
                        style: { fontSize: 11 },
                      }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null
                        const row = payload[0].payload as {
                          short: string
                          raw: number
                          max: number
                          pct: number
                        }
                        return (
                          <div className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-sm dark:border-slate-700 dark:bg-slate-900">
                            <p className="font-medium text-slate-900 dark:text-slate-100">{row.short}</p>
                            <p className="text-slate-600 dark:text-slate-400">
                              Avg {row.raw.toFixed(2)} / {row.max} ({row.pct}% of max)
                            </p>
                          </div>
                        )
                      }}
                    />
                    <Bar dataKey="pct" fill={CHART_ACCENT} radius={[4, 4, 0, 0]} name="% of max" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recent Evaluations</CardTitle>
          <CardDescription>
            Latest LLM-as-Judge results (up to 10 shown; chart above uses up to 25)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {evalsLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : evaluations && evaluations.length > 0 ? (
            <div className="space-y-3">
              {evaluations.slice(0, 10).map(evaluation => (
                <div
                  key={evaluation.id}
                  className="flex items-start justify-between rounded-md border border-border p-4"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-mono text-sm font-medium">…{evaluation.query_id.slice(-6)}</p>
                      <Badge
                        variant={
                          evaluation.score >= 8.5
                            ? 'success'
                            : evaluation.score >= 7.5
                              ? 'warning'
                              : 'error'
                        }
                        className="text-xs"
                      >
                        {evaluation.score.toFixed(1)}/10
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{evaluation.reasoning}</p>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-muted-foreground">
                      <span>Factual: {evaluation.factual_accuracy}/3</span>
                      <span>Complete: {evaluation.completeness}/3</span>
                      <span>Citation: {evaluation.citation_quality}/2</span>
                      <span>Relevance: {evaluation.relevance}/2</span>
                      {evaluation.hallucinations_detected && (
                        <span className="text-red-600">⚠ Hallucination</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {evaluation.timestamp
                        ? new Date(evaluation.timestamp).toLocaleString()
                        : 'Just now'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-md border border-border bg-muted/30 p-4 text-center">
              <p className="text-sm text-muted-foreground">
                No evaluations yet. Submit queries to see results here.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
