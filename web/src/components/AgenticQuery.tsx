'use client'

import { useState, useLayoutEffect, useEffect, useCallback } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Label, Textarea } from '@/components/ui/Form'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Loaders'
import { useDocuments, useSubmitQuery, useQueryResult } from '@/hooks/useApi'
import { useWebSocketQuery } from '@/hooks/useWebSocketQuery'
import {
  readAgenticQuerySnapshot,
  writeAgenticQuerySnapshot,
  clearAgenticQuerySnapshot,
} from '@/lib/agenticQuerySession'
import { staggerContainer, staggerItem } from '@/lib/motion'
import {
  Lightbulb,
  CheckCircle,
  AlertCircle,
  MessageSquare,
  RefreshCw,
  BookOpen,
} from 'lucide-react'
import type { Document, QueryRequest } from '@/types/api'

export function AgenticQuery() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const [question, setQuestion] = useState('')
  const [useWebSocket, setUseWebSocket] = useState(true)
  const { data: documents } = useDocuments()
  const { mutate: submitQuery } = useSubmitQuery()
  const reducedMotion = useReducedMotion() ?? false

  const {
    messages: wsMessages,
    isLoading: wsLoading,
    error: wsError,
    connect: connectWebSocket,
    reset: resetWebSocket,
  } = useWebSocketQuery()

  const [currentQueryId, setCurrentQueryId] = useState<string | null>(null)
  const { data: pollResult, isLoading: pollLoading } = useQueryResult(currentQueryId)

  const isLoading = useWebSocket ? wsLoading : pollLoading

  useLayoutEffect(() => {
    const s = readAgenticQuerySnapshot()
    if (!s) return
    setSelectedDocId(s.selectedDocId)
    setQuestion(s.question)
    setUseWebSocket(s.useWebSocket)
    setCurrentQueryId(s.currentQueryId)
  }, [])

  const persistForm = useCallback(() => {
    writeAgenticQuerySnapshot({
      selectedDocId,
      question,
      useWebSocket,
      currentQueryId,
    })
  }, [selectedDocId, question, useWebSocket, currentQueryId])

  useEffect(() => {
    persistForm()
  }, [persistForm])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedDocId || !question) return

    const queryRequest: QueryRequest = {
      doc_id: selectedDocId,
      question: question.trim(),
      include_sources: true,
    }

    if (useWebSocket) {
      connectWebSocket(queryRequest)
    } else {
      submitQuery(queryRequest, {
        onSuccess: (data) => {
          setCurrentQueryId(data.query_id)
        },
      })
    }
  }

  const handleReset = () => {
    clearAgenticQuerySnapshot()
    setQuestion('')
    setCurrentQueryId(null)
    resetWebSocket()
  }

  const wsAnswer = wsMessages.find(m => m.type === 'answer')
  const finalAnswer = useWebSocket ? wsAnswer?.content : pollResult?.answer
  const showWsStream =
    useWebSocket &&
    (wsLoading || (wsMessages.length > 0 && !wsAnswer && !wsError))
  const references = useWebSocket ? wsAnswer?.references : pollResult?.references
  const timing = useWebSocket ? undefined : pollResult?.timing

  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Agentic query</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Streamed reasoning and answers over your document tree
        </p>
      </header>

      <motion.div
        className="grid gap-6 lg:grid-cols-3"
        initial="hidden"
        animate="visible"
        variants={staggerContainer(reducedMotion)}
      >
        <motion.div variants={staggerItem(reducedMotion)} className="lg:col-span-1">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <BookOpen className="h-4 w-4 text-primary" strokeWidth={1.75} aria-hidden />
                New query
              </CardTitle>
              <CardDescription>Document and question</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="doc-select">Document</Label>
                <select
                  id="doc-select"
                  value={selectedDocId || ''}
                  onChange={(e) => setSelectedDocId(e.target.value || null)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select a document…</option>
                  {documents?.map((doc: Document) => (
                    <option key={doc.doc_id} value={doc.doc_id}>
                      {doc.filename}
                    </option>
                  ))}
                </select>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="question">Question</Label>
                  <Textarea
                    id="question"
                    placeholder="e.g. What was Q3 revenue?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={isLoading}
                    className="resize-none"
                    rows={4}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Mode</Label>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                    <button
                      type="button"
                      onClick={() => setUseWebSocket(true)}
                      className={`flex items-center justify-center gap-2 rounded-md border-2 px-3 py-2.5 text-sm font-medium transition-colors ${
                        useWebSocket
                          ? 'border-primary bg-primary/5 text-primary'
                          : 'border-border text-muted-foreground hover:border-primary/30'
                      }`}
                    >
                      <MessageSquare className="h-4 w-4 shrink-0" strokeWidth={1.75} aria-hidden />
                      WebSocket
                    </button>
                    <button
                      type="button"
                      onClick={() => setUseWebSocket(false)}
                      className={`flex items-center justify-center gap-2 rounded-md border-2 px-3 py-2.5 text-sm font-medium transition-colors ${
                        !useWebSocket
                          ? 'border-primary bg-primary/5 text-primary'
                          : 'border-border text-muted-foreground hover:border-primary/30'
                      }`}
                    >
                      <RefreshCw className="h-4 w-4 shrink-0" strokeWidth={1.75} aria-hidden />
                      Polling
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={!selectedDocId || !question.trim() || isLoading}
                  className="w-full"
                >
                  {isLoading && <Spinner className="mr-2 h-4 w-4" />}
                  {isLoading ? 'Processing…' : 'Submit query'}
                </Button>

                {(finalAnswer || wsError) && (
                  <Button type="button" variant="outline" onClick={handleReset} className="w-full">
                    New query
                  </Button>
                )}
              </form>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)} className="lg:col-span-2">
          <Card className="min-h-[320px]">
            <CardHeader>
              <CardTitle className="text-base">Response</CardTitle>
              <CardDescription>
                {useWebSocket ? 'Live stream with reasoning steps' : 'Results via polling'}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!selectedDocId ? (
                <p className="text-sm text-muted-foreground">Select a document to begin.</p>
              ) : isLoading || showWsStream ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Spinner className="h-5 w-5" />
                    <p className="text-sm font-medium">
                      {wsLoading ? 'Processing query…' : 'Reconnect to continue (tab was in background)'}
                    </p>
                  </div>
                  {useWebSocket && wsMessages.length > 0 && (
                    <ul className="space-y-2 text-sm">
                      {wsMessages.map((msg, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 rounded-md border border-border bg-muted/40 p-3"
                        >
                          {msg.type === 'status' && (
                            <>
                              <Lightbulb
                                className="mt-0.5 h-4 w-4 shrink-0 text-primary"
                                strokeWidth={1.75}
                                aria-hidden
                              />
                              <span>{msg.message}</span>
                            </>
                          )}
                          {msg.type === 'reasoning' && (
                            <>
                              <Lightbulb
                                className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400"
                                strokeWidth={1.75}
                                aria-hidden
                              />
                              <div>
                                <p className="font-medium">Found {msg.nodes_found} nodes</p>
                                <ul className="mt-1 space-y-0.5 pl-1">
                                  {msg.messages?.map((m, j) => (
                                    <li key={j} className="text-xs text-muted-foreground">
                                      · {m}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            </>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : wsError ? (
                <div className="flex items-start gap-3 rounded-md border border-destructive/40 bg-destructive/5 p-4">
                  <AlertCircle className="h-5 w-5 shrink-0 text-destructive" strokeWidth={1.75} />
                  <div>
                    <p className="font-medium text-destructive">Error</p>
                    <p className="text-sm text-muted-foreground">{wsError}</p>
                  </div>
                </div>
              ) : finalAnswer ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <h3 className="flex items-center gap-2 text-sm font-semibold">
                      <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400" strokeWidth={1.75} />
                      Answer
                    </h3>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{finalAnswer}</p>
                  </div>

                  {timing && (
                    <div className="rounded-md border border-border bg-muted/30 p-4">
                      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                        Latency
                      </p>
                      <dl className="mt-3 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                        <div>
                          <dt className="text-muted-foreground">Total</dt>
                          <dd className="font-mono font-medium tabular-nums">{timing.total_ms}ms</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Tree search</dt>
                          <dd className="font-mono font-medium tabular-nums">{timing.tree_search_ms}ms</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Tree fetch</dt>
                          <dd className="font-mono font-medium tabular-nums">{timing.tree_fetch_ms}ms</dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Answer</dt>
                          <dd className="font-mono font-medium tabular-nums">{timing.answer_gen_ms}ms</dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {references && references.length > 0 && (
                    <div className="space-y-2">
                      <h3 className="text-sm font-semibold">Sources</h3>
                      <ul className="space-y-2">
                        {references.map((ref, i) => {
                          const nodeId = typeof ref === 'string' ? ref : ref.node_id || ''
                          const title =
                            typeof ref === 'string' ? `Node ${ref}` : ref.title || `Node ${nodeId}`

                          return (
                            <li
                              key={i}
                              className="rounded-md border border-border p-3"
                            >
                              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                                <div className="min-w-0 flex-1 text-sm">
                                  <p className="font-medium">{title}</p>
                                  {typeof ref !== 'string' && ref.pages && (
                                    <p className="mt-0.5 text-xs text-muted-foreground">
                                      Pages {ref.pages}
                                    </p>
                                  )}
                                </div>
                                <Badge variant="outline" className="w-fit shrink-0 font-mono text-xs">
                                  {nodeId}
                                </Badge>
                              </div>
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )}
                </div>
              ) : null}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
