import axios, { AxiosInstance } from 'axios'
import {
  Document,
  QueryRequest,
  QueryResponse,
  CacheStats,
  ServiceHealth,
  ParserMetrics,
  TreeNode,
  IngestionResponse,
} from '@/types/api'

function normalizeDocStatus(raw: string): Document['status'] {
  if (raw === 'completed' || raw === 'parsed') return 'completed'
  if (raw === 'processing') return 'processing'
  return 'error'
}

class ApiClient {
  private client: AxiosInstance
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:8083'
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 30000,
      headers: {
        'Accept': 'application/json',
      },
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        console.error('API Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  // Document endpoints
  async listDocuments(): Promise<Document[]> {
    const response = await this.client.get('/documents')
    const raw = (response.data.documents || []) as Record<string, unknown>[]
    return raw.map((d) => ({
      doc_id: String(d.doc_id ?? ''),
      filename: String(d.filename ?? ''),
      pages: typeof d.pages === 'number' ? d.pages : Number(d.pages) || 0,
      uploaded_at:
        typeof d.uploaded_at === 'string' && d.uploaded_at
          ? d.uploaded_at
          : new Date().toISOString(),
      status: normalizeDocStatus(String(d.status ?? '')),
    }))
  }

  async getDocument(docId: string): Promise<Document> {
    const response = await this.client.get(`/documents/${docId}`)
    return response.data
  }

  async getDocumentTree(docId: string): Promise<TreeNode> {
    const response = await this.client.get(`/documents/${docId}/tree`)
    return response.data
  }

  async uploadDocument(file: File): Promise<IngestionResponse> {
    const formData = new FormData()
    formData.append('file', file)

    // Let the runtime set multipart boundary (manual Content-Type breaks uploads)
    const response = await this.client.post('/documents/upload', formData)
    return response.data
  }

  // Query endpoints (polling)
  async submitQuery(request: QueryRequest): Promise<{ query_id: string }> {
    const response = await this.client.post('/query', request)
    return response.data
  }

  async getQueryResult(queryId: string): Promise<QueryResponse> {
    const response = await this.client.get(`/query/${queryId}`)
    return response.data
  }

  // Health/Metrics endpoints
  async getHealth(): Promise<ServiceHealth> {
    const response = await this.client.get('/health')
    return response.data
  }

  async getCacheStats(): Promise<CacheStats> {
    // Use API gateway so the browser is not blocked by CORS (cache-service has no CORS headers).
    const response = await this.client.get('/cache/stats')
    return response.data
  }

  async getParserMetrics(): Promise<ParserMetrics> {
    const response = await this.client.get('/parser/metrics')
    return response.data
  }

  // Evaluation endpoints (via gateway — direct :8084 calls are blocked by CORS in the browser)
  async getEvaluationMetrics(): Promise<any> {
    const response = await this.client.get('/evaluation/metrics')
    return response.data
  }

  async getRecentEvaluations(limit: number = 10): Promise<any[]> {
    const response = await this.client.get('/evaluation/evaluations', {
      params: { limit },
    })
    return response.data.evaluations || []
  }

  // WebSocket connection
  getWebSocketUrl(): string {
    const baseUrl = this.baseUrl.replace(/^http/, 'ws')
    return `${baseUrl}/ws`
  }

  connectWebSocket(
    queryRequest: QueryRequest,
    onMessage: (message: any) => void,
    onError: (error: Event) => void,
    onClose: () => void
  ): WebSocket {
    const ws = new WebSocket(this.getWebSocketUrl())

    ws.onopen = () => {
      ws.send(JSON.stringify(queryRequest))
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        onMessage(message)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }

    ws.onerror = onError
    ws.onclose = onClose

    return ws
  }
}

// Singleton instance
export const apiClient = new ApiClient()
