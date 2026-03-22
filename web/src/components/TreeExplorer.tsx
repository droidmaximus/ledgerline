'use client'

import { useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Loaders'
import { useDocuments, useDocumentTree } from '@/hooks/useApi'
import { staggerContainer, staggerItem } from '@/lib/motion'
import { ChevronRight, ChevronDown, File, Network } from 'lucide-react'
import type { Document, TreeNode } from '@/types/api'

interface TreeNodeProps {
  node: TreeNode
  level: number
}

function TreeNodeComponent({ node, level }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(level === 0)
  const hasChildren = node.children && node.children.length > 0

  return (
    <div className="space-y-1">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-start gap-2 rounded-md px-3 py-2 hover:bg-muted/80"
        style={{ marginLeft: `${level * 12}px` }}
      >
        {hasChildren ? (
          expanded ? (
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
          ) : (
            <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
          )
        ) : (
          <div className="h-4 w-4" />
        )}
        <div className="flex-1 text-left">
          <p className="font-medium text-sm">{node.title}</p>
          <p className="font-mono text-xs text-muted-foreground tabular-nums">
            p.{node.start_index}–{node.end_index}
          </p>
        </div>
        <Badge variant="outline" className="text-xs">
          {node.node_id}
        </Badge>
      </button>

      {expanded && node.summary && (
        <div className="ml-6 rounded-md border-l-2 border-primary/40 bg-muted/40 p-3 text-xs">
          <p className="text-foreground/90">{node.summary}</p>
        </div>
      )}

      {expanded && hasChildren && (
        <div className="space-y-0">
          {node.children!.map((child) => (
            <TreeNodeComponent key={child.node_id} node={child} level={level + 1} />
          ))}
        </div>
      )}
    </div>
  )
}

export function TreeExplorer() {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null)
  const { data: documents, isLoading: docsLoading } = useDocuments()
  const { data: tree, isLoading: treeLoading } = useDocumentTree(selectedDocId)
  const reducedMotion = useReducedMotion() ?? false

  const selectedDoc = documents?.find(d => d.doc_id === selectedDocId)

  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-6">
        <h1 className="flex flex-wrap items-center gap-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          <Network className="h-7 w-7 text-primary sm:h-8 sm:w-8" strokeWidth={1.5} aria-hidden />
          Tree explorer
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Hierarchical document tree per filing (structure from PageIndex)
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
            <CardTitle className="text-lg">Documents</CardTitle>
            <CardDescription>Select a document to explore</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {docsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : documents && documents.length > 0 ? (
              documents.map((doc: Document) => (
                <button
                  key={doc.doc_id}
                  onClick={() => setSelectedDocId(doc.doc_id)}
                  className={`w-full rounded-md border p-3 text-left transition-colors ${
                    selectedDocId === doc.doc_id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/40'
                  }`}
                >
                  <p className="flex items-center gap-2 text-sm font-medium">
                    <File className="h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} aria-hidden />
                    {doc.filename}
                  </p>
                  <p className="font-mono text-xs text-muted-foreground tabular-nums">{doc.pages} pages</p>
                  <Badge
                    variant={
                      doc.status === 'completed'
                        ? 'success'
                        : doc.status === 'processing'
                          ? 'warning'
                          : 'error'
                    }
                    className="mt-2 text-xs"
                  >
                    {doc.status}
                  </Badge>
                </button>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No documents available</p>
            )}
          </CardContent>
        </Card>
        </motion.div>

        <motion.div variants={staggerItem(reducedMotion)} className="lg:col-span-2">
        <Card className="min-h-[280px]">
          <CardHeader>
            <CardTitle className="text-lg">
              {selectedDoc ? selectedDoc.filename : 'Select a document'}
            </CardTitle>
            <CardDescription>
              {selectedDoc && `${selectedDoc.pages} pages • ${selectedDoc.status}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!selectedDocId ? (
              <p className="text-sm text-muted-foreground">
                Select a document to load its tree.
              </p>
            ) : treeLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map(i => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : tree ? (
              <div className="max-h-[600px] overflow-y-auto space-y-0">
                <TreeNodeComponent node={tree} level={0} />
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Tree not available yet. Wait for processing to finish.
              </p>
            )}
          </CardContent>
        </Card>
        </motion.div>
      </motion.div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">About document trees</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            Ledgerline stores each document as a hierarchical tree. Structure generation uses the{' '}
            <strong>PageIndex</strong> framework; each node represents a logical section with:
          </p>
          <ul className="ml-4 space-y-1 list-disc">
            <li><strong>Node ID:</strong> Unique identifier for tree navigation</li>
            <li><strong>Title:</strong> Section heading</li>
            <li><strong>Pages:</strong> Document page range (start-end)</li>
            <li><strong>Summary:</strong> AI-generated summary of section content</li>
            <li><strong>Hierarchy:</strong> Parent-child relationships enable reasoning-based navigation</li>
          </ul>
          <p className="mt-2">
            This structure enables LLM-driven tree search without vector databases, using document hierarchy instead of chunk embeddings.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
