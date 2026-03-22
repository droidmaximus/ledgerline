package handlers

import (
	"strings"
	"testing"
)

func TestExtractContextFromNodes_IncludesTextAndSummary(t *testing.T) {
	tree := map[string]interface{}{
		"node_id": "0001",
		"title":   "Root",
		"summary": "S",
		"nodes": []interface{}{
			map[string]interface{}{
				"node_id": "0002",
				"title":   "Fin",
				"summary": "Revenue 100",
				"text":    "Detailed line with 100 USD",
			},
		},
	}
	ctx, missing := extractContextFromNodes(tree, []string{"0002"})
	if ctx == "" {
		t.Fatal("expected non-empty context")
	}
	if missing != 0 {
		t.Fatalf("expected missing=0, got %d", missing)
	}
	if !strings.Contains(ctx, "Revenue 100") {
		t.Fatalf("expected summary in context, got %q", ctx)
	}
	if !strings.Contains(ctx, "Detailed line") {
		t.Fatalf("expected text in context, got %q", ctx)
	}
}

func TestExtractContextFromNodes_MissingID(t *testing.T) {
	tree := map[string]interface{}{
		"node_id": "0001",
		"title":   "Root",
		"summary": "Root summary",
		"nodes": []interface{}{
			map[string]interface{}{
				"node_id": "0002",
				"title":   "Leaf",
				"summary": "Only this node exists",
			},
		},
	}
	ctx, missing := extractContextFromNodes(tree, []string{"9999", "0002"})
	if missing != 1 {
		t.Fatalf("expected missing=1 for unknown id, got %d", missing)
	}
	if !strings.Contains(ctx, "Only this node exists") {
		t.Fatalf("expected partial context from node 0002, got %q", ctx)
	}
}

func TestExtractContextFromNodes_EmptyNodeIDs(t *testing.T) {
	tree := map[string]interface{}{
		"node_id": "0001",
		"title":   "Root",
		"summary": "S",
	}
	ctx, missing := extractContextFromNodes(tree, []string{})
	if ctx != "" {
		t.Fatalf("expected empty context, got %q", ctx)
	}
	if missing != 0 {
		t.Fatalf("expected missing=0 with no ids, got %d", missing)
	}
}
