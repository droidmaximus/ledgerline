package config

import (
	"os"
	"strconv"

	"github.com/pageindex/gateway/internal/messaging"
)

type Config struct {
	Port                   int
	CacheServiceURL        string
	IngestionServiceURL    string
	EvaluationServiceURL   string
	ClaudeAPIKey           string
	ClaudeModel            string
	AWSRegion              string
	KafkaBrokers           string
	KafkaTopicQueriesDone  string
	QueriesPublisher       *messaging.QueriesCompletedPublisher
}

func Load() (*Config, error) {
	cfg := &Config{
		Port:                  getEnvInt("API_GATEWAY_PORT", 8083),
		CacheServiceURL:       getEnv("CACHE_SERVICE_URL", "http://localhost:8082"),
		IngestionServiceURL:   getEnv("INGESTION_SERVICE_URL", "http://localhost:8080"),
		EvaluationServiceURL:  getEnv("EVALUATION_SERVICE_URL", "http://localhost:8084"),
		ClaudeAPIKey:          getEnv("CLAUDE_API_KEY", ""),
		ClaudeModel:           getEnv("CLAUDE_MODEL", "claude-haiku-4-5-20251001"),
		AWSRegion:             getEnv("AWS_REGION", "us-east-1"),
		KafkaBrokers:          getEnv("KAFKA_BROKERS", "localhost:9092"),
		KafkaTopicQueriesDone: getEnv("KAFKA_TOPIC_QUERIES", "queries.completed"),
	}

	cfg.QueriesPublisher = messaging.NewQueriesCompletedPublisher(cfg.KafkaBrokers, cfg.KafkaTopicQueriesDone)

	return cfg, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	valueStr := os.Getenv(key)
	if valueStr == "" {
		return defaultValue
	}
	value, err := strconv.Atoi(valueStr)
	if err != nil {
		return defaultValue
	}
	return value
}
