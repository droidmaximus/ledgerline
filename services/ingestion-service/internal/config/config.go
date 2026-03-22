package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

type Config struct {
	// Server
	Port int

	// AWS S3
	AWSRegion          string
	AWSAccessKeyID     string
	AWSSecretAccessKey string
	S3BucketDocuments  string
	S3EndpointURL      string

	// Kafka
	KafkaBrokers       []string
	KafkaTopicIngested string

	// File Upload
	MaxUploadSizeMB int
	MaxFileSize     int64 // MaxFileSize in bytes

	// Logging
	LogLevel string
}

func Load() (*Config, error) {
	maxUploadSizeMB := getEnvInt("MAX_UPLOAD_SIZE_MB", 50)

	cfg := &Config{
		Port:               getEnvInt("INGESTION_SERVICE_PORT", 8080),
		AWSRegion:          getEnv("AWS_REGION", "us-east-1"),
		AWSAccessKeyID:     getEnv("AWS_ACCESS_KEY_ID", "minioadmin"),
		AWSSecretAccessKey: getEnv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
		S3BucketDocuments:  getEnv("S3_BUCKET_DOCUMENTS", "pageindex-documents-dev"),
		S3EndpointURL:      getEnv("S3_ENDPOINT_URL", "http://localhost:9000"),
		MaxUploadSizeMB:    maxUploadSizeMB,
		MaxFileSize:        int64(maxUploadSizeMB) * 1024 * 1024, // Convert MB to bytes
		LogLevel:           getEnv("LOG_LEVEL", "info"),
	}

	// Parse Kafka brokers
	brokerStr := getEnv("KAFKA_BROKERS", "localhost:9092")
	cfg.KafkaBrokers = strings.Split(brokerStr, ",")
	for i := range cfg.KafkaBrokers {
		cfg.KafkaBrokers[i] = strings.TrimSpace(cfg.KafkaBrokers[i])
	}

	cfg.KafkaTopicIngested = getEnv("KAFKA_TOPIC_INGESTED", "documents.ingested")

	// Validate required configuration
	if cfg.S3BucketDocuments == "" {
		return nil, fmt.Errorf("S3_BUCKET_DOCUMENTS is required")
	}

	if len(cfg.KafkaBrokers) == 0 {
		return nil, fmt.Errorf("KAFKA_BROKERS is required")
	}

	return cfg, nil
}

func getEnv(key, defaultValue string) string {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	return value
}

func getEnvInt(key string, defaultValue int) int {
	value := os.Getenv(key)
	if value == "" {
		return defaultValue
	}
	intValue, err := strconv.Atoi(value)
	if err != nil {
		return defaultValue
	}
	return intValue
}
