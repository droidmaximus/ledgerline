package llm

import (
	"encoding/json"
	"fmt"
)

// nodeOutline is a compact view for node selection (no full nested document or long text).
type nodeOutline struct {
	NodeID     string `json:"node_id"`
	Title      string `json:"title"`
	Summary    string `json:"summary,omitempty"`
	Snippet    string `json:"snippet,omitempty"`
	StartIndex int    `json:"start_index,omitempty"`
	EndIndex   int    `json:"end_index,omitempty"`
}

// CompactTreeOutline flattens the tree into a list of {node_id, title, summary, page range}.
// Summaries are truncated to keep prompts small; full text stays server-side for answer generation.
func CompactTreeOutline(tree map[string]interface{}, summaryMaxRunes int) ([]byte, error) {
	if summaryMaxRunes <= 0 {
		summaryMaxRunes = 400
	}
	snippetMaxRunes := 800
	var out []nodeOutline

	var walk func(m map[string]interface{})
	walk = func(m map[string]interface{}) {
		nid, _ := m["node_id"].(string)
		title, _ := m["title"].(string)
		summary, _ := m["summary"].(string)
		text, _ := m["text"].(string)
		if len([]rune(summary)) > summaryMaxRunes {
			r := []rune(summary)
			summary = string(r[:summaryMaxRunes]) + "…"
		}
		if len([]rune(text)) > snippetMaxRunes {
			r := []rune(text)
			text = string(r[:snippetMaxRunes]) + "…"
		}
		si, ei := 0, 0
		if v, ok := m["start_index"].(float64); ok {
			si = int(v)
		}
		if v, ok := m["end_index"].(float64); ok {
			ei = int(v)
		}
		if nid != "" || title != "" {
			out = append(out, nodeOutline{
				NodeID:     nid,
				Title:      title,
				Summary:    summary,
				Snippet:    text,
				StartIndex: si,
				EndIndex:   ei,
			})
		}
		if nodes, ok := m["nodes"].([]interface{}); ok {
			for _, ch := range nodes {
				if cm, ok := ch.(map[string]interface{}); ok {
					walk(cm)
				}
			}
		}
	}

	walk(tree)
	if len(out) == 0 {
		return nil, fmt.Errorf("empty tree outline")
	}
	return json.Marshal(out)
}
