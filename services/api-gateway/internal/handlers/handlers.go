package handlers

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"sync"
	"time"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/websocket/v2"
	"github.com/google/uuid"
	"github.com/pageindex/gateway/internal/clients"
	"github.com/pageindex/gateway/internal/config"
	"github.com/pageindex/gateway/internal/llm"
	"github.com/pageindex/gateway/internal/messaging"
	"github.com/rs/zerolog"
)

type QueryRequest struct {
	DocID    string `json:"doc_id"`
	Question string `json:"question"`
}

type QueryResponse struct {
	QueryID string `json:"query_id"`
	Status  string `json:"status"`
}

type FullQueryResponse struct {
	QueryID    string     `json:"query_id"`
	Status     string     `json:"status"`
	Answer     string     `json:"answer,omitempty"`
	References []string   `json:"references,omitempty"`
	Error      string     `json:"error,omitempty"`
	Timing     TimingInfo `json:"timing,omitempty"`
}

type TimingInfo struct {
	TotalMs      int64 `json:"total_ms"`
	TreeFetchMs  int64 `json:"tree_fetch_ms"`
	TreeSearchMs int64 `json:"tree_search_ms"`
	AnswerGenMs  int64 `json:"answer_gen_ms"`
}

var (
	queries = make(map[string]*FullQueryResponse)
	queryMu = sync.RWMutex{}
)

func publishQueryCompleted(cfg *config.Config, logger zerolog.Logger, msg messaging.QueryCompletedMessage) {
	if cfg.QueriesPublisher == nil {
		return
	}
	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		if err := cfg.QueriesPublisher.Publish(ctx, msg); err != nil {
			logger.Warn().Err(err).Str("query_id", msg.QueryID).Msg("failed to publish queries.completed")
			return
		}
		logger.Info().Str("query_id", msg.QueryID).Msg("published queries.completed for evaluation")
	}()
}

func HandleQuery(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		var req QueryRequest
		if err := c.BodyParser(&req); err != nil {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Invalid request body",
			})
		}

		if req.DocID == "" || req.Question == "" {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "doc_id and question are required",
			})
		}

		queryID := uuid.New().String()

		// Store query with pending status
		queryMu.Lock()
		queries[queryID] = &FullQueryResponse{
			QueryID: queryID,
			Status:  "processing",
		}
		queryMu.Unlock()

		// Process async
		go func() {
			processQuery(queryID, req, cfg, logger)
		}()

		return c.Status(fiber.StatusOK).JSON(QueryResponse{
			QueryID: queryID,
			Status:  "processing",
		})
	}
}

func GetQuery(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		queryID := c.Params("id")

		queryMu.RLock()
		result, exists := queries[queryID]
		queryMu.RUnlock()

		if !exists {
			return c.Status(fiber.StatusNotFound).JSON(fiber.Map{
				"error": "Query not found",
			})
		}

		return c.JSON(result)
	}
}

func ListDocuments(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		// Get documents from cache service
		resp, err := http.Get(cfg.CacheServiceURL + "/documents")
		if err != nil {
			logger.Error().Err(err).Msg("Failed to query cache service for documents")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error":     "Failed to list documents",
				"documents": []interface{}{},
			})
		}
		defer resp.Body.Close()

		// Read response
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			logger.Error().Err(err).Msg("Failed to read cache service response")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error":     "Failed to read document list",
				"documents": []interface{}{},
			})
		}

		logger.Debug().
			Int("status_code", resp.StatusCode).
			Int("body_size", len(body)).
			Msg("Document list retrieved from cache service")

		// Return the response as-is
		c.Set("Content-Type", "application/json")
		return c.Status(resp.StatusCode).Send(body)
	}
}

// GetCacheStats — forward cache /cache/stats (browser CORS).
func GetCacheStats(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		cacheClient := clients.NewCacheClient(cfg.CacheServiceURL)
		stats, err := cacheClient.GetStats(context.Background())
		if err != nil {
			logger.Error().Err(err).Msg("Failed to get cache stats")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to get cache stats",
			})
		}
		return c.JSON(stats)
	}
}

// GetEvaluationMetrics — forward evaluation /metrics.
func GetEvaluationMetrics(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		resp, err := http.Get(cfg.EvaluationServiceURL + "/metrics")
		if err != nil {
			logger.Error().Err(err).Msg("Failed to reach evaluation service /metrics")
			return c.Status(fiber.StatusBadGateway).JSON(fiber.Map{
				"error": "evaluation service unavailable",
			})
		}
		defer resp.Body.Close()
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			logger.Error().Err(err).Msg("Failed to read evaluation metrics response")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"error": "failed to read metrics"})
		}
		c.Set("Content-Type", "application/json")
		return c.Status(resp.StatusCode).Send(body)
	}
}

// ListEvaluationEvaluations — forward evaluation /evaluations.
func ListEvaluationEvaluations(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		limit := 10
		if q := c.Query("limit"); q != "" {
			if n, err := strconv.Atoi(q); err == nil && n > 0 && n <= 100 {
				limit = n
			}
		}
		url := fmt.Sprintf("%s/evaluations?limit=%d", cfg.EvaluationServiceURL, limit)
		resp, err := http.Get(url)
		if err != nil {
			logger.Error().Err(err).Msg("Failed to reach evaluation service /evaluations")
			return c.Status(fiber.StatusBadGateway).JSON(fiber.Map{
				"evaluations": []interface{}{},
				"error":       "evaluation service unavailable",
			})
		}
		defer resp.Body.Close()
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{"evaluations": []interface{}{}})
		}
		c.Set("Content-Type", "application/json")
		return c.Status(resp.StatusCode).Send(body)
	}
}

func GetDocument(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		docID := c.Params("id")

		cacheClient := clients.NewCacheClient(cfg.CacheServiceURL)
		tree, err := cacheClient.GetTree(context.Background(), docID)
		if err != nil {
			logger.Error().Err(err).Str("doc_id", docID).Msg("Failed to get document")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to get document",
			})
		}

		return c.JSON(fiber.Map{
			"doc_id":   docID,
			"metadata": tree,
		})
	}
}

func GetDocumentTree(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		docID := c.Params("id")

		cacheClient := clients.NewCacheClient(cfg.CacheServiceURL)
		tree, err := cacheClient.GetTree(context.Background(), docID)
		if err != nil {
			logger.Error().Err(err).Str("doc_id", docID).Msg("Failed to get tree")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to get tree",
			})
		}

		transformedTree := transformTreeStructure(tree)

		return c.JSON(transformedTree)
	}
}

// transformTreeStructure renames `nodes` -> `children` for the web UI.
func transformTreeStructure(tree map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})

	for k, v := range tree {
		if k == "nodes" {
			if nodesArr, ok := v.([]interface{}); ok {
				children := make([]map[string]interface{}, len(nodesArr))
				for i, node := range nodesArr {
					if nodeMap, ok := node.(map[string]interface{}); ok {
						children[i] = transformTreeStructure(nodeMap)
					}
				}
				result["children"] = children
			}
		} else {
			result[k] = v
		}
	}

	return result
}

func UploadDocument(cfg *config.Config, logger zerolog.Logger) fiber.Handler {
	return func(c *fiber.Ctx) error {
		contentType := c.Get("Content-Type")
		if contentType == "" {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Content-Type header is required",
			})
		}

		bodyBytes := c.Body()
		if len(bodyBytes) == 0 {
			return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
				"error": "Request body is empty",
			})
		}

		logger.Info().
			Str("url", cfg.IngestionServiceURL+"/documents/upload").
			Str("content_type", contentType).
			Int("body_size", len(bodyBytes)).
			Msg("Proxying upload request to ingestion service")

		req, err := http.NewRequest("POST", cfg.IngestionServiceURL+"/documents/upload", io.NopCloser(bytes.NewReader(bodyBytes)))
		if err != nil {
			logger.Error().Err(err).Msg("Failed to create proxy request")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to forward upload request",
			})
		}

		req.Header.Set("Content-Type", contentType)
		req.Header.Set("Content-Length", c.Get("Content-Length"))

		httpClient := &http.Client{}
		resp, err := httpClient.Do(req)
		if err != nil {
			logger.Error().Err(err).Msg("Failed to proxy request to ingestion service")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to forward upload request",
			})
		}
		defer resp.Body.Close()

		// Read response body
		respBody, err := io.ReadAll(resp.Body)
		if err != nil {
			logger.Error().Err(err).Msg("Failed to read proxy response")
			return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
				"error": "Failed to read upload response",
			})
		}

		logger.Info().
			Int("status_code", resp.StatusCode).
			Int("response_size", len(respBody)).
			Msg("Upload proxy response received")

		// Forward the response
		c.Set("Content-Type", "application/json")
		return c.Status(resp.StatusCode).Send(respBody)
	}
}

func HandleWebSocket(cfg *config.Config, logger zerolog.Logger) func(*websocket.Conn) {
	return func(ws *websocket.Conn) {
		defer ws.Close()

		for {
			var req QueryRequest
			if err := ws.ReadJSON(&req); err != nil {
				logger.Error().Err(err).Msg("WebSocket read error")
				break
			}

			if req.DocID == "" || req.Question == "" {
				ws.WriteJSON(fiber.Map{
					"type":  "error",
					"error": "doc_id and question are required",
				})
				continue
			}

			// Stream query processing
			go func() {
				streamQuery(req, cfg, logger, ws)
			}()
		}
	}
}

func processQuery(queryID string, req QueryRequest, cfg *config.Config, logger zerolog.Logger) {
	startTime := time.Now()
	treeStart := time.Now()
	cacheClient := clients.NewCacheClient(cfg.CacheServiceURL)
	tree, err := cacheClient.GetTree(context.Background(), req.DocID)
	if err != nil {
		logger.Error().Err(err).Str("doc_id", req.DocID).Msg("Failed to get tree")
		queryMu.Lock()
		queries[queryID].Status = "error"
		queries[queryID].Error = "Failed to retrieve document tree"
		queryMu.Unlock()
		return
	}
	treeFetchMs := time.Since(treeStart).Milliseconds()
	logger.Info().Int64("tree_fetch_ms", treeFetchMs).Msg("Tree fetched")
	treeSearchStart := time.Now()
	claudeClient := llm.NewClaudeClient(cfg.ClaudeAPIKey, cfg.ClaudeModel)
	nodeIDs, err := claudeClient.FindRelevantNodes(context.Background(), tree, req.Question)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to find relevant nodes")
		queryMu.Lock()
		queries[queryID].Status = "error"
		queries[queryID].Error = "Failed to search document"
		queryMu.Unlock()
		return
	}
	treeSearchMs := time.Since(treeSearchStart).Milliseconds()
	logger.Info().Int64("tree_search_ms", treeSearchMs).Int("nodes_found", len(nodeIDs)).Msg("Tree search completed")
	if len(nodeIDs) == 0 {
		fallbackNodeIDs := buildFallbackNodeIDs(tree)
		nodeIDs = fallbackNodeIDs
	}

	contextStart := time.Now()
	contextStr, missingNodes := extractContextFromNodes(tree, nodeIDs)
	contextMs := time.Since(contextStart).Milliseconds()
	logger.Info().
		Str("query_id", queryID).
		Str("doc_id", req.DocID).
		Int("node_ids_len", len(nodeIDs)).
		Int("context_length", len(contextStr)).
		Int("missing_nodes", missingNodes).
		Int64("context_extract_ms", contextMs).
		Msg("query context extraction complete")

	answerStart := time.Now()
	answer, err := claudeClient.GenerateAnswer(context.Background(), req.Question, contextStr)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to generate answer")
		queryMu.Lock()
		queries[queryID].Status = "error"
		queries[queryID].Error = "Failed to generate answer"
		queryMu.Unlock()
		return
	}
	answerGenMs := time.Since(answerStart).Milliseconds()

	// Update query with result
	queryMu.Lock()
	queries[queryID] = &FullQueryResponse{
		QueryID:    queryID,
		Status:     "completed",
		Answer:     answer,
		References: nodeIDs,
		Timing: TimingInfo{
			TotalMs:      time.Since(startTime).Milliseconds(),
			TreeFetchMs:  treeFetchMs,
			TreeSearchMs: treeSearchMs,
			AnswerGenMs:  answerGenMs,
		},
	}
	queryMu.Unlock()

	logger.Info().Str("query_id", queryID).Str("doc_id", req.DocID).Msg("Query processed successfully")

	publishQueryCompleted(cfg, logger, messaging.QueryCompletedMessage{
		QueryID:   queryID,
		DocID:     req.DocID,
		Question:  req.Question,
		Answer:    answer,
		TreePath:  nodeIDs,
		LatencyMs: time.Since(startTime).Milliseconds(),
	})
}

func streamQuery(req QueryRequest, cfg *config.Config, logger zerolog.Logger, ws *websocket.Conn) {
	startTime := time.Now()
	streamQueryID := uuid.New().String()

	// Send status update
	ws.WriteJSON(fiber.Map{
		"type":    "status",
		"message": "Fetching document tree...",
	})

	// Get tree
	treeStart := time.Now()
	cacheClient := clients.NewCacheClient(cfg.CacheServiceURL)
	tree, err := cacheClient.GetTree(context.Background(), req.DocID)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to get tree")
		ws.WriteJSON(fiber.Map{
			"type":  "error",
			"error": "Failed to retrieve document",
		})
		ws.WriteJSON(fiber.Map{
			"type": "done",
		})
		return
	}
	logger.Info().Int64("tree_fetch_ms", time.Since(treeStart).Milliseconds()).Msg("Tree fetched (streaming)")

	ws.WriteJSON(fiber.Map{
		"type":    "status",
		"message": "Searching document structure...",
	})

	// Find relevant nodes
	searchStart := time.Now()
	claudeClient := llm.NewClaudeClient(cfg.ClaudeAPIKey, cfg.ClaudeModel)
	nodeIDs, err := claudeClient.FindRelevantNodes(context.Background(), tree, req.Question)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to find relevant nodes")
		ws.WriteJSON(fiber.Map{
			"type":  "error",
			"error": "Failed to search document",
		})
		ws.WriteJSON(fiber.Map{
			"type": "done",
		})
		return
	}
	logger.Info().Int64("search_ms", time.Since(searchStart).Milliseconds()).Int("nodes_found", len(nodeIDs)).Msg("Search completed (streaming)")

	ws.WriteJSON(fiber.Map{
		"type":        "progress",
		"nodes_found": len(nodeIDs),
	})

	// Extract context and generate answer
	contextStart := time.Now()
	contextStr, missingNodes := extractContextFromNodes(tree, nodeIDs)
	logger.Info().
		Str("doc_id", req.DocID).
		Int("node_ids_len", len(nodeIDs)).
		Int("context_length", len(contextStr)).
		Int("missing_nodes", missingNodes).
		Int64("context_extract_ms", time.Since(contextStart).Milliseconds()).
		Msg("query context extraction complete (streaming)")

	ws.WriteJSON(fiber.Map{
		"type":    "status",
		"message": "Generating answer...",
	})

	answerStart := time.Now()
	answer, err := claudeClient.GenerateAnswer(context.Background(), req.Question, contextStr)
	if err != nil {
		logger.Error().Err(err).Msg("Failed to generate answer")
		ws.WriteJSON(fiber.Map{
			"type":  "error",
			"error": "Failed to generate answer",
		})
		ws.WriteJSON(fiber.Map{
			"type": "done",
		})
		return
	}
	logger.Info().Int64("answer_gen_ms", time.Since(answerStart).Milliseconds()).Int64("total_ms", time.Since(startTime).Milliseconds()).Msg("Answer generated (streaming)")

	// Send complete response
	ws.WriteJSON(fiber.Map{
		"type":       "answer",
		"content":    answer,
		"references": nodeIDs,
	})

	// Send done message - client will close connection
	ws.WriteJSON(fiber.Map{
		"type": "done",
	})

	publishQueryCompleted(cfg, logger, messaging.QueryCompletedMessage{
		QueryID:   streamQueryID,
		DocID:     req.DocID,
		Question:  req.Question,
		Answer:    answer,
		TreePath:  nodeIDs,
		LatencyMs: time.Since(startTime).Milliseconds(),
	})
}

// extractContextFromNodes joins title/summary/text for each node_id (missing IDs counted).
func extractContextFromNodes(tree map[string]interface{}, nodeIDs []string) (string, int) {
	nodeIndex := make(map[string]map[string]interface{})
	indexNodes(tree, nodeIndex)
	contextParts := []string{}
	missingNodeCount := 0
	for _, nodeID := range nodeIDs {
		if node, found := nodeIndex[nodeID]; found {
			if title, exists := node["title"].(string); exists && title != "" {
				contextParts = append(contextParts, "Section: "+title)
			}
			if summary, exists := node["summary"].(string); exists && summary != "" {
				contextParts = append(contextParts, summary)
			}
			if text, exists := node["text"].(string); exists && text != "" {
				contextParts = append(contextParts, text)
			}
		} else {
			missingNodeCount++
		}
	}

	return joinStrings(contextParts, "\n\n"), missingNodeCount
}

func buildFallbackNodeIDs(tree map[string]interface{}) []string {
	fallback := []string{}

	if rootID, ok := tree["node_id"].(string); ok && rootID != "" {
		fallback = append(fallback, rootID)
	}

	if nodes, ok := tree["nodes"].([]interface{}); ok {
		for _, n := range nodes {
			if node, ok := n.(map[string]interface{}); ok {
				if nodeID, ok := node["node_id"].(string); ok && nodeID != "" {
					fallback = append(fallback, nodeID)
				}
			}
			if len(fallback) >= 3 {
				break
			}
		}
	}

	return fallback
}

func indexNodes(tree map[string]interface{}, index map[string]map[string]interface{}) {
	if nodeID, ok := tree["node_id"].(string); ok {
		index[nodeID] = tree
	}

	if nodes, ok := tree["nodes"].([]interface{}); ok {
		for _, n := range nodes {
			if node, ok := n.(map[string]interface{}); ok {
				indexNodes(node, index)
			}
		}
	}
}

func joinStrings(strs []string, sep string) string {
	result := ""
	for i, s := range strs {
		if i > 0 {
			result += sep
		}
		result += s
	}
	return result
}
