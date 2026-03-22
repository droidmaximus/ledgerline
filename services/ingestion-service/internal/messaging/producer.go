package messaging

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/segmentio/kafka-go"
)

type KafkaProducer struct {
	writer *kafka.Writer
}

type DocumentIngestedMessage struct {
	DocID     string            `json:"doc_id"`
	S3URI     string            `json:"s3_uri"`
	Filename  string            `json:"filename"`
	Timestamp time.Time         `json:"timestamp"`
	Metadata  map[string]string `json:"metadata"`
}

func NewKafkaProducer(brokers []string) (*KafkaProducer, error) {
	writer := kafka.NewWriter(kafka.WriterConfig{
		Brokers: brokers,
		Topic:   "documents.ingested", // Will be overridden per message
	})

	return &KafkaProducer{
		writer: writer,
	}, nil
}

func (kp *KafkaProducer) PublishDocumentIngested(ctx context.Context, msg DocumentIngestedMessage) error {
	msgBytes, err := json.Marshal(msg)
	if err != nil {
		return fmt.Errorf("failed to marshal message: %w", err)
	}

	err = kp.writer.WriteMessages(ctx, kafka.Message{
		Key:   []byte(msg.DocID),
		Value: msgBytes,
	})
	if err != nil {
		return fmt.Errorf("failed to publish message: %w", err)
	}

	return nil
}

func (kp *KafkaProducer) Close() error {
	return kp.writer.Close()
}
