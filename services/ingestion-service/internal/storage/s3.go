package storage

import (
	"bytes"
	"context"
	"fmt"

	"github.com/aws/aws-sdk-go-v2/aws"
	awscfg "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/credentials"
	"github.com/aws/aws-sdk-go-v2/service/s3"
	"github.com/pageindex/ingestion/internal/config"
)

type S3Client struct {
	client *s3.Client
	bucket string
}

func NewS3Client(cfg *config.Config) (*S3Client, error) {
	// Load AWS configuration
	awsConfig, err := awscfg.LoadDefaultConfig(context.Background(),
		awscfg.WithRegion(cfg.AWSRegion),
		awscfg.WithCredentialsProvider(
			credentials.NewStaticCredentialsProvider(cfg.AWSAccessKeyID, cfg.AWSSecretAccessKey, ""),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load AWS config: %w", err)
	}

	// Create S3 client with optional endpoint override for local MinIO development
	s3Client := s3.NewFromConfig(awsConfig, func(o *s3.Options) {
		if cfg.S3EndpointURL != "" {
			o.BaseEndpoint = aws.String(cfg.S3EndpointURL)
			o.UsePathStyle = true
		}
	})

	return &S3Client{
		client: s3Client,
		bucket: cfg.S3BucketDocuments,
	}, nil
}

// UploadDocument uploads a PDF to S3 and returns the S3 URI
func (sc *S3Client) UploadDocument(ctx context.Context, key string, data []byte) (string, error) {
	_, err := sc.client.PutObject(ctx, &s3.PutObjectInput{
		Bucket: aws.String(sc.bucket),
		Key:    aws.String(key),
		Body:   bytes.NewReader(data),
	})
	if err != nil {
		return "", fmt.Errorf("failed to upload to S3: %w", err)
	}

	uri := fmt.Sprintf("s3://%s/%s", sc.bucket, key)
	return uri, nil
}

// GetPresignedURL generates a presigned URL for downloading the document
func (sc *S3Client) GetPresignedURL(ctx context.Context, key string, expirationSeconds int64) (string, error) {
	// TODO: Implement presigned URL generation
	// For now, return a simple S3 URL
	return fmt.Sprintf("s3://%s/%s", sc.bucket, key), nil
}
