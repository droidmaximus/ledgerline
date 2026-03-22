# Implementation Plan: Agentic Financial Intelligence Engine (Vectorless RAG)

## Project Overview

**Goal**: Build a portfolio-showcase microservices system demonstrating vectorless RAG using PageIndex framework for financial document analysis.

**Core Innovation**: Replace traditional vector databases and chunking with PageIndex's hierarchical tree navigation, enabling LLM reasoning-based retrieval with strong reported accuracy on financial document QA (see PageIndex / Vectify publications and evals).

**Target Architecture**: Event-driven polyglot microservices on AWS EKS with Go, Python, Kafka, and Kubernetes.

---

## Technology Stack

### Languages & Frameworks
- **Go**: Fiber framework for high-performance services (Ingestion, API Gateway)
- **Python**: FastAPI for LLM-integrated services (Parser, Cache Manager)
- **PageIndex**: Vectorless RAG framework (https://github.com/VectifyAI/PageIndex)

### Infrastructure
- **Message Queue**: Apache Kafka (AWS MSK managed service)
- **Cache**: Redis (AWS ElastiCache)
- **Storage**: AWS S3 (documents + tree structures)
- **Container Orchestration**: AWS EKS (Elastic Kubernetes Service)
- **GitOps**: ArgoCD for declarative deployments
- **Observability**: Prometheus + Grafana + OpenTelemetry + Jaeger

### Supporting Tools
- **LLM Provider**: OpenAI API (GPT-4.1 for PageIndex operations)
- **Container Registry**: AWS ECR
- **IaC**: Terraform for cloud resources
- **CI/CD**: GitHub Actions
- **Load Balancer**: NGINX Ingress Controller
- **Secrets**: AWS Secrets Manager + Kubernetes Secrets

---

## Project Structure

```
pageindex/
├── services/
│   ├── ingestion-service/          # Go - High-throughput PDF ingestion
│   │   ├── cmd/
│   │   │   └── main.go
│   │   ├── internal/
│   │   │   ├── handlers/
│   │   │   │   ├── upload.go
│   │   │   │   └── health.go
│   │   │   ├── storage/
│   │   │   │   └── s3.go
│   │   │   ├── messaging/
│   │   │   │   └── producer.go
│   │   │   └── config/
│   │   │       └── config.go
│   │   ├── Dockerfile
│   │   ├── go.mod
│   │   └── go.sum
│   ├── parser-service/             # Python - PageIndex document parsing
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── consumer.py
│   │   │   ├── pageindex_client.py
│   │   │   ├── storage.py
│   │   │   └── config.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── cache-service/              # Python - Redis tree caching
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── cache.py
│   │   │   ├── consumer.py
│   │   │   └── metrics.py
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── api-gateway/                # Go - WebSocket streaming queries
│   │   ├── cmd/
│   │   │   └── main.go
│   │   ├── internal/
│   │   │   ├── handlers/
│   │   │   │   ├── query.go
│   │   │   │   ├── websocket.go
│   │   │   │   └── documents.go
│   │   │   ├── llm/
│   │   │   │   └── tree_search.go
│   │   │   ├── clients/
│   │   │   │   └── cache.go
│   │   │   └── middleware/
│   │   │       └── cors.go
│   │   ├── Dockerfile
│   │   ├── go.mod
│   │   └── go.sum
│   └── evaluation-service/         # Python - LLM-as-a-Judge (Phase 6)
│       ├── app/
│       │   ├── main.py
│       │   ├── judge.py
│       │   └── storage.py
│       ├── Dockerfile
│       └── requirements.txt
├── kubernetes/
│   ├── base/
│   │   ├── kafka/
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── redis/
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   ├── ingestion-service/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── configmap.yaml
│   │   ├── parser-service/
│   │   ├── cache-service/
│   │   ├── api-gateway/
│   │   └── observability/
│   │       ├── prometheus/
│   │       └── grafana/
│   └── overlays/
│       ├── dev/
│       │   └── kustomization.yaml
│       └── prod/
│           ├── kustomization.yaml
│           ├── hpa.yaml
│           └── ingress.yaml
├── infrastructure/
│   └── terraform/
│       ├── main.tf
│       ├── eks.tf
│       ├── vpc.tf
│       ├── msk.tf
│       ├── elasticache.tf
│       ├── s3.tf
│       ├── iam.tf
│       └── variables.tf
├── docker/
│   └── docker-compose.yml          # Local development stack
├── docs/
│   └── api-spec.yaml               # OpenAPI; user-facing guide is README.md
├── scripts/
│   ├── dev/
│   │   ├── start-local.ps1         # Windows: start app services
│   │   └── stop-local.ps1
│   ├── setup/
│   │   ├── init-kafka-topics.sh
│   │   └── seed-sample-data.sh
│   └── deploy/
│       └── deploy-to-eks.sh
├── sample-data/                    # Local PDFs only (gitignored; use scripts/seed or add your own)
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── build-images.yml
│       └── deploy.yml
├── .gitignore
├── .env.example
├── Makefile
├── README.md                       # User guide (setup, run, tests, deploy summary)
└── AGENTS.md                       # This file — phased plan for maintainers/agents
```

---

## Implementation Phases

## Phase 0: Project Initialization (Foundation)

**Objective**: Set up project structure, local development environment, and CI/CD pipeline.

**Duration**: 2-3 days

### Tasks

#### 0.1 Repository Initialization
- [ ] Initialize Git repository with .gitignore (Go, Python, Kubernetes, .env, node_modules)
- [ ] Create complete directory structure (all folders from project structure)
- [ ] Add MIT or Apache 2.0 LICENSE file
- [ ] Create initial README.md with project description

#### 0.2 Environment Configuration
- [ ] Create `.env.example` with all required variables:
  ```bash
  # AWS Configuration
  AWS_REGION=us-east-1
  AWS_ACCESS_KEY_ID=your_key
  AWS_SECRET_ACCESS_KEY=your_secret
  S3_BUCKET_DOCUMENTS=pageindex-documents
  S3_BUCKET_TREES=pageindex-trees
  
  # Kafka Configuration
  KAFKA_BROKERS=localhost:9092
  KAFKA_TOPIC_INGESTED=documents.ingested
  KAFKA_TOPIC_PARSED=documents.parsed
  KAFKA_TOPIC_QUERIES=queries.completed
  
  # Redis Configuration
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD=
  
  # OpenAI API
  GEMINI_API_KEY=your_gemini_key
  CHATGPT_API_KEY=your_openai_key  # PageIndex uses this env var
  
  # Service Ports
  INGESTION_SERVICE_PORT=8080
  PARSER_SERVICE_PORT=8081
  CACHE_SERVICE_PORT=8082
  API_GATEWAY_PORT=8083
  ```

#### 0.3 Docker Compose Setup
- [ ] Create `docker/docker-compose.yml` with:
  - Zookeeper (for Kafka)
  - Kafka (single broker)
  - Redis (single instance)
  - MinIO (S3-compatible local storage)
  - Kafka UI (for debugging)
  - RedisInsight (optional, for Redis debugging)
- [ ] Test: `docker-compose up -d` and verify all containers healthy
- [ ] Create init scripts for Kafka topics

#### 0.4 Makefile Creation
- [ ] Create `Makefile` with commands:
  ```makefile
  # Local Development
  .PHONY: up down logs clean
  up:
      docker-compose -f docker/docker-compose.yml up -d
  down:
      docker-compose -f docker/docker-compose.yml down
  logs:
      docker-compose -f docker/docker-compose.yml logs -f
  clean:
      docker-compose -f docker/docker-compose.yml down -v
  
  # Service Management
  .PHONY: run-ingestion run-parser run-cache run-gateway
  run-ingestion:
      cd services/ingestion-service && go run cmd/main.go
  run-parser:
      cd services/parser-service && python -m app.main
  run-cache:
      cd services/cache-service && python -m app.main
  run-gateway:
      cd services/api-gateway && go run cmd/main.go
  
  # Testing
  .PHONY: test
  test:
      cd services/ingestion-service && go test ./...
      cd services/api-gateway && go test ./...
      cd services/parser-service && pytest tests/ -v
      cd services/cache-service && pytest tests/ -v
  
  # Build
  .PHONY: build-all build-ingestion build-parser build-cache build-gateway
  build-all: build-ingestion build-parser build-cache build-gateway
  build-ingestion:
      docker build -t pageindex-ingestion:latest services/ingestion-service
  build-parser:
      docker build -t pageindex-parser:latest services/parser-service
  build-cache:
      docker build -t pageindex-cache:latest services/cache-service
  build-gateway:
      docker build -t pageindex-gateway:latest services/api-gateway
  
  # Kubernetes
  .PHONY: deploy-dev deploy-prod k8s-status
  deploy-dev:
      kubectl apply -k kubernetes/overlays/dev
  deploy-prod:
      kubectl apply -k kubernetes/overlays/prod
  k8s-status:
      kubectl get pods -A
  ```

#### 0.5 GitHub Actions CI/CD
- [ ] Create `.github/workflows/ci.yml`:
  - Trigger on push/pull_request
  - Jobs: lint-go, lint-python, test-go, test-python
  - Build Docker images (multi-arch: amd64, arm64)
  - Push to AWS ECR (on main branch)
- [ ] Set up GitHub Secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_REGION`
  - `ECR_REGISTRY`

#### 0.6 Documentation
- [ ] Maintain `README.md` as the single user-facing guide (setup, infra, services, tests, deploy pointers, troubleshooting)
- [ ] Keep `docs/api-spec.yaml` (OpenAPI 3.0 spec); deeper design detail lives in this `AGENTS.md` where needed

### Verification Checklist
- [ ] `docker-compose up` runs all services successfully
- [ ] Kafka topics created automatically
- [ ] MinIO accessible at http://localhost:9000
- [ ] Redis accessible at localhost:6379
- [ ] All Makefile commands execute without errors
- [ ] GitHub Actions workflow passes on sample commit

---

## Phase 1: Ingestion Service (Go)

**Objective**: Build high-throughput PDF upload service with S3 storage and Kafka event publishing.

**Duration**: 3-4 days

### Tasks

#### 1.1 Go Project Setup
- [ ] Initialize Go module: `cd services/ingestion-service && go mod init github.com/yourusername/pageindex/ingestion`
- [ ] Install dependencies:
  ```bash
  go get github.com/gofiber/fiber/v2
  go get github.com/segmentio/kafka-go
  go get github.com/aws/aws-sdk-go-v2/service/s3
  go get github.com/aws/aws-sdk-go-v2/config
  go get github.com/google/uuid
  go get github.com/rs/zerolog/log
  go get github.com/joho/godotenv
  ```

#### 1.2 Configuration Module
- [ ] Create `internal/config/config.go`:
  - Load from environment variables
  - Validate required fields
  - Struct for S3, Kafka, Server config

#### 1.3 S3 Storage Client
- [ ] Create `internal/storage/s3.go`:
  - `NewS3Client()` - Initialize AWS S3 client
  - `UploadDocument(ctx, reader, filename) (string, error)` - Upload PDF, return S3 URI
  - `GeneratePresignedURL(ctx, key) (string, error)` - For parser service access
  - Use UUID for unique document IDs

#### 1.4 Kafka Producer
- [ ] Create `internal/messaging/producer.go`:
  - `NewKafkaProducer(brokers []string) (*Producer, error)`
  - `PublishDocumentIngested(ctx, docID, s3URI, metadata) error`
  - Message schema: `{"doc_id", "s3_uri", "filename", "timestamp", "metadata"}`
  - Async with error handling

#### 1.5 HTTP Handlers
- [ ] Create `internal/handlers/upload.go`:
  - `POST /documents/upload` - Accept multipart/form-data PDF
  - Validate file type (PDF only)
  - Size limit: 50MB max
  - Return: `{"doc_id", "status", "message"}`
- [ ] Create `internal/handlers/health.go`:
  - `GET /health` - Return service health
  - `GET /ready` - Readiness probe (check S3 + Kafka connectivity)

#### 1.6 Main Application
- [ ] Create `cmd/main.go`:
  - Initialize config, logger, S3 client, Kafka producer
  - Set up Fiber app with middleware (logger, recover, CORS)
  - Register routes
  - Graceful shutdown (handle SIGINT/SIGTERM)

#### 1.7 Testing
- [ ] Unit tests:
  - `internal/handlers/upload_test.go` - Mock S3 and Kafka
  - `internal/storage/s3_test.go` - Test with localstack or minio
  - `internal/messaging/producer_test.go` - Mock Kafka
- [ ] Integration test: Full upload flow with docker-compose services

#### 1.8 Containerization
- [ ] Create `Dockerfile`:
  ```dockerfile
  # Multi-stage build
  FROM golang:1.21-alpine AS builder
  WORKDIR /app
  COPY go.mod go.sum ./
  RUN go mod download
  COPY . .
  RUN CGO_ENABLED=0 GOOS=linux go build -o ingestion-service cmd/main.go
  
  FROM alpine:latest
  RUN apk --no-cache add ca-certificates
  WORKDIR /root/
  COPY --from=builder /app/ingestion-service .
  EXPOSE 8080
  CMD ["./ingestion-service"]
  ```

#### 1.9 Kubernetes Manifests
- [ ] Create `kubernetes/base/ingestion-service/deployment.yaml`:
  - 3 replicas
  - Resource limits: 256Mi memory, 200m CPU
  - Readiness/liveness probes
  - Environment variables from ConfigMap/Secret
- [ ] Create `kubernetes/base/ingestion-service/service.yaml`:
  - ClusterIP service on port 8080
- [ ] Create `kubernetes/base/ingestion-service/configmap.yaml`:
  - Kafka brokers, S3 bucket names, service config

### Verification Checklist
- [ ] Service starts successfully with `go run cmd/main.go`
- [ ] Upload PDF: `curl -F "file=@test.pdf" http://localhost:8080/documents/upload`
- [ ] Response contains valid `doc_id`
- [ ] PDF appears in MinIO bucket: `mc ls local/pageindex-documents/`
- [ ] Kafka message published: `kafka-console-consumer --topic documents.ingested --from-beginning`
- [ ] Health endpoints return 200 OK
- [ ] Docker image builds: `docker build -t pageindex-ingestion .`
- [ ] Unit tests pass: `go test ./...`

---

## Phase 2: Parser Service (Python + PageIndex)

**Objective**: Consume ingestion events, process PDFs with PageIndex, generate tree structures.

**Duration**: 5-6 days

### Tasks

#### 2.1 Python Project Setup
- [ ] Create `services/parser-service/requirements.txt`:
  ```txt
  fastapi==0.109.0
  uvicorn[standard]==0.27.0
  pageindex==0.3.0  # Check latest version
  aiokafka==0.10.0
  boto3==1.34.0
  openai==1.12.0
  python-dotenv==1.0.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  pytest==7.4.0
  pytest-asyncio==0.23.0
  httpx==0.26.0
  ```
- [ ] Install: `pip install -r requirements.txt`

#### 2.2 Configuration
- [ ] Create `app/config.py`:
  - Use Pydantic BaseSettings
  - Load from environment: KAFKA_BROKERS, S3_BUCKET, GEMINI_API_KEY, etc.
  - Validate required fields

#### 2.3 S3 Storage Client
- [ ] Create `app/storage.py`:
  - `download_document(s3_uri: str) -> bytes` - Download PDF from S3
  - `upload_tree(doc_id: str, tree_json: dict) -> str` - Upload tree JSON to S3
  - Use boto3 async client (aioboto3)

#### 2.4 PageIndex Integration
- [ ] Create `app/pageindex_client.py`:
  - `async def generate_tree(pdf_path: str) -> dict` - Main function
  - Use PageIndex's `pdf_to_tree()` function:
    ```python
    from pageindex import pdf_to_tree
    import asyncio
    
    tree = asyncio.run(pdf_to_tree(
        pdf_path=pdf_path,
        if_add_node_summary='yes',
        if_add_doc_description='yes',
        if_add_node_id='yes',
        model='gpt-4o-2024-11-20'
    ))
    ```
  - Error handling for PageIndex failures
  - Logging with page count and processing time

#### 2.5 Kafka Consumer
- [ ] Create `app/consumer.py`:
  - `class DocumentConsumer` - aiokafka consumer
  - Subscribe to `documents.ingested` topic
  - Consumer group: `parser-service`
  - Message processing:
    1. Deserialize message
    2. Download PDF from S3
    3. Generate PageIndex tree
    4. Upload tree JSON to S3
    5. Publish to `documents.parsed` topic
    6. Commit offset
  - Error handling with retry logic (exponential backoff)
  - Dead letter queue for failed messages

#### 2.6 Kafka Producer
- [ ] Create `app/producer.py`:
  - `async def publish_parsed(doc_id, tree_s3_uri, page_count, processing_time)`
  - Publish to `documents.parsed` topic
  - Message schema: `{"doc_id", "tree_s3_uri", "status", "page_count", "processing_time_ms"}`

#### 2.7 FastAPI Application
- [ ] Create `app/main.py`:
  - FastAPI app with health endpoints
  - Background task to start Kafka consumer
  - `GET /health` - Service health
  - `GET /metrics` - Processing stats (documents processed, avg time, errors)
  - Graceful shutdown

#### 2.8 Testing
- [ ] Create `tests/test_pageindex_client.py`:
  - Mock OpenAI API calls
  - Test tree structure validation
- [ ] Create `tests/test_consumer.py`:
  - Mock Kafka consumer
  - Test message processing flow
- [ ] Integration test with sample PDFs

#### 2.9 Containerization
- [ ] Create `Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  
  # Install system dependencies for PyMuPDF (PageIndex dependency)
  RUN apt-get update && apt-get install -y \
      gcc \
      && rm -rf /var/lib/apt/lists/*
  
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  COPY app/ ./app/
  
  EXPOSE 8081
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
  ```

#### 2.10 Kubernetes Manifests
- [ ] Create `kubernetes/base/parser-service/deployment.yaml`:
  - 2 replicas (can scale based on Kafka lag)
  - Resource limits: 1Gi memory, 500m CPU (PageIndex is CPU-intensive)
  - Mount secret for GEMINI_API_KEY
  - Environment variables
- [ ] Create `kubernetes/base/parser-service/service.yaml`
- [ ] Create `kubernetes/base/parser-service/secret.yaml.example` (for OpenAI key)

### Verification Checklist
- [ ] Service starts: `python -m app.main`
- [ ] Consumer connects to Kafka successfully
- [ ] Upload PDF via ingestion service
- [ ] Parser logs show PDF processing
- [ ] Tree JSON appears in S3: `aws s3 ls s3://pageindex-trees/`
- [ ] Kafka message published to `documents.parsed`
- [ ] Tree structure validates (has node_id, title, start_index, summary fields)
- [ ] Health endpoint returns 200
- [ ] Handle malformed PDFs gracefully (error logging, no crash)

---

## Phase 3: Cache Manager Service (Python + Redis)

**Objective**: Implement hot/cold tree caching with Redis for low-latency retrieval.

**Duration**: 3-4 days

### Tasks

#### 3.1 Python Project Setup
- [ ] Create `services/cache-service/requirements.txt`:
  ```txt
  fastapi==0.109.0
  uvicorn[standard]==0.27.0
  redis[hiredis]==5.0.1
  aiokafka==0.10.0
  boto3==1.34.0
  pydantic==2.5.0
  pydantic-settings==2.1.0
  prometheus-client==0.19.0
  python-dotenv==1.0.0
  pytest==7.4.0
  httpx==0.26.0
  ```

#### 3.2 Configuration
- [ ] Create `app/config.py`:
  - Redis connection settings (host, port, password, DB)
  - Kafka settings
  - Cache TTL (default: 3600 seconds = 1 hour)
  - S3 bucket for trees

#### 3.3 Redis Cache Client
- [ ] Create `app/cache.py`:
  - `class TreeCache`:
    - `async def get(doc_id: str) -> dict | None` - Retrieve from cache
    - `async def set(doc_id: str, tree: dict, ttl: int = 3600)` - Store with TTL
    - `async def delete(doc_id: str)` - Invalidate cache
    - `async def exists(doc_id: str) -> bool` - Check if cached
  - Implement compression (zlib) for large trees
  - Key format: `tree:{doc_id}`
  - Track cache hits/misses for metrics

#### 3.4 Kafka Consumer (Auto-Warming)
- [ ] Create `app/consumer.py`:
  - Subscribe to `documents.parsed` topic
  - Consumer group: `cache-service`
  - On message received:
    1. Download tree from S3
    2. Store in Redis cache
    3. Log success
  - Background task in FastAPI app

#### 3.5 REST API
- [ ] Create `app/main.py` with FastAPI endpoints:
  - `GET /cache/tree/{doc_id}` - Get tree (cache-aside pattern):
    - Check Redis first
    - If miss, fetch from S3 and cache
    - Return tree JSON
  - `DELETE /cache/tree/{doc_id}` - Invalidate
  - `GET /cache/stats` - Cache statistics:
    - Total hits, misses, hit rate
    - Cached items count
    - Memory usage
  - `GET /health` - Health check
  - `GET /metrics` - Prometheus metrics

#### 3.6 Metrics Implementation
- [ ] Create `app/metrics.py`:
  - Prometheus metrics:
    - `cache_hits_total` (Counter)
    - `cache_misses_total` (Counter)
    - `cache_hit_rate` (Gauge)
    - `cache_operations_duration_seconds` (Histogram)
    - `cached_trees_count` (Gauge)
  - `/metrics` endpoint for Prometheus scraping

#### 3.7 Testing
- [ ] Create `tests/test_cache.py`:
  - Test cache get/set/delete operations
  - Test TTL expiration
  - Test compression
- [ ] Create `tests/test_api.py`:
  - Test all REST endpoints
  - Test cache-aside pattern

#### 3.8 Containerization
- [ ] Create `Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  
  COPY app/ ./app/
  
  EXPOSE 8082
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
  ```

#### 3.9 Kubernetes Manifests
- [ ] Create `kubernetes/base/cache-service/deployment.yaml`:
  - 2 replicas
  - Resource limits: 512Mi memory, 300m CPU
  - Environment variables for Redis connection
- [ ] Create `kubernetes/base/cache-service/service.yaml`
- [ ] Create `kubernetes/base/redis/statefulset.yaml` (for K8s Redis deployment)

### Verification Checklist
- [ ] Service starts successfully
- [ ] Kafka consumer connects and auto-warms cache
- [ ] `GET /cache/tree/{doc_id}` returns tree from Redis
- [ ] Cache miss triggers S3 fetch and caching
- [ ] `GET /cache/stats` shows accurate metrics
- [ ] Redis CLI shows cached data: `redis-cli GET tree:{doc_id}`
- [ ] TTL expires after configured time
- [ ] `/metrics` endpoint returns Prometheus format
- [ ] Compression reduces storage size significantly

---

## Phase 4: API Gateway (Go + WebSocket)

**Objective**: Build user-facing API with streaming query responses and tree-based retrieval.

**Duration**: 5-6 days

### Tasks

#### 4.1 Go Project Setup
- [ ] Initialize: `cd services/api-gateway && go mod init github.com/yourusername/pageindex/gateway`
- [ ] Install dependencies:
  ```bash
  go get github.com/gofiber/fiber/v2
  go get github.com/gofiber/websocket/v2
  go get github.com/go-resty/resty/v2  # HTTP client
  go get github.com/sashabaranov/go-openai
  go get github.com/google/uuid
  go get github.com/rs/zerolog/log
  go get go.opentelemetry.io/otel
  go get github.com/gofiber/contrib/otelfiber
  ```

#### 4.2 Configuration
- [ ] Create `internal/config/config.go`:
  - OpenAI API key
  - Cache service URL
  - Server port
  - CORS origins

#### 4.3 Cache Service Client
- [ ] Create `internal/clients/cache.go`:
  - `GetTree(ctx context.Context, docID string) (map[string]interface{}, error)`
  - HTTP client to cache-service
  - Retry logic with exponential backoff

#### 4.4 LLM Tree Search Logic
- [ ] Create `internal/llm/tree_search.go`:
  - `FindRelevantNodes(ctx, tree, query) ([]string, error)` - Returns node_ids
  - Prompt template:
    ```go
    prompt := fmt.Sprintf(`You are given a PageIndex document tree structure and a user query.
    Your task is to identify which nodes (by node_id) are most likely to contain information relevant to the query.
    
    Document Tree:
    %s
    
    User Query: %s
    
    Respond with ONLY a JSON object in this format:
    {
      "reasoning": "Brief explanation of why these nodes are relevant",
      "node_ids": ["0001", "0007", "0012"]
    }
    
    Do not include any other text.`, treeJSON, query)
    ```
  - Parse LLM response, extract node_ids
  - Handle malformed JSON responses

- [ ] Create `internal/llm/answer_generation.go`:
  - `GenerateAnswer(ctx, query, nodeContents) (string, error)` - Final answer
  - Prompt template:
    ```go
    prompt := fmt.Sprintf(`You are a financial analysis expert. Answer the user's question using ONLY the provided context from the document.
    
    Context:
    %s
    
    Question: %s
    
    Instructions:
    - Provide specific numbers and facts
    - Include page numbers or section references when citing
    - If the answer is not in the context, say "I cannot find this information in the document"
    - Be concise but complete
    
    Answer:`, nodeContents, query)
    ```

#### 4.5 REST API Handlers
- [ ] Create `internal/handlers/query.go`:
  - `POST /query` - Submit query
    - Request: `{"doc_id": "xxx", "question": "What is Q3 revenue?"}`
    - Response: `{"query_id": "uuid", "status": "processing"}`
    - Start async processing
  - `GET /query/{query_id}` - Get query status/result
    - Response: `{"status": "completed", "answer": "...", "references": [...]}`

- [ ] Create `internal/handlers/websocket.go`:
  - `GET /ws` - WebSocket endpoint for streaming
  - Upgrades HTTP connection to WebSocket
  - Streaming flow:
    1. Client sends: `{"doc_id": "xxx", "question": "..."}`
    2. Server streams: `{"type": "status", "message": "Fetching document tree..."}`
    3. Server streams: `{"type": "reasoning", "message": "Navigating to revenue section..."}`
    4. Server streams: `{"type": "progress", "nodes_found": 3}`
    5. Server streams: `{"type": "answer", "content": "Q3 revenue was...", "references": [...]}`
    6. Server closes connection

- [ ] Create `internal/handlers/documents.go`:
  - `GET /documents` - List processed documents (query cache-service)
  - `GET /documents/{doc_id}` - Get document metadata
  - `GET /documents/{doc_id}/tree` - Get tree structure

#### 4.6 WebSocket Implementation
- [ ] Implement WebSocket message handling:
  - Connection management (track active connections)
  - Message parsing and validation
  - Error handling (send error messages to client)
  - Graceful disconnect

#### 4.7 Query Processing Pipeline
- [ ] Create `internal/pipeline/query_processor.go`:
  - Orchestrate full query flow:
    1. Fetch tree from cache-service
    2. Call LLM for tree search (FindRelevantNodes)
    3. Extract node contents from tree
    4. Call LLM for answer generation
    5. Format response with citations
  - Stream progress updates via WebSocket
  - Handle errors at each step

#### 4.8 Middleware
- [ ] Create `internal/middleware/cors.go` - CORS configuration
- [ ] Create `internal/middleware/ratelimit.go` - Rate limiting (100 req/min per IP)
- [ ] Add OpenTelemetry instrumentation for tracing

#### 4.9 Main Application
- [ ] Create `cmd/main.go`:
  - Initialize config, logger, OpenAI client, HTTP clients
  - Set up Fiber with middleware
  - Register HTTP routes and WebSocket route
  - Graceful shutdown

#### 4.10 Testing
- [ ] Unit tests:
  - `internal/llm/tree_search_test.go` - Mock OpenAI responses
  - `internal/handlers/query_test.go` - Test REST endpoints
- [ ] Integration test with WebSocket client

#### 4.11 Containerization
- [ ] Create `Dockerfile` (multi-stage build)

#### 4.12 Kubernetes Manifests
- [ ] Create `kubernetes/base/api-gateway/deployment.yaml`:
  - 3 replicas initially
  - Resource limits: 512Mi memory, 300m CPU
  - Environment variables
- [ ] Create `kubernetes/base/api-gateway/service.yaml`:
  - Type: LoadBalancer (for external access)
  - Port 80 → 8083
- [ ] Create `kubernetes/base/api-gateway/hpa.yaml`:
  - Min: 2, Max: 10 replicas
  - Target CPU: 70%

### Verification Checklist
- [ ] Service starts successfully
- [ ] REST query: `curl -X POST http://localhost:8083/query -d '{"doc_id":"xxx","question":"What is revenue?"}'`
- [ ] WebSocket test with wscat: `wscat -c ws://localhost:8083/ws`
- [ ] Streaming response includes reasoning steps
- [ ] Final answer includes page citations
- [ ] Concurrent queries handled correctly (test with 10 simultaneous)
- [ ] Rate limiting works (test with >100 requests)
- [ ] OpenTelemetry traces visible

---

## Phase 5: AWS EKS Deployment

**Objective**: Deploy entire system to production-ready Kubernetes cluster with full observability.

**Duration**: 4-5 days

### Tasks

#### 5.1 AWS Infrastructure (Terraform)

##### 5.1.1 VPC Setup
- [ ] Create `infrastructure/terraform/vpc.tf`:
  - VPC with public and private subnets across 3 AZs
  - NAT Gateways for private subnets
  - Internet Gateway
  - Route tables

##### 5.1.2 EKS Cluster
- [ ] Create `infrastructure/terraform/eks.tf`:
  - EKS cluster version 1.28
  - Node groups:
    - On-demand: 2 t3.medium nodes (for critical services)
    - Spot: 0-5 t3.large nodes (for parser service)
  - IRSA (IAM Roles for Service Accounts) configuration
  - Security groups

##### 5.1.3 AWS MSK (Kafka)
- [ ] Create `infrastructure/terraform/msk.tf`:
  - MSK cluster (3 brokers across 3 AZs)
  - kafka.m5.large instances
  - Encrypted storage and in-transit
  - CloudWatch logging enabled

##### 5.1.4 ElastiCache (Redis)
- [ ] Create `infrastructure/terraform/elasticache.tf`:
  - Redis cluster mode disabled (single shard)
  - cache.r6g.large instance
  - Automatic failover enabled
  - Encryption at rest and in transit

##### 5.1.5 S3 Buckets
- [ ] Create `infrastructure/terraform/s3.tf`:
  - Bucket: `pageindex-documents-prod` (for PDFs)
  - Bucket: `pageindex-trees-prod` (for tree JSON)
  - Versioning enabled
  - Encryption: SSE-S3
  - Lifecycle policies (delete old documents after 90 days)

##### 5.1.6 IAM Roles
- [ ] Create `infrastructure/terraform/iam.tf`:
  - Service account roles with IRSA:
    - `ingestion-service-role` (S3 write, Kafka publish)
    - `parser-service-role` (S3 read/write, Kafka read/publish)
    - `cache-service-role` (S3 read, Kafka read)
    - `api-gateway-role` (minimal)
  - Policies with least privilege

##### 5.1.7 ECR Repositories
- [ ] Create `infrastructure/terraform/ecr.tf`:
  - Repositories for each service
  - Lifecycle policies (keep last 10 images)

##### 5.1.8 Terraform Execution
- [ ] Initialize: `terraform init`
- [ ] Plan: `terraform plan -out=tfplan`
- [ ] Apply: `terraform apply tfplan`
- [ ] Output important values (EKS endpoint, MSK brokers, Redis endpoint)

#### 5.2 Kubernetes Cluster Setup

##### 5.2.1 kubectl Configuration
- [ ] Configure kubectl: `aws eks update-kubeconfig --name pageindex-cluster`
- [ ] Verify: `kubectl get nodes`

##### 5.2.2 Install Kubernetes Addons
- [ ] AWS Load Balancer Controller:
  ```bash
  helm repo add eks https://aws.github.io/eks-charts
  helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    --namespace kube-system \
    --set clusterName=pageindex-cluster
  ```
- [ ] EBS CSI Driver (for persistent volumes)
- [ ] Metrics Server: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`
- [ ] Cluster Autoscaler

#### 5.3 Observability Stack

##### 5.3.1 Prometheus + Grafana
- [ ] Install kube-prometheus-stack:
  ```bash
  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace
  ```
- [ ] Configure ServiceMonitors for custom services
- [ ] Create custom Grafana dashboards:
  - System overview (CPU, memory, pods)
  - Service metrics (request rate, latency, errors)
  - Cache metrics (hit rate, memory usage)
  - Kafka metrics (lag, throughput)

##### 5.3.2 OpenTelemetry Collector
- [ ] Install OpenTelemetry Operator
- [ ] Deploy collector to receive traces from services
- [ ] Configure exporters (Jaeger, Prometheus)

##### 5.3.3 Jaeger (Distributed Tracing)
- [ ] Install Jaeger via Helm
- [ ] Configure ingress for Jaeger UI

##### 5.3.4 Logging (Optional)
- [ ] Install Loki for log aggregation
- [ ] Configure Promtail to ship logs
- [ ] Set up log dashboards in Grafana

#### 5.4 Deploy Application Services

##### 5.4.1 Create Kustomize Overlays
- [ ] Update `kubernetes/overlays/prod/kustomization.yaml`:
  - Set namespaces
  - Set image tags (from ECR)
  - Configure replicas for production
  - Add resource limits
  - Add HPA configurations

##### 5.4.2 Create Kubernetes Secrets
- [ ] Create secret for OpenAI API key:
  ```bash
  kubectl create secret generic gemini-api-key \
    --from-literal=GEMINI_API_KEY=... \
    --namespace default
  ```
- [ ] Create secret for AWS credentials (if not using IRSA)

##### 5.4.3 Deploy Services
- [ ] Apply base resources: `kubectl apply -k kubernetes/base/`
- [ ] Apply production overlay: `kubectl apply -k kubernetes/overlays/prod/`
- [ ] Verify all pods running: `kubectl get pods -A`

#### 5.5 Ingress Configuration

##### 5.5.1 Install NGINX Ingress Controller
- [ ] Install via Helm:
  ```bash
  helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
  helm install nginx-ingress ingress-nginx/ingress-nginx \
    --namespace ingress-nginx --create-namespace
  ```

##### 5.5.2 Configure Ingress
- [ ] Create `kubernetes/overlays/prod/ingress.yaml`:
  - Route `/query`, `/ws`, `/documents` to api-gateway
  - TLS termination
  - Rate limiting annotations

##### 5.5.3 DNS & TLS
- [ ] Point domain to LoadBalancer: `api.yourdomain.com`
- [ ] Install cert-manager for Let's Encrypt:
  ```bash
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
  ```
- [ ] Create ClusterIssuer for Let's Encrypt
- [ ] Certificate should auto-provision

#### 5.6 Horizontal Pod Autoscaling (HPA)

- [ ] Create HPA for API Gateway:
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: api-gateway-hpa
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: api-gateway
    minReplicas: 2
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
  ```
- [ ] Create HPA for Parser Service (based on Kafka lag)

#### 5.7 Monitoring & Alerts

##### 5.7.1 Prometheus Alerting Rules
- [ ] Create alert rules in `kubernetes/base/observability/prometheus/alerts.yaml`:
  - High error rate (>5%)
  - Pod crash loops
  - Kafka consumer lag (>1000 messages)
  - Redis memory usage (>80%)
  - API Gateway latency (p95 >5s)

##### 5.7.2 Alertmanager Configuration
- [ ] Configure notification channels (Slack, email, PagerDuty)
- [ ] Set alert routing rules

#### 5.8 ArgoCD GitOps

##### 5.8.1 Install ArgoCD
- [ ] Install: `kubectl create namespace argocd`
- [ ] Apply: `kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`
- [ ] Expose UI: Port-forward or Ingress

##### 5.8.2 Configure Applications
- [ ] Create ArgoCD Application manifests: `kubernetes/argocd/pageindex-app.yaml`
- [ ] Configure GitHub repo sync
- [ ] Enable auto-sync and self-heal
- [ ] Apply: `kubectl apply -f kubernetes/argocd/`

##### 5.8.3 Test GitOps Flow
- [ ] Make change to Kubernetes manifests
- [ ] Push to GitHub
- [ ] Verify ArgoCD auto-deploys changes

#### 5.9 Runbooks & Documentation

- [ ] Create runbooks in `docs/`:
  - `docs/runbooks/deployment.md` - Deployment procedures
  - `docs/runbooks/scaling.md` - Manual scaling procedures
  - `docs/runbooks/troubleshooting.md` - Common issues
  - `docs/runbooks/disaster-recovery.md` - Backup/restore procedures

### Verification Checklist
- [ ] All Terraform resources created successfully
- [ ] EKS cluster accessible via kubectl
- [ ] All application pods in Running state
- [ ] External LoadBalancer accessible
- [ ] DNS resolves to LoadBalancer IP
- [ ] TLS certificate issued and valid
- [ ] End-to-end test: Upload PDF → Query → Receive answer
- [ ] Prometheus scraping all services
- [ ] Grafana dashboards showing live data
- [ ] Jaeger showing distributed traces
- [ ] Alerts fire correctly (test by killing pod)
- [ ] HPA scales pods under load
- [ ] ArgoCD syncs on Git push
- [ ] Log into Grafana at `https://grafana.yourdomain.com`
- [ ] Public API accessible at `https://api.yourdomain.com`

---

## Phase 6: LLM Observability & Self-Healing

**Objective**: Implement LLM-as-a-Judge evaluation with automated quality monitoring.

**Duration**: 3-4 days

### Tasks

#### 6.1 Extend Kafka Topics
- [ ] Create new topic: `queries.completed`
- [ ] Update API Gateway to publish query logs:
  - Message: `{"query_id", "doc_id", "question", "answer", "tree_path", "latency_ms", "timestamp"}`

#### 6.2 PostgreSQL Setup
- [ ] Deploy PostgreSQL in Kubernetes or use AWS RDS
- [ ] Create database: `pageindex_eval`
- [ ] Create tables:
  - `queries` (query_id, doc_id, question, answer, tree_path, timestamp)
  - `evaluations` (eval_id, query_id, score, reasoning, judge_model, timestamp)

#### 6.3 Evaluation Service
- [ ] Create `services/evaluation-service/app/main.py`:
  - FastAPI app
  - Kafka consumer for `queries.completed`
- [ ] Create `app/storage.py`:
  - PostgreSQL client (SQLAlchemy or asyncpg)
  - `store_query()`, `store_evaluation()`, `get_queries()`
- [ ] Create `app/judge.py`:
  - LLM-as-a-Judge implementation:
    ```python
    async def judge_answer(question: str, answer: str, tree_context: dict) -> dict:
        prompt = f"""You are an expert evaluator for financial document QA systems.
        
        Question: {question}
        Answer: {answer}
        Available Context: {tree_context}
        
        Evaluate the answer on these criteria:
        1. Factual accuracy (0-3 points)
        2. Completeness (0-3 points)
        3. Citation quality (0-2 points)
        4. Relevance (0-2 points)
        
        Return JSON:
        {{
          "total_score": 0-10,
          "factual_accuracy": 0-3,
          "completeness": 0-3,
          "citation_quality": 0-2,
          "relevance": 0-2,
          "reasoning": "Detailed explanation",
          "hallucinations_detected": true/false
        }}
        """
        # Call OpenAI GPT-4o-mini (cheaper)
        response = await openai.ChatCompletion.acreate(...)
        return parse_json(response)
    ```
- [ ] Sampling strategy: Evaluate 10% of queries randomly

#### 6.4 Metrics & Dashboards
- [ ] Export evaluation metrics to Prometheus:
  - `llm_accuracy_score` (Gauge) - Average score
  - `llm_hallucination_rate` (Gauge) - % with hallucinations
  - `llm_queries_evaluated_total` (Counter)
- [ ] Create Grafana dashboard:
  - Line chart: Accuracy over time
  - Gauge: Current accuracy (target >85%)
  - Table: Recent low-scoring queries
  - Alert threshold visualizations

#### 6.5 Alerting
- [ ] Add Prometheus alert rules:
  ```yaml
  - alert: LowLLMAccuracy
    expr: llm_accuracy_score < 8.5
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "LLM accuracy dropped below 85%"
      description: "Current accuracy: {{ $value }}"
  
  - alert: HighHallucinationRate
    expr: llm_hallucination_rate > 0.05
    for: 30m
    labels:
      severity: critical
    annotations:
      summary: "Hallucination rate exceeds 5%"
  ```

#### 6.6 A/B Testing Framework (Optional)
- [ ] Implement prompt variant testing:
  - Store multiple prompt templates
  - Randomly assign queries to variants
  - Compare accuracy between variants
  - Statistical significance testing

#### 6.7 Automated Remediation (Optional)
- [ ] Trigger notifications on alerts:
  - Slack webhook with low-scoring query examples
  - Email to engineering team
- [ ] Automated actions:
  - Flag documents with low accuracy for review
  - Suggest prompt improvements based on patterns

#### 6.8 Testing & Deployment
- [ ] Create test suite with known good/bad answers
- [ ] Verify judge scores align with expectations
- [ ] Deploy to Kubernetes

### Verification Checklist
- [ ] Evaluation service consumes `queries.completed` topic
- [ ] Queries stored in PostgreSQL
- [ ] LLM judge evaluates sample queries
- [ ] Scores stored in database
- [ ] Grafana dashboard shows accuracy metrics
- [ ] Alerts fire when accuracy drops (test with bad answers)
- [ ] Review alert notifications in Slack/email

---

## Data Flow Summary

### Document Ingestion Flow
```
User Upload PDF
    ↓
Ingestion Service (Go)
    ↓ (Store PDF)
AWS S3 (documents bucket)
    ↓ (Publish event)
Kafka Topic: documents.ingested
    ↓ (Consume)
Parser Service (Python + PageIndex)
    ↓ (Process with LLM)
PageIndex Tree Generation
    ↓ (Store tree)
AWS S3 (trees bucket)
    ↓ (Publish event)
Kafka Topic: documents.parsed
    ↓ (Consume)
Cache Service (Python + Redis)
    ↓ (Cache tree)
Redis (in-memory cache)
```

### Query Flow
```
User Query
    ↓
API Gateway (Go)
    ↓ (Fetch tree)
Cache Service → Redis (cache hit) OR S3 (cache miss)
    ↓ (Tree structure)
API Gateway
    ↓ (Tree search prompt)
OpenAI GPT-4.1
    ↓ (Relevant node_ids)
API Gateway (extract node contents)
    ↓ (Answer generation prompt)
OpenAI GPT-4.1
    ↓ (Final answer)
API Gateway (stream via WebSocket)
    ↓
User receives answer with citations
    ↓ (Log query)
Kafka Topic: queries.completed
    ↓ (Optional: evaluation)
Evaluation Service → LLM Judge → PostgreSQL
```

---

## Kafka Topics Schema

### documents.ingested
```json
{
  "doc_id": "uuid-v4",
  "s3_uri": "s3://pageindex-documents-prod/uuid.pdf",
  "filename": "nvidia-2025-q3-10k.pdf",
  "timestamp": "2026-02-28T10:00:00Z",
  "metadata": {
    "company": "NVIDIA",
    "period": "Q3-2025",
    "document_type": "10-K"
  }
}
```

### documents.parsed
```json
{
  "doc_id": "uuid-v4",
  "tree_s3_uri": "s3://pageindex-trees-prod/uuid.json",
  "status": "completed",
  "page_count": 48,
  "processing_time_ms": 45000,
  "timestamp": "2026-02-28T10:01:30Z"
}
```

### queries.completed (Phase 6)
```json
{
  "query_id": "uuid-v4",
  "doc_id": "uuid-v4",
  "question": "What was Q3 2025 revenue?",
  "answer": "Q3 2025 revenue was $57.0 billion, up 62.5% YoY (page 3).",
  "tree_path": ["0001", "0003", "0007"],
  "latency_ms": 2500,
  "timestamp": "2026-02-28T10:05:00Z"
}
```

---

## Tree Search Algorithm (Detailed)

The core innovation is LLM-driven tree navigation instead of vector similarity search:

### Step 1: Fetch Document Tree
```python
tree = cache_service.get_tree(doc_id)
# Tree structure:
{
  "title": "NVIDIA Q3 2025 10-K",
  "node_id": "0001",
  "structure": [
    {
      "title": "Financial Statements",
      "node_id": "0002",
      "start_index": 3,
      "end_index": 15,
      "summary": "Consolidated financial statements including income statement, balance sheet...",
      "nodes": [
        {
          "title": "Condensed Consolidated Statements of Income",
          "node_id": "0003",
          "start_index": 3,
          "end_index": 5,
          "summary": "Revenue and operating results for Q3 2025..."
        }
      ]
    }
  ]
}
```

### Step 2: LLM Tree Search
```python
prompt = f"""Given this document tree structure, identify which nodes (by node_id) 
contain information relevant to answering this query.

Document Tree:
{json.dumps(tree, indent=2)}

Query: {user_question}

Return JSON only:
{{
  "reasoning": "Brief explanation",
  "node_ids": ["0001", "0003"]
}}
"""

response = openai.ChatCompletion.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)
node_ids = parse_json(response)["node_ids"]
```

### Step 3: Extract Node Contents
```python
relevant_content = []
for node_id in node_ids:
    node = find_node_by_id(tree, node_id)
    content = {
        "title": node["title"],
        "pages": f"{node['start_index']}-{node['end_index']}",
        "summary": node["summary"],
        "text": node.get("text", "")  # Full text if available
    }
    relevant_content.append(content)
```

### Step 4: Generate Answer
```python
context = "\n\n".join([
    f"Section: {c['title']} (Pages {c['pages']})\n{c['summary']}\n{c['text']}"
    for c in relevant_content
])

prompt = f"""Answer the question using ONLY the provided context.

Context:
{context}

Question: {user_question}

Instructions:
- Provide specific numbers and facts
- Include page references
- If not in context, say "Information not found"

Answer:"""

answer = openai.ChatCompletion.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": prompt}],
    temperature=0
)
```

### Key Advantages Over Vector RAG
1. **Reasoning-based**: LLM understands document structure, not just semantic similarity
2. **Explainable**: Clear tree path shows navigation logic
3. **Accurate**: No chunk boundary problems or context loss
4. **Traceable**: Citations include exact page ranges
5. **No vector DB**: Simpler architecture, lower cost

---

## Success Metrics

### Technical Metrics
- ✅ **Performance**: Process 100-page PDF in <60 seconds
- ✅ **Latency**: Query response time <3s (p95)
- ✅ **Availability**: System uptime >99.5%
- ✅ **Durability**: Zero data loss (Kafka persistence + S3)
- ✅ **Cache Efficiency**: Hit rate >80%
- ✅ **Scalability**: Handle 50 concurrent queries

### Business Metrics (Portfolio Value)
- ✅ **Working Demo**: Live system on custom domain
- ✅ **Code Quality**: Comprehensive README, documented code
- ✅ **Architecture**: Clear diagrams and design docs
- ✅ **Observability**: Grafana dashboards showing system health
- ✅ **Modern Stack**: Demonstrates Kubernetes, Go, Python, Kafka, LLMOps, Cloud

### LLM Quality Metrics (Phase 6)
- ✅ **Accuracy**: Average score >8.5/10
- ✅ **Hallucination Rate**: <5%
- ✅ **Citation Quality**: >90% of answers include page references

---

## Cost Estimation

### AWS Monthly Costs (Development)
- **EKS Cluster**: ~$70 (2 t3.medium nodes)
- **AWS MSK**: ~$150 (1 broker, t3.small)
- **ElastiCache**: ~$15 (cache.t3.micro)
- **S3 Storage**: ~$5 (100GB)
- **Data Transfer**: ~$10
- **OpenAI API**: ~$100 (development testing)
- **Total**: ~$350/month

### AWS Monthly Costs (Production)
- **EKS Cluster**: ~$280 (4 m5.large nodes)
- **AWS MSK**: ~$450 (3 brokers, kafka.m5.large)
- **ElastiCache**: ~$120 (cache.r6g.large with failover)
- **S3 Storage**: ~$20 (500GB with versioning)
- **Data Transfer**: ~$50
- **RDS PostgreSQL**: ~$30 (db.t3.micro for eval service)
- **OpenAI API**: ~$600 (1M tokens/day)
- **Total**: ~$1,550/month

### Cost Optimization Strategies
1. **Spot Instances**: Use for parser service (50-70% savings)
2. **Auto-scaling**: Scale down during off-hours (nights/weekends)
3. **Reserved Capacity**: 1-year EKS savings plan (30% savings)
4. **Cheaper LLM Models**: Use GPT-4.1-mini for tree search (10x cheaper)
5. **Caching**: Aggressive Redis caching reduces OpenAI calls
6. **Document Quotas**: Limit processing to prevent runaway costs

---

## Timeline Estimate

| Phase | Focus | Duration |
|-------|-------|----------|
| **Phase 0** | Project initialization, Docker Compose, CI/CD | 2-3 days |
| **Phase 1** | Ingestion service (Go) | 3-4 days |
| **Phase 2** | Parser service (Python + PageIndex) | 5-6 days |
| **Phase 3** | Cache service (Python + Redis) | 3-4 days |
| **Phase 4** | API Gateway (Go + WebSocket) | 5-6 days |
| **Phase 5** | AWS EKS deployment + observability | 4-5 days |
| **Phase 6** | LLM observability (optional) | 3-4 days |

**Total for MVP (Phases 0-5)**: 3-4 weeks full-time  
**Total with Phase 6**: 4-5 weeks full-time

**Recommended Approach**: Complete Phases 0-5 first for working demo, then add Phase 6 for portfolio differentiation.

---

## Security Best Practices

### 1. Secret Management
- **Never commit**: `.env` files, API keys, passwords
- **Use AWS Secrets Manager** or Kubernetes Secrets (sealed with SealedSecrets)
- **Rotate credentials** regularly (quarterly)

### 2. Network Security
- **Private subnets**: All services except API Gateway
- **Security groups**: Restrict to necessary ports only
- **mTLS**: Between services (Phase 2 - Istio service mesh)

### 3. API Security
- **Rate limiting**: 100 requests/min per IP
- **Authentication**: JWT tokens (Phase 2)
- **Input validation**: Validate PDF files (magic bytes, size limits)
- **CORS**: Whitelist allowed origins only

### 4. Data Security
- **Encryption at rest**: S3 (SSE-S3), Redis (TLS), RDS (encryption)
- **Encryption in transit**: TLS 1.3 for all services
- **Data retention**: Delete documents after 90 days (GDPR compliance)

### 5. Audit & Compliance
- **Logging**: All API requests, errors, security events
- **Monitoring**: Alert on suspicious activity (high error rates, failed auth)
- **Compliance**: No PII in logs, data residency (single region)

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **PageIndex API breaking changes** | Medium | High | Pin versions, monitor GitHub releases, maintain fork |
| **OpenAI API costs exceed budget** | High | Medium | Rate limiting, caching, quotas, use cheaper models |
| **Kafka operational complexity** | Medium | Medium | Use managed AWS MSK, comprehensive monitoring |
| **EKS cost overruns** | Medium | High | Auto-scaling, spot instances, budget alerts |
| **Tree search accuracy issues** | Medium | High | Extensive testing with sample queries, LLM judge (Phase 6) |
| **WebSocket connection instability** | Low | Medium | Auto-reconnect in client, fallback to polling |
| **Redis memory exhaustion** | Medium | Medium | TTL policies, LRU eviction, monitoring alerts |
| **S3 data loss** | Low | High | Versioning enabled, cross-region replication (Phase 2) |

---

## Post-MVP Enhancements (Phase 2 Backlog)

### Infrastructure
1. **Multi-region deployment**: Active-active for lower latency globally
2. **Disaster recovery**: Automated backup/restore procedures
3. **Service mesh**: Istio for mTLS, advanced traffic routing
4. **Multi-cloud**: GCP/Azure for vendor diversity

### Features
1. **Multi-document queries**: Search across multiple 10-Ks simultaneously
2. **Vision-based RAG**: Use PageIndex vision mode for chart extraction
3. **Comparative analysis**: "Compare Q3 2024 vs Q3 2025 revenue"
4. **Document versioning**: Track changes in updated reports
5. **Export results**: PDF/Excel reports from query results

### Performance
1. **Rust cache service**: Replace Python cache for 10x performance
2. **GPU acceleration**: For PageIndex OCR processing
3. **Query caching**: Cache common questions
4. **CDN**: CloudFront for static assets

### Business
1. **Frontend dashboard**: React/Next.js UI for document management
2. **User authentication**: OAuth2, SSO integration
3. **API marketplace**: Expose as SaaS with usage-based pricing
4. **Compliance certifications**: SOC2, HIPAA for enterprise
5. **Fine-tuned models**: Custom financial domain models

---

## References & Resources

### PageIndex
- **GitHub**: https://github.com/VectifyAI/PageIndex
- **Documentation**: https://docs.pageindex.ai/
- **API Docs**: https://docs.pageindex.ai/quickstart
- **Blog**: https://pageindex.ai/blog/pageindex-intro

### Technology Documentation
- **Fiber (Go)**: https://docs.gofiber.io/
- **FastAPI (Python)**: https://fastapi.tiangolo.com/
- **Kafka**: https://kafka.apache.org/documentation/
- **Redis**: https://redis.io/docs/
- **Kubernetes**: https://kubernetes.io/docs/
- **AWS EKS**: https://docs.aws.amazon.com/eks/
- **Terraform**: https://developer.hashicorp.com/terraform/docs
- **ArgoCD**: https://argo-cd.readthedocs.io/

### Sample Financial Documents
- **SEC EDGAR**: https://www.sec.gov/edgar/searchedgar/companysearch.html
- **NVIDIA 10-K**: Search on EDGAR
- **Apple Earnings**: https://investor.apple.com/

---

## Getting Started Checklist

Before beginning implementation:

- [ ] AWS account created with billing alerts set
- [ ] Domain name registered (optional but recommended)
- [ ] OpenAI API key obtained (with sufficient credits)
- [ ] GitHub repository created (public for portfolio)
- [ ] Local development environment:
  - [ ] Go 1.21+ installed
  - [ ] Python 3.11+ installed
  - [ ] Docker Desktop installed
  - [ ] kubectl installed
  - [ ] AWS CLI configured
  - [ ] Terraform installed (for Phase 5)
- [ ] Review PageIndex documentation and examples
- [ ] Clone sample financial PDFs for testing

**Ready to Start**: Phase 0 - Project Initialization

---

## Support & Community

- **Questions**: Open GitHub issues
- **Discussions**: GitHub Discussions tab
- **PageIndex Discord**: https://discord.com/invite/VuXuf29EUj
- **Updates**: Follow @PageIndexAI on Twitter

---

*This implementation plan provides a complete roadmap from zero to production deployment. Follow phases sequentially for best results. Good luck building!*

---

## Learned User Preferences

- Prefer executing fixes in-repo (run commands, restart services, reproduce issues) instead of only instructing the user what to run.
- Do not stop after a single failed command; retry with alternative approaches and diagnose before concluding.
- When maintaining LLM wiring in this project, prefer the Claude path and avoid Gemini/OpenAI-compat environment indirection in parser or gateway unless explicitly required.
- Use evidence-first debugging (narrow hypotheses, minimal temporary logging, reproduce, then remove instrumentation once confirmed).

## Learned Workspace Facts

- The repository includes a Next.js frontend under `web/`; document listing and uploads are exercised through the API gateway and cache service, not by calling every backend port from the browser.
- Local Docker Compose creates MinIO buckets such as `pageindex-documents-dev` and `pageindex-trees-dev`; S3 bucket environment variables must match those names or uploads and tree writes fail with `NoSuchBucket`.
- The API gateway must load the repo-root `.env` reliably (try multiple paths, use override semantics if needed); an empty `CLAUDE_API_KEY` can produce mock LLM behavior instead of real answers.
- The parser may use fallback tree generation when native PageIndex `pdf_to_tree` is unavailable; downstream answers depend on how rich the stored tree is (summaries and any text fields the gateway includes in context).
- Observability accuracy metrics come from `evaluation-service`, PostgreSQL, and Kafka `queries.completed`; averages stay at zero when the DB is misconfigured, init fails, or sampling selects no queries—use `postgresql+asyncpg://...` with credentials matching the live Postgres container/volume, and remember default sampling is fractional (~10%).
- Cache hit rate stays at zero until `documents.parsed` is consumed and subsequent tree reads hit Redis; direct browser calls to the cache-service origin can fail for CORS even when curl shows 200—proxy stats APIs through the gateway when the UI needs them.
- Some paths or file splits described in earlier phases (e.g. standalone `internal/handlers/health.go`) may not exist in the current tree; confirm under `services/*` before editing.
