'use client'

import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Loaders'
import { useUploadDocument, useDocuments } from '@/hooks/useApi'
import { staggerContainer, staggerItem } from '@/lib/motion'
import { Upload, AlertCircle, Cpu, Database } from 'lucide-react'
import type { Document } from '@/types/api'

export function Ingestion() {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { mutate: uploadDocument, isPending } = useUploadDocument()
  const { data: documents, isLoading, error: documentsError } = useDocuments()
  const reducedMotion = useReducedMotion() ?? false

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(e.type === 'dragenter' || e.type === 'dragover')
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    const files = e.dataTransfer.files
    const file = files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleFile = (files: FileList | null) => {
    const file = files?.[0]
    if (file) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleUpload = () => {
    if (!selectedFile) {
      setError('Please select a file first')
      return
    }

    setError(null)

    uploadDocument(selectedFile, {
      onSuccess: () => {
        setSelectedFile(null)
        setError(null)
      },
      onError: (err: unknown) => {
        const anyErr = err as {
          response?: { data?: { error?: string; message?: string } }
          message?: string
        }
        const backendError = anyErr?.response?.data?.error ?? anyErr?.response?.data?.message
        const message =
          backendError ||
          anyErr?.message ||
          'Upload failed. Make sure the ingestion service is running on port 8080.'
        setError(message)
      },
    })
  }

  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-6">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Document ingestion</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload financial documents for analysis
        </p>
      </header>

      {(error || documentsError) && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertCircle
                className="h-5 w-5 shrink-0 text-destructive"
                strokeWidth={1.75}
                aria-hidden
              />
              <div>
                <p className="font-medium text-destructive">{error || 'Backend service unavailable'}</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Start stack:{' '}
                  <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                    docker-compose up -d
                  </code>{' '}
                  and gateway on <span className="font-mono">8083</span>.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <motion.div
        className="grid gap-6 lg:grid-cols-3"
        initial="hidden"
        animate="visible"
        variants={staggerContainer(reducedMotion)}
      >
        <motion.div className="lg:col-span-2" variants={staggerItem(reducedMotion)}>
          <Card>
            <CardHeader>
              <CardTitle>Upload PDF</CardTitle>
              <CardDescription>Drag and drop or select (max 50MB)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`rounded-md border-2 border-dashed p-8 text-center transition-colors ${
                  dragActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => handleFile(e.target.files)}
                  className="hidden"
                  id="pdf-upload"
                  disabled={isPending}
                />
                <label
                  htmlFor="pdf-upload"
                  className="flex cursor-pointer flex-col items-center gap-2"
                >
                  <Upload className="h-8 w-8 text-muted-foreground" strokeWidth={1.75} aria-hidden />
                  <span className="font-medium">
                    {selectedFile ? selectedFile.name : 'Click to upload or drag and drop'}
                  </span>
                  {selectedFile && (
                    <span className="font-mono text-sm text-muted-foreground tabular-nums">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  )}
                </label>
              </div>

              {selectedFile && (
                <div className="space-y-3">
                  <Button onClick={handleUpload} disabled={isPending} className="w-full sm:w-auto">
                    {isPending && <Spinner className="mr-2 h-4 w-4" />}
                    {isPending ? 'Uploading…' : 'Upload document'}
                  </Button>
                  {error && (
                    <div className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-3">
                      <AlertCircle className="h-4 w-4 shrink-0 text-destructive" strokeWidth={1.75} />
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)}>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="text-base">Pipeline</CardTitle>
              <CardDescription>End-to-end flow</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Upload className="h-4 w-4" strokeWidth={1.75} aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium">Ingestion (Go)</p>
                  <p className="text-xs text-muted-foreground">Validates and stores PDF in object storage</p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-foreground">
                  <Cpu className="h-4 w-4" strokeWidth={1.75} aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium">Parser (Python)</p>
                  <p className="text-xs text-muted-foreground">
                    Tree generation via PageIndex (parser service)
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-foreground">
                  <Database className="h-4 w-4" strokeWidth={1.75} aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium">Cache (Redis)</p>
                  <p className="text-xs text-muted-foreground">Hot tree for low-latency reads</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      <Card>
        <CardHeader>
          <CardTitle>Upload status</CardTitle>
          <CardDescription>Processing progress</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : documents && documents.length > 0 ? (
            <ul className="divide-y divide-border rounded-md border border-border">
              {documents.map((doc: Document) => (
                <li
                  key={doc.doc_id}
                  className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{doc.filename}</p>
                    <p className="mt-0.5 font-mono text-xs text-muted-foreground tabular-nums">
                      {doc.pages} pages · {doc.doc_id.slice(0, 8)}…
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === 'processing' && <Spinner className="h-4 w-4" />}
                    <Badge
                      variant={
                        doc.status === 'completed'
                          ? 'success'
                          : doc.status === 'processing'
                            ? 'warning'
                            : 'error'
                      }
                    >
                      {doc.status}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
