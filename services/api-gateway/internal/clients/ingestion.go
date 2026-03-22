package clients

import (
	"context"
	"fmt"
	"io"

	"github.com/go-resty/resty/v2"
)

type IngestionClient struct {
	client  *resty.Client
	baseURL string
}

func NewIngestionClient(baseURL string) *IngestionClient {
	return &IngestionClient{
		client:  resty.New(),
		baseURL: baseURL,
	}
}

func (ic *IngestionClient) UploadDocument(ctx context.Context, filename string, file io.Reader) (map[string]interface{}, error) {
	var response map[string]interface{}

	resp, err := ic.client.R().
		SetContext(ctx).
		SetFileReader("file", filename, file).
		SetResult(&response).
		Post(fmt.Sprintf("%s/documents/upload", ic.baseURL))

	if err != nil {
		return nil, fmt.Errorf("failed to upload document: %w", err)
	}

	if resp.StatusCode() < 200 || resp.StatusCode() >= 300 {
		return nil, fmt.Errorf("ingestion service returned status %d: %s", resp.StatusCode(), resp.String())
	}

	// Parse response
	if err := resp.Result().(*map[string]interface{}); err != nil {
		response = *resp.Result().(*map[string]interface{})
	}

	return response, nil
}
