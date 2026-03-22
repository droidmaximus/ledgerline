package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
	"github.com/joho/godotenv"
	"github.com/pageindex/gateway/internal/config"
	"github.com/pageindex/gateway/internal/handlers"
	"github.com/rs/zerolog"
)

func init() {
	// Load .env from common repo locations (service may run from subdir).
	// godotenv.Load stops at first missing file, so try sequentially.
	var err error
	for _, p := range []string{".env", "../../.env", "../../../.env"} {
		if _, statErr := os.Stat(p); statErr == nil {
			err = godotenv.Overload(p)
			if err == nil {
				break
			}
		}
	}
	log.SetOutput(os.Stderr)
}

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	logger := zerolog.New(os.Stderr).With().Timestamp().Logger()

	// Create Fiber app (BodyLimit must exceed max PDF upload; default 4MB breaks ~4MB+ files)
	app := fiber.New(fiber.Config{
		AppName:      "API Gateway",
		ServerHeader: "Fiber",
		BodyLimit:    55 * 1024 * 1024, // 55 MiB — aligns with ingestion MAX_UPLOAD_SIZE_MB default 50
	})

	// CORS middleware
	app.Use(func(c *fiber.Ctx) error {
		c.Set("Access-Control-Allow-Origin", "*")
		c.Set("Access-Control-Allow-Methods", "GET,POST,HEAD,PUT,DELETE,PATCH,OPTIONS")
		c.Set("Access-Control-Allow-Headers", "Content-Type,Authorization")

		// Handle preflight requests
		if c.Method() == "OPTIONS" {
			return c.SendStatus(200)
		}
		return c.Next()
	})

	// Health endpoints
	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status":  "ok",
			"service": "api-gateway",
		})
	})

	// Register routes
	app.Post("/query", handlers.HandleQuery(cfg, logger))
	app.Get("/query/:id", handlers.GetQuery(cfg, logger))
	app.Post("/documents/upload", handlers.UploadDocument(cfg, logger))
	app.Get("/documents", handlers.ListDocuments(cfg, logger))
	app.Get("/documents/:id", handlers.GetDocument(cfg, logger))
	app.Get("/documents/:id/tree", handlers.GetDocumentTree(cfg, logger))
	app.Get("/cache/stats", handlers.GetCacheStats(cfg, logger))
	app.Get("/evaluation/metrics", handlers.GetEvaluationMetrics(cfg, logger))
	app.Get("/evaluation/evaluations", handlers.ListEvaluationEvaluations(cfg, logger))

	// WebSocket route
	app.Use("/ws", func(c *fiber.Ctx) error {
		if websocket.IsWebSocketUpgrade(c) {
			return c.Next()
		}
		return fiber.ErrUpgradeRequired
	})
	app.Get("/ws", websocket.New(handlers.HandleWebSocket(cfg, logger)))

	// Start server
	go func() {
		server := fmt.Sprintf(":%d", cfg.Port)
		logger.Info().Str("addr", server).Msg("Starting API Gateway")
		if err := app.Listen(server); err != nil {
			logger.Error().Err(err).Msg("Server error")
		}
	}()

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	logger.Info().Msg("Shutdown signal received")

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := app.ShutdownWithContext(shutdownCtx); err != nil {
		logger.Error().Err(err).Msg("Error during graceful shutdown")
	}

	if cfg.QueriesPublisher != nil {
		if err := cfg.QueriesPublisher.Close(); err != nil {
			logger.Warn().Err(err).Msg("Kafka queries.completed writer close")
		}
	}

	logger.Info().Msg("API Gateway stopped")
}
