#!/bin/bash

# PageIndex Setup Script
# Run this after cloning to set up your local development environment

set -e

echo "=========================================="
echo "PageIndex Setup Script"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "✓ Docker found"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✓ Docker Compose found"

if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git."
    exit 1
fi
echo "✓ Git found"

echo ""
echo "=========================================="
echo "Environment Configuration"
echo "=========================================="
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✓ Created .env (edit with your API keys)"
    else
        echo "⚠ .env.example not found, creating basic .env"
        cat > .env << 'EOF'
# AWS Configuration (leave empty for local development with MinIO)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_BUCKET_DOCUMENTS=pageindex-documents
S3_BUCKET_TREES=pageindex-trees
S3_ENDPOINT_URL=http://minio:9000

# Kafka Configuration
KAFKA_BROKERS=kafka:9092
KAFKA_TOPIC_INGESTED=documents.ingested
KAFKA_TOPIC_PARSED=documents.parsed
KAFKA_TOPIC_QUERIES=queries.completed

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# OpenAI API (REQUIRED - add your key!)
OPENAI_API_KEY=sk-your-key-here
CHATGPT_API_KEY=sk-your-key-here

# Service Ports
INGESTION_SERVICE_PORT=8080
PARSER_SERVICE_PORT=8081
CACHE_SERVICE_PORT=8082
API_GATEWAY_PORT=8083

# Logger level
LOG_LEVEL=info
EOF
    fi
    
    echo "⚠️  IMPORTANT: Edit .env and add your OpenAI API key:"
    echo "    OPENAI_API_KEY=sk-..."
    echo ""
else
    echo "✓ .env file exists"
fi

echo ""
echo "=========================================="
echo "Network Setup"
echo "=========================================="
echo ""

# Create Docker network
if ! docker network inspect pageindex-network &>/dev/null; then
    echo "Creating Docker network..."
    docker network create pageindex-network
    echo "✓ Created pageindex-network"
else
    echo "✓ pageindex-network exists"
fi

echo ""
echo "=========================================="
echo "Installing Dependencies"
echo "=========================================="
echo ""

echo ""
echo "=========================================="
echo "Pulling Docker Images"
echo "=========================================="
echo ""

echo "Pulling Docker images (this may take a minute)..."
docker-compose -f docker/docker-compose.yml pull --quiet 2>/dev/null && echo "✓ Images pulled successfully"

echo ""
echo "=========================================="
echo "Setup Complete! 🎉"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env and add your OpenAI API key:"
echo "   nano .env"
echo ""
echo "2. Start services:"
echo "   make up"
echo ""
echo "3. Wait for services to be healthy (30-60 seconds):"
echo "   make health-check"
echo ""
echo "4. Read the user guide:"
echo "   cat README.md"
echo ""
echo "5. Run tests:"
echo "   make test"
echo ""
