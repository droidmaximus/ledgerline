.PHONY: help up down logs clean test build build-all push health-check redis-cli kafka-topics kafka-consumer kafka-producer minio-cli setup init-kafka seed-data run-ingestion run-parser run-cache run-gateway install-dependencies deploy-dev deploy-prod

# Default target
help:
	@echo "PageIndex Financial Intelligence Engine"
	@echo "=========================================="
	@echo ""
	@echo "Local Development:"
	@echo "  make up              - Start all containers"
	@echo "  make down            - Stop containers (keep volumes)"
	@echo "  make clean           - Remove everything (reset state)"
	@echo "  make logs            - View logs from all services"
	@echo "  make health-check    - Check all services health"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run service unit tests (Go + Python)"
	@echo ""
	@echo "Building:"
	@echo "  make build-all       - Build all Docker images"
	@echo "  make build-ingestion - Build ingestion service"
	@echo "  make build-parser    - Build parser service"
	@echo "  make build-cache     - Build cache service"
	@echo "  make build-gateway   - Build api gateway"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make setup           - Initialize project (first time)"
	@echo "  make init-kafka      - Create Kafka topics"
	@echo "  make seed-data       - Seed sample documents"
	@echo "  make redis-cli       - Connect to Redis CLI"
	@echo "  make kafka-topics    - List Kafka topics"
	@echo "  make kafka-consumer  - Consume Kafka messages"
	@echo "  make minio-cli       - Connect to MinIO CLI"
	@echo ""
	@echo "Cloud Deployment:"
	@echo "  make deploy-dev      - Deploy to development EKS cluster"
	@echo "  make deploy-prod     - Deploy to production EKS cluster"
	@echo ""

# ============================================================================
# LOCAL DEVELOPMENT
# ============================================================================

up:
	@echo "Starting services..."
	docker-compose -f docker/docker-compose.yml up -d
	@echo "Waiting for services to be healthy (30 seconds)..."
	@sleep 30
	@echo "✓ Services started"
	@echo "Kafka: http://localhost:8090"
	@echo "MinIO: http://localhost:9000"
	@echo "Redis: localhost:6379"

down:
	@echo "Stopping services..."
	docker-compose -f docker/docker-compose.yml down

clean:
	@echo "Removing all containers and volumes..."
	docker-compose -f docker/docker-compose.yml down -v
	@echo "✓ All cleaned"

logs:
	docker-compose -f docker/docker-compose.yml logs -f
	@sleep 5
	@echo "Infrastructure ready!"
	@echo "  - Kafka: localhost:9092"
	@echo "  - Kafka UI: http://localhost:8090"
	@echo "  - Redis: localhost:6379"
	@echo "  - MinIO: http://localhost:9000 (admin/minioadmin)"
	@echo "  - MinIO Console: http://localhost:9001"
	@echo "  - PostgreSQL: localhost:5432"

down: ## Stop all services
	@echo "Stopping all services..."
	docker-compose -f docker/docker-compose.yml down

clean: ## Stop services and remove volumes (WARNING: deletes all data)
	@echo "Stopping services and removing volumes..."
	docker-compose -f docker/docker-compose.yml down -v
	@echo "All data removed!"

restart: down up ## Restart all services

logs: ## Show logs from all services
	docker-compose -f docker/docker-compose.yml logs -f

status: ## Show status of all services
	@docker-compose -f docker/docker-compose.yml ps

# ==========================================
# Service Management (Local Development)
# ==========================================
run-ingestion: ## Run ingestion service locally
	@echo "Starting Ingestion Service on port 8080..."
	cd services/ingestion-service && go run cmd/main.go

run-parser: ## Run parser service locally
	@echo "Starting Parser Service on port 8081..."
	cd services/parser-service && python -m app.main

run-cache: ## Run cache service locally
	@echo "Starting Cache Service on port 8082..."
	cd services/cache-service && python -m app.main

run-gateway: ## Run API gateway locally
	@echo "Starting API Gateway on port 8083..."
	cd services/api-gateway && go run cmd/main.go

run-evaluation: ## Run evaluation service locally
	@echo "Starting Evaluation Service on port 8084..."
	cd services/evaluation-service && python -m app.main

# ==========================================
# Testing
# ==========================================
test: ## Run all tests
	@echo "Running Go tests..."
	@cd services/ingestion-service && go test ./... -v || true
	@cd services/api-gateway && go test ./... -v || true
	@echo "Running Python tests..."
	@cd services/parser-service && pytest tests/ -v || true
	@cd services/cache-service && pytest tests/ -v || true

# ==========================================
# Build
# ==========================================
build-all: build-ingestion build-parser build-cache build-gateway ## Build all Docker images

build-ingestion: ## Build ingestion service Docker image
	@echo "Building ingestion service..."
	docker build -t pageindex-ingestion:latest services/ingestion-service

build-parser: ## Build parser service Docker image
	@echo "Building parser service..."
	docker build -t pageindex-parser:latest services/parser-service

build-cache: ## Build cache service Docker image
	@echo "Building cache service..."
	docker build -t pageindex-cache:latest services/cache-service

build-gateway: ## Build API gateway Docker image
	@echo "Building API gateway..."
	docker build -t pageindex-gateway:latest services/api-gateway

build-evaluation: ## Build evaluation service Docker image
	@echo "Building evaluation service..."
	docker build -t pageindex-evaluation:latest services/evaluation-service

# ==========================================
# Dependencies
# ==========================================
deps-go: ## Install Go dependencies
	@echo "Installing Go dependencies..."
	@cd services/ingestion-service && go mod download
	@cd services/api-gateway && go mod download

deps-python: ## Install Python dependencies
	@echo "Installing Python dependencies..."
	@cd services/parser-service && pip install -r requirements.txt
	@cd services/cache-service && pip install -r requirements.txt
	@cd services/evaluation-service && pip install -r requirements.txt

# ==========================================
# Linting & Formatting
# ==========================================
lint-go: ## Lint Go code
	@echo "Linting Go code..."
	@cd services/ingestion-service && golangci-lint run ./... || true
	@cd services/api-gateway && golangci-lint run ./... || true

lint-python: ## Lint Python code
	@echo "Linting Python code..."
	@cd services/parser-service && ruff check . || true
	@cd services/cache-service && ruff check . || true

format-go: ## Format Go code
	@echo "Formatting Go code..."
	@cd services/ingestion-service && go fmt ./...
	@cd services/api-gateway && go fmt ./...

format-python: ## Format Python code
	@echo "Formatting Python code..."
	@cd services/parser-service && black app/ tests/
	@cd services/cache-service && black app/ tests/

# ==========================================
# Kubernetes (requires kubectl configured)
# ==========================================
k8s-deploy-dev: ## Deploy to Kubernetes (dev overlay)
	@echo "Deploying to Kubernetes (dev)..."
	kubectl apply -k kubernetes/overlays/dev

k8s-deploy-prod: ## Deploy to Kubernetes (prod overlay)
	@echo "Deploying to Kubernetes (prod)..."
	kubectl apply -k kubernetes/overlays/prod

k8s-status: ## Show Kubernetes status
	@echo "Kubernetes Status:"
	kubectl get pods -A

k8s-logs-ingestion: ## Show ingestion service logs
	kubectl logs -f deployment/ingestion-service

k8s-logs-parser: ## Show parser service logs
	kubectl logs -f deployment/parser-service

k8s-logs-cache: ## Show cache service logs
	kubectl logs -f deployment/cache-service

k8s-logs-gateway: ## Show API gateway logs
	kubectl logs -f deployment/api-gateway

# ==========================================
# Database Management
# ==========================================
db-migrate: ## Run database migrations (Phase 6)
	@echo "Running database migrations..."
	@cd services/evaluation-service && alembic upgrade head

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "Resetting database..."
	docker-compose -f docker/docker-compose.yml exec postgres psql -U pageindex -d pageindex_eval -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# ==========================================
# Utilities
# ==========================================
kafka-topics: ## List Kafka topics
	@docker exec pageindex-kafka kafka-topics --bootstrap-server localhost:9092 --list

kafka-consume-ingested: ## Consume from documents.ingested topic
	@docker exec -it pageindex-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic documents.ingested --from-beginning

kafka-consume-parsed: ## Consume from documents.parsed topic
	@docker exec -it pageindex-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic documents.parsed --from-beginning

redis-cli: ## Open Redis CLI
	@docker exec -it pageindex-redis redis-cli

minio-cli: ## Open MinIO CLI
	@docker exec -it pageindex-minio-init /bin/sh

# ==========================================
# Monitoring
# ==========================================
metrics: ## Show service metrics (requires services running)
	@echo "Fetching metrics..."
	@curl -s http://localhost:8082/cache/stats | jq .

health-check: ## Check health of all services
	@echo "Checking service health..."
	@echo "Ingestion Service:" && curl -s http://localhost:8080/health || echo "NOT RUNNING"
	@echo "Parser Service:" && curl -s http://localhost:8081/health || echo "NOT RUNNING"
	@echo "Cache Service:" && curl -s http://localhost:8082/health || echo "NOT RUNNING"
	@echo "API Gateway:" && curl -s http://localhost:8083/health || echo "NOT RUNNING"

# ==========================================
# Default target
# ==========================================
.DEFAULT_GOAL := help
