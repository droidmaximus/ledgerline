package handlers

import (
	"context"
	"io"
	"strconv"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"
	"github.com/pageindex/ingestion/internal/config"
	"github.com/pageindex/ingestion/internal/messaging"
	"github.com/pageindex/ingestion/internal/storage"
	"github.com/rs/zerolog"
)

func RegisterRoutes(app *fiber.App, s3Client *storage.S3Client, producer *messaging.KafkaProducer, cfg *config.Config, logger zerolog.Logger) {
	app.Post("/documents/upload", handleUpload(s3Client, producer, cfg, logger))
}

func handleUpload(s3Client *storage.S3Client, producer *messaging.KafkaProducer, cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		// Get file from form
		file, err := c.FormFile("file")
		if err != nil {
			logger.Error().Err(err).Msg("failed to get file from form")
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "No file provided",
			})
		}

		// Validate file size
		if file.Size > cfg.MaxFileSize {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "File size exceeds maximum allowed size",
			})
		}

		// Read file
		src, err := file.Open()
		if err != nil {
			logger.Error().Err(err).Msg("failed to open file")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to read file",
			})
		}
		defer src.Close()

		// Generate document ID
		docID := uuid.New().String()

		// Upload to S3
		fileBytes, err := io.ReadAll(src)
		if err != nil {
			logger.Error().Err(err).Msg("failed to read file bytes")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to process file",
			})
		}

		s3URI, err := s3Client.UploadDocument(c.Context(), docID+".pdf", fileBytes)
		if err != nil {
			logger.Error().Err(err).Str("doc_id", docID).Msg("failed to upload to S3")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to upload file",
			})
		}

		// Publish Kafka event
		msg := messaging.DocumentIngestedMessage{
			DocID:     docID,
			S3URI:     s3URI,
			Filename:  file.Filename,
			Timestamp: time.Now(),
			Metadata: map[string]string{
				"size": strconv.FormatInt(file.Size, 10),
			},
		}

		if err := producer.PublishDocumentIngested(context.Background(), msg); err != nil {
			logger.Error().Err(err).Str("doc_id", docID).Msg("failed to publish Kafka event")
			// Continue anyway - file is uploaded
		}

		logger.Info().Str("doc_id", docID).Str("filename", file.Filename).Msg("Document uploaded successfully")

		return c.Status(fiber.StatusOK).JSON(fiber.Map{
			"doc_id":  docID,
			"status":  "uploaded",
			"message": "Document uploaded successfully",
		})
	}
}
