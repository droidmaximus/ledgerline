package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
)

type TreeSearchRequest struct {
	Tree  map[string]interface{} `json:"tree"`
	Query string                 `json:"query"`
}

type TreeSearchResponse struct {
	Reasoning string   `json:"reasoning"`
	NodeIDs   []string `json:"node_ids"`
}

type ClaudeClient struct {
	apiKey string
	model  string
}

// Claude API request/response types
type ClaudeMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type ClaudeRequest struct {
	Model     string          `json:"model"`
	MaxTokens int             `json:"max_tokens"`
	Messages  []ClaudeMessage `json:"messages"`
}

type ClaudeResponse struct {
	Content []struct {
		Type string `json:"type"`
		Text string `json:"text"`
	} `json:"content"`
	StopReason string `json:"stop_reason"`
}

func NewClaudeClient(apiKey, model string) *ClaudeClient {
	if model == "" {
		model = "claude-haiku-4-5-20251001" // Default to Haiku (fast and cost-effective)
	}
	return &ClaudeClient{
		apiKey: apiKey,
		model:  model,
	}
}

// stripMarkdownJSON removes markdown code blocks (```json...```) and returns the JSON content
func stripMarkdownJSON(response string) string {
	// Pattern to match ```json ... ``` or ``` ... ```
	pattern := regexp.MustCompile("(?s)^```(?:json)?\\s*(.+?)\\s*```$")
	if matches := pattern.FindStringSubmatch(strings.TrimSpace(response)); matches != nil {
		return strings.TrimSpace(matches[1])
	}
	return response
}

func (cc *ClaudeClient) FindRelevantNodes(ctx context.Context, tree map[string]interface{}, query string) ([]string, error) {
	if cc.apiKey == "" {
		// Mock response for testing without Claude key
		return []string{"0001", "0003"}, nil
	}

	outlineJSON, err := CompactTreeOutline(tree, 400)
	if err != nil {
		outlineJSON, err = json.Marshal(tree)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal tree: %w", err)
		}
	}

	nodeIDs, err := cc.findRelevantNodesWithPrompt(ctx, string(outlineJSON), query, false)
	if err != nil {
		nodeIDs, err = cc.findRelevantNodesWithPrompt(ctx, string(outlineJSON), query, true)
		if err != nil {
			return nil, err
		}
	}
	return nodeIDs, nil
}

func (cc *ClaudeClient) findRelevantNodesWithPrompt(ctx context.Context, outlineJSON string, query string, strictRetry bool) ([]string, error) {
	prompt := fmt.Sprintf(`You are given a compact list of document sections. Each item has node_id, title, summary, an optional page range (start_index, end_index), and a short content snippet (snippet).
Pick the node_ids (usually 2–6) most likely to contain information to answer the query. Prefer sections whose title or summary matches financial metrics, tables, or the topic asked.

Sections JSON:
%s

Query: %s

Return ONLY valid JSON in this exact shape (no markdown fences, no other text):
{"reasoning":"brief reason","node_ids":["0001","0002"]}`, outlineJSON, query)
	if strictRetry {
		prompt += "\n\nReturn ONLY a raw JSON object. No markdown code blocks. No commentary before or after the JSON."
	}

	content, err := cc.callClaudeAPI(ctx, prompt, 512)
	if err != nil {
		return nil, err
	}

	cleanedContent := stripMarkdownJSON(strings.TrimSpace(content))
	var result TreeSearchResponse
	if err := json.Unmarshal([]byte(cleanedContent), &result); err != nil {
		return nil, fmt.Errorf("failed to parse LLM response: %w", err)
	}

	return result.NodeIDs, nil
}

func (cc *ClaudeClient) GenerateAnswer(ctx context.Context, query string, docContext string) (string, error) {
	if cc.apiKey == "" {
		// Mock response for testing
		return "This is a sample answer generated without Claude API key.", nil
	}

	docContext = strings.TrimSpace(docContext)
	var prompt string
	if docContext == "" {
		prompt = fmt.Sprintf(`No document passages were retrieved for this question.

Respond with exactly one sentence:
No relevant passages were retrieved from the document structure.

Question: %s`, query)
	} else {
		prompt = fmt.Sprintf(`You are a financial document assistant. Answer using ONLY the context below.

Rules:
- Use specific numbers, amounts, and phrases from the context when they apply.
- Do not say you cannot answer, do not claim insufficient context, and do not refuse when the context contains relevant information.
- If the context is ambiguous, state what the context says and cite the section wording.
- If the context truly does not address the question, say so in one sentence without fabricating figures.

Context:
%s

Question: %s

Answer:`, docContext, query)
	}

	answer, err := cc.callClaudeAPI(ctx, prompt, 1024)
	if err != nil {
		return "", err
	}

	return answer, nil
}

func (cc *ClaudeClient) callClaudeAPI(ctx context.Context, prompt string, maxTokens int) (string, error) {
	// Claude API endpoint
	url := "https://api.anthropic.com/v1/messages"

	// Prepare request body
	requestBody := ClaudeRequest{
		Model:     cc.model,
		MaxTokens: maxTokens,
		Messages: []ClaudeMessage{
			{
				Role:    "user",
				Content: prompt,
			},
		},
	}

	bodyBytes, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(bodyBytes))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("x-api-key", cc.apiKey)
	req.Header.Set("anthropic-version", "2023-06-01")

	// Use timeout for faster failures
	client := &http.Client{
		Timeout: 20 * 1000000000, // 20 seconds
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("failed to call Claude API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("Claude API error (status %d): %s", resp.StatusCode, string(body))
	}

	var result ClaudeResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", fmt.Errorf("failed to decode response: %w", err)
	}

	if len(result.Content) == 0 {
		return "", fmt.Errorf("no content in Claude response")
	}

	return result.Content[0].Text, nil
}
