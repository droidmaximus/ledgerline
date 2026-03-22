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
	"github.com/joho/godotenv"
	"github.com/pageindex/ingestion/internal/config"
	"github.com/pageindex/ingestion/internal/handlers"
	"github.com/pageindex/ingestion/internal/messaging"
	"github.com/pageindex/ingestion/internal/storage"
	"github.com/rs/zerolog"
)

func init() {
	// Load .env file if it exists
	_ = godotenv.Load(".env", "../../.env", "../../../.env")

	// Set up logging
	log.SetOutput(os.Stderr)
}

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	logger := zerolog.New(os.Stderr).With().Timestamp().Logger()

	// Initialize S3 client
	s3Client, err := storage.NewS3Client(cfg)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to initialize S3 client")
	}
	logger.Info().Msg("S3 client initialized")

	// Initialize Kafka producer
	producer, err := messaging.NewKafkaProducer(cfg.KafkaBrokers)
	if err != nil {
		logger.Fatal().Err(err).Msg("Failed to initialize Kafka producer")
	}
	defer producer.Close()
	logger.Info().Msg("Kafka producer initialized")

	// Create Fiber app (default BodyLimit 4MB rejects uploads near 4MB+; match MAX_UPLOAD_SIZE_MB)
	app := fiber.New(fiber.Config{
		AppName:      "Ingestion Service",
		ServerHeader: "Fiber",
		BodyLimit:    55 * 1024 * 1024, // 55 MiB — align with config MAX_UPLOAD_SIZE_MB default 50
	})

	// Middleware
	app.Use(func(c *fiber.Ctx) error {
		c.Set("X-Custom-Header", "InsertedByMiddleware")
		return c.Next()
	})

	// Routes
	handlers.RegisterRoutes(app, s3Client, producer, cfg, logger)

	// Health endpoint
	app.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{
			"status":  "ok",
			"service": "ingestion",
		})
	})

	// Readiness endpoint
	app.Get("/ready", func(c *fiber.Ctx) error {
		// TODO: Add actual readiness checks for S3 and Kafka
		return c.JSON(fiber.Map{
			"ready": true,
		})
	})

	// Start server in a goroutine
	go func() {
		server := fmt.Sprintf(":%d", cfg.Port)
		logger.Info().Str("addr", server).Msg("Starting ingestion service")
		if err := app.Listen(server); err != nil {
			logger.Error().Err(err).Msg("Server error")
		}
	}()

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Wait for interrupt signal
	sig := <-sigChan
	logger.Info().Str("signal", sig.String()).Msg("Received shutdown signal")

	// Shutdown with timeout
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := app.ShutdownWithContext(shutdownCtx); err != nil {
		logger.Error().Err(err).Msg("Error during graceful shutdown")
	}

	logger.Info().Msg("Ingestion service stopped")
}
