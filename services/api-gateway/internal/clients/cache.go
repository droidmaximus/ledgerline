package clients

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/go-resty/resty/v2"
)

type CacheClient struct {
	client  *resty.Client
	baseURL string
}

func NewCacheClient(baseURL string) *CacheClient {
	return &CacheClient{
		client:  resty.New(),
		baseURL: baseURL,
	}
}

func (cc *CacheClient) GetTree(ctx context.Context, docID string) (map[string]interface{}, error) {
	var tree map[string]interface{}

	resp, err := cc.client.R().
		SetContext(ctx).
		SetResult(&tree).
		Get(fmt.Sprintf("%s/cache/tree/%s", cc.baseURL, docID))

	if err != nil {
		return nil, fmt.Errorf("failed to get tree: %w", err)
	}

	if resp.StatusCode() != 200 {
		return nil, fmt.Errorf("cache service returned status %d", resp.StatusCode())
	}

	// Parse response properly
	if err := json.Unmarshal(resp.Body(), &tree); err != nil {
		return nil, fmt.Errorf("failed to parse tree: %w", err)
	}

	return tree, nil
}

func (cc *CacheClient) GetStats(ctx context.Context) (map[string]interface{}, error) {
	var stats map[string]interface{}

	resp, err := cc.client.R().
		SetContext(ctx).
		SetResult(&stats).
		Get(fmt.Sprintf("%s/cache/stats", cc.baseURL))

	if err != nil {
		return nil, fmt.Errorf("failed to get cache stats: %w", err)
	}

	if resp.StatusCode() != 200 {
		return nil, fmt.Errorf("cache service returned status %d", resp.StatusCode())
	}

	return stats, nil
}
