#!/bin/bash

# Initialize Kafka topics
# Run after Kafka container is healthy

set -e

KAFKA_CONTAINER="pageindex-kafka-1"
BROKER="localhost:9092"

echo "Initializing Kafka topics..."

# Function to create topic
create_topic() {
    local topic=$1
    local partitions=${2:-3}
    local replication=${3:-1}
    
    echo "Creating topic: $topic"
    docker exec $KAFKA_CONTAINER kafka-topics.sh \
        --bootstrap-server $BROKER \
        --create \
        --topic $topic \
        --partitions $partitions \
        --replication-factor $replication \
        --if-not-exists 2>/dev/null || echo "Topic $topic already exists or error"
}

# Create topics
create_topic "documents.ingested" 3 1
create_topic "documents.parsed" 3 1
create_topic "queries.completed" 3 1

echo "Listing all topics..."
docker exec $KAFKA_CONTAINER kafka-topics.sh \
    --bootstrap-server $BROKER \
    --list

echo "✓ Topics initialized"
