package messaging

import (
	"context"
	"encoding/json"
	"strings"
	"time"

	"github.com/segmentio/kafka-go"
)

// QueryCompletedMessage matches the evaluation-service consumer and Phase 6 schema.
type QueryCompletedMessage struct {
	QueryID   string   `json:"query_id"`
	DocID     string   `json:"doc_id"`
	Question  string   `json:"question"`
	Answer    string   `json:"answer"`
	TreePath  []string `json:"tree_path"`
	LatencyMs int64    `json:"latency_ms"`
	Timestamp string   `json:"timestamp"`
}

// QueriesCompletedPublisher sends completed Q&A events for LLM-as-judge evaluation.
type QueriesCompletedPublisher struct {
	w *kafka.Writer
}

func splitBrokers(csv string) []string {
	if strings.TrimSpace(csv) == "" {
		return nil
	}
	var out []string
	for _, p := range strings.Split(csv, ",") {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

// NewQueriesCompletedPublisher returns nil when brokersCSV is empty (publishing disabled).
func NewQueriesCompletedPublisher(brokersCSV, topic string) *QueriesCompletedPublisher {
	brokers := splitBrokers(brokersCSV)
	if len(brokers) == 0 || strings.TrimSpace(topic) == "" {
		return nil
	}
	return &QueriesCompletedPublisher{
		w: kafka.NewWriter(kafka.WriterConfig{
			Brokers:      brokers,
			Topic:        topic,
			Balancer:     &kafka.LeastBytes{},
			RequiredAcks: int(kafka.RequireOne),
			Async:        false,
		}),
	}
}

// Close releases the writer.
func (p *QueriesCompletedPublisher) Close() error {
	if p == nil || p.w == nil {
		return nil
	}
	return p.w.Close()
}

// Publish sends one message; safe to call with nil receiver.
func (p *QueriesCompletedPublisher) Publish(ctx context.Context, msg QueryCompletedMessage) error {
	if p == nil || p.w == nil {
		return nil
	}
	if msg.Timestamp == "" {
		msg.Timestamp = time.Now().UTC().Format(time.RFC3339)
	}
	b, err := json.Marshal(msg)
	if err != nil {
		return err
	}
	return p.w.WriteMessages(ctx, kafka.Message{
		Key:   []byte(msg.QueryID),
		Value: b,
	})
}
