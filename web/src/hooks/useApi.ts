import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/services/api-client'
import type {
  Document,
  QueryRequest,
  QueryResponse,
  TreeNode,
  CacheStats,
  ServiceHealth,
  ParserMetrics,
  IngestionResponse,
} from '@/types/api'

// Document Queries
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: () => apiClient.listDocuments(),
    refetchInterval: 5000, // Poll every 5 seconds
  })
}

export function useDocument(docId: string | null) {
  return useQuery({
    queryKey: ['documents', docId],
    queryFn: () => docId ? apiClient.getDocument(docId) : null,
    enabled: !!docId,
  })
}

export function useDocumentTree(docId: string | null) {
  return useQuery({
    queryKey: ['documents', docId, 'tree'],
    queryFn: () => docId ? apiClient.getDocumentTree(docId) : null,
    enabled: !!docId,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (file: File) => apiClient.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
  })
}

// Query Mutations
export function useSubmitQuery() {
  return useMutation({
    mutationFn: (request: QueryRequest) => apiClient.submitQuery(request),
  })
}

export function useQueryResult(queryId: string | null, pollingInterval: number = 500) {
  return useQuery({
    queryKey: ['queries', queryId],
    queryFn: () => queryId ? apiClient.getQueryResult(queryId) : null,
    enabled: !!queryId,
    refetchInterval: (data: any) => {
      // Stop polling when complete
      if (data?.status === 'completed' || data?.status === 'error') {
        return false
      }
      return pollingInterval
    },
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
  })
}

// Health & Metrics
export function useServiceHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 30000, // Every 30 seconds
  })
}

export function useCacheStats() {
  return useQuery({
    queryKey: ['cache-stats'],
    queryFn: () => apiClient.getCacheStats(),
    refetchInterval: 10000, // Every 10 seconds
  })
}

export function useParserMetrics() {
  return useQuery({
    queryKey: ['parser-metrics'],
    queryFn: () => apiClient.getParserMetrics(),
    refetchInterval: 15000, // Every 15 seconds
  })
}

// Evaluation metrics
export function useEvaluationMetrics() {
  return useQuery({
    queryKey: ['evaluation-metrics'],
    queryFn: () => apiClient.getEvaluationMetrics(),
    refetchInterval: 30000, // Every 30 seconds
  })
}

export function useRecentEvaluations(limit: number = 10) {
  return useQuery({
    queryKey: ['recent-evaluations', limit],
    queryFn: () => apiClient.getRecentEvaluations(limit),
    refetchInterval: 30000, // Every 30 seconds
  })
}
