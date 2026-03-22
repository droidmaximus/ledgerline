// Document Types
export interface Document {
  doc_id: string
  filename: string
  uploaded_at: string
  pages: number
  status: 'completed' | 'processing' | 'error'
  tree_generated_at?: string
}

// Tree Node Types
export interface TreeNode {
  node_id: string
  title: string
  start_index: number
  end_index: number
  summary: string
  children?: TreeNode[]
}

// Query Types
export interface QueryRequest {
  doc_id: string
  question: string
  include_sources?: boolean
}

export interface QueryReference {
  node_id: string
  title: string
  pages: string
  relevance_score: number
}

export interface QueryResponse {
  query_id: string
  status: 'processing' | 'completed' | 'error'
  answer?: string
  references?: QueryReference[]
  timing?: {
    total_ms: number
    tree_fetch_ms: number
    tree_search_ms: number
    answer_gen_ms: number
  }
  error?: string
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'acknowledged' | 'status' | 'reasoning' | 'answer' | 'error' | 'complete'
  query_id?: string
  message?: string
  step?: number
  nodes_found?: number
  messages?: string[]
  content?: string
  references?: QueryReference[]
  error?: string
}

// Cache Stats
export interface CacheStats {
  hits: number
  misses: number
  cached_items: number
  hit_rate: number
}

// Service Metrics
export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy'
  service: string
  timestamp?: string
}

export interface ParserMetrics {
  documents_processed: number
  avg_processing_time_ms: number
  errors: number
}

// Ingestion Status
export interface IngestionResponse {
  doc_id: string
  status: 'uploaded' | 'processing' | 'error'
  message: string
}

// Evaluation Types (Phase 6)
export interface EvaluationLog {
  eval_id: string
  query_id: string
  score: number
  reasoning: string
  judge_model: string
  timestamp: string
}

// Dashboard Metrics
export interface DashboardMetrics {
  total_documents: number
  documents_processing: number
  recent_queries: number
  system_uptime_hours: number
  cache_hit_rate: number
  avg_query_time_ms: number
}
